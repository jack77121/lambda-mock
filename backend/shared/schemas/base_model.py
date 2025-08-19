from typing import Generic, Literal, TypeVar

from humps import camelize
from pydantic import BaseModel


def to_camel(string):
    return camelize(string)


T = TypeVar("T")


class CamelBaseModel(BaseModel):
    class Config:
        alias_generator = to_camel
        populate_by_name = True


class ApiResponseBase(CamelBaseModel, Generic[T]):
    status: Literal["success", "fail", "error"]
    message: str
    data: T
