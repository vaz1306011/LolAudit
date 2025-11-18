from typing import Optional

from pydantic import BaseModel


class UpdateInfo(BaseModel):
    has_update: bool = False
    latest: str = ""
    url: str = ""
    notes: str = ""
    error: Optional[str] = None
