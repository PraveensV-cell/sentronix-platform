from dataclasses import dataclass


@dataclass
class Detection:
    label: str

    confidence: float

    x1: int
    y1: int

    x2: int
    y2: int
