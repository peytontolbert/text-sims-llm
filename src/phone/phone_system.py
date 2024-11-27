from typing import Dict, Optional
import time
from src.llm.llm_interface import LLMDecisionMaker
from src.ears.whisper_manager import WhisperManager
from src.voice.speech import Speech
import numpy as np
import logging

logger = logging.getLogger(__name__)

class PhoneSystem:
    def __init__(self, character):
        self.character = character
        self.in_call = False
        self.llm = LLMDecisionMaker()
        self.whisper = WhisperManager()
        self.speech = Speech()
        self.call_history = []
        
    def handle_text_call(self, message: str) -> str:
        """Handle incoming text messages"""
        self.in_call = True
        response = self._process_message(message)
        self.in_call = False
        return response
        
    def start_call(self) -> dict:
        """Start a voice call with the character"""
        try:
            if self.in_call:
                return {
                    "success": False,
                    "message": "Already in a call"
                }
            
            self.in_call = True
            
            # Add memory of starting the call
            self.character.memory.add_memory(
                "Started a phone conversation",
                importance=0.6,
                emotions={'excitement': 0.7, 'social': 0.8}
            )
            
            # Generate greeting response
            greeting = self._process_message("Hello")
            
            # Convert greeting to speech using the correct method
            audio_path = self.speech.complete_task(greeting)
            
            return {
                "success": True,
                "message": "Call started",
                "greeting": greeting,
                "audio_path": str(audio_path)
            }
            
        except Exception as e:
            logger.error(f"Error starting call: {e}")
            self.in_call = False
            return {
                "success": False,
                "error": str(e)
            }
        
    def end_call(self):
        """End the current voice call"""
        try:
            if self.in_call:
                self.in_call = False
                self.whisper.end_call()
                
                # Add memory of ending the call
                self.character.memory.add_memory(
                    "Ended a phone conversation",
                    importance=0.4,
                    emotions={'satisfaction': 0.5}
                )
                
                farewell = self._process_message("Goodbye")
                self._store_conversation("User ended call", farewell)
                return {
                    "success": True,
                    "message": "Call ended",
                    "farewell": farewell
                }
            return {
                "success": True,
                "message": "No active call"
            }
        except Exception as e:
            logger.error(f"Error ending call: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        
    def process_voice_input(self):
        """Process voice input during an active call"""
        if not self.in_call:
            return None
            
        transcription = self.whisper.get_transcription()
        if transcription != "No speech detected.":
            response = self._process_message(transcription)
            audio_response = self.speech.complete_task(response)
            return {
                "transcription": transcription,
                "text_response": response,
                "audio_path": str(audio_response)
            }
        return None
        
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
        
    def handle_voice_message(self, audio_data: np.ndarray, sample_rate: int) -> dict:
        """Handle incoming voice message during call"""
        if not self.in_call:
            return {
                "success": False,
                "error": "Not in a call. Please start a call first."
            }
        
        try:
            # Transcribe incoming audio using whisper
            transcription = self.whisper.transcribe_audio({
                "array": audio_data,
                "sampling_rate": sample_rate
            })
            
            if not transcription or transcription == "No speech detected.":
                return {
                    "success": False,
                    "error": "No speech detected"
                }
            
            # Process the message and get response
            text_response = self._process_message(transcription)
            
            # Convert response to speech using the correct method
            audio_path = self.speech.complete_task(text_response)
            
            return {
                "success": True,
                "transcription": transcription,
                "text_response": text_response,
                "audio_path": str(audio_path)
            }
            
        except Exception as e:
            logger.error(f"Error processing voice message: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    