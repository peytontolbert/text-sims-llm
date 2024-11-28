from src.activities.base_activity import BaseActivity
from src.utils.constants import ActivityType
from typing import Dict

class FridgeActivity(BaseActivity):
    def initialize_actions(self):
        self.available_actions = ['grab_ingredient', 'lookup_ingredient', 'leave_fridge']

    def get_decision_prompt(self, context: Dict) -> str:
        return f"""
        You are currently using the fridge.
        Hunger need: {context['needs'].get('hunger', 0)}
        Available ingredients: {context.get('available_ingredients', [])}

        Available actions:
        - grab_ingredient: Take an ingredient to prepare food
        - lookup_ingredient: Check what ingredients are available
        - leave_fridge: Close the fridge

        Consider:
        1. Are you hungry?
        2. Do you need to prepare a meal?
        3. Do you know what ingredients are available?

        Respond with one of the available actions.
        """

    def process_decision(self, decision: Dict, context: Dict) -> Dict:
        action = decision.get('action')
        if action not in self.available_actions:
            action = 'leave_fridge'
        
        return {
            'action': action,
            'thought': f"Considering hunger ({context['needs'].get('hunger', 0)}), deciding to {action}"
        } 