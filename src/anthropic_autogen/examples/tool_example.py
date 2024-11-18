import asyncio
import json
import os
from dotenv import load_dotenv
from autogen_core.application import SingleThreadedAgentRuntime
from autogen_core.base import AgentId
from autogen_core.components.tool_agent import ToolAgent
from autogen_core.components import FunctionCall
from anthropic_autogen.tools.shell import shell_tool

async def main():
    load_dotenv()
    
    runtime = SingleThreadedAgentRuntime()
    
    await ToolAgent.register(
        runtime,
        "tool_executor",
        lambda: ToolAgent("Shell command executor", [shell_tool])
    )
    
    runtime.start()
    tool_id = AgentId("tool_executor", "default")
    
    shell_call = FunctionCall(
        arguments=json.dumps({"command": "pwd", "working_dir": "."}),
        id="shell-1",
        name="execute_shell"
    )
    
    result = await runtime.send_message(shell_call, tool_id)
    print(f"Shell execution result: {result}")
    
    await runtime.stop()

if __name__ == "__main__":
    asyncio.run(main())