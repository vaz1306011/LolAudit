import logging
from typing import Optional

import requests

from lolaudit.lcu import wait_for_lcu_prot_and_token

logger = logging.getLogger(__name__)


class Requester:
    def __init__(self) -> None:
        super().__init__()
        self.port = None
        self.token = None
        self.__session = requests.Session()
        self.__session.verify = False
        self.__session.auth = None
        self.__session.headers.update({"Accept": "application/json"})

    def get(self, url: str) -> dict:
        try:
            url = f"https://127.0.0.1:{self.port}{url}"
            response = self.__session.get(url, timeout=(3, 10))
            return response.json()
        except requests.exceptions.ConnectionError:
            logger.warning(f"get request失敗: {url}")
            return {}

    def post(self, url: str) -> None:
        try:
            url = f"https://127.0.0.1:{self.port}{url}"
            self.__session.post(url, timeout=(3, 10))
        except requests.exceptions.ConnectionError:
            logger.warning(f"post request失敗: {url}")

    def delete(self, url: str) -> None:
        try:
            url = f"https://127.0.0.1:{self.port}{url}"
            self.__session.delete(url, timeout=(3, 10))
        except requests.exceptions.ConnectionError:
            logger.warning(f"delete request失敗: {url}")

    def get_port_and_token(self) -> tuple[Optional[str], Optional[str]]:
        return self.port, self.token

    def wait_for_refresh_port_and_token(self) -> None:
        self.port, self.token = wait_for_lcu_prot_and_token()
        self.__session.auth = ("riot", self.token)
