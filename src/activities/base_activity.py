from abc import ABC, abstractmethod
from typing import Dict, Optional
from src.utils.constants import ActivityType

class BaseActivity(ABC):
    def __init__(self, activity_type: ActivityType):
        self.type = activity_type
        self.available_actions = []
        self.initialize_actions()

    @abstractmethod
    def initialize_actions(self):
        """Define available actions for this activity"""
        pass

    @abstractmethod
    def get_decision_prompt(self, context: Dict) -> str:
        """Create activity-specific decision prompt"""
        pass

    @abstractmethod
    def process_decision(self, decision: Dict, context: Dict) -> Dict:
        """Process and validate activity-specific decisions"""
        pass

    def get_available_actions(self) -> list[str]:
        return self.available_actions 