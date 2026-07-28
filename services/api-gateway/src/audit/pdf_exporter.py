import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Table
from reportlab.platypus import TableStyle


class AuditPDFExporter:
    """
    Export audit logs to PDF.
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

        filename = datetime.now().strftime("%Y%m%d_%H%M%S") + "_audit_logs.pdf"

        filepath = os.path.join(
            directory,
            filename,
        )

        document = SimpleDocTemplate(
            filepath,
            pagesize=A4,
        )

        data = [
            [
                "ID",
                "User",
                "Action",
                "Resource",
                "Description",
                "IP",
                "Created At",
            ]
        ]

        for log in audit_logs:
            data.append(
                [
                    str(log.id),
                    str(log.user_id),
                    log.action,
                    log.resource,
                    log.description,
                    str(log.ip_address),
                    str(log.created_at),
                ]
            )

        table = Table(data)

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.darkblue,
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        1,
                        colors.black,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "ALIGN",
                        (0, 0),
                        (-1, -1),
                        "CENTER",
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, 0),
                        10,
                    ),
                    (
                        "BACKGROUND",
                        (0, 1),
                        (-1, -1),
                        colors.beige,
                    ),
                ]
            )
        )

        document.build(
            [
                table,
            ]
        )

        return filepath
