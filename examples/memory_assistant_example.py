"""Example testing complex memory relationships and entity tracking."""

import asyncio
from pathlib import Path
from dotenv import load_dotenv
import os
import time
from typing import List, Dict
from collections import defaultdict
from colorama import init as colorama_init, Fore, Style
from mem0 import Memory
from mem0.llms.anthropic import AnthropicLLM
from openai import OpenAI

from autogen_core.base import CancellationToken
from autogen_agentchat.messages import TextMessage
from autogen_core.components.models import UserMessage
from autogen_mem0.core.config.manager import ConfigManager
from autogen_mem0.core.agents import AgentConfig, MemoryEnabledAssistant
from autogen_mem0.core.messaging import TextMessage as AutogenTextMessage
from autogen_mem0.models import AnthropicChatCompletionClient
from autogen_mem0.models._model_info import resolve_model, calculate_cost, get_model_pricing
from autogen_core.components.models import FunctionExecutionResultMessage
from autogen_mem0.core.adapters import MessageAdapterFactory
import logging

# Initialize colorama
colorama_init()

# Configure custom logger
class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors and emojis to log messages"""
    
    # Color codes
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    
    # Emojis for different contexts
    EMOJIS = {
        'MEMORY': '🧠',
        'COST': '💰',
        'ERROR': '❌',
        'QUESTION': '❓',
        'STATS': '📊',
        'SUCCESS': '✨',
        'CONFIG': '⚙️',
        'OPTIMIZE': '🔧',
        'API': '🌐',
        'VECTOR': '📦',
        'EMBED': '🔢'
    }
    
    def format(self, record):
        # Get the message
        msg = record.getMessage()
        
        # Add emoji based on context tag
        for tag, emoji in self.EMOJIS.items():
            if tag in msg:
                msg = f"{emoji} {msg}"
                break
        
        # Add color based on context tag
        if "MEMORY" in msg:
            msg = f"{self.CYAN}{msg}{self.RESET}"
        elif "COST" in msg:
            msg = f"{self.YELLOW}{msg}{self.RESET}"
        elif "ERROR" in msg:
            msg = f"{self.RED}{msg}{self.RESET}"
        elif "QUESTION" in msg:
            msg = f"{self.MAGENTA}{msg}{self.RESET}"
        elif "STATS" in msg:
            msg = f"{self.BLUE}{msg}{self.RESET}"
        elif "SUCCESS" in msg:
            msg = f"{self.GREEN}{msg}{self.RESET}"
        elif "CONFIG" in msg:
            msg = f"{self.CYAN}{msg}{self.RESET}"
        elif "OPTIMIZE" in msg:
            msg = f"{self.GREEN}{msg}{self.RESET}"
        elif "API" in msg:
            msg = f"{self.BLUE}{msg}{self.RESET}"
        elif "VECTOR" in msg:
            msg = f"{self.MAGENTA}{msg}{self.RESET}"
        elif "EMBED" in msg:
            msg = f"{self.YELLOW}{msg}{self.RESET}"
            
        record.msg = msg
        return super().format(record)

# Set up logger
logger = logging.getLogger('memory_assistant')
logger.setLevel(logging.INFO)

# Remove any existing handlers
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Console handler with our custom formatter
console_handler = logging.StreamHandler()
console_handler.setFormatter(ColoredFormatter('%(message)s'))
logger.addHandler(console_handler)

class ModelUsageTracker:
    """Tracks usage for a specific model."""
    def __init__(self, model_name: str, model_type: str):
        self.model_name = model_name
        self.model_type = model_type  # main_llm, fact_llm, embeddings
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_cost = 0.0
        try:
            self.pricing = get_model_pricing(model_name)
        except:
            # Default pricing for OpenAI models (per million tokens)
            if model_name == "text-embedding-3-small":
                self.pricing = {
                    "input_price_per_mtok": 0.02,
                    "output_price_per_mtok": 0.02
                }
            elif "gpt-4" in model_name:
                self.pricing = {
                    "input_price_per_mtok": 10.0,
                    "output_price_per_mtok": 30.0
                }
            elif "gpt-3.5" in model_name:
                self.pricing = {
                    "input_price_per_mtok": 0.5,
                    "output_price_per_mtok": 1.5
                }
            else:
                self.pricing = {
                    "input_price_per_mtok": 0.0,
                    "output_price_per_mtok": 0.0
                }
        
    def add_usage(self, input_tokens: int, output_tokens: int):
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        cost = (input_tokens * self.pricing["input_price_per_mtok"] + 
                output_tokens * self.pricing["output_price_per_mtok"]) / 1_000_000
        self.total_cost += cost
        return cost
        
    def get_stats(self):
        return {
            "model": self.model_name,
            "type": self.model_type,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.input_tokens + self.output_tokens,
            "total_cost": self.total_cost
        }

class PerformanceMonitor:
    def __init__(self, main_model: str):
        self.operation_times = defaultdict(list)
        self.batch_times = []
        self.total_start_time = None
        
        # Track usage for different components
        self.trackers = {
            "main_llm": ModelUsageTracker(main_model, "main_llm"),
            "fact_llm": None,  # Will be set when memory is initialized
            "embeddings": None,  # Will be set when memory is initialized
            "anthropic": ModelUsageTracker(main_model, "anthropic")  # Initialize for main model if it's Anthropic
        }
        self.operation_costs = defaultdict(float)
        
    def set_memory_models(self, memory):
        """Set trackers for memory module models.""" 
        if hasattr(memory.llm, "config") and hasattr(memory.llm.config, "model"):
            self.trackers["fact_llm"] = ModelUsageTracker(memory.llm.config.model, "fact_llm")
            
        if hasattr(memory.embedding_model, "config") and hasattr(memory.embedding_model.config, "model"):
            self.trackers["embeddings"] = ModelUsageTracker(memory.embedding_model.config.model, "embeddings")
            
        # Initialize Anthropic tracker if needed
        if hasattr(memory.llm, "client") and isinstance(memory.llm, AnthropicLLM):
            self.trackers["anthropic"] = ModelUsageTracker(memory.llm.config.model, "anthropic")
            
    def start_batch(self):
        return time.time()
        
    def end_batch(self, start_time, input_tokens=0, output_tokens=0, model_type="main_llm", cost=0.0, total_cost=0.0):
        duration = time.time() - start_time
        self.batch_times.append(duration)
        if input_tokens or output_tokens:
            tracker = self.trackers.get(model_type)
            if tracker:
                tracker_cost = tracker.add_usage(input_tokens, output_tokens)
                self.operation_costs["batch_processing"] += tracker_cost
        if cost:
            self.operation_costs["batch_processing"] += cost
        if total_cost:
            self.operation_costs["batch_processing"] += total_cost
        return duration
        
    def start_operation(self, operation_name: str):
        return time.time()
        
    def end_operation(self, operation_name: str, start_time: float, 
                     input_tokens=0, output_tokens=0, model_type="main_llm"):
        duration = time.time() - start_time
        self.operation_times[operation_name].append(duration)
        if input_tokens or output_tokens:
            tracker = self.trackers.get(model_type)
            if tracker:
                cost = tracker.add_usage(input_tokens, output_tokens)
                self.operation_costs[operation_name] += cost
        return duration
        
    def start_total(self):
        self.total_start_time = time.time()
        
    def end_total(self):
        if self.total_start_time is None:
            return 0
        return time.time() - self.total_start_time
        
    def print_stats(self):
        """Print performance statistics."""
        logger.info("\nSTATS Performance Statistics:")
        logger.info(f"STATS Total time: {self.end_total():.2f}s")
        
        if self.batch_times:
            logger.info(f"STATS Average batch time: {sum(self.batch_times)/len(self.batch_times):.2f}s")
            logger.info(f"STATS Max batch time: {max(self.batch_times):.2f}s")
            logger.info(f"STATS Min batch time: {min(self.batch_times):.2f}s")
        
        if self.trackers:
            logger.info("\nSTATS Token Usage by Model:")
            total_cost = 0
            total_tokens = 0
            
            for model_type, tracker in self.trackers.items():
                model_info = tracker.get_stats()
                if model_info:
                    logger.info(f"\nSTATS {model_type} ({tracker.model_name}):")
                    logger.info(f"STATS   Total tokens: {model_info['total_tokens']:,}")
                    logger.info(f"STATS   Prompt tokens: {model_info['input_tokens']:,}")
                    logger.info(f"STATS   Completion tokens: {model_info['output_tokens']:,}")
                    
                    if model_info['total_cost'] > 0:
                        logger.info(f"COST   Estimated cost: ${model_info['total_cost']:.4f}")
                        total_cost += model_info['total_cost']
                    total_tokens += model_info['total_tokens']
            
            if total_tokens > 0:
                logger.info(f"\nSTATS Overall:")
                logger.info(f"STATS   Total tokens across models: {total_tokens:,}")
            if total_cost > 0:
                logger.info(f"COST   Total estimated cost: ${total_cost:.4f}")
        
        logger.info("\nSTATS Operation Statistics:")
        for op, times in self.operation_times.items():
            avg_time = sum(times)/len(times)
            total_time = sum(times)
            cost = self.operation_costs[op]
            logger.info(f"{op}:")
            logger.info(f"  Time: avg={avg_time:.2f}s, total={total_time:.2f}s")
            logger.info(f"  Cost: ${cost:.4f}")

async def format_response(response):
    """Format the response to show relevant information cleanly."""
    # Get main response content
    main_content = response.chat_message.content
    main_usage = response.chat_message.models_usage

    # Get memory operations info
    memory_calls = []
    for msg in response.inner_messages:
        if isinstance(msg, FunctionExecutionResultMessage):
            # Extract memory query
            for call in msg.content:
                if call.name == 'recall_memory':
                    import json
                    query = json.loads(call.arguments)['query']
                    memory_calls.append(f"{Fore.CYAN}Memory Query:{Style.RESET_ALL} {query}")
                    if msg.models_usage:
                        memory_calls.append(f"  {Fore.YELLOW}Tokens:{Style.RESET_ALL} {msg.models_usage.prompt_tokens + msg.models_usage.completion_tokens:,}")

    # Format the output
    output = []
    output.append(f"{Fore.GREEN}Response:{Style.RESET_ALL}")
    output.append(f"{Fore.CYAN}" + "-" * 80 + f"{Style.RESET_ALL}")
    output.append(main_content)
    output.append(f"{Fore.CYAN}" + "-" * 80 + f"{Style.RESET_ALL}")

    if main_usage:
        output.append(f"{Fore.MAGENTA}Main LLM Usage:{Style.RESET_ALL}")
        output.append(f"- {Fore.YELLOW}Input Tokens:{Style.RESET_ALL}  {main_usage.prompt_tokens:,}")
        output.append(f"- {Fore.YELLOW}Output Tokens:{Style.RESET_ALL} {main_usage.completion_tokens:,}")
        output.append(f"- {Fore.YELLOW}Total Tokens:{Style.RESET_ALL}  {main_usage.prompt_tokens + main_usage.completion_tokens:,}")

    if memory_calls:
        output.append(f"{Fore.BLUE}Memory Operations:{Style.RESET_ALL}")
        output.extend(memory_calls)

    return "\n".join(output)

# async def send_message(agent: MemoryEnabledAssistant, messages: List[AutogenTextMessage], monitor=None):
#     """Helper to send a message and wait for response."""
#     start_time = monitor.start_operation("message") if monitor else None
    
#     response = await agent.on_messages(messages, CancellationToken())
    
#     if monitor:
#         if hasattr(agent._model_client, "_last_request_cost"):
#             # Track Anthropic costs and tokens
#             cost = agent._model_client._last_request_cost
#             total_cost = agent._model_client._total_cost
            
#             # Get usage from response message
#             usage = response.chat_message.models_usage
#             monitor.end_operation("message", start_time,
#                                 input_tokens=usage.prompt_tokens if usage else 0,
#                                 output_tokens=usage.completion_tokens if usage else 0,
#                                 cost=cost,
#                                 total_cost=total_cost,
#                                 model_type="anthropic")
#         elif hasattr(agent._model_client, "_actual_usage"):
#             usage = agent._model_client._actual_usage
#             monitor.end_operation("message", start_time,
#                                 input_tokens=usage.prompt_tokens,
#                                 output_tokens=usage.completion_tokens,
#                                 model_type="main_llm")
    
#     # Format and print response
#     formatted_response = await format_response(response)
#     logger.info(formatted_response)
    
#     return response.chat_message.content

def build_memory(memory, messages, monitor):
    """Helper to build memory from messages."""
    try:
        # Add messages in smaller batches to avoid recursion
        for i in range(0, len(messages), 2):
            batch = messages[i:i+2]
            start_time = monitor.start_operation("add_memory")
            
            # Estimate tokens for the batch
            batch_text = "\n".join(msg["content"] for msg in batch)
            input_tokens = len(batch_text.split()) * 1.3  # Rough estimate
            
            # Track memory operation - don't pass monitor in metadata
            result = memory.add(
                messages=batch,
                user_id="Jason",  # Set a consistent user ID
                agent_id="memory_agent"  # Set a consistent agent ID
            )
            
            # Get actual tokens from result if available
            if isinstance(result, dict) and "results" in result:
                output_tokens = len(str(result["results"]).split()) * 1.3  # Rough estimate
            else:
                output_tokens = len(str(result).split()) * 1.3  # Rough estimate
                
            monitor.end_operation("add_memory", start_time, 
                                input_tokens=int(input_tokens),
                                output_tokens=int(output_tokens),
                                model_type="fact_llm")  # Use fact_llm since it's used for memory operations
            logger.info(f"MEMORY Building memory from messages...")
            
    except Exception as e:
        logger.error(f"ERROR Error building memory: {e}")
        raise

async def main():
    """Run memory relationship test."""
    model_name = "claude-3-5-sonnet-latest"

    # Load environment variables
    load_dotenv()

    # Load configuration
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    config_manager = ConfigManager(config_path)

    # Get memory configuration
    memory_config = config_manager.get_memory_config()
    logger.info(f"CONFIG Memory config: {memory_config}")

    # Create Anthropic client
    client = AnthropicChatCompletionClient(
        model=resolve_model(model_name),
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        config_manager=config_manager, 
        prompt_caching=True
    )

    # Create agent config with memory enabled
    agent_config = AgentConfig(
        name="memory_agent",
        description="An AI assistant with memory capabilities.",
        memory_config=memory_config,
        context={
            "user_id": "test_user_123",
            "agent_id": "memory_agent_23",
            "session_id": "test_session_213"
        }
    )

    # Create memory-enabled agent
    agent = MemoryEnabledAssistant(
        config=agent_config,
        model_client=client
    )

    # Set up performance monitoring
    monitor = PerformanceMonitor(model_name)
    monitor.start_total()

    # Set memory model trackers once agent is initialized
    monitor.set_memory_models(agent._memory)

    # Optimize memory module settings
    logger.info("OPTIMIZE Optimizing memory module settings...")

    # Configure vector store optimization
    if hasattr(agent._memory.vector_store, 'client'):
        # For Qdrant, configure optimizations
        if hasattr(agent._memory.vector_store.client, 'update_collection'):
            logger.info("VECTOR OPTIMIZE Enabling vector store optimizations")
            agent._memory.vector_store.client.update_collection(
                collection_name=agent._memory.vector_store.collection_name,
                hnsw_config={
                    "m": 16,  # Good balance of accuracy vs memory
                    "ef_construct": 128,  # Higher accuracy during index construction
                    "max_indexing_threads": 4,  # Moderate parallelism for index building
                    "on_disk": False,  # Keep in RAM for faster access
                },
                quantization_config={
                    "scalar": {
                        "type": "int8",  # Good compression with minimal accuracy loss
                        "quantile": 0.95,  # Preserve most important value ranges
                        "always_ram": True,  # Keep quantized vectors in RAM
                    }
                },
                optimizers_config={
                    "default_segment_number": 2,  # Balance between parallelism and overhead
                    "max_segment_size": 50000,  # 50MB segments for quick updates
                    "memmap_threshold": 50000,  # Memory map segments over 50MB
                    "indexing_threshold": 10000,  # Index segments over 10MB
                    "flush_interval_sec": 5,  # Frequent flushes for persistence
                    "max_optimization_threads": 4,  # Moderate parallelism for optimization
                },
            )
            logger.info("VECTOR OPTIMIZE Vector store optimization complete")

    # Configure OpenAI embeddings optimization
    if hasattr(agent._memory.embedding_model, 'client'):
        logger.info("EMBED OPTIMIZE Configuring embedding optimizations")
        if isinstance(agent._memory.embedding_model.client, OpenAI):
            # Create a reference to the original embed method
            original_embed = agent._memory.embedding_model.embed

            # Replace with wrapped version that handles float encoding
            def wrapped_embed(*args, **kwargs):
                vectors = original_embed(*args, **kwargs)
                return list(vectors)

            agent._memory.embedding_model.embed = wrapped_embed

            # If using text-embedding-3 models, reduce dimensions for better performance
            if "text-embedding-3" in agent._memory.embedding_model.config.model:
                agent._memory.embedding_model.config.embedding_dims = 1024  # Reduced from default 1536

    # Test messages with complex relationships
    messages = [
        TextMessage(
            content="Family Connections: Sarah is married to Mike who works at Netflix. Jason has two sisters, Emma and Grace. Alex has two dogs and a cat.",
            source="user",
        ),
        TextMessage(
            content="Neighbor Connections: Neighbor Lisa adopted cats from Tom's shelter. Lisa's daughter Maya takes dance with Sarah's daughter Sophie. Their dance teacher Christina used to work with Mike. Christina's husband James works at Google (different department than Sarah).",
            source="user",
        ),
        TextMessage(
            content="Professional Network: James's brother Peter (Tesla) carpools with Yuki. Peter's wife Maria photographed Sarah and Mike's wedding. Maria's assistant Lucas dates Emma's friend Olivia. Olivia's twin Oscar works at Tom's shelter and adopted Lisa's cat's kitten.",
            source="user",
        ),
        TextMessage(
            content="Additional Connections: Neighbor Mark's dog plays with Alex's dogs. Mark's sister Amy is a barista near Le Petit Bistro and brings coffee to Mike and Christina's colleague Jack. Jack's daughter Lily is classmates with Maya and Sophie. Lily's mom Hannah teaches yoga to Grace and Olivia. Hannah's husband Daniel plans to open a restaurant with Mike.",
            source="user",
        ),
    ]

    # build agentchat messages from factory
    agentchat_messages = MessageAdapterFactory.adapt(messages, "anthropic_autogen.core.messaging.ChatMessage", "autogen_agentchat.messages.ChatMessage")

    # Process initial messages
    for message in agentchat_messages:
        response = await agent.on_messages([message], CancellationToken())
        formatted_response = await format_response(response)
        logger.info(formatted_response)

    logger.info("MEMORY Testing memory recall...")
    test_questions = [
        "What's the name of Sarah's husband and where does he work?",
        "Who are Jason's sisters?",
        "What pets does Alex have?",
        "Who works at Netflix?",
        "Who is planning to open a restaurant together?"
    ]

    for question in test_questions:
        logger.info(f"\nQUESTION: {question}")
        start_time = monitor.start_operation("query")

        # Create user message from question
        user_message = TextMessage(content=question, source="user")

        # Get response from agent
        response = await agent.on_messages([user_message], CancellationToken())

        # Log the response
        logger.info(f"MEMORY Response: {await format_response(response)}")

        # Update monitoring stats
        input_tokens = len(question.split()) * 1.3  # Rough estimate
        output_tokens = len(str(response).split()) * 1.3  # Rough estimate

        monitor.end_operation("query", start_time,
                            input_tokens=int(input_tokens),
                            output_tokens=int(output_tokens),
                            model_type="main_llm")  # Use main_llm since we're using the assistant

    logger.info("STATS Performance statistics:")
    monitor.print_stats()

    # Cleanup
    agent.close()

if __name__ == "__main__":
    asyncio.run(main())
