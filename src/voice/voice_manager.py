from pathlib import Path
from typing import Optional
from src.voice.speech import Speech

class VoiceManager:
    def __init__(self):
        self.speech_engine = Speech()
        self.virtual_mic = None
        self.output_mode = "speakers"  # or "virtual_mic"
    
    def set_virtual_mic(self, virtual_mic):
        """Set the virtual microphone for browser voice chat"""
        self.virtual_mic = virtual_mic
        
    def set_output_mode(self, mode: str):
        """Set whether voice should output to speakers or virtual mic"""
        if mode in ["speakers", "virtual_mic"]:
            self.output_mode = mode
    
    def speak(self, text: str) -> Optional[Path]:
        """Generate speech and route it to the appropriate output"""
        try:
            audio_file = self.speech_engine.complete_task(text)
            
            if not audio_file:
                return None
                
            if self.output_mode == "virtual_mic" and self.virtual_mic:
                self.virtual_mic.play_audio(audio_file)
            else:
                # Play through system speakers
                self.speech_engine.play_audio(audio_file)
                
            return audio_file
            
        except Exception as e:
            print(f"Error generating speech: {e}")
            return None 