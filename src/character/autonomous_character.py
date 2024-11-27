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
import time
from datetime import datetime

class AutonomousCharacter:
    def __init__(self, name: str, house: House):
        self.name = name
        self.position = Position(0, 0)
        self.house = house
        self.browser = BrowserInterface()
        self.current_action = None
        self.thought = None
        self.last_action_time = time.time()
        self.decision_maker = LLMDecisionMaker()
        self.action_history = []
        
        # Replace direct needs dict with Needs system
        self.needs_system = Needs()
        self.memory = Memory()
        self.current_room = self.house.get_room(self.position)
        self.coding_system = CodingSystem(name)
        self.journal_system = JournalSystem(name)
        self.knowledge_system = KnowledgeSystem()
        
        # Add some initial knowledge
        self._initialize_knowledge()

    @property
    def needs(self) -> Dict[str, float]:
        return self.needs_system.values

    def update(self, delta_time: float) -> str:
        current_time = datetime.now()
        
        # Add current state as episodic memory with more context
        state_memory = (
            f"At {current_time.strftime('%H:%M')} in {self.current_room.value}. "
            f"Urgent needs: {self.needs_system.get_urgent_needs()}. "
            f"Last action: {self.action_history[-1] if self.action_history else 'None'}"
        )
        
        self.knowledge_system.add_episodic_memory(
            state_memory,
            emotions=self.memory.get_emotional_context()
        )
        
        # Detect and store periodic patterns
        if len(self.action_history) >= 10:
            recent_actions = self.action_history[-10:]
            pattern = self._detect_patterns(recent_actions)
            if pattern:
                self.knowledge_system.add_periodic_pattern(
                    pattern,
                    "hourly",
                    metadata={
                        'time_of_day': current_time.strftime('%H:%M'),
                        'needs_state': self.needs_system.get_need_status()
                    }
                )
        
        # Update needs using the needs system
        self.needs_system.update(delta_time)
        
        # Get current context
        context = self._get_context()
        
        # Get decision from LLM
        decision = self.decision_maker.make_decision(context)
        
        # Record the decision in memory
        self.memory.add_memory(
            f"Decided to {decision['action']} {decision['target']} because {decision['thought']}",
            importance=0.5
        )
        
        # Execute decision
        result = self._execute_decision(decision)
        
        # Record the result in memory
        self.memory.add_memory(
            f"Action result: {result}",
            importance=0.3
        )
        
        # Store the result as episodic memory
        self.knowledge_system.add_episodic_memory(
            f"Action result: {result}",
            emotions=self.memory.get_emotional_context()
        )
        
        self.thought = decision['thought']
        return result

    def _get_context(self) -> Dict:
        urgent_needs = self.needs_system.get_urgent_needs()
        need_status = self.needs_system.get_need_status()
        current_room = self.house.get_room(self.position)
        available_objects = self.house.get_objects_in_room(self.position)
        
        return {
            'current_room': current_room.value,
            'available_objects': [obj.type.value for obj in available_objects],
            'needs': self.needs,
            'need_status': need_status,
            'urgent_needs': urgent_needs,
            'recent_actions': self.action_history[-5:],
            'recent_memories': self.memory.get_recent_memories(5),
            'important_memories': self.memory.get_important_memories(),
            'emotional_state': self.memory.get_emotional_context(),
            'available_directions': self._get_available_directions()
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
        
        if target_object:
            if object_type == ObjectType.COMPUTER:
                if action == "code":
                    # Generate a coding task based on character's context
                    context = self._get_context()
                    coding_prompt = self._generate_coding_prompt(context)
                    
                    # Use LLM to generate the code
                    filename, content = self.coding_system.generate_code(coding_prompt)
                    
                    if filename and content:
                        if self.coding_system.create_file(filename, content):
                            self.memory.add_memory(
                                f"Created a new program: {filename}",
                                importance=0.7,
                                emotions={"pride": 0.8, "creativity": 0.9}
                            )
                            return f"Created new Python file: {filename}"
                    return "Failed to create Python file"

                elif action == "run_code":
                    files = self.coding_system.list_files()
                    if not files:
                        return "No Python files found"
                    latest_file = max(files)
                    success, output = self.coding_system.run_file(latest_file)
                    
                    # Record the result in memory
                    if success:
                        self.memory.add_memory(
                            f"Successfully ran program {latest_file}",
                            importance=0.6,
                            emotions={"satisfaction": 0.7}
                        )
                        return f"Ran {latest_file} successfully:\n{output}"
                    else:
                        self.memory.add_memory(
                            f"Failed to run program {latest_file}",
                            importance=0.5,
                            emotions={"frustration": 0.6}
                        )
                        return f"Failed to run {latest_file}: {output}"

                elif action == "write_journal":
                    # Generate journal content based on character's context
                    context = self._get_context()
                    journal_content = self._generate_journal_content(context)
                    
                    if self.journal_system.write_entry(journal_content):
                        self.memory.add_memory(
                            "Wrote in my journal about my thoughts and feelings",
                            importance=0.6,
                            emotions={"reflective": 0.8, "peaceful": 0.6}
                        )
                        return "Wrote a new journal entry"
                    return "Failed to write journal entry"

                elif action == "read_journal":
                    entries = self.journal_system.read_entries(5)  # Read last 5 entries
                    if entries:
                        self.memory.add_memory(
                            "Read through my past journal entries",
                            importance=0.5,
                            emotions={"nostalgic": 0.7, "reflective": 0.8}
                        )
                        return f"Read {len(entries)} journal entries"
                    return "No journal entries found"
            elif object_type == ObjectType.PHONE:
                # Initialize phone system if not exists
                if not hasattr(self, 'phone_system'):
                    self.phone_system = PhoneSystem(self)
                return True
            
            # Apply need effects using the needs system
            for need, effect in target_object.need_effects.items():
                self.needs_system.modify(need, effect)
            
            self.current_action = f"{action} {object_type.value}"
            self.last_action_time = time.time()
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
        return self.phone_system.start_call(message)

    def _initialize_knowledge(self):
        # Add basic semantic knowledge about the house and objects
        for pos, room_type in self.house.rooms.items():
            self.knowledge_system.add_semantic_knowledge(
                f"The {room_type.value} is located at position ({pos.x}, {pos.y})",
                metadata={'room_type': room_type.value}
            )
            
        # Add knowledge about object effects
        for pos, objects in self.house.objects.items():
            for obj in objects:
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