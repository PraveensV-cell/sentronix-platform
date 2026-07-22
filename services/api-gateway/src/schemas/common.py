from pydantic import BaseModel, ConfigDict


class BaseRequest(BaseModel):
    """
    Base class for every request model.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class BaseResponse(BaseModel):
    """
    Base class for every response model.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )
