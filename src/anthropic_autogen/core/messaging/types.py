from enum import Enum
from typing import Union, List
from autogen_core.components import Image

class MessageCategory(Enum):
    CHAT = "chat"
    TASK = "task"
    CONTROL = "control"

class MessagePriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3
