import socket
import json
import logging
from typing import Optional
import time

class WorldClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.socket = None
        self.logger = logging.getLogger("WorldClient")
        
    def connect(self) -> bool:
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.host, self.port))
                self.logger.info(f"Successfully connected to world server on attempt {attempt + 1}")
                return True
            except Exception as e:
                self.logger.warning(f"Connection attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                self.socket = None
        
        self.logger.error("Failed to connect after all retries")
        return False
            
    def disconnect(self):
        if self.socket:
            self.socket.close()
            
    def send_message(self, message: dict) -> Optional[dict]:
        if not self.socket:
            self.logger.error("Not connected to server")
            return None
        
        try:
            # Send the message
            message_json = json.dumps(message)
            self.socket.send(message_json.encode())
            
            # Read the response in chunks
            chunks = []
            while True:
                chunk = self.socket.recv(8192)  # Increased buffer size
                if not chunk:
                    break
                chunks.append(chunk)
                if chunk.endswith(b'}'):  # Check for end of JSON
                    break
                
            if not chunks:
                raise ConnectionError("No response received from server")
            
            # Combine chunks and parse JSON
            response_data = b''.join(chunks)
            try:
                response = json.loads(response_data.decode())
                if response.get('status') == 'error':
                    self.logger.error(f"Server error: {response.get('message')}")
                    return None
                return response
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON in response: {e}")
                self.logger.debug(f"Raw response: {response_data.decode()[:200]}...")  # Log first 200 chars
                return None
            
        except Exception as e:
            self.logger.error(f"Error sending message: {str(e)}")
            # Try to reconnect
            if self.connect():
                try:
                    # Retry the message once if reconnection successful
                    message_json = json.dumps(message)
                    self.socket.send(message_json.encode())
                    response_data = self.socket.recv(8192)
                    if not response_data:
                        raise ConnectionError("No response received from server after reconnect")
                    return json.loads(response_data.decode())
                except Exception as e:
                    self.logger.error(f"Error sending message after reconnect: {str(e)}")
            return None
            
    def get_world_state(self):
        response = self.send_message({'command': 'get_world_state'})
        if response and response.get('status') == 'success':
            return response.get('world_state')
        return None
        
    def register_character(self, character) -> bool:
        """Register a character with the world server"""
        try:
            character_data = character.serialize()
            response = self.send_message({
                'command': 'register_character',
                'character': character_data
            })
            success = response and response.get('status') == 'success'
            if success:
                self.logger.info(f"Successfully registered character {character.name}")
            else:
                self.logger.error(f"Failed to register character {character.name}")
            return success
        except Exception as e:
            self.logger.error(f"Error registering character: {str(e)}")
            return False
        
    def update_character_state(self, character):
        response = self.send_message({
            'command': 'update_character',
            'character': character.serialize()
        })
        return response and response.get('status') == 'success' 