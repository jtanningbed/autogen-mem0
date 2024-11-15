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
