from typing import Dict
import time
from llm_interface import LLMDecisionMaker

class PhoneSystem:
    def __init__(self, character):
        self.character = character
        self.in_call = False
        self.llm = LLMDecisionMaker()
        
    def start_call(self, user_message: str) -> str:
        self.in_call = True
        
        # Create context for the conversation
        context = {
            'current_room': self.character.current_room.value,
            'emotional_state': self.character.memory.get_emotional_context(),
            'recent_memories': self.character.memory.get_recent_memories(3),
            'needs': self.character.needs,
            'user_message': user_message
        }
        
        # Get response from LLM
        response = self.llm.handle_phone_call(context)
        
        # Update character's needs
        self.character.needs_system.modify('social', 10)
        self.character.needs_system.modify('fun', 5)
        self.character.needs_system.modify('energy', -2)
        
        # Add memory of the call
        self.character.memory.add_memory(
            f"Had a phone conversation about: {user_message}",
            importance=0.6,
            emotions={'happiness': 0.6, 'social': 0.7}
        )
        
        return response
    
    def end_call(self):
        self.in_call = False 