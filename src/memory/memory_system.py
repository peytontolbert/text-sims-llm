
# File: memory_system.py
import time
from typing import List, Dict
from collections import deque

class Memory:
    def __init__(self, max_size: int = 50):
        self.memories = deque(maxlen=max_size)
        self.important_memories = []
        self.emotional_state = {
            'happiness': 0.5,
            'stress': 0.3,
            'energy': 0.8
        }

    def add_memory(self, memory: str, importance: float = 0.0, emotions: Dict[str, float] = None):
        timestamp = time.time()
        memory_entry = {
            'content': memory,
            'timestamp': timestamp,
            'importance': importance,
            'emotions': emotions or {}
        }
        
        self.memories.append(memory_entry)
        
        if importance > 0.7:
            self.important_memories.append(memory_entry)
            
        # Update emotional state
        if emotions:
            for emotion, value in emotions.items():
                if emotion in self.emotional_state:
                    self.emotional_state[emotion] = (
                        self.emotional_state[emotion] * 0.7 + value * 0.3
                    )

    def get_recent_memories(self, n: int = 5) -> List[str]:
        return [m['content'] for m in list(self.memories)[-n:]]

    def get_important_memories(self) -> List[str]:
        return [m['content'] for m in self.important_memories]

    def get_emotional_context(self) -> Dict[str, float]:
        return self.emotional_state
