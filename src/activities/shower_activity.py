from src.activities.base_activity import BaseActivity
from src.utils.constants import ActivityType
from typing import Dict

class ShowerActivity(BaseActivity):
    def initialize_actions(self):
        self.available_actions = ['continue_showering', 'finish_shower']

    def get_decision_prompt(self, context: Dict) -> str:
        return f"""
        You are taking a shower.
        Duration: {context['activity_duration']} seconds
        Hygiene: {context['needs'].get('hygiene', 0)}
        Comfort: {context['needs'].get('comfort', 0)}

        Available actions:
        - continue_showering: Keep showering
        - finish_shower: Exit the shower

        Consider:
        1. Is your hygiene need satisfied?
        2. Have you been showering long enough?
        3. Are there other pressing needs?

        Respond with one of the available actions.
        """

    def process_decision(self, decision: Dict, context: Dict) -> Dict:
        action = decision.get('action')
        if action not in self.available_actions:
            action = 'finish_shower'
        
        return {
            'action': action,
            'thought': f"Hygiene level is {context['needs'].get('hygiene', 0)}, deciding to {action}"
        } 