import os
import subprocess
import logging
from datetime import datetime
from llm_interface import LLMDecisionMaker

class CodingSystem:
    def __init__(self, character_name: str):
        self.character_name = character_name
        self.coding_directory = f"character_files/{character_name}/code"
        self.logger = logging.getLogger('CodingSystem')
        self.llm = LLMDecisionMaker()
        self.setup_directory()

    def setup_directory(self):
        """Create necessary directories for the character's code"""
        os.makedirs(self.coding_directory, exist_ok=True)

    def generate_code(self, prompt: str) -> tuple[str, str]:
        """Generate code based on a prompt using LLM"""
        context = {
            "task": "code_generation",
            "prompt": prompt,
            "previous_files": self.list_files(),
            "character_name": self.character_name
        }

        response = self.llm.generate_code(context)
        
        # Expected response format:
        # {
        #     "filename": "example.py",
        #     "description": "A program that...",
        #     "code": "print('Hello...')"
        # }

        if isinstance(response, dict) and "filename" in response and "code" in response:
            return response["filename"], response["code"]
        return None, None

    def create_file(self, filename: str, content: str) -> bool:
        """Create a new Python file with the given content"""
        try:
            file_path = os.path.join(self.coding_directory, filename)
            with open(file_path, 'w') as f:
                f.write(content)
            self.logger.info(f"Created file: {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Error creating file {filename}: {str(e)}")
            return False

    def run_file(self, filename: str) -> tuple[bool, str]:
        """Run a Python file and return the result"""
        try:
            file_path = os.path.join(self.coding_directory, filename)
            if not os.path.exists(file_path):
                return False, f"File {filename} does not exist"

            # Run the Python file in a separate process with restricted permissions
            result = subprocess.run(
                ['python', file_path],
                capture_output=True,
                text=True,
                timeout=5,  # 5 second timeout
                env={"PYTHONPATH": self.coding_directory}  # Restrict import path
            )

            # Log the execution
            self.logger.info(f"Ran file: {filename}")
            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, f"Error: {result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "Code execution timed out"
        except Exception as e:
            self.logger.error(f"Error running file {filename}: {str(e)}")
            return False, str(e)

    def list_files(self) -> list[str]:
        """List all Python files in the character's coding directory"""
        try:
            return [f for f in os.listdir(self.coding_directory) if f.endswith('.py')]
        except Exception as e:
            self.logger.error(f"Error listing files: {str(e)}")
            return [] 