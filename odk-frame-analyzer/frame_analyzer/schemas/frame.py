from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel
from loguru import logger  # Haider added this for debugging

class BaseFrame(BaseModel):
    img: str = None
    taken_at: datetime = None
    lat_lng: Dict = None
    stream_id: str = None
    stream_meta: Dict = {}


class ImgFrame(BaseFrame):
    taken_at: datetime = datetime.now()
    #logger.info("Time now: ", datetime.now()) # Haider added this for debugging.
    lat_lng: Dict = {}
    stream_id: str = "none"


class RawFrame(BaseFrame):
    img: str
    taken_at: datetime
    lat_lng: Dict
    stream_id: str


class AnalyzedFrame(BaseFrame):
    taken_at: datetime
    lat_lng: Dict
    stream_id: str
    stream_meta: Dict = {}

    blurred_image: Optional[str] = None
    detected_objects: List = []
    object_count: Dict = {}
    # Breaks z/s naming convention to maintain compatibility with ODK-API, database
    analyser_meta: Dict = {}
    img_meta: Dict = {}
    classification: Dict = {}

    def to_signal(self):
        return {
            "text": str(self.classification),
            "location": {
                "geometrie": {
                    "type": "Point",
                    "coordinates": [self.lat_lng["lng"], self.lat_lng["lat"]]
                }
            },
            "category": {
                "sub_category": "/signals/v1/public/terms/categories/afval/sub_categories/handhaving-op-afval"
            },
            "reporter": {
                "email": "ODK@amsterdam.nl"
            },
            "incident_date_start": self.taken_at.strftime("%Y-%m-%d %H:%M")
        }
