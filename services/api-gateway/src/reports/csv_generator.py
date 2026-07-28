import os

import pandas as pd


class CSVGenerator:
    """
    Generates CSV reports.
    """

    def generate_detection_report(
        self,
        detections,
        output_path: str,
    ):
        """
        Export detections to CSV.
        """

        os.makedirs(
            os.path.dirname(output_path),
            exist_ok=True,
        )

        rows = []

        for detection in detections:
            rows.append(
                {
                    "ID": detection.id,
                    "Camera": detection.camera_id,
                    "Object": detection.label,
                    "Confidence": detection.confidence,
                    "X1": detection.x1,
                    "Y1": detection.y1,
                    "X2": detection.x2,
                    "Y2": detection.y2,
                    "Detected At": detection.detected_at,
                }
            )

        dataframe = pd.DataFrame(rows)

        dataframe.to_csv(
            output_path,
            index=False,
        )

        return output_path

    def generate_alert_report(
        self,
        alerts,
        output_path: str,
    ):
        """
        Export alerts to CSV.
        """

        os.makedirs(
            os.path.dirname(output_path),
            exist_ok=True,
        )

        rows = []

        for alert in alerts:
            rows.append(
                {
                    "ID": alert.id,
                    "Camera": alert.camera_id,
                    "Detection": alert.detection_id,
                    "Title": alert.title,
                    "Message": alert.message,
                    "Severity": alert.severity,
                    "Status": alert.status,
                    "Created At": alert.created_at,
                }
            )

        dataframe = pd.DataFrame(rows)

        dataframe.to_csv(
            output_path,
            index=False,
        )

        return output_path

    def generate_recording_report(
        self,
        recordings,
        output_path: str,
    ):
        """
        Export recordings to CSV.
        """

        os.makedirs(
            os.path.dirname(output_path),
            exist_ok=True,
        )

        rows = []

        for recording in recordings:
            rows.append(
                {
                    "ID": recording.id,
                    "Camera": recording.camera_id,
                    "File Name": recording.file_name,
                    "File Path": recording.file_path,
                    "Duration": recording.duration,
                    "Size (MB)": recording.size,
                    "Start Time": recording.start_time,
                    "End Time": recording.end_time,
                    "Created At": recording.created_at,
                }
            )

        dataframe = pd.DataFrame(rows)

        dataframe.to_csv(
            output_path,
            index=False,
        )

        return output_path
