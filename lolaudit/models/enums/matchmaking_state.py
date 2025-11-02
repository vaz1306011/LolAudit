from enum import Enum, auto


class MatchmakingState(Enum):
    NONE = auto()
    PENALTY = auto()
    WAITING_ACCEPT = auto()
    DECLINED = auto()
    ACCEPTED = auto()
    UNKNOW = auto()
