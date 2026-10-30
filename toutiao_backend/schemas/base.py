from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class SchemaBase(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        from_attributes=True,
    )


DataT = TypeVar("DataT")


class PageData(SchemaBase, Generic[DataT]):
    list: list[DataT]
    total: int
    has_more: bool
