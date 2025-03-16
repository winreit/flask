import pydantic
from typing import Optional, Type


class CreateOwner(pydantic.BaseModel):
    owner: str
    password: str

    @pydantic.validator("password")
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Password is too short")
        return value


class PatchOwner(pydantic.BaseModel):
    owner: Optional[str]
    password: Optional[str]

    @pydantic.validator("password")
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Password is too short")
        return value


VALIDATION_CLASS = Type[CreateOwner] | Type[PatchOwner]