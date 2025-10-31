class GameflowError(Exception):
    pass


class UnknownGameflowStateError(GameflowError):
    def __init__(self, state: str) -> None:
        super().__init__(f"未知gameflow狀態:{state}")
