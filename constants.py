# File: constants.py
from enum import Enum

class Direction(Enum):
    NORTH = 'north'
    SOUTH = 'south'
    EAST = 'east'
    WEST = 'west'

class RoomType(Enum):
    BEDROOM = 'bedroom'
    KITCHEN = 'kitchen'
    LIVING_ROOM = 'living_room'
    BATHROOM = 'bathroom'
    HALLWAY = 'hallway'

class ObjectType(Enum):
    BED = 'bed'
    FRIDGE = 'fridge'
    STOVE = 'stove'
    TV = 'tv'
    COMPUTER = 'computer'
    TOILET = 'toilet'
    SHOWER = 'shower'
    COUCH = 'couch'
    PHONE = 'phone'
