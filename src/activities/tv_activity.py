from src.activities.base_activity import BaseActivity
from src.utils.constants import ActivityType
from typing import Dict

class TVActivity(BaseActivity):
    def initialize_actions(self):
        self.available_actions = ['continue_watching', 'change_channel', 'stop_watching']

    def get_decision_prompt(self, context: Dict) -> str:
        return f"""
        You are watching TV.
        Duration: {context['activity_duration']} seconds
        Energy: {context['needs'].get('energy', 0)}
        Fun: {context['needs'].get('fun', 0)}
        Social: {context['needs'].get('social', 0)}

        Available actions:
        - continue_watching: Keep watching the current program
        - change_channel: Switch to a different channel
        - stop_watching: Turn off the TV

        Consider:
        1. Are you being entertained?
        2. How is your energy level?
        3. Have you been watching for too long?

        Respond with one of the available actions.
        """

    def process_decision(self, decision: Dict, context: Dict) -> Dict:
        action = decision.get('action')
        if action not in self.available_actions:
            action = 'stop_watching'
        
        return {
            'action': action,
            'thought': f"Based on needs (fun: {context['needs'].get('fun', 0)}, "
                      f"energy: {context['needs'].get('energy', 0)}), deciding to {action}"
        } 