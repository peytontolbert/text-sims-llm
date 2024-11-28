import json
import os
from typing import Dict, List, Optional, Set
from src.utils.models import Position
from src.utils.constants import BuildingType, RoomType
from src.environment.house import House
from src.environment.house_manager import HouseManager
from src.environment.world_state import WorldState

class Plot:
    def __init__(self, position: Position, building_type: BuildingType = None):
        self.position = position
        self.building_type = building_type
        self.building = None
        self.owner = None
        self.locked = False
        self.allowed_visitors: Set[str] = set()  # Set of character names allowed to enter

    def lock(self, owner_name: str):
        if self.owner == owner_name:
            self.locked = True
            return True
        return False

    def unlock(self, owner_name: str):
        if self.owner == owner_name:
            self.locked = False
            return True
        return False

    def can_enter(self, character_name: str) -> bool:
        return (not self.locked or 
                character_name == self.owner or 
                character_name in self.allowed_visitors)

    def grant_access(self, owner_name: str, visitor_name: str) -> bool:
        if self.owner == owner_name:
            self.allowed_visitors.add(visitor_name)
            return True
        return False

    def revoke_access(self, owner_name: str, visitor_name: str) -> bool:
        if self.owner == owner_name:
            self.allowed_visitors.discard(visitor_name)
            return True
        return False

class GameMap:
    def __init__(self):
        self.plots: Dict[Position, Plot] = {}
        self.house_manager = HouseManager()
        self.world_state = WorldState()
        self.load_map()

    def load_map(self):
        """Load map data from JSON file"""
        map_path = os.path.join(os.path.dirname(__file__), 'map.json')
        try:
            with open(map_path, 'r') as f:
                map_data = json.load(f)
                
            # Initialize plots from map data
            for area in map_data['plots'].values():
                for plot_data in area.values():
                    position = Position(plot_data['position']['x'], plot_data['position']['y'])
                    building_type = BuildingType[plot_data['type']]
                    
                    plot = Plot(position, building_type)
                    
                    # Set additional plot data if available
                    if 'owner' in plot_data:
                        plot.owner = plot_data['owner']
                    if 'locked' in plot_data:
                        plot.locked = plot_data['locked']
                    if 'allowed_visitors' in plot_data:
                        plot.allowed_visitors = set(plot_data['allowed_visitors'])
                    
                    # If it's a house plot, link it to the house database
                    if building_type == BuildingType.HOUSE and 'house_id' in plot_data:
                        house_data = self.house_manager.get_house_by_id(plot_data['house_id'])
                        if house_data and not house_data['owner']:
                            plot.building = self.house_manager.create_house_instance(plot_data['house_id'])
                    
                    self.plots[position] = plot
                    
        except FileNotFoundError:
            print(f"Warning: Map database not found at {map_path}")
            self.initialize_default_map()

    def save_map(self):
        """Save current map state back to JSON"""
        map_data = {
            "plots": {
                "residential_area": {},
                "commercial_area": {},
                "empty_plots": {}
            }
        }
        
        for pos, plot in self.plots.items():
            plot_data = {
                "position": {"x": pos.x, "y": pos.y},
                "type": plot.building_type.name,
                "owner": plot.owner,
                "locked": plot.locked,
                "allowed_visitors": list(plot.allowed_visitors)
            }
            
            if plot.building_type == BuildingType.HOUSE:
                area = "residential_area"
            elif plot.building_type == BuildingType.SUPERMARKET:
                area = "commercial_area"
            else:
                area = "empty_plots"
                
            map_data["plots"][area][f"plot_{pos.x}_{pos.y}"] = plot_data
        
        map_path = os.path.join(os.path.dirname(__file__), 'map.json')
        with open(map_path, 'w') as f:
            json.dump(map_data, f, indent=4)

    def assign_house_to_character(self, character_name: str, house_position: Position) -> bool:
        plot = self.plots.get(house_position)
        if plot and plot.building_type == BuildingType.HOUSE:
            # First check if character already owns this house
            if plot.owner == character_name:
                # Create new house data if it doesn't exist
                house_id = "house_1"
                if house_id not in self.house_manager.houses:
                    new_house_data = {
                        "id": house_id,
                        "name": "Default House",
                        "position": {"x": house_position.x, "y": house_position.y},
                        "owner": character_name,
                        "price": 20000,
                        "rooms": {
                            "hallway": {
                                "type": "HALLWAY",
                                "position": {"x": 0, "y": -1},
                                "objects": ["door"]
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
                        },
                        "description": "A comfortable starter home."
                    }
                    self.house_manager.add_house(new_house_data)
                
                plot.building = self.house_manager.create_house_instance(house_id)
                return True
            
            # If house is unowned, assign it
            if not plot.owner:
                # Find the house in the house manager
                house_data = self.house_manager.get_house_by_position(house_position)
                if house_data:
                    if self.house_manager.assign_house_to_owner(house_data['id'], character_name):
                        plot.owner = character_name
                        plot.building = self.house_manager.create_house_instance(house_data['id'])
                        self.save_map()
                        return True
                else:
                    # If no house data found, create a new default house
                    new_house_id = f"house_{len(self.house_manager.houses) + 1}"
                    new_house_data = {
                        "id": new_house_id,
                        "name": f"New House {new_house_id}",
                        "position": {"x": house_position.x, "y": house_position.y},
                        "owner": character_name,
                        "price": 20000,
                        "rooms": {
                            "hallway": {
                                "type": "HALLWAY",
                                "position": {"x": 0, "y": -1},
                                "objects": ["door"]
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
                        },
                        "description": "A newly built home."
                    }
                    
                    if self.house_manager.add_house(new_house_data):
                        plot.owner = character_name
                        plot.building = self.house_manager.create_house_instance(new_house_id)
                        self.save_map()
                        return True
        return False

    def get_available_houses(self) -> List[Position]:
        return [pos for pos, plot in self.plots.items() 
                if plot.building_type == BuildingType.HOUSE and not plot.owner]

    def get_empty_plots(self) -> List[Position]:
        return [pos for pos, plot in self.plots.items() 
                if plot.building_type == BuildingType.EMPTY]

    def get_plot(self, position: Position) -> Optional[Plot]:
        return self.plots.get(position)

    def is_valid_move(self, position: Position) -> bool:
        return position in self.plots

    def can_enter_plot(self, position: Position, character_name: str) -> bool:
        plot = self.plots.get(position)
        if plot:
            return plot.can_enter(character_name)
        return False

    def get_building(self, position: Position) -> Optional[House]:
        plot = self.plots.get(position)
        if plot:
            return plot.building
        return None

    def initialize_default_map(self):
        """Initialize a default map if JSON file is not found"""
        # Add default house plots
        for y in range(3):
            pos = Position(0, y)
            plot = Plot(pos, BuildingType.HOUSE)
            self.plots[pos] = plot

        # Add supermarket
        supermarket_pos = Position(2, 0)
        plot = Plot(supermarket_pos, BuildingType.SUPERMARKET)
        self.plots[supermarket_pos] = plot

        # Add empty plots
        empty_positions = [
            Position(2, 1),
            Position(2, 2),
            Position(1, 2)
        ]
        for pos in empty_positions:
            plot = Plot(pos, BuildingType.EMPTY)
            self.plots[pos] = plot

    def move_character(self, character_name: str, new_position: Position) -> bool:
        """Move a character to a new position if valid"""
        if self.is_valid_move(new_position):
            plot = self.get_plot(new_position)
            if plot and plot.can_enter(character_name):
                self.world_state.set_character_position(character_name, new_position)
                return True
        return False

    def get_character_location(self, character_name: str) -> Optional[Position]:
        """Get a character's current position"""
        return self.world_state.get_character_position(character_name)

    def update(self, delta_time: float):
        """Update the game world state"""
        self.world_state.update_time(delta_time)

    def add_new_house(self, character_name: str) -> Optional[Position]:
        """Add a new house plot to the map for a character"""
        # Find a suitable position for the new house
        # Try positions incrementally until finding an unused spot
        for x in range(-5, 6):  # Search in a reasonable range
            for y in range(-5, 6):
                new_pos = Position(x, y)
                if new_pos not in self.plots:
                    # Create new plot with house
                    plot = Plot(new_pos, BuildingType.HOUSE)
                    plot.owner = character_name
                    
                    # Create a new house instance
                    house_id = f"house_{len(self.house_manager.houses) + 1}"
                    new_house_data = {
                        "id": house_id,
                        "name": f"New House {house_id}",
                        "position": {"x": x, "y": y},
                        "owner": character_name,
                        "price": 20000,
                        "rooms": {
                            "hallway": {
                                "type": "HALLWAY",
                                "position": {"x": 0, "y": -1},
                                "objects": ["door"]
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
                        },
                        "description": "A newly built home."
                    }
                    
                    # Add house to house manager
                    self.house_manager.add_house(new_house_data)
                    plot.building = self.house_manager.create_house_instance(house_id)
                    
                    # Add plot to map
                    self.plots[new_pos] = plot
                    self.save_map()
                    
                    return new_pos
        
        return None
