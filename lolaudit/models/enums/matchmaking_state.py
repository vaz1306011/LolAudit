from enum import Enum, auto


class MatchmakingState(Enum):
    NONE = auto()
    LOBBY = auto()
    PENALTY = auto()
    MATCHING = auto()
    WAITING_ACCEPT = auto()
    DECLINED = auto()
    ACCEPTED = auto()
    UNKNOW = auto()
