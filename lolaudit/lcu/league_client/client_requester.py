import logging

import requests

logger = logging.getLogger(__name__)


class ClientRequester:
    def __init__(self) -> None:
        super().__init__()
        self.__port: str
        self.__token: str
        self.__session = requests.Session()
        self.__session.verify = False
        self.__session.auth = None
        self.__session.headers.update({"Accept": "application/json"})

    @property
    def port(self) -> str:
        return self.__port

    @port.setter
    def port(self, value: str) -> None:
        self.__port = value

    @property
    def token(self) -> str:
        return self.__token

    @token.setter
    def token(self, value: str) -> None:
        self.__token = value
        self.__session.auth = ("riot", self.__token)

    def get(self, url: str) -> dict:
        try:
            url = f"https://127.0.0.1:{self.port}{url}"
            response = self.__session.get(url, timeout=(3, 10))
            return response.json()
        except (requests.exceptions.ConnectionError, requests.exceptions.InvalidURL):
            logger.debug(f"get request失敗: {url}")
            return {}

    def post(self, url: str) -> None:
        try:
            url = f"https://127.0.0.1:{self.port}{url}"
            self.__session.post(url, timeout=(3, 10))
        except (requests.exceptions.ConnectionError, requests.exceptions.InvalidURL):
            logger.debug(f"post request失敗: {url}")

    def delete(self, url: str) -> None:
        try:
            url = f"https://127.0.0.1:{self.port}{url}"
            self.__session.delete(url, timeout=(3, 10))
        except (requests.exceptions.ConnectionError, requests.exceptions.InvalidURL):
            logger.debug(f"delete request失敗: {url}")
