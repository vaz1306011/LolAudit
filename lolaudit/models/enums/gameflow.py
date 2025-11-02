from enum import Enum, auto


class Gameflow(Enum):
    LOADING = auto()
    NONE = auto()
    LOBBY = auto()
    MATCHMAKING = auto()
    READY_CHECK = auto()
    CHAMP_SELECT = auto()
    IN_PROGRESS = auto()
    RECONNECT = auto()
    PRE_END_OF_GAME = auto()
    END_OF_GAME = auto()
    UNKNOWN = auto()
