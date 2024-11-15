from typing import Dict, Optional
from pydantic import BaseModel

class WorkflowState(BaseModel):
    """State of a workflow execution"""
    workflow_id: str
    current_step: int
    total_steps: int
    status: str = "running"
    error: Optional[str] = None
    state: Dict = {}

class StateStore:
    """Stores workflow state"""
    
    def __init__(self):
        self._states: Dict[str, WorkflowState] = {}
        
    async def save_state(
        self,
        workflow_id: str,
        state: WorkflowState
    ) -> None:
        """Save workflow state"""
        self._states[workflow_id] = state
        
    async def get_state(
        self,
        workflow_id: str
    ) -> Optional[WorkflowState]:
        """Get workflow state"""
        return self._states.get(workflow_id)
