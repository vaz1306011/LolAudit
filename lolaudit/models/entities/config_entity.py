from pydantic import BaseModel


class Config(BaseModel):
    always_on_top: bool = True
    backguard_startup: bool = True
    auto_accept: bool = True
    auto_rematch: bool = True
    auto_start_match: bool = True
    accept_delay: int = 3
