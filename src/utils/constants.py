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
    DOOR = 'door'
    FOOD = 'food'
    DRINK = 'drink'

class BuildingType(Enum):
    HOUSE = "house"
    SUPERMARKET = "supermarket"
    EMPTY = "empty"

class ActivityState(Enum):
    IDLE = 'idle'
    BUSY = 'busy'
    NEEDS_EXIT = 'needs_exit'

class ActivityType(Enum):
    TOILET_USE = 'toilet_use'
    FRIDGE_USE = 'fridge_use'
    COMPUTER_USE = 'computer_use'
    TV_WATCHING = 'tv_watching'
    SLEEPING = 'sleeping'
    EATING = 'eating'
    SHOWER_USE = 'shower_use'
