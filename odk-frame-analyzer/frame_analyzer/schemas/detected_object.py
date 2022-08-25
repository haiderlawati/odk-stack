from typing import Tuple
from pydantic import BaseModel


class BoundingBox(BaseModel):
    coordinate1: Tuple[int, int]
    coordinate2: Tuple[int, int]


class DetectedObject(BaseModel):
    detected_object_type: str
    confidence: float
    bbox: BoundingBox