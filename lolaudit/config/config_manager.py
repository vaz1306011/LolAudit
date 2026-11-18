import json
import logging
from pathlib import Path

from appdirs import user_config_dir
from PySide6.QtCore import QObject

from lolaudit.models import Config, ConfigKeys

logger = logging.getLogger(__name__)


class ConfigManager(QObject):
    def __init__(self) -> None:
        self.__setting_path = self.get_config_path()
        logger.info(f"Config路徑: {self.__setting_path}")
        self.setting = Config()
        self.__extra: dict = {}  # 檔案中未知的欄位,存檔時原樣保留
        self.load_config()

    def get_config_path(self) -> str:
        path = Path(user_config_dir("LOL_Audit"), "config.json")
        return str(path)

    def load_config(self) -> None:
        try:
            with open(self.__setting_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            self.save_config()
            return
        except (OSError, json.JSONDecodeError) as e:
            # 讀取失敗時使用預設值,但不覆蓋原檔案
            logger.warning(f"讀取設定檔失敗,使用預設值且不覆蓋檔案: {e}")
            return

        if not isinstance(data, dict):
            logger.warning("設定檔內容不是物件,使用預設值且不覆蓋檔案")
            return

        known = Config.model_fields.keys()
        values = {}
        for key, value in data.items():
            if key not in known:
                self.__extra[key] = value
                continue
            try:
                # 逐欄位驗證,型別錯誤的欄位退回預設值
                Config(**{key: value})
                values[key] = value
            except ValueError as e:
                logger.warning(f"設定欄位 {key} 的值無效,使用預設值: {e}")
        self.setting = Config(**values)

    def save_config(self) -> None:
        Path(self.__setting_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.__setting_path, "w", encoding="utf-8") as f:
            json.dump(
                {**self.__extra, **self.setting.model_dump()},
                f,
                ensure_ascii=False,
                indent=2,
            )

    def set_config(self, key: ConfigKeys, value: object) -> None:
        if hasattr(self.setting, key.value):
            setattr(self.setting, key.value, value)
            self.save_config()
        else:
            raise AttributeError(f"Setting has no attribute '{key}'")

    def get_config(self, key: ConfigKeys) -> bool | int:
        if hasattr(self.setting, key.value):
            return getattr(self.setting, key.value)
        else:
            raise AttributeError(f"Setting has no attribute '{key}'")
