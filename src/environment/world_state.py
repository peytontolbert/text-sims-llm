from typing import Dict, Optional
from src.utils.position import Position
import logging
import json
import os
from datetime import datetime
import time

class WorldState:
    def __init__(self):
        # Initialize logger
        self.logger = logging.getLogger("WorldState")
        
        # Initialize basic attributes
        self.character_positions = {}
        self.characters = {}
        self.current_time = 8.0
        self.current_day = 1
        self.current_season = "spring"
        self.current_year = 1
        self.weather = "sunny"
        self.temperature = 22.0
        
        # Create default state file if it doesn't exist
        state_path = os.path.join(os.path.dirname(__file__), 'world_state.json')
        if not os.path.exists(state_path):
            self.logger.info("Creating default world state file")
            self._create_default_state()
        
        # Load state after initializing all attributes
        try:
            self.load_state()
            self.logger.info("World state loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load world state: {str(e)}")
            # Ensure we have at least empty character structures
            self.characters = {}
            self.character_positions = {}

    def _create_default_state(self):
        """Create a default world state file if none exists"""
        default_state = {
            "characters": {},
            "time": {
                "current_time": 8.0,
                "day": 1,
                "season": "spring",
                "year": 1
            },
            "weather": {
                "current": "sunny",
                "temperature": 22.0,
                "conditions": []
            },
            "buildings": {
                "supermarket": {
                    "position": {"x": 2, "y": 0},
                    "status": "open",
                    "current_visitors": [],
                    "inventory_last_restocked": datetime.now().isoformat()
                }
            },
            "events": {
                "scheduled": [],
                "active": []
            },
            "metadata": {
                "last_saved": datetime.now().isoformat(),
                "version": "1.0",
                "game_days_elapsed": 0
            }
        }
        
        state_path = os.path.join(os.path.dirname(__file__), 'world_state.json')
        with open(state_path, 'w') as f:
            json.dump(default_state, f, indent=4)
        
        return default_state

    def load_state(self):
        """Load world state from JSON file"""
        state_path = os.path.join(os.path.dirname(__file__), 'world_state.json')
        try:
            if not os.path.exists(state_path):
                self.logger.warning("World state file not found, creating default state")
                state_data = self._create_default_state()
            else:
                with open(state_path, 'r') as f:
                    state_data = json.load(f)
            
            # Load character positions
            for char_name, char_data in state_data.get('characters', {}).items():
                pos = char_data.get('position', {})
                self.character_positions[char_name] = Position(pos.get('x', 0), pos.get('y', 0))
                # Also load character data into characters dict
                self.characters[char_name] = char_data
            
            # Load time and date
            time_data = state_data.get('time', {})
            self.current_time = time_data.get('current_time', 8.0)
            self.current_day = time_data.get('day', 1)
            self.current_season = time_data.get('season', 'spring')
            self.current_year = time_data.get('year', 1)
            
            # Load weather
            weather_data = state_data.get('weather', {})
            self.weather = weather_data.get('current', 'sunny')
            self.temperature = weather_data.get('temperature', 22.0)
            
            self.logger.info(f"Loaded world state: Day {self.current_day}, {self.current_season} {self.current_year}, "
                          f"Time {self.current_time:.1f}, Weather: {self.weather}")
            
        except Exception as e:
            self.logger.error(f"Error loading world state: {str(e)}")
            # Create default state if loading fails
            state_data = self._create_default_state()
            self.characters = {}
            self.character_positions = {}
            self.current_time = 8.0
            self.current_day = 1
            self.current_season = "spring"
            self.current_year = 1
            self.weather = "sunny"
            self.temperature = 22.0

    def save_state(self):
        """Save current world state to JSON"""
        state_data = {
            "characters": {
                name: {
                    "position": {"x": pos.x, "y": pos.y} if pos else {"x": 0, "y": 0},
                    "home_position": {"x": pos.x, "y": pos.y} if pos else {"x": 0, "y": 0},
                    "last_active": datetime.now().isoformat(),
                    "status": "active" if self.is_character_online(name) else "offline",
                    "online": self.characters.get(name, {}).get('online', False),
                    "last_update": self.characters.get(name, {}).get('last_update', 0)
                }
                for name, pos in self.character_positions.items()
            },
            "time": {
                "current_time": self.current_time,
                "day": self.current_day,
                "season": self.current_season,
                "year": self.current_year
            },
            "weather": {
                "current": self.weather,
                "temperature": self.temperature,
                "conditions": []
            },
            "buildings": {
                "supermarket": {
                    "position": {"x": 2, "y": 0},
                    "status": "open" if self.is_daytime() else "closed",
                    "current_visitors": [],
                    "inventory_last_restocked": datetime.now().isoformat()
                }
            },
            "events": {
                "scheduled": [],
                "active": []
            },
            "metadata": {
                "last_saved": datetime.now().isoformat(),
                "version": "1.0",
                "game_days_elapsed": (self.current_year - 1) * 4 * 30 + 
                                   (["spring", "summer", "fall", "winter"].index(self.current_season)) * 30 +
                                   self.current_day - 1
            }
        }
        
        state_path = os.path.join(os.path.dirname(__file__), 'world_state.json')
        with open(state_path, 'w') as f:
            json.dump(state_data, f, indent=4)
        
        logging.debug("Saved world state")

    def update_time(self, delta_time: float):
        """Update game time (in hours)"""
        self.current_time = (self.current_time + delta_time) % 24
        
        # Handle day changes
        if self.current_time < delta_time:  # We wrapped around to a new day
            self.current_day += 1
            if self.current_day > 30:  # New season
                self.current_day = 1
                seasons = ["spring", "summer", "fall", "winter"]
                current_season_idx = seasons.index(self.current_season)
                self.current_season = seasons[(current_season_idx + 1) % 4]
                
                if self.current_season == "spring":  # New year
                    self.current_year += 1
            
            # Save state at the start of each new day
            self.save_state()
            
        logging.debug(f"Time updated to {self.current_time:.1f}, Day {self.current_day} of {self.current_season}")

    def get_time(self) -> float:
        """Get current game time (in hours)"""
        return self.current_time

    def is_daytime(self) -> bool:
        """Check if it's currently daytime (between 6:00 and 20:00)"""
        return 6 <= self.current_time < 20

    def set_character_position(self, character_name: str, position: Position):
        """Set a character's position in the world"""
        try:
            self.character_positions[character_name] = position
            
            # Ensure character exists in characters dict
            if character_name not in self.characters:
                self.characters[character_name] = {
                    'name': character_name,
                    'position': {'x': position.x, 'y': position.y},
                    'online': True,
                    'last_update': time.time(),
                    'status': 'active'
                }
            else:
                # Update existing character's position
                self.characters[character_name]['position'] = {
                    'x': position.x,
                    'y': position.y
                }
                self.characters[character_name]['last_update'] = time.time()
            
            self.logger.debug(f"Set position for character {character_name} to {position}")
            self.save_state()  # Save state after position update
            
        except Exception as e:
            self.logger.error(f"Error setting character position: {str(e)}")

    def get_character_position(self, character_name: str) -> Optional[Position]:
        """Get a character's current position"""
        return self.character_positions.get(character_name)

    def get_current_date_string(self) -> str:
        """Get a formatted string of the current date"""
        return f"Day {self.current_day} of {self.current_season.capitalize()}, Year {self.current_year}"

    def get_current_time_string(self) -> str:
        """Get a formatted string of the current time"""
        hours = int(self.current_time)
        minutes = int((self.current_time % 1) * 60)
        return f"{hours:02d}:{minutes:02d}"

    def set_character_online(self, character_name: str, is_online: bool = True):
        """Update a character's online status"""
        if character_name not in self.characters:
            self.characters[character_name] = {}
        self.characters[character_name]['online'] = is_online
        self.characters[character_name]['last_update'] = time.time()
        self.save_state()

    def is_character_online(self, character_name: str) -> bool:
        """Check if a character is currently online"""
        if character_name not in self.characters:
            return False
        char_data = self.characters[character_name]
        # Consider character online if they've updated in the last 30 seconds
        return (char_data.get('online', False) and 
                char_data.get('last_update', 0) > time.time() - 30)

    def serialize(self) -> dict:
        """Serialize world state"""
        try:
            return {
                'time': {
                    'current_time': self.current_time,
                    'day': self.current_day,
                    'season': self.current_season,
                    'year': self.current_year
                },
                'weather': {
                    'current': self.weather,
                    'temperature': self.temperature,
                    'conditions': []
                },
                'characters': {
                    name: {
                        'position': {
                            'x': pos.x,
                            'y': pos.y
                        } if pos else {'x': 0, 'y': 0},
                        'home_position': {
                            'x': pos.x,
                            'y': pos.y
                        } if pos else {'x': 0, 'y': 0},
                        'last_active': datetime.now().isoformat(),
                        'status': 'active' if self.is_character_online(name) else 'offline',
                        'online': self.characters.get(name, {}).get('online', False),
                        'last_update': self.characters.get(name, {}).get('last_update', 0)
                    }
                    for name, pos in self.character_positions.items()
                },
                'buildings': {
                    'supermarket': {
                        'position': {'x': 2, 'y': 0},
                        'status': 'open' if self.is_daytime() else 'closed',
                        'current_visitors': [],
                        'inventory_last_restocked': datetime.now().isoformat()
                    }
                },
                'events': {
                    'scheduled': [],
                    'active': []
                },
                'metadata': {
                    'last_saved': datetime.now().isoformat(),
                    'version': '1.0',
                    'game_days_elapsed': (self.current_year - 1) * 4 * 30 + 
                                       (["spring", "summer", "fall", "winter"].index(self.current_season)) * 30 +
                                       self.current_day - 1
                }
            }
        except Exception as e:
            logging.error(f"Error serializing world state: {e}")
            return {
                'time': {
                    'current_time': 8.0,
                    'day': 1,
                    'season': 'spring',
                    'year': 1
                },
                'weather': {
                    'current': 'sunny',
                    'temperature': 22.0,
                    'conditions': []
                },
                'characters': {},
                'buildings': {},
                'events': {
                    'scheduled': [],
                    'active': []
                },
                'metadata': {
                    'last_saved': datetime.now().isoformat(),
                    'version': '1.0',
                    'game_days_elapsed': 0
                }
            }