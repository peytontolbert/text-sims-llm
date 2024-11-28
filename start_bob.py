import logging
from src.character.autonomous_character import AutonomousCharacter
from src.client.world_client import WorldClient
from src.environment.house import House
from src.utils.models import Position
from src.environment.map import GameMap
import time
import json

def create_character_from_state(world_state: dict, name: str, game_map: GameMap) -> AutonomousCharacter:
    """Create a character instance from world state"""
    logger = logging.getLogger("CharacterCreation")
    
    # Try to find an existing house for our character
    character_house = None
    
    # First check if character already has a house
    for pos, plot in game_map.plots.items():
        if plot.owner == name:
            character_house = pos
            logger.info(f"Found existing house for {name} at {pos}")
            break
    
    # If no house found, try to find an empty plot
    if not character_house:
        empty_plots = game_map.get_empty_plots()
        if empty_plots:
            character_house = empty_plots[0]  # Take first empty plot
            logger.info(f"Assigning empty plot at {character_house} to {name}")
        else:
            # Find a new position that doesn't overlap with existing plots
            x, y = 0, 0
            while Position(x, y) in game_map.plots:
                x += 1
                if x > 10:  # Wrap to next row after 10 columns
                    x = 0
                    y += 1
            character_house = Position(x, y)
            logger.info(f"Creating new plot at {character_house} for {name}")
    
    # Now ensure we have a house at this position
    if not game_map.assign_house_to_character(name, character_house):
        logger.error(f"Failed to assign house at {character_house} to {name}")
        raise Exception("Failed to create or assign house for character")
    
    # Get the house instance
    house = game_map.get_building(character_house)
    if not house:
        logger.error(f"Failed to get house instance at {character_house}")
        raise Exception("Failed to get house instance")
    
    logger.info(f"Successfully created/assigned house for {name} at {character_house}")
    
    # Create character with house and game_map
    character = AutonomousCharacter(name, house, game_map)
    
    # Initialize character position
    game_map.world_state.set_character_position(name, character_house)
    
    # Authorize character to use their house
    house.authorize_user(name)
    
    return character

def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("BobClient")
    
    try:
        # Create game map instance
        game_map = GameMap()
        
        # Connect to world server
        world_client = WorldClient("localhost", 6000)
        
        # Wait for connection
        if not world_client.connect():
            logger.error("Failed to connect to world server")
            return
            
        # Get world state from server
        world_state = world_client.get_world_state()
        if not world_state:
            logger.error("Failed to get world state")
            return
            
        # Create character instance with game map
        character = create_character_from_state(world_state, "Bob", game_map)
        
        # Register character with world
        if not world_client.register_character(character):
            logger.error("Failed to register character with world")
            return
            
        logger.info("Bob successfully connected and registered")
        
        # Main loop
        try:
            while True:
                # Update character
                result = character.update(2.0)  # 2 second update interval
                
                # Update game map
                game_map.update(2.0 / 3600.0)  # Convert seconds to hours
                
                # Send character state to server
                world_client.update_character_state(character)
                
                # Log status
                logger.info(f"\nThought: {character.thought}")
                logger.info(f"Action: {result}")
                logger.info("\nNeeds:")
                for need, value in character.needs.items():
                    logger.info(f"  {need}: {value:.1f}")
                    
                time.sleep(2)
                
        except KeyboardInterrupt:
            logger.info("Shutting down Bob...")
            
    except Exception as e:
        logger.error(f"Error in Bob client: {str(e)}", exc_info=True)
    finally:
        if 'world_client' in locals():
            world_client.disconnect()

if __name__ == "__main__":
    main()
