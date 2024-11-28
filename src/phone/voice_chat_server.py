from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
import logging
from pathlib import Path
from src.phone.phone_system import PhoneSystem
from src.utils.models import Position

app = Flask(__name__, static_folder='.')
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('phone_system.log')
    ]
)
logger = logging.getLogger(__name__)

class VoiceChatServer:
    def __init__(self):
        self.phone_system = None
        self.character = None
        self.game_map = None
        
    def initialize_phone_system(self, character):
        """Initialize phone system with character reference"""
        self.character = character
        self.game_map = character.game_map
        self.phone_system = PhoneSystem(character)
        return {"success": True, "message": "Phone system initialized"}

voice_server = VoiceChatServer()

@app.route('/')
def serve_index():
    """Serve the main phone interface"""
    return send_from_directory('.', 'index.html')

@app.route('/text-message', methods=['POST'])
def receive_text_message():
    try:
        if not voice_server.phone_system:
            return jsonify({
                "success": False,
                "error": "Phone system not initialized"
            })
            
        data = request.json
        message = data.get('message')
        
        if not message:
            return jsonify({
                "success": False,
                "error": "No message provided"
            })
        
        # Get character's response
        response = voice_server.phone_system.handle_text_call(message)
        
        # Try to convert response to speech
        try:
            audio_path = voice_server.phone_system.speech.complete_task(response)
            
            # Read the audio file
            with open(str(audio_path), 'rb') as audio_file:
                audio_data = audio_file.read()
                
            return jsonify({
                "success": True,
                "text_response": response,
                "audio_data": list(audio_data)  # Convert bytes to list for JSON
            })
            
        except Exception as e:
            logger.error(f"Speech generation failed: {e}")
            # Return just the text response if speech fails
            return jsonify({
                "success": True,
                "text_response": response,
                "audio_data": None
            })
            
    except Exception as e:
        logger.error(f"Error handling text message: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.after_request
def add_header(response):
    """Add headers to prevent caching for API endpoints"""
    if request.endpoint != 'serve_index':  # Don't add for static files
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

@app.route('/start-call', methods=['POST'])
def start_call():
    try:
        logger.debug("Received start-call request")
        
        if not voice_server.phone_system:
            logger.error("Phone system not initialized")
            return make_response(jsonify({
                "success": False,
                "error": "Phone system not initialized"
            }), 503)
            
        data = request.get_json(silent=True) or {}
        target_character = data.get('character')
        initial_message = data.get('message', '')
        
        if not target_character:
            return make_response(jsonify({
                "success": False,
                "error": "No target character specified"
            }), 400)
            
        # Verify character exists
        world_state = voice_server.character.house.game_map.world_state
        if target_character not in world_state.character_positions:
            return make_response(jsonify({
                "success": False,
                "error": f"Character '{target_character}' not found"
            }), 404)
        
        # Start call with specified character
        result = voice_server.phone_system.start_call(target_character, initial_message)
        logger.debug(f"Start call result: {result}")
        
        return make_response(jsonify(result), 200 if result.get("success") else 400)
            
    except Exception as e:
        logger.error(f"Error starting call: {str(e)}", exc_info=True)
        return make_response(jsonify({
            "success": False,
            "error": str(e)
        }), 500)

@app.route('/end-call', methods=['POST'])
def end_call():
    try:
        if not voice_server.phone_system:
            return jsonify({
                "success": False,
                "error": "Phone system not initialized"
            })
            
        result = voice_server.phone_system.end_call()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error ending call: {e}")
        # Make sure to reset call status even if there's an error
        if voice_server.phone_system:
            voice_server.phone_system.in_call = False
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/initialize', methods=['POST'])
def initialize():
    """Initialize the phone system with a character"""
    try:
        data = request.json
        character = data.get('character')
        result = voice_server.initialize_phone_system(character)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error initializing phone system: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/character-status')
def get_character_status():
    """Get the current status of the character"""
    try:
        if not voice_server.character:
            return jsonify({
                "success": False,
                "error": "Character not initialized"
            })
            
        world_state = voice_server.game_map.world_state
        char_data = world_state.characters.get(voice_server.character.name, {})
        
        return jsonify({
            "success": True,
            "room": voice_server.character.current_room.value if hasattr(voice_server.character, 'current_room') else None,
            "activity": voice_server.character.current_action if hasattr(voice_server.character, 'current_action') else None,
            "thought": voice_server.character.thought if hasattr(voice_server.character, 'thought') else None,
            "in_call": voice_server.phone_system.in_call if voice_server.phone_system else False,
            "online": world_state.is_character_online(voice_server.character.name),
            "last_update": char_data.get('last_update', 0)
        })
        
    except Exception as e:
        logger.error(f"Error getting character status: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/available-characters', methods=['GET'])
def get_available_characters():
    try:
        if not voice_server.character or not voice_server.game_map:
            return jsonify({
                "success": False,
                "error": "Character system not initialized"
            })
            
        # Get list of characters from world state
        world_state = voice_server.game_map.world_state
        characters = []
        
        # Add character details
        for char_name, char_data in world_state.characters.items():
            # Skip the current character
            if char_name == voice_server.character.name:
                continue
                
            # Get character position and online status
            pos = world_state.get_character_position(char_name)
            is_online = world_state.is_character_online(char_name)
            
            if pos:
                plot = voice_server.game_map.get_plot(pos)
                room = "Unknown"
                if plot and plot.building:
                    room = plot.building.get_room(Position(0, 0)).value
                
                characters.append({
                    "name": char_name,
                    "location": room,
                    "online": is_online,
                    "last_update": char_data.get('last_update', 0)
                })
        
        return jsonify({
            "success": True,
            "characters": characters
        })
        
    except Exception as e:
        logger.error(f"Error getting available characters: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/debug/character-status/<character_name>')
def debug_character_status(character_name):
    """Debug endpoint to check character status"""
    try:
        if not voice_server.game_map:
            return jsonify({
                "success": False,
                "error": "Game map not initialized"
            })
            
        world_state = voice_server.game_map.world_state
        char_data = world_state.characters.get(character_name, {})
        
        return jsonify({
            "success": True,
            "character_name": character_name,
            "in_world_state": character_name in world_state.characters,
            "in_positions": character_name in world_state.character_positions,
            "in_active_set": character_name in voice_server.game_map.active_characters,
            "online_status": world_state.is_character_online(character_name),
            "last_update": char_data.get('last_update', 0),
            "full_data": char_data
        })
        
    except Exception as e:
        logger.error(f"Error getting debug character status: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

def run_server(host='0.0.0.0', port=5000):
    print(f"Server running at http://{host}:{port}")
    app.run(host=host, port=port)

if __name__ == '__main__':
    run_server() 