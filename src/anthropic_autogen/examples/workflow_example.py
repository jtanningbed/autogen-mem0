import asyncio
import json
import os
from dotenv import load_dotenv
from autogen_core.application import SingleThreadedAgentRuntime
from autogen_core.base import AgentId
from autogen_core.components.tool_agent import ToolAgent
from autogen_core.components import FunctionCall
from anthropic_autogen.agents.claude_agent import ClaudeAgent
from anthropic_autogen.core.messaging import ChatMessage
from anthropic_autogen.tools.shell import shell_tool

async def main():
    load_dotenv()
    
    runtime = SingleThreadedAgentRuntime()
    
    # Register both agents
    await ClaudeAgent.register(runtime, "claude", lambda: ClaudeAgent(
        agent_id=AgentId(key="claude-1", type="assistant"),
        name="Claude Assistant",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        model="claude-3-opus-20240229"
    ))
    
    await ToolAgent.register(
        runtime,
        "tool_executor",
        lambda: ToolAgent("Shell command executor", [shell_tool])
    )
    
    runtime.start()
    claude_id = AgentId("claude", "default")
    tool_id = AgentId("tool_executor", "default")
    
    # Chat with Claude
    await runtime.send_message(ChatMessage(content="Tell me a programming joke", source="user"), claude_id)
    
    # Execute shell command
    shell_call = FunctionCall(
        arguments=json.dumps({"command": "ls -la", "working_dir": "."}),
        id="shell-1",
        name="execute_shell"
    )
    result = await runtime.send_message(shell_call, tool_id)
    print(f"Directory listing: {result.content}")
    
    await runtime.stop()

if __name__ == "__main__":
    asyncio.run(main())
