import json
import os
from typing import Dict, List, Optional
from src.utils.models import Position
from src.environment.house import House
from src.environment.world_state import WorldState
import logging
import time

class GameMap:
    def __init__(self):
        # Initialize logger first
        self.logger = logging.getLogger("GameMap")
        
        # Initialize basic structures
        self.active_characters = set()
        self.characters = {}
        self.character_positions = {}
        self.plots: Dict[Position, House] = {}
        
        try:
            # Initialize world state
            self.world_state = WorldState()
            self.logger.info("World state initialized")
            
            # Load map state and sync with world state
            self._load_map_state()
            self._sync_with_world_state()
            self.logger.info("GameMap initialized successfully")
        except Exception as e:
            self.logger.error(f"Error during GameMap initialization: {str(e)}")
            raise
        
    def _load_map_state(self):
        """Load initial map state from configuration"""
        try:
            map_config_path = os.path.join(os.path.dirname(__file__), 'houses.json')
            with open(map_config_path, 'r') as f:
                map_data = json.load(f)
                
            # Load houses/plots
            for plot_data in map_data.get('plots', []):
                pos = Position(plot_data['position']['x'], plot_data['position']['y'])
                house = House(pos)
                if 'owner' in plot_data:
                    house.owner = plot_data['owner']
                self.plots[pos] = house
                
            self.logger.info(f"Loaded {len(self.plots)} plots from map configuration")
            
        except Exception as e:
            self.logger.error(f"Error loading map state: {str(e)}")
            # Create a default plot if loading fails
            default_pos = Position(0, 0)
            self.plots[default_pos] = House(default_pos)
            
    def _sync_with_world_state(self):
        """Synchronize game map state with world state"""
        try:
            if not hasattr(self.world_state, 'characters'):
                self.logger.warning("World state missing characters dict, initializing empty")
                self.world_state.characters = {}
            
            # Sync characters from world state
            for char_name, char_data in self.world_state.characters.items():
                # Update characters dict
                self.characters[char_name] = char_data
                
                # Update character positions
                if 'position' in char_data:
                    pos = Position(
                        char_data['position']['x'],
                        char_data['position']['y']
                    )
                    self.character_positions[char_name] = pos
                
                # Update active characters
                if char_data.get('online', False) and \
                   time.time() - char_data.get('last_update', 0) < 30:
                    self.active_characters.add(char_name)
            
            self.logger.info(f"Successfully synced {len(self.characters)} characters from world state")
            
        except Exception as e:
            self.logger.error(f"Error syncing with world state: {str(e)}")
            # Initialize empty state if sync fails
            self.characters = {}
            self.character_positions = {}
            self.active_characters = set()
            
    def register_character(self, character_data: dict) -> bool:
        """Register a character with the game map"""
        try:
            name = character_data['name']
            
            # Update character data
            character_data['online'] = True
            character_data['last_update'] = time.time()
            character_data['status'] = 'active'
            
            # Update world state first
            self.world_state.characters[name] = character_data
            pos = Position(
                character_data['position']['x'],
                character_data['position']['y']
            )
            self.world_state.set_character_position(name, pos)
            
            # Update local tracking
            self.characters[name] = character_data
            self.character_positions[name] = pos
            self.active_characters.add(name)
            
            self.logger.info(f"Successfully registered character {name} at position {pos}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering character: {str(e)}")
            return False
            
    def update_character(self, character_data: dict) -> bool:
        """Update a character's state in the game map"""
        try:
            name = character_data['name']
            
            # Update timestamps and status
            character_data['last_update'] = time.time()
            character_data['online'] = True
            character_data['status'] = 'active'
            
            # Update local tracking
            self.characters[name] = character_data
            self.active_characters.add(name)
            
            # Update position
            pos = Position(
                character_data['position']['x'],
                character_data['position']['y']
            )
            self.character_positions[name] = pos
            
            # Update world state
            self.world_state.characters[name] = character_data
            self.world_state.set_character_position(name, pos)
            
            self.logger.info(f"Successfully updated character {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating character: {str(e)}")
            return False
            
    def get_empty_plots(self) -> List[Position]:
        """Get list of unowned plots"""
        return [pos for pos, house in self.plots.items() if not house.owner]
        
    def assign_house_to_character(self, character_name: str, position: Position) -> bool:
        """Assign a house at the given position to a character"""
        # Create a new house if one doesn't exist at this position
        if position not in self.plots:
            self.plots[position] = House(position)
            self.logger.info(f"Created new house at {position}")
        
        house = self.plots[position]
        if not house.owner:
            house.owner = character_name
            # Add character to active characters set
            self.active_characters.add(character_name)
            # Update world state
            self.world_state.characters[character_name] = {
                'name': character_name,
                'position': {'x': position.x, 'y': position.y},
                'online': True,
                'last_update': time.time(),
                'status': 'active'
            }
            self.logger.info(f"Assigned house at {position} to {character_name}")
            return True
        elif house.owner == character_name:
            # Ensure character is in active set and world state
            self.active_characters.add(character_name)
            if character_name not in self.world_state.characters:
                self.world_state.characters[character_name] = {
                    'name': character_name,
                    'position': {'x': position.x, 'y': position.y},
                    'online': True,
                    'last_update': time.time(),
                    'status': 'active'
                }
            return True  # Already owned by this character
        
        return False
        
    def get_building(self, position: Position) -> Optional[House]:
        """Get building at the given position"""
        return self.plots.get(position)
        
    def update(self, delta_time: float):
        """Update game map state"""
        # Update world time
        self.world_state.update_time(delta_time)
        
        # Update houses
        for house in self.plots.values():
            house.update(delta_time)
            
    def serialize(self) -> dict:
        """Serialize game map state"""
        return {
            'plots': [
                {
                    'position': {'x': pos.x, 'y': pos.y},
                    'owner': house.owner if house.owner else None
                }
                for pos, house in self.plots.items()
            ],
            'characters': self.characters,
            'world_state': self.world_state.serialize()
        }
