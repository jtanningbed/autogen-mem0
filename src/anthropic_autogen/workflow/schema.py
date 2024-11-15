from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field
from uuid import uuid4
from datetime import datetime

class WorkflowStepInput(BaseModel):
    """Input parameters for a workflow step"""
    type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    context_vars: List[str] = Field(default_factory=list)

class WorkflowStep(BaseModel):
    """Definition of a workflow step"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    type: Literal["chat", "tool", "parallel", "conditional"]
    input: WorkflowStepInput
    timeout: Optional[float] = None
    retry: Optional[int] = None
    dependencies: List[str] = Field(default_factory=list)
    condition: Optional[str] = None

class WorkflowDefinition(BaseModel):
    """Complete workflow definition"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    version: str
    steps: List[WorkflowStep]
    metadata: Dict[str, Any] = Field(default_factory=dict)

class WorkflowState(BaseModel):
    """Workflow execution state"""
    workflow_id: str
    status: Literal["pending", "running", "completed", "failed", "cancelled"]
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    current_step: Optional[str] = None
    completed_steps: Dict[str, Any] = Field(default_factory=dict)
    failed_steps: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
