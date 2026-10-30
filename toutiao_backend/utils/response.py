from typing import Generic, TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class ApiResponse(BaseModel, Generic[DataT]):
    code: int = 200
    message: str = "success"
    data: DataT | None = None


def success_response(
    message: str = "success",
    data: DataT | None = None,
) -> ApiResponse[DataT]:
    return ApiResponse[DataT](code=200, message=message, data=data)
