from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
import logging
from pathlib import Path
from src.phone.phone_system import PhoneSystem

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
        
    def initialize_phone_system(self, character):
        """Initialize phone system with character reference"""
        self.character = character
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
        logger.debug(f"Request data: {request.get_data()}")
        logger.debug(f"Request JSON: {request.get_json(silent=True)}")
        
        if not voice_server.phone_system:
            logger.error("Phone system not initialized")
            return make_response(jsonify({
                "success": False,
                "error": "Phone system not initialized"
            }), 503)  # Service Unavailable
            
        # Initialize phone system if not already done
        if not voice_server.character:
            logger.warning("Character not initialized, attempting to initialize...")
            try:
                # Create a basic character initialization
                from src.character.autonomous_character import AutonomousCharacter
                from src.environment.house import House
                
                house = House()
                character = AutonomousCharacter("AI Assistant", house)
                voice_server.initialize_phone_system(character)
                logger.info("Successfully initialized character and phone system")
            except Exception as e:
                logger.error(f"Failed to initialize character: {e}")
                return make_response(jsonify({
                    "success": False,
                    "error": "Failed to initialize character system"
                }), 500)
            
        logger.debug(f"Phone system state - in_call: {voice_server.phone_system.in_call}")
        
        # Get message from request body (if any)
        data = request.get_json(silent=True) or {}
        initial_message = data.get('message', '')
        logger.debug(f"Initial message: {initial_message}")
            
        # Start call with optional initial message
        logger.debug("Attempting to start call...")
        result = voice_server.phone_system.start_call(initial_message)
        logger.debug(f"Start call result: {result}")
        
        if result.get("success", False):
            logger.info("Call started successfully")
            return make_response(jsonify(result), 200)
        else:
            logger.warning(f"Call start failed: {result.get('error', 'Unknown error')}")
            return make_response(jsonify(result), 400)  # Bad Request
            
    except Exception as e:
        logger.error(f"Error starting call: {str(e)}", exc_info=True)
        return make_response(jsonify({
            "success": False,
            "error": str(e),
            "in_call": voice_server.phone_system.in_call if voice_server.phone_system else False
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
            
        return jsonify({
            "success": True,
            "room": voice_server.character.current_room.value,
            "activity": voice_server.character.current_action,
            "thought": voice_server.character.thought,
            "in_call": voice_server.phone_system.in_call if voice_server.phone_system else False
        })
        
    except Exception as e:
        logger.error(f"Error getting character status: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

def run_server(host='0.0.0.0', port=5000):
    print(f"Server running at http://{host}:{port}")
    app.run(host=host, port=port)

if __name__ == '__main__':
    run_server() 