from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.schemas.alert import (
    AlertCreate,
    AlertResponse,
    AlertUpdate,
)
from src.services.alert import AlertService

router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"],
)


@router.post(
    "",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_alert(
    alert: AlertCreate,
    db: Session = Depends(get_db),
):

    return AlertService(db).create_alert(alert)


@router.get(
    "",
    response_model=list[AlertResponse],
)
def list_alerts(
    db: Session = Depends(get_db),
):

    return AlertService(db).list_alerts()


@router.get(
    "/{alert_id}",
    response_model=AlertResponse,
)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
):

    alert = AlertService(db).get_alert(alert_id)

    if alert is None:
        raise HTTPException(
            status_code=404,
            detail="Alert not found",
        )

    return alert


@router.put(
    "/{alert_id}",
    response_model=AlertResponse,
)
def update_alert(
    alert_id: int,
    alert_data: AlertUpdate,
    db: Session = Depends(get_db),
):

    alert = AlertService(db).update_alert(
        alert_id,
        alert_data,
    )

    if alert is None:
        raise HTTPException(
            status_code=404,
            detail="Alert not found",
        )

    return alert


@router.delete(
    "/{alert_id}",
)
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
):

    deleted = AlertService(db).delete_alert(alert_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Alert not found",
        )

    return {
        "success": True,
        "message": "Alert deleted successfully",
    }
