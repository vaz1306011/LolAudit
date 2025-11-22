from pprint import pformat
from typing import Optional

from lolaudit.models.entities.response.matchmaking_info import MatchmakingInfo


class MatchmakingError(Exception):
    pass


class UnknownMatchmakingInfoError(MatchmakingError):
    def __init__(self, matchmaking_info: MatchmakingInfo) -> None:
        super().__init__(f"未知matchmaking:\n{pformat(matchmaking_info)}")


class UnknownSearchStateError(MatchmakingError):
    def __init__(self, search_state: Optional[str]) -> None:
        if search_state is not None:
            super().__init__(f"未知searchState: {search_state}")
        else:
            super().__init__(f"未知searchState:{type(None)}")


class UnknownPlayerResponseError(MatchmakingError):
    def __init__(self, player_response: Optional[str]) -> None:
        if player_response is not None:
            super().__init__(f"未知playerResponse: {player_response}")
        else:
            super().__init__(f"未知playerResponse:{type(None)}")
