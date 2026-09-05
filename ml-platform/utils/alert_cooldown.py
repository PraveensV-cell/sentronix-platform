from datetime import datetime, timedelta


# -------------------------------------------------
# SETTINGS
# -------------------------------------------------

COOLDOWN_TIME = {
    "fire": 60,
    "weapon": 60,
    "restricted_object": 45,
    "smoke": 60,
    "person": 15,
    "vehicle": 15,
}


# Store last alerts

last_alerts = {}


# -------------------------------------------------
# CHECK COOLDOWN
# -------------------------------------------------


def can_send_alert(
    object_name: str,
):

    current_time = datetime.now()

    if object_name not in last_alerts:
        last_alerts[object_name] = current_time

        return True

    previous_time = last_alerts[object_name]

    cooldown = COOLDOWN_TIME.get(
        object_name,
        30,
    )

    elapsed = current_time - previous_time

    if elapsed >= timedelta(seconds=cooldown):
        last_alerts[object_name] = current_time

        return True

    return False


# -------------------------------------------------
# TEST
# -------------------------------------------------


def main():

    print("Alert Cooldown Test")

    result1 = can_send_alert("fire")

    result2 = can_send_alert("fire")

    print(
        "First alert:",
        result1,
    )

    print(
        "Second alert:",
        result2,
    )


if __name__ == "__main__":
    main()
