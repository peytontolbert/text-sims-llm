
# File: game.py
import time
from typing import Optional
from environment.house import House
from src.character.character import SimCharacter
from src.utils.constants import Direction, ObjectType

class SimsGame:
    def __init__(self):
        self.house = House()
        self.character = SimCharacter("Alex", self.house)
        self.running = True
        self.last_update = time.time()

    def process_command(self, command: str) -> str:
        parts = command.lower().split()
        if not parts:
            return "Please enter a command."

        action = parts[0]
        if action == "quit":
            self.running = False
            return "Goodbye!"

        if action == "move":
            if len(parts) < 2:
                return "Please specify a direction (north/south/east/west)."
            try:
                direction = Direction(parts[1])
                if self.character.move(direction):
                    return f"Moved {direction.value}"
                return "Cannot move in that direction"
            except ValueError:
                return "Invalid direction"

        if action == "use":
            if len(parts) < 3:
                return "Please specify an object and action (e.g., 'use computer browse')."
            try:
                object_type = ObjectType(parts[1])
                action = parts[2]
                if self.character.perform_action(object_type, action):
                    return f"Using {object_type.value} to {action}"
                return f"Cannot {action} with {object_type.value} here"
            except ValueError:
                return "Invalid object or action"

        if action == "status":
            return self.character.get_status()

        if action == "help":
            return self.get_help_text()

        if action == "look":
            return self.get_room_description()

        return "Unknown command. Type 'help' for available commands."

    def update(self):
        current_time = time.time()
        delta_time = current_time - self.last_update
        self.character.update_needs(delta_time)
        self.last_update = current_time

    def get_help_text(self) -> str:
        return """
Available commands:
  move <direction> - Move in a direction (north/south/east/west)
  use <object> <action> - Interact with an object
  status - Show current status
  look - Describe current room
  help - Show this help text
  quit - Exit the game
"""

    def get_room_description(self) -> str:
        room = self.house.get_room(self.character.position)
        objects = self.house.get_objects_in_room(self.character.position)
        
        description = [f"You are in the {room.value}."]
        if objects:
            description.append("You see:")
            for obj in objects:
                description.append(f"- {obj.description}")
                description.append(f"  Available actions: {', '.join(obj.actions)}")
        else:
            description.append("The room is empty.")
        
        return "\n".join(description)

    def run(self):
        print("Welcome to Text-Based Sims!")
        print(self.get_help_text())
        
        while self.running:
            self.update()
            
            # Show urgent needs
            urgent_needs = self.character.get_urgent_needs()
            if urgent_needs:
                print(f"\nUrgent needs: {', '.join(urgent_needs)}")
            
            command = input("\nWhat would you like to do? ").strip()
            result = self.process_command(command)
            print(result)

        # Clean up browser if it was used
        if self.character.browser:
            self.character.browser.close()