"""Schema utilities for tools."""

from typing import Dict, Any, Optional, List, Type
from dataclasses import dataclass, field
from pydantic import BaseModel, create_model


def create_tool_models(
    name: str,
    input_fields: Dict[str, tuple[Type, str]],
    output_fields: Dict[str, tuple[Type, str]],
) -> tuple[Type[BaseModel], Type[BaseModel]]:
    """Create input and output Pydantic models for a tool.
    
    Args:
        name: Tool name (used to generate model names)
        input_fields: Dict mapping field names to (type, description) tuples
        output_fields: Dict mapping field names to (type, description) tuples
        
    Returns:
        Tuple of (input model class, output model class)
    """
    # Create input model
    input_model = create_model(
        f"{name}Input",
        **{
            field_name: (field_type, ...)
            for field_name, (field_type, _) in input_fields.items()
        }
    )
    
    # Create output model
    output_model = create_model(
        f"{name}Output",
        **{
            field_name: (field_type, ...)
            for field_name, (field_type, _) in output_fields.items()
        }
    )
    
    # Add field descriptions
    for field_name, (_, description) in input_fields.items():
        input_model.model_fields[field_name].description = description
        
    for field_name, (_, description) in output_fields.items():
        output_model.model_fields[field_name].description = description
    
    return input_model, output_model
