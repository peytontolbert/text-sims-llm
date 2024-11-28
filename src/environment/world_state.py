from typing import Dict, Optional
from src.utils.models import Position
import logging
import json
import os
from datetime import datetime

class WorldState:
    def __init__(self):
        self.character_positions: Dict[str, Position] = {}
        self.current_time: float = 8.0  # Start at 8:00 AM
        self.current_day: int = 1
        self.current_season: str = "spring"
        self.current_year: int = 1
        self.weather: str = "sunny"
        self.temperature: float = 22.0
        self.load_state()

    def load_state(self):
        """Load world state from JSON file"""
        state_path = os.path.join(os.path.dirname(__file__), 'world_state.json')
        try:
            with open(state_path, 'r') as f:
                state_data = json.load(f)
                
            # Load character positions
            for char_name, char_data in state_data['characters'].items():
                pos = char_data['position']
                self.character_positions[char_name] = Position(pos['x'], pos['y'])
            
            # Load time and date
            self.current_time = state_data['time']['current_time']
            self.current_day = state_data['time']['day']
            self.current_season = state_data['time']['season']
            self.current_year = state_data['time']['year']
            
            # Load weather
            self.weather = state_data['weather']['current']
            self.temperature = state_data['weather']['temperature']
            
            logging.info(f"Loaded world state: Day {self.current_day}, {self.current_season} {self.current_year}, "
                        f"Time {self.current_time:.1f}, Weather: {self.weather}")
                        
        except FileNotFoundError:
            logging.warning(f"World state file not found at {state_path}, using default values")
            self.save_state()  # Create initial state file

    def save_state(self):
        """Save current world state to JSON"""
        state_data = {
            "characters": {
                name: {
                    "position": {"x": pos.x, "y": pos.y},
                    "home_position": {"x": pos.x, "y": pos.y},  # Assuming current position is home
                    "last_active": datetime.now().isoformat(),
                    "status": "active"
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
        self.character_positions[character_name] = position
        logging.debug(f"Character {character_name} moved to position {position}")
        self.save_state()  # Save state when character position changes

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