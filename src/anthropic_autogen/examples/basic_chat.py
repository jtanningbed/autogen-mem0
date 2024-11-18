import asyncio
import os
from dotenv import load_dotenv
from autogen_core.base import AgentId
from anthropic_autogen.agents import ClaudeAgent
from anthropic_autogen.core.messaging import ChatMessage, ChatContent

async def main():
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    print(f"API Key loaded: {'Yes' if api_key else 'No'}")
    
    # Initialize Claude agent with latest model
    claude = ClaudeAgent(
        agent_id=AgentId(key="claude-1", type="assistant"),
        name="Claude Assistant",
        api_key=api_key,
        model="claude-3-opus-20240229"
    )
    
    try:
        print("Starting Claude agent...")
        await claude.start()
        
        print("Sending test message...")
        test_message = ChatMessage(
            content=ChatContent(text="Tell me a short joke about programming"),
            sender=AgentId(key="user-1", type="user"),
            recipient=claude.agent_id
        )
        
        response = await claude.handle_chat(test_message)
        print(f"Claude's response: {response}")
        
    finally:
        await claude.stop()

if __name__ == "__main__":
    asyncio.run(main())