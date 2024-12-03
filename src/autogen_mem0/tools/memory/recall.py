from typing import Optional
from .models import RecallMemoryInput, RecallMemoryOutput
from mem0 import Memory
from autogen_core.components.tools._base import BaseTool, CancellationToken

class RecallMemoryTool(BaseTool):
    """Tool for recalling memories."""
    
    def __init__(self, memory: Memory):
        super().__init__(
            args_type=RecallMemoryInput,
            return_type=RecallMemoryOutput,
            name="recall_memory",
            description="Recall previously stored information from memory. Note: Context will be automatically provided from the client."
        )
        self.memory = memory

    async def run(self, args: RecallMemoryInput, cancellation_token: Optional[CancellationToken] = None) -> RecallMemoryOutput:
        """Recall memories with context."""
        user_id = args.user_id
        agent_id = args.agent_id
        run_id = args.run_id
        
        if not any([user_id, agent_id, run_id]):
            raise ValueError("At least one of user_id, agent_id, or run_id must be provided")
            
        try:
            # Search with top-level parameters and optional metadata filters
            results = self.memory.search(
                query=args.query,
                user_id=user_id,
                agent_id=agent_id,
                run_id=run_id,
                limit=args.limit or 10,
                filters=args.filters  # Optional metadata filters like {"topic": "geography"}
            )
            
            # Handle both v1.1 and legacy formats
            if isinstance(results, dict):
                return RecallMemoryOutput(
                    results=results.get("results", []),
                    relations=results.get("relations")
                )
            else:
                # Legacy format returns just the results list
                return RecallMemoryOutput(results=results)
                
        except Exception as e:
            raise ValueError(f"Failed to recall memories: {str(e)}")