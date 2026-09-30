"""Request and response models. Request bodies reject unknown fields."""

from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    """Base for request bodies: unknown fields are rejected and strings are trimmed."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class LoginIn(BaseModel):
    model_config = ConfigDict(extra="forbid")  # passwords are not trimmed
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class MeOut(BaseModel):
    display_name: str
