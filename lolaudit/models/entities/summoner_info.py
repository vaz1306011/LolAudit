from typing import Optional

from pydantic import BaseModel, model_validator

from lolaudit.exceptions import SummonerInfoError


class SummonerInfo(BaseModel):
    puuid: Optional[str] = None
    gameName: Optional[str] = None
    tagLine: Optional[str] = None

    @model_validator(mode="before")
    def validate_fields(cls, values) -> None:
        if not values.get("puuid"):
            raise SummonerInfoError("無法取得puuid")
        if not values.get("gameName"):
            raise SummonerInfoError("無法取得gameName")
        if not values.get("tagLine"):
            raise SummonerInfoError("無法取得tagLine")
        return values
