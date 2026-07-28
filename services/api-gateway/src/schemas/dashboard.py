from pydantic import BaseModel
from pydantic import ConfigDict


class DashboardSummary(BaseModel):
    """
    Dashboard summary statistics.
    """

    total_cameras: int

    online_cameras: int

    total_detections: int

    total_alerts: int

    open_alerts: int

    critical_alerts: int

    total_recordings: int

    ai_status: str

    database_status: str

    system_status: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class DashboardTrend(BaseModel):
    """
    Time-series dashboard data.
    """

    labels: list[str]

    values: list[int]


class DashboardResponse(BaseModel):
    """
    Complete dashboard response.
    """

    summary: DashboardSummary

    detection_trend: DashboardTrend

    alert_trend: DashboardTrend

    recording_trend: DashboardTrend

    model_config = ConfigDict(
        from_attributes=True,
    )
