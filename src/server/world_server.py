import socket
import threading
import json
import logging
from typing import Dict
from src.utils.models import Position
import time

class WorldServer:
    def __init__(self, game_map, host="0.0.0.0", port=6000):
        self.game_map = game_map
        self.host = host
        self.port = port
        self.running = False
        self.clients: Dict[str, socket.socket] = {}
        self.logger = logging.getLogger("WorldServer")
        
        # Initialize character tracking
        self.characters = {}
        self.initialize_character_system()
        
    def initialize_character_system(self):
        """Initialize the character tracking system"""
        try:
            # Ensure all required attributes exist
            if not hasattr(self.game_map.world_state, 'characters'):
                self.game_map.world_state.characters = {}
            
            if not hasattr(self.game_map, 'active_characters'):
                self.game_map.active_characters = set()
            
            if not hasattr(self.game_map, 'character_positions'):
                self.game_map.character_positions = {}
            
            if not hasattr(self.game_map, 'characters'):
                self.game_map.characters = {}
            
            # Sync with existing world state data
            for char_name, char_data in self.game_map.world_state.characters.items():
                # Update game map characters
                self.game_map.characters[char_name] = char_data
                
                # Update positions if available
                if 'position' in char_data:
                    pos = Position(
                        char_data['position']['x'],
                        char_data['position']['y']
                    )
                    self.game_map.character_positions[char_name] = pos
                
                # Update active characters
                if char_data.get('online', False) and \
                   time.time() - char_data.get('last_update', 0) < 30:
                    self.game_map.active_characters.add(char_name)
                    
            self.logger.info(f"Character system initialized with {len(self.game_map.characters)} characters")
            
        except Exception as e:
            self.logger.error(f"Error initializing character system: {str(e)}")
            raise

    def start(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            
            self.logger.info(f"World server started on {self.host}:{self.port}")
            
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                except Exception as e:
                    self.logger.error(f"Error accepting client: {str(e)}")
                    
        except Exception as e:
            self.logger.error(f"Error starting server: {str(e)}")
            raise
                
    def handle_client(self, client_socket, address):
        try:
            self.logger.info(f"New client connected from {address}")
            while self.running:
                try:
                    data = client_socket.recv(4096)
                    if not data:
                        break
                        
                    message = json.loads(data.decode())
                    response = self.process_message(message)
                    
                    response_json = json.dumps(response)
                    client_socket.send(response_json.encode())
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"Invalid JSON received from {address}: {e}")
                    error_response = json.dumps({
                        "status": "error",
                        "message": "Invalid JSON format"
                    })
                    client_socket.send(error_response.encode())
                    
                except Exception as e:
                    self.logger.error(f"Error handling client message: {str(e)}")
                    error_response = json.dumps({
                        "status": "error",
                        "message": str(e)
                    })
                    client_socket.send(error_response.encode())
                    
        except Exception as e:
            self.logger.error(f"Client handler error for {address}: {str(e)}")
        finally:
            self.logger.info(f"Client disconnected: {address}")
            client_socket.close()
            
    def process_message(self, message):
        try:
            command = message.get('command')
            
            if command == 'get_world_state':
                # Ensure character system is initialized
                if not hasattr(self.game_map.world_state, 'characters'):
                    self.initialize_character_system()
                    
                world_state = self.game_map.serialize()
                return {
                    'status': 'success',
                    'world_state': world_state
                }
                
            elif command == 'register_character':
                character_data = message.get('character')
                if character_data:
                    name = character_data['name']
                    # Update character data
                    character_data['online'] = True
                    character_data['last_update'] = time.time()
                    character_data['status'] = 'active'
                    
                    # Add to world state characters
                    self.game_map.world_state.characters[name] = character_data
                    
                    # Add to active characters set
                    self.game_map.active_characters.add(name)
                    
                    # Register with game map
                    if self.game_map.register_character(character_data):
                        self.logger.info(f"Character {name} registered successfully")
                        return {'status': 'success'}
                        
                return {
                    'status': 'error',
                    'message': 'Failed to register character'
                }
                
            elif command == 'update_character':
                character_data = message.get('character')
                if character_data:
                    name = character_data['name']
                    character_data['last_update'] = time.time()
                    
                    # Update in world state
                    self.game_map.world_state.characters[name] = character_data
                    
                    # Ensure character is in active set
                    self.game_map.active_characters.add(name)
                    
                    if self.game_map.update_character(character_data):
                        return {'status': 'success'}
                        
                return {
                    'status': 'error',
                    'message': 'Failed to update character'
                }
                
            return {
                'status': 'error',
                'message': 'Unknown command'
            }
            
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
            
    def stop(self):
        self.running = False
        if hasattr(self, 'server_socket'):
            self.server_socket.close()