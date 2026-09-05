import json
from datetime import datetime, timedelta
from pathlib import Path

from notifications.notification_service import (
    create_notification,
)

ALERT_DIR = Path("logs")
ALERT_FILE = ALERT_DIR / "alerts.json"

CONFIDENCE_THRESHOLD = 0.70

CLASS_PRIORITY = {
    "fire": "CRITICAL",
    "weapon": "CRITICAL",
    "restricted_object": "HIGH",
    "smoke": "HIGH",
    "person": "NORMAL",
    "vehicle": "NORMAL",
    "helmet": "LOW",
    "safety_vest": "LOW",
}

ALERT_COOLDOWN = {
    "fire": 60,
    "weapon": 60,
    "restricted_object": 45,
    "smoke": 60,
    "person": 15,
    "vehicle": 15,
    "helmet": 30,
    "safety_vest": 30,
}

last_alert_time = {}


def create_directory():
    ALERT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def check_cooldown(
    class_name,
):
    current_time = datetime.now()

    if class_name not in last_alert_time:
        last_alert_time[class_name] = current_time
        return True

    previous_time = last_alert_time[class_name]

    cooldown = ALERT_COOLDOWN.get(
        class_name,
        30,
    )

    difference = current_time - previous_time

    if difference >= timedelta(seconds=cooldown):
        last_alert_time[class_name] = current_time

        return True

    return False


def check_detection(
    class_name,
    confidence,
):
    if confidence < CONFIDENCE_THRESHOLD:
        return None

    if class_name not in CLASS_PRIORITY:
        return None

    if not check_cooldown(class_name):
        print(f"Cooldown active: {class_name}")

        return None

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "object": class_name,
        "confidence": round(
            confidence,
            3,
        ),
        "priority": CLASS_PRIORITY[class_name],
        "status": "ACTIVE",
    }


def save_alert(
    alert,
):
    create_directory()

    alerts = []

    if ALERT_FILE.exists():
        try:
            with open(
                ALERT_FILE,
                "r",
                encoding="utf-8",
            ) as file:
                alerts = json.load(file)

        except (
            json.JSONDecodeError,
            OSError,
        ):
            alerts = []

    alerts.append(alert)

    with open(
        ALERT_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            alerts,
            file,
            indent=4,
        )

    notification = create_notification(alert)

    if notification:
        print(
            f"NOTIFICATION CREATED: {notification['priority']} {notification['object']}"
        )


def main():
    print("Sentronix Alert Engine")

    create_directory()

    alert = check_detection(
        "fire",
        0.92,
    )

    if alert:
        save_alert(alert)

        print("CRITICAL ALERT CREATED")

    else:
        print("No alert")


if __name__ == "__main__":
    main()
