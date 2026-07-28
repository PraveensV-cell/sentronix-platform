import csv
import os
from datetime import datetime


class AuditCSVExporter:
    """
    Export audit logs to CSV.
    """

    def export(
        self,
        audit_logs,
    ):

        directory = os.path.join(
            "storage",
            "audit_logs",
        )

        os.makedirs(
            directory,
            exist_ok=True,
        )

        filename = datetime.now().strftime("%Y%m%d_%H%M%S") + "_audit_logs.csv"

        filepath = os.path.join(
            directory,
            filename,
        )

        with open(
            filepath,
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.writer(file)

            writer.writerow(
                [
                    "ID",
                    "User ID",
                    "Action",
                    "Resource",
                    "Description",
                    "IP Address",
                    "Created At",
                ]
            )

            for log in audit_logs:
                writer.writerow(
                    [
                        log.id,
                        log.user_id,
                        log.action,
                        log.resource,
                        log.description,
                        log.ip_address,
                        log.created_at,
                    ]
                )

        return filepath
