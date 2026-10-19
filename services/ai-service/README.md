# AI service model configuration

`YOLO_MODEL` selects the Ultralytics model path. The service's current default
is the lightweight checkpoint packaged with this service. For a locally supplied
YOLO11s checkpoint:

1. Put `yolo11s.pt` in the repository-root `models/` directory.
2. Set `YOLO_MODEL=/models/yolo11s.pt` in the root `.env`.
3. Start the AI service with Docker Compose; the model directory is mounted
   read-only at `/models`.

Keep model binaries out of Git. The detector reports object classes and
confidence; it does not itself identify a person or confirm an activity.
