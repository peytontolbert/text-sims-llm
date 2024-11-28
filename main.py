import time
from src.phone.voice_chat_server import run_server
from src.server.world_server import WorldServer
import threading
import logging
from src.environment.map import GameMap
from src.environment.world_state import WorldState

def run_server_wrapper(host, port):
    try:
        run_server(host=host, port=port)
    except Exception as e:
        logging.error(f"Server thread error: {str(e)}", exc_info=True)

def run_world_server(world_server):
    try:
        world_server.start()
    except Exception as e:
        logging.error(f"World server error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # Create game map first (it will create its own world state)
        game_map = GameMap()
        
        # Get the world state reference from game map
        world_state = game_map.world_state
        
        # Initialize and start world server with game map
        world_server = WorldServer(game_map)
        world_server_thread = threading.Thread(target=run_world_server, args=(world_server,))
        world_server_thread.daemon = True
        world_server_thread.start()
        
        # Start the voice chat server in a separate thread
        server_thread = threading.Thread(target=run_server_wrapper, args=('0.0.0.0', 5000))
        server_thread.daemon = True
        server_thread.start()
        
        logger.info("All servers started successfully")
        
        # Keep main thread alive and monitor threads
        while True:
            time.sleep(1)
            if not world_server_thread.is_alive():
                logger.error("World server thread died unexpectedly")
                break
            if not server_thread.is_alive():
                logger.error("Voice chat server thread died unexpectedly")
                break
            
            # Update world state time
            world_state.update_time(1.0 / 3600.0)  # Update time by 1 second converted to hours
                
    except KeyboardInterrupt:
        logger.info("\nShutting down servers gracefully...")
    except Exception as e:
        logger.error(f"Main thread error: {str(e)}", exc_info=True)
    finally:
        # Cleanup
        if 'world_server' in locals():
            world_server.stop()
        # Give threads a moment to clean up
        time.sleep(2)