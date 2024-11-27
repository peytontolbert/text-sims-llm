"""
This is the audio agent that completes audio tasks for the input
"""
import os
import openai
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Speech:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.client = openai.OpenAI(api_key=self.api_key)
        self.speech_file_path = Path(__file__).parent / "speech.mp3"

    def complete_task(self, input):
        response = self.client.audio.speech.create(
            model="tts-1",
            input=input,
            voice="alloy",
        )
        # Save the file and return the path
        response.stream_to_file(self.speech_file_path)
        return self.speech_file_path
