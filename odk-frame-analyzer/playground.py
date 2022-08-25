"""
This file can be used for some general playing around with the code.
"""

from datetime import datetime
from io import BytesIO
import sys
import base64
import asyncio

from PIL import Image

from frame_analyzer.schemas.frame import RawFrame, AnalyzedFrame
from frame_analyzer.detection.yolov5_detector import YOLOv5Detector
from frame_analyzer.utils.image_util import get_image_size, blur_privacy_objects, draw_bounding_boxes
from frame_analyzer.utils.persist_util import save_to_disk
from frame_analyzer.rmq.worker import RabbitMQWorker

def worker():
    sys.path.insert(0, 'yolov5')

    w = RabbitMQWorker("q", "weights/garb_weights.pt")
    w.connect("localhost", "odk", "development")

    loop = asyncio.get_event_loop()
    loop.create_task(w.start())
    loop.run_forever()


def detect():
    sys.path.append("yolov5")
    weights_location = "weights/garb_weights.pt"
    yolo = YOLOv5Detector(weights_location)

    with open("images/license-plates.jpg", "rb") as f:
        base64_img = base64.b64encode(f.read()).decode("utf-8")
        raw_frame = RawFrame(
            img=base64_img,
            taken_at=datetime.now(),
            lat_lng={'lat': 33, 'lng': 44}
        )

        result: AnalyzedFrame = yolo.detect(raw_frame=raw_frame)
        # result: AnalysedFrame = yolo.detect(base64_img)

        print(result.object_count)
        print(get_image_size(result.img))

        blurred_img = blur_privacy_objects(
            result.img, result.detected_objects)

        img2 = Image.open(BytesIO(base64.b64decode(blurred_img)))
        # img2.show()

        bbox_img = draw_bounding_boxes(
            blurred_img, result.detected_objects,
            include_privacy_objects=True)

        img1 = Image.open(BytesIO(base64.b64decode(bbox_img)))
        img1.show()

        # save_to_disk(bbox_img, raw_frame.lat_lng, raw_frame.taken_at, bbox=True, blur=True)


if __name__ == "__main__":
    # worker()
    detect()
