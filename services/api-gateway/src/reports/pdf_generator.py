import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Spacer
from reportlab.platypus import Table
from reportlab.platypus import TableStyle


class PDFGenerator:
    """
    Generates PDF reports.
    """

    def __init__(self):

        self.styles = getSampleStyleSheet()

    def generate_detection_report(
        self,
        detections,
        output_path: str,
    ):
        """
        Generate PDF report for detections.
        """

        os.makedirs(
            os.path.dirname(output_path),
            exist_ok=True,
        )

        document = SimpleDocTemplate(output_path)

        elements = []

        elements.append(
            Paragraph(
                "SENTRONIX Detection Report",
                self.styles["Title"],
            )
        )

        elements.append(Spacer(1, 20))

        elements.append(
            Paragraph(
                f"Generated : {datetime.now()}",
                self.styles["Normal"],
            )
        )

        elements.append(Spacer(1, 20))

        table_data = [
            [
                "ID",
                "Camera",
                "Object",
                "Confidence",
                "Time",
            ]
        ]

        for detection in detections:
            table_data.append(
                [
                    str(detection.id),
                    str(detection.camera_id),
                    detection.label,
                    f"{detection.confidence:.2f}",
                    str(detection.detected_at),
                ]
            )

        table = Table(table_data)

        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ]
            )
        )

        elements.append(table)

        document.build(elements)

        return output_path

    def generate_alert_report(
        self,
        alerts,
        output_path: str,
    ):
        """
        Generate PDF report for alerts.
        """

        os.makedirs(
            os.path.dirname(output_path),
            exist_ok=True,
        )

        document = SimpleDocTemplate(output_path)

        elements = []

        elements.append(
            Paragraph(
                "SENTRONIX Alert Report",
                self.styles["Title"],
            )
        )

        elements.append(Spacer(1, 20))

        elements.append(
            Paragraph(
                f"Generated : {datetime.now()}",
                self.styles["Normal"],
            )
        )

        elements.append(Spacer(1, 20))

        table_data = [
            [
                "ID",
                "Camera",
                "Severity",
                "Status",
                "Created",
            ]
        ]

        for alert in alerts:
            table_data.append(
                [
                    str(alert.id),
                    str(alert.camera_id),
                    alert.severity,
                    alert.status,
                    str(alert.created_at),
                ]
            )

        table = Table(table_data)

        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.red),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                ]
            )
        )

        elements.append(table)

        document.build(elements)

        return output_path

    def generate_recording_report(
        self,
        recordings,
        output_path: str,
    ):
        """
        Generate PDF report for recordings.
        """

        os.makedirs(
            os.path.dirname(output_path),
            exist_ok=True,
        )

        document = SimpleDocTemplate(output_path)

        elements = []

        elements.append(
            Paragraph(
                "SENTRONIX Recording Report",
                self.styles["Title"],
            )
        )

        elements.append(Spacer(1, 20))

        elements.append(
            Paragraph(
                f"Generated : {datetime.now()}",
                self.styles["Normal"],
            )
        )

        elements.append(Spacer(1, 20))

        table_data = [
            [
                "ID",
                "Camera",
                "File",
                "Duration",
                "Size (MB)",
            ]
        ]

        for recording in recordings:
            table_data.append(
                [
                    str(recording.id),
                    str(recording.camera_id),
                    recording.file_name,
                    f"{recording.duration:.2f}",
                    f"{recording.size:.2f}",
                ]
            )

        table = Table(table_data)

        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.green),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ]
            )
        )

        elements.append(table)

        document.build(elements)

        return output_path
