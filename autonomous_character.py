# File: autonomous_character.py
from typing import Dict, List, Optional
from models import Position
from constants import Direction, ObjectType
from house import House
from browser_interface import BrowserInterface
from llm_interface import LLMDecisionMaker
from memory_system import Memory
from needs_system import Needs
from phone_system import PhoneSystem
import time

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

    @property
    def needs(self) -> Dict[str, float]:
        return self.needs_system.values

    def update(self, delta_time: float) -> str:
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
                self.browser.browse('http://www.google.com')
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

    def handle_phone_call(self, message: str) -> str:
        """Handle incoming phone calls from the user"""
        if not hasattr(self, 'phone_system'):
            self.phone_system = PhoneSystem(self)
        return self.phone_system.start_call(message)