from datetime import date

from pydantic import BaseModel


class DailyDetection(BaseModel):
    date: date
    detections: int


class DailyAlert(BaseModel):
    date: date
    alerts: int


class CameraStatistic(BaseModel):
    camera_id: int
    camera_name: str
    detections: int


class ObjectStatistic(BaseModel):
    label: str
    count: int


class DashboardAnalytics(BaseModel):
    daily_detections: list[DailyDetection]
    daily_alerts: list[DailyAlert]
    camera_statistics: list[CameraStatistic]
    object_statistics: list[ObjectStatistic]
