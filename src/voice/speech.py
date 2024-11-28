"""
This is the audio agent that completes audio tasks for the input
"""
import os
import openai
from pathlib import Path
from dotenv import load_dotenv
import time
import logging


load_dotenv()

class Speech:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.logger = logging.getLogger(__name__)
        self.client = openai.OpenAI(api_key=self.api_key)
        # Create a unique directory for speech files
        self.speech_dir = Path(__file__).parent / "speech_files"
        self.speech_dir.mkdir(exist_ok=True)

    def complete_task(self, input_text: str) -> Path:
        """Convert text to speech and save to file"""
        try:
            # Create unique filename using timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            speech_file = self.speech_dir / f"speech_{timestamp}.mp3"
            
            self.logger.info(f"Generating speech for text: {input_text[:50]}...")
            
            # Generate speech
            response = self.client.audio.speech.create(
                model="tts-1",
                input=input_text,
                voice="alloy",
            )
            
            # Save the file
            response.stream_to_file(str(speech_file))
            
            self.logger.info(f"Speech file saved to: {speech_file}")
            
            # Verify file exists and has content
            if not speech_file.exists():
                raise Exception("Speech file was not created")
                
            return speech_file
            
        except Exception as e:
            self.logger.error(f"Error in text-to-speech conversion: {e}")
            raise
