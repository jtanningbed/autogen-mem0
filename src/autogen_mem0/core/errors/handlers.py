"""Error handling utilities."""

from typing import Callable, Optional, Type, TypeVar
from functools import wraps
import logging

from . import (
    MemoryError, MemoryStoreError, MemoryRecallError,
    ToolError, ToolExecutionError,
    AdapterError, AdapterConversionError
)

T = TypeVar('T')

logger = logging.getLogger(__name__)

def handle_memory_errors(
    error_class: Type[Exception] = MemoryError,
    default_handler: Optional[Callable[[Exception], T]] = None
):
    """Decorator for handling memory-related errors.
    
    Args:
        error_class: Error class to convert to
        default_handler: Optional handler for the error
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Memory error in {func.__name__}: {str(e)}")
                if default_handler:
                    return default_handler(e)
                raise error_class(str(e)) from e
        return wrapper
    return decorator

def handle_tool_errors(
    error_class: Type[Exception] = ToolError,
    default_handler: Optional[Callable[[Exception], T]] = None
):
    """Decorator for handling tool-related errors."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Tool error in {func.__name__}: {str(e)}")
                if default_handler:
                    return default_handler(e)
                raise error_class(str(e)) from e
        return wrapper
    return decorator

def handle_adapter_errors(
    error_class: Type[Exception] = AdapterError,
    default_handler: Optional[Callable[[Exception], T]] = None
):
    """Decorator for handling adapter-related errors."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Adapter error in {func.__name__}: {str(e)}")
                if default_handler:
                    return default_handler(e)
                raise error_class(str(e)) from e
        return wrapper
    return decorator