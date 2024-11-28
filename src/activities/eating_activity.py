from src.activities.base_activity import BaseActivity
from src.utils.constants import ActivityType
from typing import Dict

class EatingActivity(BaseActivity):
    def initialize_actions(self):
        self.available_actions = ['continue_eating', 'finish_meal']

    def get_decision_prompt(self, context: Dict) -> str:
        return f"""
        You are eating a meal.
        Duration: {context['activity_duration']} seconds
        Hunger: {context['needs'].get('hunger', 0)}
        Energy: {context['needs'].get('energy', 0)}

        Available actions:
        - continue_eating: Keep eating the meal
        - finish_meal: Stop eating

        Consider:
        1. Are you still hungry?
        2. Have you eaten enough?
        3. How's your energy level?

        Respond with one of the available actions.
        """

    def process_decision(self, decision: Dict, context: Dict) -> Dict:
        action = decision.get('action')
        if action not in self.available_actions:
            action = 'finish_meal'
        
        return {
            'action': action,
            'thought': f"Hunger level is {context['needs'].get('hunger', 0)}, deciding to {action}"
        } 