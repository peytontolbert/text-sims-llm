import faiss
import numpy as np
from typing import List, Dict, Tuple
import torch
from sentence_transformers import SentenceTransformer
import json
import time
from datetime import datetime
import os

class KnowledgeSystem:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        # Initialize the sentence transformer model
        self.encoder = SentenceTransformer(model_name)
        self.vector_dim = 384  # Dimension of embeddings from the model

        # Initialize FAISS indices for different memory types
        self.semantic_index = faiss.IndexFlatL2(self.vector_dim)
        self.episodic_index = faiss.IndexFlatL2(self.vector_dim)
        self.periodic_index = faiss.IndexFlatL2(self.vector_dim)

        # Storage for the actual memories
        self.semantic_memories = []
        self.episodic_memories = []
        self.periodic_memories = []

        # Create directory for persistent storage
        os.makedirs('knowledge_store', exist_ok=True)

    def add_semantic_knowledge(self, knowledge: str, metadata: Dict = None):
        """Add factual, conceptual knowledge"""
        embedding = self._encode_text(knowledge)
        self.semantic_index.add(np.array([embedding]))
        self.semantic_memories.append({
            'content': knowledge,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat()
        })

    def add_episodic_memory(self, memory: str, emotions: Dict[str, float] = None):
        """Add experience-based memories with emotional context"""
        embedding = self._encode_text(memory)
        self.episodic_index.add(np.array([embedding]))
        self.episodic_memories.append({
            'content': memory,
            'emotions': emotions or {},
            'timestamp': datetime.now().isoformat()
        })

    def add_periodic_pattern(self, pattern: str, frequency: str, metadata: Dict = None):
        """Add recurring patterns or habits"""
        embedding = self._encode_text(pattern)
        self.periodic_index.add(np.array([embedding]))
        self.periodic_memories.append({
            'content': pattern,
            'frequency': frequency,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat()
        })

    def query_knowledge(self, query: str, k: int = 5) -> Dict[str, List[Dict]]:
        """Query all knowledge types and return relevant matches"""
        query_embedding = self._encode_text(query)
        query_vector = np.array([query_embedding])

        # Search each index
        semantic_distances, semantic_indices = self.semantic_index.search(query_vector, k)
        episodic_distances, episodic_indices = self.episodic_index.search(query_vector, k)
        periodic_distances, periodic_indices = self.periodic_index.search(query_vector, k)

        return {
            'semantic': [self.semantic_memories[i] for i in semantic_indices[0] if i >= 0],
            'episodic': [self.episodic_memories[i] for i in episodic_indices[0] if i >= 0],
            'periodic': [self.periodic_memories[i] for i in periodic_indices[0] if i >= 0]
        }

    def _encode_text(self, text: str) -> np.ndarray:
        """Encode text to vector using sentence transformer"""
        return self.encoder.encode(text)

    def save_state(self):
        """Save knowledge bases to disk"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        save_dir = f'knowledge_store/knowledge_state_{timestamp}'
        os.makedirs(save_dir, exist_ok=True)

        # Save indices
        faiss.write_index(self.semantic_index, f'{save_dir}/semantic.index')
        faiss.write_index(self.episodic_index, f'{save_dir}/episodic.index')
        faiss.write_index(self.periodic_index, f'{save_dir}/periodic.index')

        # Save memories
        with open(f'{save_dir}/memories.json', 'w') as f:
            json.dump({
                'semantic': self.semantic_memories,
                'episodic': self.episodic_memories,
                'periodic': self.periodic_memories
            }, f, indent=4)

    def load_state(self, state_dir: str):
        """Load knowledge bases from disk"""
        self.semantic_index = faiss.read_index(f'{state_dir}/semantic.index')
        self.episodic_index = faiss.read_index(f'{state_dir}/episodic.index')
        self.periodic_index = faiss.read_index(f'{state_dir}/periodic.index')

        with open(f'{state_dir}/memories.json', 'r') as f:
            memories = json.load(f)
            self.semantic_memories = memories['semantic']
            self.episodic_memories = memories['episodic']
            self.periodic_memories = memories['periodic'] 