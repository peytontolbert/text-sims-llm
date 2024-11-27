# File: autonomous_game.py
import time
import logging
from datetime import datetime
from house import House
from autonomous_character import AutonomousCharacter
import os
import json

class AutonomousSimsGame:
    def __init__(self):
        self.house = House()
        self.character = AutonomousCharacter("Alex", self.house)
        self.running = True
        self.last_update = time.time()
        
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

    def run(self):
        self.logger.info("Starting Autonomous Sims Simulation...")
        try:
            while self.running:
                result = self.update()
                print(f"\nThought: {self.character.thought}")
                print(f"Action: {result}")
                print("\nNeeds:")
                for need, value in self.character.needs.items():
                    print(f"  {need}: {value:.1f}")
                print("\nPress Ctrl+C to stop the simulation")
                time.sleep(2)  # Add delay between actions
        except KeyboardInterrupt:
            self.logger.info("\nSimulation stopped by user")
            self.save_character_state()  # Save state when stopping
        except Exception as e:
            self.logger.error(f"Simulation crashed with error: {str(e)}", exc_info=True)
            self.save_character_state()  # Save state on crash too
        finally:
            if self.character.browser:
                self.character.browser.close()
