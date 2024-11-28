# File: autonomous_game.py
import time
import logging
from datetime import datetime, timedelta
from src.environment.house import House
from src.character.autonomous_character import AutonomousCharacter
import os
import json
from src.phone.voice_chat_server import voice_server
from src.environment.map import GameMap
from src.utils.position import Position
from src.utils.constants import RoomType

class AutonomousSimsGame:
    def __init__(self, character_name: str):
        try:
            # Set up logging first
            self.setup_logging(character_name)
            self.logger.info(f"Initializing game for character {character_name}")
            
            # Initialize game map
            self.game_map = GameMap()
            
            # Create character using the robust method
            self.character = self._create_character(character_name)
            
            # Initialize character data
            character_data = {
                'name': character_name,
                'position': {
                    'x': self.character.position.x,
                    'y': self.character.position.y
                },
                'online': True,
                'last_update': time.time(),
                'current_room': self.character.current_room.value,
                'status': 'active',
                'needs': self.character.needs,
                'thought': None,
                'current_action': None
            }
            
            # Register character with game map
            if not self.game_map.register_character(character_data):
                raise Exception(f"Failed to register character {character_name} with game map")
            
            # Initialize voice server with character reference
            voice_server.initialize_phone_system(self.character)
            
            self.running = True
            self.last_update = time.time()
            self.last_knowledge_save = time.time()
            self.knowledge_save_interval = 300  # Save knowledge every 5 minutes
            
            self.logger.info(f"Character {character_name} initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing game: {str(e)}", exc_info=True)
            raise

    def setup_logging(self, character_name: str):
        # Create a timestamp for the log file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Configure the main logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/game_{character_name}_{timestamp}.log'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(f'AutonomousGame_{character_name}')
        
        # Create separate loggers for LLM and actions with their own files
        llm_handler = logging.FileHandler(f'logs/llm_{character_name}_{timestamp}.log')
        llm_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.llm_logger = logging.getLogger(f'LLM_{character_name}')
        self.llm_logger.addHandler(llm_handler)
        self.llm_logger.propagate = False  # Prevent duplicate logging
        
        action_handler = logging.FileHandler(f'logs/actions_{character_name}_{timestamp}.log')
        action_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.action_logger = logging.getLogger(f'Actions_{character_name}')
        self.action_logger.addHandler(action_handler)
        self.action_logger.propagate = False  # Prevent duplicate logging

    def update(self):
        current_time = time.time()
        delta_time = current_time - self.last_update
        
        # Update game world
        self.game_map.update(delta_time / 3600.0)  # Convert seconds to hours
        
        # Check if it's time to save knowledge
        if current_time - self.last_knowledge_save >= self.knowledge_save_interval:
            self.logger.info("Saving knowledge system state...")
            self.character.knowledge_system.save_state()
            self.last_knowledge_save = current_time
        
        # Log the current state before update
        self.logger.info("\nCurrent State:")
        self.logger.info(f"Location: {self.character.current_room}")
        self.logger.info("Needs:")
        for need, value in self.character.needs.items():
            self.logger.info(f"  {need}: {value:.1f}")
        
        # Get and log the LLM response
        result = self.character.update(delta_time)
        
        # Log the LLM thought process
        self.llm_logger.info(f"\nLLM Response:")
        self.llm_logger.info(f"Thought: {self.character.thought}")
        self.llm_logger.info(f"Chosen Action: {result}")
        
        # Log the action result
        self.action_logger.info(f"\nAction Executed: {result}")
        self.action_logger.info(f"New Location: {self.character.current_room}")
        
        self.last_update = current_time
        return result

    def save_character_state(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        state = {
            'name': self.character.name,
            'position': {'x': self.character.position.x, 'y': self.character.position.y},
            'current_room': self.character.current_room.value,
            'needs': self.character.needs,
            'action_history': self.character.action_history[-10:],  # Last 10 actions
            'timestamp': timestamp
        }
        
        # Create states directory if it doesn't exist
        os.makedirs('states', exist_ok=True)
        
        # Save to JSON file
        with open(f'states/character_state_{self.character.name}_{timestamp}.json', 'w') as f:
            json.dump(state, f, indent=4)
            
        # Also save knowledge system state when saving character state
        self.character.knowledge_system.save_state()

    def _create_character(self, name: str) -> AutonomousCharacter:
        """Create a character instance with proper house assignment"""
        logger = logging.getLogger("CharacterCreation")
        
        # Try to find an existing house for our character
        character_house = None
        
        # First check if character already has a house
        for pos, plot in self.game_map.plots.items():
            if plot.owner == name:
                character_house = pos
                logger.info(f"Found existing house for {name} at {pos}")
                break
        
        # If no house found, try to find an empty plot
        if not character_house:
            empty_plots = self.game_map.get_empty_plots()
            if empty_plots:
                character_house = empty_plots[0]  # Take first empty plot
                logger.info(f"Assigning empty plot at {character_house} to {name}")
            else:
                # Find a new position that doesn't overlap with existing plots
                x, y = 0, 0
                while Position(x, y) in self.game_map.plots:
                    x += 1
                    if x > 10:  # Wrap to next row after 10 columns
                        x = 0
                        y += 1
                character_house = Position(x, y)
                logger.info(f"Creating new plot at {character_house} for {name}")
        
        # Now ensure we have a house at this position
        if not self.game_map.assign_house_to_character(name, character_house):
            logger.error(f"Failed to assign house at {character_house} to {name}")
            raise Exception("Failed to create or assign house for character")
        
        # Get the house instance
        house = self.game_map.get_building(character_house)
        if not house:
            logger.error(f"Failed to get house instance at {character_house}")
            raise Exception("Failed to get house instance")
        
        logger.info(f"Successfully created/assigned house for {name} at {character_house}")
        
        # Create character with house and game_map
        character = AutonomousCharacter(name, house, self.game_map)
        
        # Initialize character position
        self.game_map.world_state.set_character_position(name, character_house)
        
        # Authorize character to use their house
        house.authorize_user(name)
        
        return character
