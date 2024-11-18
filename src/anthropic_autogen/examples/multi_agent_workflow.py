import asyncio
import os
from dotenv import load_dotenv
from autogen_core.base import AgentId
from autogen_core.application import SingleThreadedAgentRuntime
from anthropic_autogen.agents.claude_agent import ClaudeAgent
from anthropic_autogen.agents.user_proxy import UserProxyAgent
from anthropic_autogen.core.messaging import ChatMessage

async def main():
    load_dotenv()
    runtime = SingleThreadedAgentRuntime()
    
    # Register agents
    await UserProxyAgent.register(runtime, "user", lambda: UserProxyAgent(
        agent_id=AgentId(key="user-1", type="user")
    ))
    
    await ClaudeAgent.register(runtime, "claude", lambda: ClaudeAgent(
        agent_id=AgentId(key="claude-1", type="assistant"),
        name="Claude Assistant",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        model="claude-3-opus-20240229"
    ))
    
    runtime.start()
    user_id = AgentId("user", "default")
    
    # Start conversation through UserProxy
    while True:
        user_message = input("\nEnter your message (or 'exit' to quit): ")
        if user_message.lower() == 'exit':
            break
            
        await runtime.send_message(
            ChatMessage(content=user_message, source="user"),
            user_id  # Send to UserProxy instead of directly to Claude
        )
    
    await runtime.stop()

if __name__ == "__main__":
    asyncio.run(main())
