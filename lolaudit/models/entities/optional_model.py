from typing import get_type_hints

from pydantic import BaseModel, model_validator


class OptonalModel(BaseModel):
    @model_validator(mode="after")
    def _fill_none(self):
        hints = get_type_hints(self.__class__)
        for name in hints:
            if getattr(self, name, None) is None:
                setattr(self, name, None)
        return self
