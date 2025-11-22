from ..optional_model import OptonalModel

""" 
{
    "dodgeData": {"dodgerId": 0, "state": "Invalid"},
    "errors": [
        {
            "errorType": "QUEUE_DODGER",
            "id": 1,
            "message": "QUEUE_DODGER",
            "penalizedSummonerId": 3862597327267648,
            "penaltyTimeRemaining": 121.07999999999998,
        }
    ],
    "estimatedQueueTime": 0.0,
    "isCurrentlyInQueue": False,
    "lobbyId": "",
    "lowPriorityData": {
        "bustedLeaverAccessToken": "",
        "penalizedSummonerIds": [],
        "penaltyTime": 0.0,
        "penaltyTimeRemaining": 0.0,
        "reason": "",
    },
    "queueId": 420,
    "readyCheck": {
        "declinerIds": [],
        "dodgeWarning": "None",
        "playerResponse": "None",
        "state": "Invalid",
        "suppressUx": False,
        "timer": 0.0,
    },
    "searchState": "Error",
    "timeInQueue": 0.0,
}

"""


class MatchmakingInfo(OptonalModel):
    class DodgeData(OptonalModel):
        dodgerId: int
        state: str

    class Error(OptonalModel):
        errorType: str
        id: int
        message: str
        penalizedSummonerId: int
        penaltyTimeRemaining: float

    class LowPriorityData(OptonalModel):
        bustedLeaverAccessToken: str
        penalizedSummonerIds: list
        penaltyTime: float
        penaltyTimeRemaining: float
        reason: str

    class ReadyCheck(OptonalModel):
        declinerIds: list
        dodgeWarning: str
        playerResponse: str
        state: str
        suppressUx: bool
        timer: float

    dodgeData: DodgeData
    errors: list[Error]
    estimatedQueueTime: float
    isCurrentlyInQueue: bool
    lobbyId: str
    lowPriorityData: LowPriorityData
    queueId: int
    readyCheck: ReadyCheck
    searchState: str
    timeInQueue: float
