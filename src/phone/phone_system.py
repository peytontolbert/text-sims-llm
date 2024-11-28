from typing import Dict
import time
from src.llm.llm_interface import LLMDecisionMaker
from src.voice.speech import Speech
import logging

logger = logging.getLogger(__name__)

class PhoneSystem:
    def __init__(self, character):
        self.character = character
        self.in_call = False
        self.llm = LLMDecisionMaker()
        self.speech = Speech()
        self.call_history = []
        
    def start_call(self, message: str = "") -> dict:
        """Start or continue a voice call with the character"""
        try:
            logger.debug(f"Starting call with message: {message}")
            logger.debug(f"Current call state: in_call={self.in_call}")
            
            # Reset call state if something went wrong before
            if self.in_call and not message:
                logger.warning("Call marked as active but receiving new start request. Resetting state.")
                self.in_call = False
            
            # Add memory of starting/continuing the call
            try:
                logger.debug("Adding memory of call start")
                if hasattr(self.character, 'memory'):
                    self.character.memory.add_memory(
                        "Phone conversation active",
                        importance=0.6,
                        emotions={'excitement': 0.7, 'social': 0.8}
                    )
            except Exception as e:
                logger.error(f"Error adding memory: {str(e)}", exc_info=True)
            
            self.in_call = True
            logger.debug("Call state set to active")
            
            # Just return success for call initialization - no message processing
            return {
                "success": True,
                "message": "Call connected. Ready to chat!",
                "in_call": True,
                "status": "ready"
            }
                
        except Exception as e:
            logger.error(f"Error in call: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "in_call": self.in_call
            }

    def handle_text_call(self, message: str) -> str:
        """Handle incoming text messages"""
        try:
            if not message or not isinstance(message, str):
                return "Error: Invalid message"
            
            response = self._process_message(message)
            return response
        except Exception as e:
            logger.error(f"Error handling text call: {e}")
            return "I'm having trouble processing that message right now."

    def _process_message(self, message: str) -> str:
        """Process incoming message and generate response"""
        # Create context for the conversation
        context = self._create_conversation_context(message)
        
        # Get response from LLM
        response = self.llm.handle_phone_call(context)
        
        # Update character's state
        self._update_character_state(message, response)
        
        # Store conversation in history
        self._store_conversation(message, response)
        
        return response
        
    def _create_conversation_context(self, message: str) -> Dict:
        """Create context for the conversation"""
        return {
            'current_room': self.character.current_room.value,
            'emotional_state': self.character.memory.get_emotional_context(),
            'recent_memories': self.character.memory.get_recent_memories(3),
            'needs': self.character.needs,
            'user_message': message,
            'call_history': self.call_history[-5:],  # Last 5 conversations
            'knowledge_context': self._get_relevant_knowledge(message)
        }
        
    def _get_relevant_knowledge(self, message: str) -> Dict:
        """Get relevant knowledge for the conversation"""
        return self.character.knowledge_system.query_knowledge(message, k=3)
        
    def _update_character_state(self, message: str, response: str):
        """Update character's needs and emotional state"""
        # Update needs
        self.character.needs_system.modify('social', 10)
        self.character.needs_system.modify('fun', 5)
        self.character.needs_system.modify('energy', -2)
        
        # Add memory of the conversation
        self.character.memory.add_memory(
            f"Had a conversation about: {message}. I responded: {response}",
            importance=0.6,
            emotions={'happiness': 0.6, 'social': 0.7}
        )
        
        # Add to knowledge system
        self.character.knowledge_system.add_episodic_memory(
            f"Phone conversation: {message} -> {response}",
            emotions=self.character.memory.get_emotional_context()
        )
        
    def _store_conversation(self, message: str, response: str):
        """Store conversation in history"""
        self.call_history.append({
            'timestamp': time.time(),
            'message': message,
            'response': response,
            'emotional_state': self.character.memory.get_emotional_context()
        })
    
    def end_call(self) -> dict:
        """End the voice call"""
        try:
            self.in_call = False
            
            # Add memory of ending the call
            self.character.memory.add_memory(
                "Ended a phone conversation",
                importance=0.4,
                emotions={'satisfaction': 0.6}
            )
            
            return {
                "success": True,
                "message": "Call ended successfully"
            }
            
        except Exception as e:
            logger.error(f"Error ending call: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    