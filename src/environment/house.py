# File: house.py
from typing import Dict, List, Optional
from src.utils.models import Position, GameObject
from src.utils.constants import RoomType, ObjectType
from collections import defaultdict
from src.environment.objects import ObjectManager
from src.utils.position import Position

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
    def __init__(self, position: Position):
        self.position = position
        self.owner = None  # Add owner attribute
        # Initialize default rooms
        self.rooms = {
            "hallway": {
                "type": "HALLWAY",
                "position": {"x": 0, "y": -1},
                "objects": ["door", "doorbell"]
            },
            "bedroom": {
                "type": "BEDROOM",
                "position": {"x": 0, "y": 0},
                "objects": ["bed"]
            },
            "bathroom": {
                "type": "BATHROOM",
                "position": {"x": 1, "y": 0},
                "objects": ["toilet", "shower"]
            },
            "living_room": {
                "type": "LIVING_ROOM",
                "position": {"x": 0, "y": 1},
                "objects": ["tv", "computer", "couch", "phone"]
            },
            "kitchen": {
                "type": "KITCHEN",
                "position": {"x": 1, "y": 1},
                "objects": ["fridge", "stove"]
            }
        }
        self.authorized_users = set()
        self.front_door = Door()
        self.doorbell_queue = []  # Store visitors waiting at door

    def get_room(self, position: Position) -> RoomType:
        """Get the room type at the given position"""
        # Convert position to room coordinates relative to house
        rel_x = position.x - self.position.x
        rel_y = position.y - self.position.y
        
        # Look up room by relative position
        for room in self.rooms.values():
            room_pos = room["position"]
            if room_pos["x"] == rel_x and room_pos["y"] == rel_y:
                return RoomType[room["type"]]
        
        # Default to LIVING_ROOM if room not found
        return RoomType.LIVING_ROOM

    def authorize_user(self, user_name: str):
        """Authorize a user to access the house"""
        self.authorized_users.add(user_name)

    def is_authorized(self, user_name: str) -> bool:
        """Check if a user is authorized to access the house"""
        return user_name in self.authorized_users

    def get_available_rooms(self) -> List[RoomType]:
        """Get list of available rooms in the house"""
        return [RoomType[room["type"]] for room in self.rooms.values()]

    def get_objects_in_room(self, room_type: RoomType) -> List[str]:
        """Get list of objects in a specific room"""
        # If passed a Position instead of RoomType, get the room type first
        if isinstance(room_type, Position):
            room_type = self.get_room(room_type)
        
        # Now look up objects for this room type
        for room in self.rooms.values():
            if room["type"] == room_type.value:
                return room["objects"]
        return []

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

    def serialize(self) -> dict:
        """Serialize house state"""
        return {
            'rooms': {
                f"{pos.x},{pos.y}": room.value
                for pos, room in self.rooms.items()
            },
            'objects': {
                f"{pos.x},{pos.y}": [
                    obj.serialize() if obj else None
                    for obj in objects
                ]
                for pos, objects in self.objects.items()
            },
            'authorized_users': list(self.authorized_users)
        }

    def ring_doorbell(self, visitor_name: str) -> bool:
        """Handle doorbell ring event"""
        if visitor_name not in self.doorbell_queue:
            self.doorbell_queue.append(visitor_name)
            # Create notification message
            notification = f"{visitor_name} is waiting at the door"
            
            # Add notification to environment for all characters in house
            for character_name in self.authorized_users:
                if character_name in self.world_state.character_positions:
                    char_pos = self.world_state.character_positions[character_name]
                    if self.position == char_pos:  # If character is in this house
                        self.memory.add_memory(
                            notification,
                            importance=0.7,
                            emotions={'alert': 0.8}
                        )
            return True
        return False
        
    def remove_from_doorbell_queue(self, visitor_name: str):
        """Remove visitor from doorbell queue after they're let in or leave"""
        if visitor_name in self.doorbell_queue:
            self.doorbell_queue.remove(visitor_name)

    def update(self, delta_time: float):
        """Update house state based on time passed"""
        # Currently no time-based updates needed, but we'll implement the method
        # for future features like:
        # - Utility costs
        # - Object wear and tear
        # - Environmental changes
        pass