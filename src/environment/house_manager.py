import json
import os
from typing import Dict, List, Optional
from src.utils.models import Position
from src.environment.house import House
from src.utils.constants import RoomType, ObjectType

class HouseManager:
    def __init__(self):
        self.houses: Dict[str, Dict] = {}
        self.load_houses()

    def load_houses(self):
        """Load houses from the JSON database"""
        houses_path = os.path.join(os.path.dirname(__file__), 'houses.json')
        try:
            with open(houses_path, 'r') as f:
                self.houses = json.load(f)
        except FileNotFoundError:
            print(f"Warning: Houses database not found at {houses_path}")
            self.houses = {}

    def save_houses(self):
        """Save current house states back to JSON"""
        houses_path = os.path.join(os.path.dirname(__file__), 'houses.json')
        with open(houses_path, 'w') as f:
            json.dump(self.houses, f, indent=4)

    def get_available_houses(self) -> List[Dict]:
        """Get list of houses without owners"""
        return [house for house in self.houses.values() if house['owner'] is None]

    def get_house_by_position(self, position: Position) -> Optional[Dict]:
        """Find house at given position"""
        for house in self.houses.values():
            house_pos = Position(house['position']['x'], house['position']['y'])
            if house_pos == position:
                return house
        return None

    def assign_house_to_owner(self, house_id: str, owner: str) -> bool:
        """Assign a house to an owner"""
        if house_id in self.houses and self.houses[house_id]['owner'] is None:
            self.houses[house_id]['owner'] = owner
            self.save_houses()
            return True
        return False

    def create_house_instance(self, house_id: str) -> House:
        """Create a House instance from house data"""
        house = House()  # Create base house instance with default layout
        
        if house_id in self.houses:
            house_data = self.houses[house_id]
            
            # Clear default layout
            house.rooms.clear()
            house.objects.clear()
            
            # Add rooms and objects from house data
            for room_id, room_data in house_data['rooms'].items():
                pos = Position(room_data['position']['x'], room_data['position']['y'])
                room_type = RoomType[room_data['type']]
                house.rooms[pos] = room_type
                
                # Create a new list for objects in this room
                house.objects[pos] = []
                
                # Add objects to room
                for obj_name in room_data['objects']:
                    game_object = house.object_manager.get_house_item(obj_name)
                    if game_object:
                        house.objects[pos].append(game_object)
                        print(f"Added {obj_name} to room at {pos}")
        
        # Verify objects were created properly
        for pos, objects in house.objects.items():
            print(f"Room at {pos} has objects: {[obj.type.value for obj in objects]}")
        
        return house

    def get_owner_house(self, owner: str) -> Optional[Dict]:
        """Get house data for a specific owner"""
        for house in self.houses.values():
            if house['owner'] == owner:
                return house
        return None

    def get_house_by_id(self, house_id: str) -> Optional[Dict]:
        """Get house data by its ID"""
        return self.houses.get(house_id)

    def add_house(self, house_data: Dict) -> bool:
        """Add a new house to the manager"""
        if 'id' not in house_data:
            return False
        
        house_id = house_data['id']
        self.houses[house_id] = house_data
        self.save_houses()
        return True
  