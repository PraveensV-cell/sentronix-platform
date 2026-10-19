# Local model files

Place locally supplied model weights in this directory. For example,
`models/yolo11s.pt` can be selected with `YOLO_MODEL=/models/yolo11s.pt` in the
root `.env`. Docker Compose mounts this directory read-only at `/models`.

Model binaries are ignored by Git and must not be committed.
