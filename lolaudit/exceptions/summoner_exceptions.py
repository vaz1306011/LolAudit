class SummonerError(Exception):
    pass


class SummonerInfoError(SummonerError):
    """授權成功，但無法取得召喚師資訊"""

    def __init__(self, message="無法取得召喚師資訊") -> None:
        super().__init__(message)
