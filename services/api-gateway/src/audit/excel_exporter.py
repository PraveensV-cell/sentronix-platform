import os
from datetime import datetime

from openpyxl import Workbook


class AuditExcelExporter:
    """
    Export audit logs to Excel.
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

        filename = datetime.now().strftime("%Y%m%d_%H%M%S") + "_audit_logs.xlsx"

        filepath = os.path.join(
            directory,
            filename,
        )

        workbook = Workbook()

        sheet = workbook.active

        if sheet is None:
            raise RuntimeError("Failed to create worksheet")

        sheet.title = "Audit Logs"

        sheet.append(
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
            sheet.append(
                [
                    log.id,
                    log.user_id,
                    log.action,
                    log.resource,
                    log.description,
                    log.ip_address,
                    str(log.created_at),
                ]
            )

        workbook.save(filepath)

        return filepath
