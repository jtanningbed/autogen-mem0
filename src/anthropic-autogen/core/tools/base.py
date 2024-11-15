from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Type, Optional
from pydantic import BaseModel

from autogen_core.base import CancellationToken
from .schema import ToolSchema, ToolResponse, ToolParameter

InputT = TypeVar('InputT', bound=BaseModel)
OutputT = TypeVar('OutputT', bound=BaseModel)
StateT = TypeVar('StateT', bound=BaseModel)

class BaseTool(ABC, Generic[InputT, OutputT, StateT]):
    """Base class for all tools"""
    
    def __init__(
        self,
        name: str,
        description: str,
        input_type: Type[InputT],
        output_type: Type[OutputT],
        state_type: Optional[Type[StateT]] = None
    ):
        self.name = name
        self.description = description
        self._input_type = input_type
        self._output_type = output_type
        self._state_type = state_type
        self._state: Optional[StateT] = None

    @property
    def schema(self) -> ToolSchema:
        """Get the tool's schema"""
        model_schema = self._input_type.model_json_schema()
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters={
                name: ToolParameter(**props)
                for name, props in model_schema.get("properties", {}).items()
            }
        )

    @abstractmethod
    async def execute(
        self,
        input_data: InputT,
        cancellation_token: Optional[CancellationToken] = None
    ) -> ToolResponse[OutputT]:
        """Execute the tool"""
        pass

    def save_state(self) -> Optional[dict]:
        """Save tool state"""
        if self._state:
            return self._state.model_dump()
        return None

    def load_state(self, state: dict) -> None:
        """Load tool state"""
        if self._state_type and state:
            self._state = self._state_type.model_validate(state)
