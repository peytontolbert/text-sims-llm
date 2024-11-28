# File: models.py
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Callable
from src.utils.constants import Direction, ObjectType, ActivityState, ActivityType
from src.environment.activities import Activity
from src.utils.position import Position

@dataclass
class ActivityInfo:
    type: ActivityType
    duration: float
    need_changes: Dict[str, float]
    exit_condition: Optional[Callable[['Activity'], bool]] = None

@dataclass
class GameObject:
    type: ObjectType
    actions: List[str]
    need_effects: Dict[str, float]
    description: str
    activity_info: Optional[ActivityInfo] = None
