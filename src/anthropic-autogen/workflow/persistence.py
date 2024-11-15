from typing import Optional, Dict, List
import json
from datetime import datetime
from pathlib import Path

from .schema import WorkflowState, WorkflowDefinition

class WorkflowStateStore:
    """Handles persistence of workflow state"""
    
    def __init__(self, storage_dir: str = ".workflow_state"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
    def save_state(self, state: WorkflowState) -> None:
        """Save workflow state to storage"""
        state_file = self.storage_dir / f"{state.workflow_id}.json"
        with state_file.open("w") as f:
            json.dump(
                state.model_dump(),
                f,
                default=str,
                indent=2
            )
            
    def load_state(self, workflow_id: str) -> Optional[WorkflowState]:
        """Load workflow state from storage"""
        state_file = self.storage_dir / f"{workflow_id}.json"
        if not state_file.exists():
            return None
            
        with state_file.open("r") as f:
            data = json.load(f)
            return WorkflowState.model_validate(data)
            
    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflow states"""
        states = []
        for state_file in self.storage_dir.glob("*.json"):
            with state_file.open("r") as f:
                data = json.load(f)
                states.append({
                    "workflow_id": data["workflow_id"],
                    "status": data["status"],
                    "start_time": data["start_time"],
                    "end_time": data.get("end_time")
                })
        return states

    def cleanup_old_states(self, max_age_days: int = 30) -> None:
        """Clean up old workflow states"""
        cutoff = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)
        for state_file in self.storage_dir.glob("*.json"):
            if state_file.stat().st_mtime < cutoff:
                state_file.unlink()
