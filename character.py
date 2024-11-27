
# File: character.py
import time
from typing import Optional, Dict, List
from models import Position
from constants import Direction, ObjectType
from house import House
from browser_interface import BrowserInterface

class SimCharacter:
    def __init__(self, name: str, house: House):
        self.name = name
        self.position = Position(0, 0)
        self.needs = {
            'energy': 100.0,
            'hunger': 100.0,
            'hygiene': 100.0,
            'fun': 100.0,
            'bladder': 100.0,
            'social': 100.0,
            'comfort': 100.0
        }
        self.house = house
        self.browser = BrowserInterface()
        self.current_action = None
        self.thought = "I wonder what I should do today..."
        self.last_action_time = time.time()

    def update_needs(self, delta_time: float):
        decay_rates = {
            'energy': 2.0,
            'hunger': 1.5,
            'hygiene': 1.0,
            'fun': 2.0,
            'bladder': 3.0,
            'social': 1.0,
            'comfort': 1.0
        }
        
        for need in self.needs:
            decay = decay_rates[need] * delta_time
            self.needs[need] = max(0.0, min(100.0, self.needs[need] - decay))

    def move(self, direction: Direction) -> bool:
        new_position = self.position.move(direction)
        if self.house.is_valid_move(new_position):
            self.position = new_position
            return True
        return False

    def get_available_actions(self) -> Dict[str, List[str]]:
        objects = self.house.get_objects_in_room(self.position)
        return {obj.type.value: obj.actions for obj in objects}

    def perform_action(self, object_type: ObjectType, action: str) -> bool:
        objects = self.house.get_objects_in_room(self.position)
        target_object = next((obj for obj in objects if obj.type == object_type), None)
        
        if target_object and action in target_object.actions:
            # Special handling for computer
            if object_type == ObjectType.COMPUTER and action == 'browse':
                self.browser.browse('http://www.google.com')
            
            # Apply need effects
            for need, effect in target_object.need_effects.items():
                self.needs[need] = max(0.0, min(100.0, self.needs[need] + effect))
            
            self.current_action = f"{action} using {object_type.value}"
            self.last_action_time = time.time()
            return True
        return False

    def get_status(self) -> str:
        room = self.house.get_room(self.position)
        status = [
            f"Location: {room.value}",
            "Needs:"
        ]
        for need, value in self.needs.items():
            status.append(f"  {need}: {value:.1f}")
        return "\n".join(status)

    def get_urgent_needs(self) -> List[str]:
        return [need for need, value in self.needs.items() if value < 30.0]
