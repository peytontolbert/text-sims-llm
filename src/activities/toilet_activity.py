from src.activities.base_activity import BaseActivity
from src.utils.constants import ActivityType
from typing import Dict

class ToiletActivity(BaseActivity):
    def initialize_actions(self):
        self.available_actions = ['continue_using', 'stop_using']

    def get_decision_prompt(self, context: Dict) -> str:
        return f"""
        You are currently using the toilet.
        Duration: {context['activity_duration']} seconds
        Bladder need: {context['needs'].get('bladder', 0)}

        Available actions:
        - continue_using: Keep using the toilet
        - stop_using: Finish using the toilet

        Consider:
        1. Has your bladder need been satisfied?
        2. Is it time to finish?

        Respond with one of the available actions.
        """

    def process_decision(self, decision: Dict, context: Dict) -> Dict:
        action = decision.get('action')
        if action not in self.available_actions:
            action = 'stop_using'
        
        return {
            'action': action,
            'thought': f"Bladder need is {context['needs'].get('bladder', 0)}, deciding to {action}"
        } 