# Autonomous Sims AI

An intelligent autonomous character simulation that uses AI to create self-directed virtual beings. The character makes decisions, maintains needs, builds memories, and learns from experiences.

## Features

- 🤖 Autonomous AI-driven character with decision making capabilities
- 🏠 Simulated house environment with multiple rooms and interactive objects
- 🧠 Advanced knowledge and memory systems
- 📝 Journal system for character reflection
- 💻 Coding system allowing the character to write and execute code
- 📱 Phone system for social interactions
- 🔄 Needs system simulating basic requirements (hunger, energy, etc.)
- 📊 Comprehensive logging system
- 🗣️ Voice chat interface

## Requirements

- Python 3.8+
- Dependencies (install via pip):
  ```bash
  pip install faiss-cpu
  pip install sentence-transformers
  pip install torch
  pip install flask
  ```

## Project Structure
```files
├── autonomous_character.py # Main character logic and behavior
├── autonomous_game.py # Game loop and simulation management
├── knowledge_system.py # Long-term memory and knowledge management
├── memory_system.py # Short-term memory and emotional state
├── needs_system.py # Character needs simulation
├── house.py # Environment definition
├── browser_interface.py # Web browsing capabilities
├── coding_system.py # Code generation and execution
├── journal_system.py # Character journaling
├── phone_system.py # Social interaction system
└── main.py # Application entry point
```


## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/peytontolbert/text-sims-ai.git
   cd text-sims-ai
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the simulation:
   ```bash
   python main.py
   ```

## How It Works

### Character System
The autonomous character maintains various systems:
- **Needs System**: Manages basic needs like energy, hunger, and social interaction
- **Knowledge System**: Stores and retrieves long-term memories and learned patterns
- **Memory System**: Handles short-term memories and emotional states
- **Decision Making**: Uses LLM to make contextual decisions based on current state

### Environment
- Multiple rooms with different functions
- Interactive objects that affect character needs
- Dynamic state tracking and persistence

### Logging
The system maintains detailed logs:
- Game state logs
- LLM decision logs
- Action execution logs
- Knowledge system state

## Directory Structure
```files
├── logs/ # Log files
├── states/ # Character state saves
├── knowledge_store/# Persistent knowledge storage
└── src/ # Source code


## Configuration

The simulation can be configured through various parameters:
- Knowledge save interval (default: 5 minutes)
- Need decay rates
- Memory retention settings
- Pattern detection thresholds

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built using the SentenceTransformers library
- FAISS for efficient similarity search
- PyTorch for machine learning capabilities

## Future Improvements

- [ ] Enhanced pattern recognition
- [ ] More sophisticated decision making
- [ ] Expanded environment interactions
- [ ] Improved social capabilities
- [ ] Multi-character interactions