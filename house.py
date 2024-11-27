# File: house.py
from typing import Dict, List, Optional
from models import Position, GameObject
from constants import RoomType, ObjectType
from collections import defaultdict

class House:
    def __init__(self):
        self.rooms: Dict[Position, RoomType] = {}
        self.objects: Dict[Position, List[GameObject]] = defaultdict(list)
        self.initialize_layout()

    def initialize_layout(self):
        # Define room layout
        self.rooms[Position(0, 0)] = RoomType.BEDROOM
        self.rooms[Position(1, 0)] = RoomType.BATHROOM
        self.rooms[Position(0, 1)] = RoomType.LIVING_ROOM
        self.rooms[Position(1, 1)] = RoomType.KITCHEN

        # Define objects in each room
        self.objects[Position(0, 0)].append(
            GameObject(
                type=ObjectType.BED,
                actions=['sleep', 'rest', 'nap'],
                need_effects={'energy': 50, 'comfort': 20},
                description="A comfortable bed for sleeping"
            )
        )

        self.objects[Position(1, 0)].extend([
            GameObject(
                type=ObjectType.TOILET,
                actions=['use'],
                need_effects={'bladder': 40},
                description="A toilet"
            ),
            GameObject(
                type=ObjectType.SHOWER,
                actions=['shower', 'quick_shower'],
                need_effects={'hygiene': 40, 'comfort': 10},
                description="A shower for getting clean"
            )
        ])

        self.objects[Position(0, 1)].extend([
            GameObject(
                type=ObjectType.TV,
                actions=['watch', 'channel_surf'],
                need_effects={'fun': 30, 'energy': -10, 'social': 5},
                description="A TV for entertainment"
            ),
            GameObject(
                type=ObjectType.COMPUTER,
                actions=['browse', 'play', 'work', 'code', 'run_code', 'write_journal', 'read_journal'],
                need_effects={'fun': 25, 'social': 20, 'energy': -15, 'coding_skill': 10, 'emotional': 15},
                description="A computer for various activities including coding and journaling"
            ),
            GameObject(
                type=ObjectType.COUCH,
                actions=['sit', 'relax', 'nap'],
                need_effects={'energy': 20, 'comfort': 30},
                description="A couch for relaxing"
            ),
            GameObject(
                type=ObjectType.PHONE,
                actions=['call', 'answer'],
                need_effects={'social': 30, 'fun': 10, 'energy': -5},
                description="A phone for making calls and socializing"
            )
        ])

        self.objects[Position(1, 1)].extend([
            GameObject(
                type=ObjectType.FRIDGE,
                actions=['get_food', 'check_ingredients'],
                need_effects={'hunger': 30},
                description="A fridge full of food"
            ),
            GameObject(
                type=ObjectType.STOVE,
                actions=['cook', 'bake', 'prepare_meal'],
                need_effects={'hunger': 40, 'fun': 10, 'energy': -20},
                description="A stove for cooking meals"
            )
        ])

    def get_room(self, position: Position) -> Optional[RoomType]:
        return self.rooms.get(position)

    def get_objects_in_room(self, position: Position) -> List[GameObject]:
        return self.objects[position]

    def is_valid_move(self, position: Position) -> bool:
        return position in self.rooms