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
  pip install -r requirements.txt
  ```

## Project Structure

```files
main.py
src/
├── character/
│   ├── autonomous_character.py  # Main character logic and behavior
│   ├── character.py            # Base character class
│   └── needs_system.py         # Character needs simulation
├── computer/
│   ├── browser.py             # Web browser simulation
│   ├── browser_interface.py   # Browser interaction layer
│   ├── coding_system.py       # Code generation and execution
│   ├── game.py               # Game mechanics
│   └── journal_system.py      # Character journaling
├── ears/
│   └── whisper_manager.py     # Speech recognition system
├── environment/
│   └── house.py              # Environment definition
├── game/
│   └── autonomous_game.py     # Game loop and simulation
├── llm/
│   └── llm_interface.py      # LLM integration
├── memory/
│   ├── knowledge_system.py    # Long-term memory
│   └── memory_system.py       # Short-term memory
├── phone/
│   ├── index.html            # Voice chat interface
│   ├── phone_system.py       # Phone functionality
│   └── voice_chat_server.py  # Voice chat server
├── utils/
│   ├── constants.py          # Game constants
│   └── models.py            # Data models
└── voice/
    └── speech.py            # Text-to-speech system
```

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/peytontolbert/text-sims-ai.git
   cd text-sims-ai
   ```

2. Create and configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the simulation:
   ```bash
   python main.py
   ```

## Main Entry Point (main.py)

The main.py file serves as the entry point for the application:

```python
from src.game.autonomous_game import AutonomousSimsGame
from src.phone.voice_chat_server import run_server
import threading

def main():
    # Initialize and run the game
    game = AutonomousSimsGame()
    
    # Start voice chat server in a separate thread
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Run the main game loop
    game.run()

if __name__ == "__main__":
    main()
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