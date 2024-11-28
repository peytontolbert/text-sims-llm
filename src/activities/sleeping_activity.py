from src.activities.base_activity import BaseActivity
from src.utils.constants import ActivityType
from typing import Dict

class SleepingActivity(BaseActivity):
    def initialize_actions(self):
        self.available_actions = ['continue_sleeping', 'wake_up']

    def get_decision_prompt(self, context: Dict) -> str:
        return f"""
        You are currently sleeping.
        Duration: {context['activity_duration']} seconds
        Energy: {context['needs'].get('energy', 0)}
        Comfort: {context['needs'].get('comfort', 0)}

        Available actions:
        - continue_sleeping: Keep sleeping
        - wake_up: Get out of bed

        Consider:
        1. Has your energy been restored?
        2. Have you slept enough?
        3. Are there any urgent needs?

        Respond with one of the available actions.
        """

    def process_decision(self, decision: Dict, context: Dict) -> Dict:
        action = decision.get('action')
        if action not in self.available_actions:
            action = 'wake_up'
        
        return {
            'action': action,
            'thought': f"Energy level is {context['needs'].get('energy', 0)}, deciding to {action}"
        } 