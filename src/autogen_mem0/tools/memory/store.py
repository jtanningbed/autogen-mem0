from typing import Optional
from autogen_core.components.tools._base import CancellationToken
from autogen_mem0.core.tools import BaseTool
from mem0 import Memory

from .models import StoreMemoryInput, StoreMemoryOutput

class StoreMemoryTool(BaseTool):
    """Tool for storing memories."""
    
    def __init__(self, memory: Memory):
        super().__init__(
            args_type=StoreMemoryInput,
            return_type=StoreMemoryOutput,
            name="store_memory",
            description="Store information in memory for later retrieval"
        )
        self.memory = memory

    async def run(self, args: StoreMemoryInput, cancellation_token: Optional[CancellationToken] = None) -> StoreMemoryOutput:
        """Store memory with context."""
        # Get context from args
        context = {}
        if args.metadata:
            context.update(args.metadata)
            
        user_id = args.user_id
        agent_id = args.agent_id
        run_id = args.run_id

        if not any([user_id, agent_id, run_id]):
            raise ValueError("At least one of user_id, agent_id, or run_id must be provided in context or args")

        # Store memory with context
        try:
            result = self.memory.add(
                messages=args.messages,
                user_id=user_id,
                agent_id=agent_id,
                run_id=run_id,
                metadata=context
            )
            
            # Handle both v1.1 and legacy formats
            if isinstance(result, dict):
                return StoreMemoryOutput(
                    results=result.get("results", []),
                    relations=result.get("relations")
                )
            else:
                # Legacy format returns just the results
                return StoreMemoryOutput(results=result)
                
        except Exception as e:
            raise ValueError(f"Failed to store memory: {str(e)}")