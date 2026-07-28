from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ReportBase(BaseModel):
    """
    Base Report Schema.
    """

    report_type: str = Field(..., min_length=1, max_length=100)

    file_name: str

    file_path: str

    generated_by: int = Field(..., gt=0)


class ReportCreate(ReportBase):
    """
    Schema used to create a report.
    """

    pass


class ReportUpdate(BaseModel):
    """
    Schema used to update report information.
    """

    report_type: str | None = None

    file_name: str | None = None

    file_path: str | None = None


class ReportResponse(ReportBase):
    """
    Schema returned from API.
    """

    id: int

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
