from src.activities.base_activity import BaseActivity
from src.utils.constants import ActivityType
from typing import Dict

class ComputerActivity(BaseActivity):
    def initialize_actions(self):
        # Main computer menu actions
        self.available_actions = [
            'browse_internet',
            'play_game',
            'open_coding',
            'open_journal',
            'exit_computer'
        ]
        
        # Coding sub-menu actions
        self.coding_actions = [
            'write_new_code',
            'edit_existing_code',
            'run_code',
            'back_to_computer'
        ]
        
        # Journal sub-menu actions
        self.journal_actions = [
            'write_entry',
            'read_entries',
            'back_to_computer'
        ]
        
        # Track current menu state
        self.current_menu = 'main'

    def get_decision_prompt(self, context: Dict) -> str:
        if self.current_menu == 'main':
            return self._get_main_menu_prompt(context)
        elif self.current_menu == 'coding':
            return self._get_coding_menu_prompt(context)
        elif self.current_menu == 'journal':
            return self._get_journal_menu_prompt(context)
        
    def _get_main_menu_prompt(self, context: Dict) -> str:
        return f"""
        You are using the computer.
        Duration: {context['activity_duration']} seconds
        Energy: {context['needs'].get('energy', 0)}
        Fun: {context['needs'].get('fun', 0)}
        Social: {context['needs'].get('social', 0)}

        Available actions:
        - browse_internet: Browse the web
        - play_game: Play a computer game
        - open_coding: Open coding environment
        - open_journal: Open journal application
        - exit_computer: Stop using computer

        Consider:
        1. What would be most beneficial now?
        2. How is your energy level?
        3. Do you need entertainment or productivity?

        Respond with one of the available actions.
        """

    def _get_coding_menu_prompt(self, context: Dict) -> str:
        return f"""
        You are in the coding environment.
        Duration: {context['activity_duration']} seconds
        Energy: {context['needs'].get('energy', 0)}

        Available actions:
        - write_new_code: Start a new coding project
        - edit_existing_code: Modify existing code
        - run_code: Execute and test code
        - back_to_computer: Return to main computer menu

        Consider:
        1. Do you have energy to write new code?
        2. Are there existing projects to work on?
        3. Is it time to test your code?

        Respond with one of the available actions.
        """

    def _get_journal_menu_prompt(self, context: Dict) -> str:
        return f"""
        You are using the journal application.
        Duration: {context['activity_duration']} seconds
        Energy: {context['needs'].get('energy', 0)}
        
        Available actions:
        - write_entry: Write a new journal entry
        - read_entries: Read previous journal entries
        - back_to_computer: Return to main computer menu

        Consider:
        1. Do you want to reflect on recent experiences?
        2. Would reading past entries be helpful now?

        Respond with one of the available actions.
        """

    def process_decision(self, decision: Dict, context: Dict) -> Dict:
        action = decision.get('action')
        
        # Handle main menu actions
        if self.current_menu == 'main':
            if action == 'open_coding':
                self.current_menu = 'coding'
                return {
                    'action': action,
                    'thought': "Opening coding environment"
                }
            elif action == 'open_journal':
                self.current_menu = 'journal'
                return {
                    'action': action,
                    'thought': "Opening journal application"
                }
            elif action not in self.available_actions:
                action = 'exit_computer'
        
        # Handle coding menu actions
        elif self.current_menu == 'coding':
            if action not in self.coding_actions:
                action = 'back_to_computer'
            if action == 'back_to_computer':
                self.current_menu = 'main'
        
        # Handle journal menu actions
        elif self.current_menu == 'journal':
            if action not in self.journal_actions:
                action = 'back_to_computer'
            if action == 'back_to_computer':
                self.current_menu = 'main'
        
        return {
            'action': action,
            'thought': f"Based on needs (energy: {context['needs'].get('energy', 0)}, "
                      f"fun: {context['needs'].get('fun', 0)}), deciding to {action}"
        } 