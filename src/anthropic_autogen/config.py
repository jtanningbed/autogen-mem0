from typing import Optional
from pydantic import BaseModel

class AgentConfig(BaseModel):
    """Configuration for an agent"""
    name: str
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    capabilities: list[str] = []

class WorkflowConfig(BaseModel):
    """Configuration for a workflow"""
    agents: dict[str, AgentConfig]
    tools: list[str]
    max_steps: int = 10
    timeout: float = 300.0

class Config(BaseModel):
    """Global configuration"""
    api_key: Optional[str] = None
    default_model: str = "claude-3-opus-20240229"
    log_level: str = "INFO"
    workflows: dict[str, WorkflowConfig] = {}
