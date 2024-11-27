from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
import numpy as np
import json
import logging
from typing import Optional
from src.ears.whisper_manager import WhisperManager
from src.voice.speech import Speech
from src.phone.phone_system import PhoneSystem
import sounddevice as sd
import soundfile as sf
import io
import wave
import time
import os

app = Flask(__name__, static_folder='.')
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceChatServer:
    def __init__(self):
        self.whisper = WhisperManager()
        self.speech = Speech()
        self.phone_system = None
        self.character = None
        
    def initialize_phone_system(self, character):
        """Initialize phone system with character reference"""
        self.character = character
        self.phone_system = PhoneSystem(character)
        return {"success": True, "message": "Phone system initialized"}

    def process_voice_message(self, audio_data: np.ndarray, sample_rate: int) -> dict:
        """Process incoming voice message and return character's response"""
        try:
            # Transcribe incoming audio
            transcription = self.whisper.transcribe_audio({
                "array": audio_data,
                "sampling_rate": sample_rate
            })
            
            logger.info(f"Transcribed message: {transcription}")
            
            if transcription and transcription != "Transcription failed.":
                # Get character's text response through phone system
                text_response = self.phone_system._process_message(transcription)
                
                # Convert response to speech
                audio_path = self.speech.complete_task(text_response)
                
                # Read the audio file and convert to array
                audio_data, sr = sf.read(str(audio_path))
                
                return {
                    "success": True,
                    "transcription": transcription,
                    "text_response": text_response,
                    "audio_response": audio_data.tolist()
                }
            else:
                return {
                    "success": False,
                    "error": "No speech detected or transcription failed"
                }
            
        except Exception as e:
            logger.error(f"Error processing voice message: {e}")
            return {
                "success": False,
                "error": str(e)
            }

voice_server = VoiceChatServer()

@app.route('/initialize', methods=['POST'])
def initialize():
    try:
        data = request.json
        character = data.get('character')
        result = voice_server.initialize_phone_system(character)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error initializing phone system: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/voice-message', methods=['POST'])
def receive_voice_message():
    try:
        # Get audio data from request
        if 'audio' not in request.files:
            return jsonify({"success": False, "error": "No audio file received"})
            
        audio_file = request.files['audio']
        
        # Read the raw audio data as bytes
        audio_bytes = audio_file.read()
        
        # Convert the audio bytes to numpy array
        audio_data = np.frombuffer(audio_bytes, dtype=np.float32)
        
        # Use a default sample rate of 16000 (what Whisper expects)
        sample_rate = 16000
        
        # Process the voice message
        response = voice_server.process_voice_message(audio_data, sample_rate)
        
        # Ensure the call stays active
        if response.get('success'):
            voice_server.phone_system.in_call = True
            
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error handling voice message: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/text-message', methods=['POST'])
def receive_text_message():
    try:
        data = request.json
        message = data.get('message')
        
        # Get character's response
        response = voice_server.phone_system.handle_text_call(message)
        
        # Convert response to speech
        audio_path = voice_server.speech.complete_task(response)
        
        # Read the audio file
        with open(str(audio_path), 'rb') as audio_file:
            audio_data = audio_file.read()
        
        return jsonify({
            "success": True,
            "text_response": response,
            "audio_data": audio_data
        })
        
    except Exception as e:
        logger.error(f"Error handling text message: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/start-call', methods=['POST'])
def start_call():
    try:
        if not voice_server.phone_system:
            return jsonify({
                "success": False, 
                "error": "Phone system not initialized. Please initialize first."
            })
            
        response = voice_server.phone_system.start_call()
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error starting call: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/end-call', methods=['POST'])
def end_call():
    try:
        response = voice_server.phone_system.end_call()
        return jsonify({"success": True, "message": response})
    except Exception as e:
        logger.error(f"Error ending call: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

def run_server(host='0.0.0.0', port=5000):
    print(f"Server running at http://{host}:{port}")
    app.run(host=host, port=port)

if __name__ == '__main__':
    run_server() 