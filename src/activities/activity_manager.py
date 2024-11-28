from typing import Dict, Optional
from src.utils.constants import ActivityType
from src.activities.base_activity import BaseActivity
from src.activities.toilet_activity import ToiletActivity
from src.activities.fridge_activity import FridgeActivity
from src.activities.computer_activity import ComputerActivity
from src.activities.tv_activity import TVActivity
from src.activities.sleeping_activity import SleepingActivity
from src.activities.eating_activity import EatingActivity
from src.activities.shower_activity import ShowerActivity
import time

class ActivityManager:
    def __init__(self):
        self.activities = {
            ActivityType.TOILET_USE: ToiletActivity(ActivityType.TOILET_USE),
            ActivityType.FRIDGE_USE: FridgeActivity(ActivityType.FRIDGE_USE),
            ActivityType.COMPUTER_USE: ComputerActivity(ActivityType.COMPUTER_USE),
            ActivityType.TV_WATCHING: TVActivity(ActivityType.TV_WATCHING),
            ActivityType.SLEEPING: SleepingActivity(ActivityType.SLEEPING),
            ActivityType.EATING: EatingActivity(ActivityType.EATING),
            ActivityType.SHOWER_USE: ShowerActivity(ActivityType.SHOWER_USE)
        }
        self.current_activity: Optional[BaseActivity] = None
        self.start_time: Optional[float] = None

    def start_activity(self, activity_type: ActivityType) -> bool:
        if activity_type in self.activities:
            self.current_activity = self.activities[activity_type]
            self.start_time = time.time()
            return True
        return False

    def get_activity_decision(self, context: Dict) -> Dict:
        if not self.current_activity:
            return {'action': 'idle', 'thought': 'No active activity'}

        # Get activity-specific prompt
        prompt = self.current_activity.get_decision_prompt(context)
        
        # Use LLM to get decision
        decision = self.llm.get_activity_decision(prompt)
        
        # Process decision through activity module
        return self.current_activity.process_decision(decision, context)

    def end_activity(self) -> None:
        self.current_activity = None
        self.start_time = None

    def get_available_actions(self) -> list[str]:
        if self.current_activity:
            return self.current_activity.get_available_actions()
        return [] 