from typing import Optional, List
from ..core.agents.chat_agent import ChatAgent
from ..core.messaging import ChatMessage, ChatContent
from ..core.models import AnthropicChatCompletionClient
from autogen_core.base import CancellationToken
from autogen_core.components.models import SystemMessage, UserMessage, AssistantMessage

class ClaudeAgent(ChatAgent):
    """Chat agent powered by Claude"""
    
    def __init__(
        self,
        *args,
        model: str = "claude-3-opus-20240229",
        api_key: str,
        system_prompt: str = "",
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.client = AnthropicChatCompletionClient(
            model=model,
            api_key=api_key
        )
        self.system_prompt = system_prompt
        self.log_prefix = "🤖 claude"

    async def _generate_response(
        self,
        message: ChatMessage,
        cancellation_token: Optional[CancellationToken] = None
    ) -> Optional[ChatMessage]:
        """Generate response using Claude"""
        # Convert conversation history to LLM messages
        messages = []
        
        if self.system_prompt:
            messages.append(SystemMessage(content=self.system_prompt))
            
        for msg in self.get_conversation_history():
            if msg.sender == self.agent_id:
                messages.append(AssistantMessage(content=msg.content.text))
            else:
                messages.append(UserMessage(content=msg.content.text))
                
        # Add current message
        messages.append(UserMessage(content=message.content.text))
        
        # Get completion
        result = await self.client.create(
            messages=messages,
            cancellation_token=cancellation_token
        )
        
        # Create response message
        return ChatMessage(
            content=ChatContent(text=result.content),
            sender=self.agent_id,
            recipient=message.sender
        )
from typing import Optional, List, Dict, Any
from autogen_core.base import AgentId, CancellationToken
from autogen_core.components.models import (
    ChatCompletionClient,
    SystemMessage,
    UserMessage, 
    AssistantMessage
)

from ..core.agents.chat_agent import ChatAgent
from ..core.messaging import ChatMessage, ChatContent
from ..core.models import AnthropicChatCompletionClient

class ClaudeAgent(ChatAgent):
    """Chat agent powered by Claude 3"""
    
    def __init__(
        self,
        agent_id: AgentId,
        name: str,
        client: Optional[ChatCompletionClient] = None,
        model: str = "claude-3-opus-20240229",
        api_key: Optional[str] = None,
        system_prompt: str = "",
        **kwargs
    ):
        super().__init__(agent_id=agent_id, name=name, **kwargs)
        
        # Initialize client if not provided
        if client is None:
            if not api_key:
                raise ValueError("Either client or api_key must be provided")
            client = AnthropicChatCompletionClient(
                model=model,
                api_key=api_key
            )
        
        self.client = client
        self.system_prompt = system_prompt
        self.log_prefix = "🤖 claude"
        
        # Track conversation state
        self._conversation_state: Dict[str, Any] = {}

    async def _generate_response(
        self,
        message: ChatMessage,
        cancellation_token: Optional[CancellationToken] = None
    ) -> Optional[ChatMessage]:
        """Generate response using Claude"""
        try:
            # Convert conversation history to LLM messages
            messages: List[SystemMessage | UserMessage | AssistantMessage] = []
            
            # Add system prompt if present
            if self.system_prompt:
                messages.append(SystemMessage(content=self.system_prompt))
                
            # Add conversation history
            for msg in self.get_conversation_history():
                if msg.sender == self.agent_id:
                    messages.append(AssistantMessage(content=msg.content.text))
                else:
                    # Handle images in user messages
                    if msg.content.images:
                        content = [{
                            "type": "text",
                            "text": msg.content.text
                        }]
                        for img in msg.content.images:
                            content.append({
                                "type": "image",
                                "image": img
                            })
                        messages.append(UserMessage(content=content))
                    else:
                        messages.append(UserMessage(content=msg.content.text))
                        
            # Add current message
            messages.append(UserMessage(content=message.content.text))
            
            # Get completion
            result = await self.client.create(
                messages=messages,
                cancellation_token=cancellation_token
            )
            
            # Update conversation state
            self._conversation_state.update({
                "last_response": result.content,
                "token_usage": result.usage.model_dump() if result.usage else None
            })
            
            # Create response message
            return ChatMessage(
                content=ChatContent(text=result.content),
                sender=self.agent_id,
                recipient=message.sender,
                metadata={
                    "token_usage": result.usage.model_dump() if result.usage else None,
                    "finish_reason": result.finish_reason
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            raise

    def get_state(self) -> Dict[str, Any]:
        """Get agent state"""
        return {
            **super().get_state(),
            "conversation_state": self._conversation_state
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        """Load agent state"""
        super().load_state(state)
        self._conversation_state = state.get("conversation_state", {})
