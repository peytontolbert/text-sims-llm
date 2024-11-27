import time
from autonomous_game import AutonomousSimsGame
from voice_chat_server import run_server
import threading

if __name__ == "__main__":
    # Start the game in a separate thread
    game = AutonomousSimsGame()
    game_thread = threading.Thread(target=game.run)
    game_thread.start()
    
    # Run the web server in the main thread
    run_server(host='0.0.0.0', port=5000)