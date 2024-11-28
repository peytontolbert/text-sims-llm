import time
from src.game.autonomous_game import AutonomousSimsGame
from src.phone.voice_chat_server import run_server
import threading
import logging

def run_game(game):
    try:
        game.run()
    except Exception as e:
        logging.error(f"Game thread error: {str(e)}", exc_info=True)

def run_server_wrapper(host, port):
    try:
        run_server(host=host, port=port)
    except Exception as e:
        logging.error(f"Server thread error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create the game instance
    game = AutonomousSimsGame()
    
    # Start the game in a separate thread
    game_thread = threading.Thread(target=run_game, args=(game,))
    game_thread.daemon = False  # Make thread non-daemon so it won't exit when main thread exits
    game_thread.start()
    
    # Start the server in a separate thread
    server_thread = threading.Thread(target=run_server_wrapper, args=('0.0.0.0', 5000))
    server_thread.daemon = True  # Make server thread daemon so it exits when main thread exits
    server_thread.start()
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
            if not game_thread.is_alive():
                logging.error("Game thread died unexpectedly")
                break
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        game.running = False  # Signal game loop to stop
        game_thread.join(timeout=5)  # Wait for game thread to finish