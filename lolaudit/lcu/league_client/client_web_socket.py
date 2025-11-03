import base64
import json
import logging
import ssl
import threading

import websocket
from PySide6.QtCore import QObject, Signal

from lolaudit.utils import web_socket

logger = logging.getLogger(__name__)


class ClientWebSocket(QObject):
    websocket_connected = Signal()
    websocket_message = Signal(str, object)
    websocket_close = Signal()

    def __init__(self):
        super().__init__()
        self.port: str
        self.token: str
        self.ws = None
        self.main_thread = None

    def __on_open(self, ws):
        logger.info("WebSocket連接已開啟")
        self.websocket_connected.emit()

    def __on_message(self, ws, msg: str):
        if not msg.strip():
            return
        try:
            _, url, data = json.loads(msg)
            self.websocket_message.emit(url, data.get("data"))
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析錯誤: {e}\n  訊息內容: {msg}")
        except Exception as e:
            logger.warning(f"解析錯誤: {e}")

    def __on_close(self, ws, close_status_code, close_msg):
        logger.info(f"WebSocket連接已關閉: {close_status_code} - {close_msg}")
        self.websocket_close.emit()
        self.ws = None

    def start_websocket(self):
        if self.ws:
            logger.warning("WebSocket已啟動，無需重複啟動")
            return
        if not self.port or not self.token:
            logger.error("無法啟動WebSocket，缺少port或token")
            return

        url = f"wss://127.0.0.1:{self.port}/"
        auth_str = base64.b64encode(f"riot:{self.token}".encode()).decode()
        header = [f"Authorization: Basic {auth_str}"]

        def run():
            self.ws = websocket.WebSocketApp(
                url,
                header=header,
                on_open=self.__on_open,
                on_message=self.__on_message,
                on_close=self.__on_close,
            )
            self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

        self.main_thread = threading.Thread(target=run, daemon=True)
        self.main_thread.start()

    def subscribe(self, url: str):
        if not self.ws:
            logger.warning("WebSocket未連接，無法訂閱頻道")
            return
        url = web_socket.format_url(url)
        subscribe_msg = [5, url]
        logger.debug(f"訂閱訊息: {subscribe_msg}")
        self.ws.send(json.dumps(subscribe_msg))
        logger.info(f"已訂閱頻道: {subscribe_msg}")

    def unsubscribe(self, url: str):
        if not self.ws:
            logger.warning("WebSocket未連接，無法取消訂閱頻道")
            return

        url = web_socket.format_url(url)
        unsubscribe_msg = [6, url]
        self.ws.send(json.dumps(unsubscribe_msg))
        logger.info(f"已取消訂閱頻道: {url}")

    def stop_websocket(self):
        if not self.ws:
            logger.warning("WebSocket未連接，無法停止")
            return

        self.ws.close()
        self.ws = None
