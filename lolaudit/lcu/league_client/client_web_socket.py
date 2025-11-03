import base64
import json
import logging
import ssl
import time
from threading import Thread

import websocket
from PySide6.QtCore import QObject, Signal

from lolaudit.utils import web_socket

logger = logging.getLogger(__name__)


class ClientWebSocket(QObject):
    websocket_on_open = Signal()
    websocket_on_message = Signal(str, object)
    websocket_on_close = Signal()

    def __init__(self):
        super().__init__()
        self.port: str
        self.token: str
        self.__ws = None
        self.__subscribed = set()
        self.__running = False

    def __on_open(self, ws):
        logger.info("WebSocket連接已開啟")
        self.websocket_on_open.emit()

    def __on_message(self, ws, msg: str):
        if not msg.strip():
            return
        try:
            _, url, data = json.loads(msg)
            self.websocket_on_message.emit(url, data.get("data"))
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析錯誤: {e}\n  訊息內容: {msg}")
        except Exception as e:
            logger.warning(f"解析錯誤: {e}")

    def __on_close(self, ws, close_status_code, close_msg):
        logger.info(f"WebSocket連接已關閉")
        self.__running = False
        self.__subscribed.clear()
        self.__ws = None
        self.websocket_on_close.emit()

    def start_websocket(self):
        if self.__running or self.__ws:
            logger.warning("WebSocket已在運行中，無法重複啟動")
            return

        def __run():
            self.__running = True
            while self.__running:
                try:
                    if not self.port or not self.token:
                        logger.error("無法啟動WebSocket，缺少port或token")
                        raise ValueError("缺少port或token")
                    url = f"wss://127.0.0.1:{self.port}/"
                    auth_str = base64.b64encode(f"riot:{self.token}".encode()).decode()
                    header = [f"Authorization: Basic {auth_str}"]
                    self.__ws = websocket.WebSocketApp(
                        url,
                        header=header,
                        on_open=self.__on_open,
                        on_message=self.__on_message,
                        on_close=self.__on_close,
                    )
                    self.__ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
                except Exception as e:
                    logger.warning(f"WebSocket連接錯誤: {e}")

                if self.__running:
                    logger.info("WebSocket嘗試重新連接中...")
                    time.sleep(3)

        Thread(target=__run, daemon=True).start()

    def subscribe(self, url: str):
        if not self.__ws:
            logger.warning("WebSocket未連接，無法訂閱頻道")
            return
        if url in self.__subscribed:
            return
        url = web_socket.format_url(url)
        subscribe_msg = [5, url]
        self.__ws.send(json.dumps(subscribe_msg))
        self.__subscribed.add(url)

        self._handle = False

    def unsubscribe(self, url: str):
        if not self.__ws:
            logger.warning(f"WebSocket未連接，無法取消訂閱頻道\n{url}")
            return
        if url not in self.__subscribed:
            return
        self.__subscribed.remove(url)
        url = web_socket.format_url(url)
        unsubscribe_msg = [6, url]
        self.__ws.send(json.dumps(unsubscribe_msg))

    def stop_websocket(self):
        if not self.__ws:
            logger.warning("WebSocket未連接，無法停止")
            return

        self.__ws.close()
        self.__subscribed.clear()
