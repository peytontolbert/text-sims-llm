# File: autonomous_character.py
from typing import Dict, List, Optional
from src.utils.models import Position
from src.utils.constants import Direction, ObjectType
from src.environment.house import House
from src.computer.browser_interface import BrowserInterface
from src.llm.llm_interface import LLMDecisionMaker
from src.memory.memory_system import Memory
from src.character.needs_system import Needs
from src.phone.phone_system import PhoneSystem
from src.computer.coding_system import CodingSystem
from src.computer.journal_system import JournalSystem
from src.memory.knowledge_system import KnowledgeSystem
from src.ears.whisper_manager import WhisperManager
from src.voice.speech import Speech
from src.voice.voice_manager import VoiceManager
import time
from datetime import datetime
from pathlib import Path
from src.environment.activities import ActivityManager
import logging
import threading

class AutonomousCharacter:
    def __init__(self, name: str, house: House):
        self.name = name
        self.position = Position(0, 0)
        self.house = house
        self.current_action = None
        self.thought = None
        self.last_action_time = time.time()
        self.decision_maker = LLMDecisionMaker()
        self.action_history = []
        
        # Initialize browser as None - will be created when needed
        self.browser = None
        self.browser_thread = None
        
        # Replace direct needs dict with Needs system
        self.needs_system = Needs()
        self.memory = Memory()
        self.current_room = self.house.get_room(self.position)
        self.coding_system = CodingSystem(name)
        self.journal_system = JournalSystem(name)
        self.knowledge_system = KnowledgeSystem()
        self.ears = WhisperManager()
        self.voice_manager = VoiceManager()
        self.activity_manager = ActivityManager()
        self.current_activity_context = None
        
        # Add some initial knowledge
        self._initialize_knowledge()

    @property
    def needs(self) -> Dict[str, float]:
        return self.needs_system.values

    @property
    def is_busy(self) -> bool:
        return self.activity_manager.is_busy

    @property
    def needs_activity_exit(self) -> bool:
        return self.activity_manager.needs_exit

    def update(self, delta_time: float) -> str:
        """Update the character's state and make decisions"""
        try:
            logging.debug("Starting character update...")
            
            # Update needs based on time passed
            self.needs_system.update(delta_time)
            
            # Regular update for non-activity state
            logging.debug("Making regular decision...")
            try:
                context = self._get_context()
                logging.debug(f"Context for decision making: {context}")
                
                # Add timeout for decision making
                start_time = time.time()
                decision = None
                try:
                    decision = self.decision_maker.make_decision(context)
                    logging.debug(f"Decision made in {time.time() - start_time:.2f} seconds")
                    logging.debug(f"Raw decision from LLM: {decision}")
                    
                    # Validate decision structure
                    if not isinstance(decision, dict) or not all(k in decision for k in ['action', 'target', 'thought']):
                        raise ValueError(f"Invalid decision structure: {decision}")
                        
                except Exception as e:
                    logging.error(f"Error in decision_maker.make_decision: {e}", exc_info=True)
                    decision = {
                        'action': 'idle',
                        'target': 'none',
                        'thought': 'Having trouble making a decision...'
                    }
                
                if not decision:
                    logging.warning("Decision maker returned None - using fallback decision")
                    decision = {
                        'action': 'idle',
                        'target': 'none',
                        'thought': 'Thinking about what to do...'
                    }
                
                self.thought = decision.get('thought', 'Thinking...')
                logging.debug(f"Final decision made: {decision}")
                
                # Execute the decision
                result = self._execute_decision(decision)
                logging.debug(f"Decision execution result: {result}")
                return result
                
            except Exception as e:
                logging.error(f"Error in regular decision making: {e}", exc_info=True)
                return "Error in decision making"
                
        except Exception as e:
            logging.error(f"Error in character update: {e}", exc_info=True)
            return "Error in character update"

    def _get_context(self) -> Dict:
        """Get the current context of the character for decision making"""
        try:
            # Get basic state information
            current_room = self.house.get_room(self.position)
            available_objects = self.house.get_objects_in_room(self.position)
            
            # Get needs information
            needs_info = {
                'needs': self.needs,
                'urgent_needs': self.needs_system.get_urgent_needs(),
                'need_status': self.needs_system.get_need_status()
            }
            
            # Get memory and emotional information
            memory_info = {
                'recent_memories': self.memory.get_recent_memories(5),
                'important_memories': self.memory.get_important_memories(),
                'emotional_state': self.memory.get_emotional_context()
            }
            
            # Get activity information
            activity_info = {
                'is_busy': self.is_busy,
                'needs_activity_exit': self.needs_activity_exit,
                'current_activity': None,
                'activity_duration': 0,
                'activity_context': self.current_activity_context
            }
            
            if self.is_busy and hasattr(self.activity_manager, 'current_activity'):
                activity = self.activity_manager.current_activity
                if activity:
                    activity_info.update({
                        'current_activity': activity.type.value,
                        'activity_duration': time.time() - activity.start_time
                    })
            
            # Build the context dictionary
            context = {
                'current_room': current_room.value if current_room else 'unknown',
                'available_objects': [obj.type.value for obj in available_objects if obj is not None],
                'available_directions': self._get_available_directions(),
                'recent_actions': self.action_history[-5:] if self.action_history else [],
                **needs_info,
                **memory_info,
                **activity_info
            }
            
            # Only check for environmental audio if we're not busy
            if not self.is_busy:
                try:
                    environmental_audio = self.listen_to_environment()
                    if environmental_audio:  # Only add to context if we heard something
                        context['environmental_audio'] = environmental_audio
                except Exception as e:
                    logging.warning(f"Failed to listen to environment: {e}")
            
            return context
            
        except Exception as e:
            logging.error(f"Error getting context: {e}", exc_info=True)
            # Return a minimal context to allow the character to continue functioning
            return {
                'current_room': 'unknown',
                'available_objects': [],
                'needs': self.needs,
                'urgent_needs': [],
                'need_status': {},
                'recent_actions': [],
                'recent_memories': [],
                'important_memories': [],
                'emotional_state': {},
                'available_directions': [],
                'is_busy': False,
                'needs_activity_exit': False
            }

    def _get_available_directions(self) -> List[str]:
        available = []
        for direction in Direction:
            new_pos = self.position.move(direction)
            if self.house.is_valid_move(new_pos):
                available.append(direction.value)
        return available

    def _execute_decision(self, decision: Dict) -> str:
        action = decision['action']
        target = decision['target']
        
        if action == 'move':
            try:
                direction = Direction(target)
                if self.move(direction):
                    result = f"Moved {direction.value} to {self.house.get_room(self.position).value}"
                    self.memory.add_memory(
                        f"Moved to {self.house.get_room(self.position).value}",
                        importance=0.4
                    )
                else:
                    result = f"Cannot move {direction.value} from here"
            except ValueError:
                result = f"Invalid direction: {target}"
        
        elif action == 'use':
            try:
                object_type = ObjectType(target)
                if self.perform_action(object_type, action):
                    result = f"Using {object_type.value}"
                    self.memory.add_memory(
                        f"Used {object_type.value} to satisfy needs",
                        importance=0.6,
                        emotions={'satisfaction': 0.7}
                    )
                else:
                    result = f"Cannot use {object_type.value} - not found in current room"
            except ValueError:
                result = f"Invalid object: {target}"
        
        elif action == 'speak':
            speech_file = self.speak(target)
            if speech_file:
                result = f"Spoke: {target}"
                self.memory.add_memory(
                    f"Said: {target}",
                    importance=0.5,
                    emotions={'expressive': 0.6}
                )
            else:
                result = "Failed to speak"
            return result
        
        else:
            result = "Idle"

        self.action_history.append(f"{action} {target}")
        return result

    def move(self, direction: Direction) -> bool:
        new_position = self.position.move(direction)
        if self.house.is_valid_move(new_position):
            self.position = new_position
            self.current_room = self.house.get_room(new_position)
            return True
        return False

    def perform_action(self, object_type: ObjectType, action: str) -> bool:
        objects = self.house.get_objects_in_room(self.position)
        target_object = next((obj for obj in objects if obj.type == object_type), None)
        
        if not target_object:
            return False

        # Initialize browser only when using computer or phone
        if object_type in [ObjectType.COMPUTER, ObjectType.PHONE]:
            if not self.browser:
                try:
                    logging.info("Initializing browser for computer/phone use...")
                    self.browser = BrowserInterface()
                    logging.info("Browser initialized successfully")
                except Exception as e:
                    logging.error(f"Failed to initialize browser: {str(e)}")
                    return False

        # Handle activity exit actions
        if action.startswith('exit_'):
            if self.is_busy and self.needs_activity_exit:
                activity_type = self.activity_manager.current_activity.type
                self.activity_manager.exit_activity()
                self.current_activity_context = None
                
                # Close browser if we're exiting computer/phone activity
                if object_type in [ObjectType.COMPUTER, ObjectType.PHONE] and self.browser:
                    try:
                        self.browser.close()
                        self.browser = None
                        logging.info("Browser closed after finishing computer/phone activity")
                    except Exception as e:
                        logging.error(f"Error closing browser: {str(e)}")
                
                self.memory.add_memory(
                    f"Finished {activity_type.value}",
                    importance=0.5,
                    emotions={'satisfied': 0.6}
                )
                return True
            return False

        # Check if object has activity info
        if target_object.activity_info and action.startswith('use_'):
            if self.is_busy:
                return False  # Can't start new activity while busy
                
            # Start the activity
            success = self.activity_manager.start_activity(
                activity_type=target_object.activity_info.type,
                duration=target_object.activity_info.duration,
                need_changes=target_object.activity_info.need_changes,
                exit_condition=target_object.activity_info.exit_condition
            )
            
            if success:
                self.current_activity_context = {
                    'object': object_type.value,
                    'start_time': time.time(),
                    'initial_needs': self.needs.copy()
                }
                self.memory.add_memory(
                    f"Started using {object_type.value}",
                    importance=0.6,
                    emotions={'engaged': 0.7}
                )
                return True

        # Handle regular actions
        if action in target_object.actions:
            for need, effect in target_object.need_effects.items():
                self.needs_system.modify(need, effect)
            return True
            
        return False

    def _generate_coding_prompt(self, context: dict) -> str:
        """Generate a coding prompt based on character's context"""
        # Consider character's needs, memories, and current state
        recent_memories = context.get('recent_memories', [])
        emotional_state = context.get('emotional_state', {})
        
        # Example prompt generation
        if "bored" in emotional_state or context['needs'].get('fun', 100) < 50:
            return "Create a fun game or entertainment program"
        elif context['needs'].get('social', 100) < 50:
            return "Create a chatbot or social interaction program"
        elif any("coding" in memory for memory in recent_memories):
            return "Continue or improve upon previous coding project"
        else:
            return "Create a useful utility program or tool"

    def _generate_journal_content(self, context: dict) -> dict:
        """Generate journal content based on character's context"""
        prompt = {
            "task": "journal_entry",
            "emotional_state": context.get('emotional_state', {}),
            "recent_memories": context.get('recent_memories', []),
            "needs": context.get('needs', {}),
            "current_room": context.get('current_room', "unknown")
        }
        
        # Get journal content from LLM
        response = self.llm.generate_journal_entry(prompt)
        
        # Format the response with additional metadata
        return {
            "text": response.get("content", ""),
            "mood": context.get('emotional_state', {}),
            "tags": response.get("tags", []),
            "related_memories": context.get('recent_memories', [])[:3]
        }

    def handle_phone_call(self, message: str) -> str:
        """Handle incoming phone calls from the user"""
        if not hasattr(self, 'phone_system'):
            self.phone_system = PhoneSystem(self)
        
        # Use start_call instead of directly calling handle_text_call
        response = self.phone_system.start_call(message)
        return response

    def _initialize_knowledge(self):
        # Add basic semantic knowledge about the house and rooms
        for pos, room_type in self.house.rooms.items():
            self.knowledge_system.add_semantic_knowledge(
                f"The {room_type.value} is located at position ({pos.x}, {pos.y})",
                metadata={'room_type': room_type.value}
            )
            
        # Add knowledge about object effects - with None check
        for pos, objects in self.house.objects.items():
            for obj in objects:
                if obj is not None:  # Add check for None objects
                    self.knowledge_system.add_semantic_knowledge(
                        f"The {obj.type.value} can be used for: {', '.join(obj.actions)}. Effects: {obj.need_effects}",
                        metadata={'object_type': obj.type.value}
                    )
            
        # Add some periodic patterns
        self.knowledge_system.add_periodic_pattern(
            "Energy levels drop significantly after continuous computer use",
            "frequent",
            metadata={'need': 'energy'}
        )

    def _detect_patterns(self, actions: List[str]) -> Optional[str]:
        """Analyze recent actions to detect patterns"""
        # Simple pattern detection example
        action_counts = {}
        for action in actions:
            action_counts[action] = action_counts.get(action, 0) + 1
            
        for action, count in action_counts.items():
            if count >= 3:  # If same action appears 3+ times in last 10 actions
                return f"Frequently performs action: {action}"
                
        return None

    def listen_to_environment(self) -> Optional[str]:
        """Listen to the environment and transcribe any speech"""
        try:
            if not self.ears.is_listening:
                self.ears.start_listening()
            
            transcription = self.ears.listen_and_transcribe()
            
            if transcription:
                self.memory.add_memory(
                    f"Heard in environment: {transcription}",
                    importance=0.5,
                    emotions={"attentive": 0.6}
                )
                
                # Add to knowledge system
                self.knowledge_system.add_episodic_memory(
                    f"Heard: {transcription}",
                    emotions={"attentive": 0.6}
                )
                
                return transcription
            
            return None

        except Exception as e:
            logging.warning(f"Error listening to environment: {e}")
            if self.ears.is_listening:
                self.ears.stop_listening()
            return None

    def speak(self, text: str) -> Optional[Path]:
        """Speak through system speakers"""
        self.voice_manager.set_output_mode("speakers")
        audio_file = self.voice_manager.speak(text)
        
        if audio_file:
            self.memory.add_memory(
                f"Spoke: {text}",
                importance=0.4,
                emotions={'expressive': 0.6}
            )
        return audio_file
        
    def speak_in_voice_chat(self, text: str) -> bool:
        """Speak through virtual microphone for voice chat"""
        self.voice_manager.set_output_mode("virtual_mic")
        audio_file = self.voice_manager.speak(text)
        
        if audio_file:
            self.memory.add_memory(
                f"Spoke in voice chat: {text}",
                importance=0.5,
                emotions={'social': 0.6}
            )
            return True
        return False