# File: house.py
from typing import Dict, List, Optional
from src.utils.models import Position, GameObject
from src.utils.constants import RoomType, ObjectType
from collections import defaultdict
from src.environment.objects import ObjectManager

class Door:
    def __init__(self):
        self.locked = False
        self.authorized_users = set()  # Set of character names allowed to use the door

    def lock(self, user: str) -> bool:
        if user in self.authorized_users:
            self.locked = True
            return True
        return False

    def unlock(self, user: str) -> bool:
        if user in self.authorized_users:
            self.locked = False
            return True
        return False

    def can_use(self, user: str) -> bool:
        return not self.locked or user in self.authorized_users

    def add_authorized_user(self, user: str):
        self.authorized_users.add(user)

    def remove_authorized_user(self, user: str):
        self.authorized_users.discard(user)

class House:
    def __init__(self):
        self.rooms: Dict[Position, RoomType] = {}
        self.objects: Dict[Position, List[GameObject]] = defaultdict(list)
        self.front_door = Door()
        self.object_manager = ObjectManager()
        self.initialize_layout()

    def initialize_layout(self):
        """Initialize default house layout if none is provided"""
        # Always ensure we have at least these basic rooms
        self.rooms = {
            Position(0, -1): RoomType.HALLWAY,
            Position(0, 0): RoomType.BEDROOM,
            Position(1, 0): RoomType.BATHROOM,
            Position(0, 1): RoomType.LIVING_ROOM,
            Position(1, 1): RoomType.KITCHEN
        }
        
        # Initialize basic objects with defaultdict
        self.objects.clear()  # Clear any existing objects
        
        # Add objects to rooms - explicitly create lists for each position
        bedroom_pos = Position(0, 0)
        self.objects[bedroom_pos] = [self.object_manager.get_house_item('bed')]
        
        hallway_pos = Position(0, -1)
        self.objects[hallway_pos] = [self.object_manager.get_house_item('door')]
        
        bathroom_pos = Position(1, 0)
        self.objects[bathroom_pos] = [
            self.object_manager.get_house_item('toilet'),
            self.object_manager.get_house_item('shower')
        ]
        
        living_room_pos = Position(0, 1)
        self.objects[living_room_pos] = [
            self.object_manager.get_house_item('tv'),
            self.object_manager.get_house_item('computer'),
            self.object_manager.get_house_item('couch'),
            self.object_manager.get_house_item('phone')
        ]
        
        kitchen_pos = Position(1, 1)
        self.objects[kitchen_pos] = [
            self.object_manager.get_house_item('fridge'),
            self.object_manager.get_house_item('stove')
        ]

    def get_room(self, position: Position) -> Optional[RoomType]:
        return self.rooms.get(position)

    def get_objects_in_room(self, position: Position) -> List[GameObject]:
        """Get all objects in a room at the given position"""
        # Debug print to check position and objects
        objects = self.objects.get(position, [])
        print(f"Getting objects at position {position}, found: {[obj.type.value for obj in objects]}")
        return objects

    def is_valid_move(self, position: Position) -> bool:
        return position in self.rooms

    def can_enter_house(self, character_name: str) -> bool:
        """Check if a character can enter the house through the front door"""
        return self.front_door.can_use(character_name)

    def authorize_user(self, character_name: str):
        """Give a character permission to use the front door"""
        self.front_door.add_authorized_user(character_name)

    def deauthorize_user(self, character_name: str):
        """Remove a character's permission to use the front door"""
        self.front_door.remove_authorized_user(character_name)

    def lock_door(self, character_name: str) -> bool:
        """Lock the front door if the character is authorized"""
        return self.front_door.lock(character_name)

    def unlock_door(self, character_name: str) -> bool:
        """Unlock the front door if the character is authorized"""
        return self.front_door.unlock(character_name)

    def is_entrance(self, position: Position) -> bool:
        """Check if a position is the entrance hallway"""
        return position == Position(0, -1)

    def is_door_locked(self) -> bool:
        """Check if the front door is locked"""
        return self.front_door.locked