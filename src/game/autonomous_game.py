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
from src.utils.models import Position

class AutonomousSimsGame:
    def __init__(self):
        self.game_map = GameMap()
        # Try to find an existing house for our character
        character_house = None
        available_houses = self.game_map.get_available_houses()
        
        # First check if character already has a house
        for pos, plot in self.game_map.plots.items():
            if plot.owner == "AI Character":
                character_house = pos
                break
        
        # If no house found, try to assign an available one
        if not character_house and available_houses:
            character_house = available_houses[0]
        
        # If still no house, create a new one
        if not character_house:
            character_house = Position(0, 0)  # Default position for new house
        
        # Now ensure we have a house at this position
        if not self.game_map.assign_house_to_character("AI Character", character_house):
            raise Exception("Failed to create or assign house for character")
        
        # Get the house instance
        self.house = self.game_map.get_building(character_house)
        if not self.house:
            raise Exception("Failed to get house instance")
        
        # Create character with valid house
        self.character = AutonomousCharacter("AI Character", self.house)
        # Initialize character position to the assigned house
        self.game_map.world_state.set_character_position("AI Character", character_house)
        # Authorize character to use their house's front door
        self.house.authorize_user("AI Character")
        
        # Initialize voice server with character reference
        voice_server.initialize_phone_system(self.character)
        
        self.running = True
        self.last_update = time.time()
        self.last_knowledge_save = time.time()
        self.knowledge_save_interval = 300  # Save knowledge every 5 minutes
        
        # Set up logging
        self.setup_logging()

    def setup_logging(self):
        # Create a timestamp for the log file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Configure the main logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/game_{timestamp}.log'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('AutonomousGame')
        
        # Create separate loggers for LLM and actions with their own files
        llm_handler = logging.FileHandler(f'logs/llm_{timestamp}.log')
        llm_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.llm_logger = logging.getLogger('LLM')
        self.llm_logger.addHandler(llm_handler)
        self.llm_logger.propagate = False  # Prevent duplicate logging
        
        action_handler = logging.FileHandler(f'logs/actions_{timestamp}.log')
        action_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.action_logger = logging.getLogger('Actions')
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
        with open(f'states/character_state_{timestamp}.json', 'w') as f:
            json.dump(state, f, indent=4)
            
        # Also save knowledge system state when saving character state
        self.character.knowledge_system.save_state()

    def run(self):
        self.logger.info("Starting Autonomous Sims Simulation...")
        try:
            while self.running:
                current_time = time.time()
                delta_time = current_time - self.last_update
                
                # Only update every 2 seconds
                if delta_time >= 2:
                    result = self.update()
                    self.last_update = current_time
                    
                    # Print status
                    print(f"\nThought: {self.character.thought}")
                    print(f"Action: {result}")
                    print("\nNeeds:")
                    for need, value in self.character.needs.items():
                        print(f"  {need}: {value:.1f}")
                    
                    # Save state periodically (every 5 minutes)
                    if current_time - self.last_knowledge_save >= self.knowledge_save_interval:
                        self.save_character_state()
                        self.last_knowledge_save = current_time
                
                # Small sleep to prevent CPU overuse
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            self.logger.info("\nSimulation stopped by user")
            self.save_character_state()
        except Exception as e:
            self.logger.error(f"Simulation crashed with error: {str(e)}", exc_info=True)
            self.save_character_state()
        finally:
            if hasattr(self.character, 'browser') and self.character.browser:
                self.character.browser.close()
