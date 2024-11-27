from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
import numpy as np
import json
import logging
from typing import Optional
from whisper_manager import WhisperManager
from speech import Speech
from phone_system import PhoneSystem
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
        self.phone_system = None  # Will be initialized with character reference
        
    def initialize_phone_system(self, character):
        self.phone_system = PhoneSystem(character)
        
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
        voice_server.initialize_phone_system(character)
        return jsonify({"success": True})
    except Exception as e:
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
        audio_response = voice_server.speech.text_to_speech(response)
        
        return jsonify({
            "success": True,
            "text_response": response,
            "audio_response": audio_response.tolist()
        })
        
    except Exception as e:
        logger.error(f"Error handling text message: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/start-call', methods=['POST'])
def start_call():
    try:
        response = voice_server.phone_system.start_call()
        return jsonify({"success": True, "message": response})
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