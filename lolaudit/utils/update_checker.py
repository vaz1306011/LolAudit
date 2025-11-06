import logging
from dataclasses import dataclass
from typing import Optional

import requests

logger = logging.getLogger(__name__)

GITHUB_REPO = "vaz1306011/LOL_audit"


@dataclass
class UpdateInfo:
    has_update: bool
    latest: str
    url: str
    notes: str
    error: Optional[str] = None


def check_update(current_version: str) -> UpdateInfo:
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    try:
        r = requests.get(url, timeout=3)
        r.raise_for_status()
        data = r.json()
        latest = data.get("tag_name", "")
        if latest and latest != current_version:
            return UpdateInfo(
                has_update=True,
                latest=latest,
                url=data.get("html_url", ""),
                notes=data.get("body", ""),
            )
        return UpdateInfo(has_update=False, latest="", url="", notes="")
    except requests.RequestException as e:
        logger.error(f"新版本檢查失敗: {e}")
        return UpdateInfo(has_update=False, latest="", url="", notes="", error=str(e))


if __name__ == "__main__":
    current_version = "1.0.0"
    result = check_update(current_version)
    print(result)
