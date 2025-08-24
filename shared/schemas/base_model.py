from typing import Generic, Literal, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponseBase(BaseModel, Generic[T]):
    success: Literal[True, False]
    message: str
    data: T
