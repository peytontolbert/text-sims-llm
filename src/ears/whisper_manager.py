from transformers import WhisperProcessor, WhisperForConditionalGeneration
import sounddevice as sd
import numpy as np
import logging
import threading
import queue
import collections
import time
from transformers import logging as transformers_logging

transformers_logging.set_verbosity_error()

class WhisperManager:
    def __init__(self, threshold=0.05):
        # Initialize Whisper model and processor silently
        try:
            self.processor = WhisperProcessor.from_pretrained("openai/whisper-small")
            self.model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-small")
            logging.info("Whisper model loaded successfully")
        except Exception as e:
            logging.error(f"Failed to load Whisper model: {e}")
            raise

        self.threshold = threshold
        self.audio_queue = queue.Queue()
        self.buffer = collections.deque(maxlen=32000)  # 2 seconds at 16kHz
        self.sample_rate = 16000
        self.channels = 1
        self.is_listening = False
        self.stream = None
        self.last_speech_time = None
        self.silence_duration = 1.0
        self.min_speech_length = 0.5  # Minimum speech duration to process

    def audio_callback(self, indata, frames, time_info, status):
        """Handle incoming audio data"""
        if status:
            logging.warning(f"Audio callback status: {status}")
            return

        try:
            audio = indata.flatten()
            rms = np.sqrt(np.mean(audio**2))
            current_time = time.time()

            # Only process if volume is above threshold
            if rms > self.threshold:
                self.buffer.extend(audio)
                self.last_speech_time = current_time
            elif self.last_speech_time is not None:
                # Add a bit more audio after speech ends
                self.buffer.extend(audio)
                
                # If silence duration exceeded and we have enough audio
                if (current_time - self.last_speech_time > self.silence_duration and 
                    len(self.buffer) > self.sample_rate * self.min_speech_length):
                    
                    # Process the audio
                    audio_data = np.array(list(self.buffer))
                    self.audio_queue.put(audio_data)
                    self.buffer.clear()
                    self.last_speech_time = None

        except Exception as e:
            logging.error(f"Error in audio callback: {e}")

    def start_listening(self):
        """Start listening for audio input"""
        if self.is_listening:
            return

        try:
            self.stream = sd.InputStream(
                callback=self.audio_callback,
                channels=self.channels,
                samplerate=self.sample_rate,
                blocksize=int(self.sample_rate * 0.1)  # 100ms blocks
            )
            self.stream.start()
            self.is_listening = True
            logging.debug("Started audio stream")
        except Exception as e:
            logging.error(f"Failed to start audio stream: {e}")
            self.is_listening = False
            raise

    def stop_listening(self):
        """Stop listening for audio input"""
        if not self.is_listening:
            return

        try:
            if self.stream:
                self.stream.stop()
                self.stream.close()
            self.is_listening = False
            self.buffer.clear()
            logging.debug("Stopped audio stream")
        except Exception as e:
            logging.error(f"Error stopping audio stream: {e}")
        finally:
            self.stream = None

    def transcribe_audio(self, audio_data):
        """Transcribe audio data to text"""
        try:
            if len(audio_data) < self.sample_rate * self.min_speech_length:
                return None

            input_features = self.processor(
                audio_data, 
                sampling_rate=self.sample_rate, 
                return_tensors="pt"
            ).input_features

            predicted_ids = self.model.generate(input_features)
            transcription = self.processor.batch_decode(
                predicted_ids, 
                skip_special_tokens=True
            )[0].strip()

            return transcription if transcription else None

        except Exception as e:
            logging.error(f"Transcription error: {e}")
            return None

    def listen_and_transcribe(self, timeout=3.0):
        """Listen for speech and return transcription"""
        try:
            # Get audio from queue with timeout
            try:
                audio_data = self.audio_queue.get(timeout=timeout)
            except queue.Empty:
                return None

            # Transcribe if we got audio
            if len(audio_data) > 0:
                transcription = self.transcribe_audio(audio_data)
                if transcription and len(transcription) > 0:
                    logging.debug(f"Transcribed: {transcription}")
                    return transcription

            return None

        except Exception as e:
            logging.error(f"Error in listen_and_transcribe: {e}")
            return None
