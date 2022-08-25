from datetime import datetime
import io
import sys
import base64
from typing import Any, List, Dict

import torch
from loguru import logger
import imageio
import cv2
import numpy as np

# for running from `main,py` 
sys.path.append("yolov5")
# for running from current file
#sys.path.append("../../yolov5")

from utils.torch_utils import select_device
from utils.datasets import letterbox
from utils.general import non_max_suppression, scale_coords

#sys.path.append("../..")

from frame_analyzer.schemas.frame import BaseFrame, AnalyzedFrame, ImgFrame


class YOLOv5Detector:
    """
    Utilizing Ultralytics YOLOv5 for detecting objects on frames.
    - Requires trained model in the form of a weights file
    - Detects if CUDA compatible GPU can be used (faster), else uses CPU (slower)

    Usage:

    ```
    # Set location of weights file (= model = pickle)
    weights_location = "../../weights/garb_weights.pt"

    # Initialize detector class 
    detector = YOLOv5Detector(weights_location)

    # Read image from disk
    with open("../../images/garbage1.jpg", "rb") as f:
        # Translate image to base64
        base64_img = base64.b64encode(f.read()).decode("utf-8")

        # Retrieve detection results
        result = detector.detect(base64_img)
    ```
    """

    def __init__(self, weights_location: str):
        self.device = select_device()
        logger.info(f"Using device: {self.device}")

        model_loaded = torch.load(weights_location, map_location=self.device)
        self.model = model_loaded['model'].float().eval()

        # Setting default values
        self.conf_thres = 0.3
        self.iou_thres = 0.5
        self.agnostic_nms = True
        self.augment = False
        self.img_size = 640

        logger.info("YOLOv5Detector initialized")

    def _create_output_json(self, bbox: List, classes: List) -> Dict[str, Any]:
        c1, c2 = (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3]))

        label = classes[int(bbox[5])]
        confidence = int(float(bbox[4]) * 100)

        return {
            'detected_object_type': label,
            'confidence': confidence,
            'bbox': {
                'coordinate1': c1,
                'coordinate2': c2
            }
        }

        # TODO: consider transform dict to pydantic class
        # bbox = BoundingBox(
        #     coordinate1=c1,
        #     coordinate2=c2
        # )

        # return DetectedObject(
        #     detected_object_type=label,
        #     confidence=confidence,
        #     bbox=bbox
        # )

    def detect(self, base64_img: str = None, raw_frame: BaseFrame = None) -> AnalyzedFrame:
        if not raw_frame:
            raw_frame = ImgFrame(
                img=base64_img
            )
        return self._detect(raw_frame)

    def _detect(self, raw_frame: BaseFrame) -> AnalyzedFrame:
        """Core to this entire application, this function detects objects on a base64 image.
        It borrows some code from yolov5 to achieve this.

        Args:
            raw_frame (RawFrame): An object that contains the base64 image

        Returns:
            AnalyzedFrame: A combination of the original frame plus its meta data,
            together with the detected objects in the form of a count and bounding boxes.
            Finally it adds meta data about time taken and information about the model used.
        """
        # Start timer
        start_time = datetime.now()

        # Remove `data:image/jpeg;base64,` from string
        if raw_frame.img.find(',') > -1:
            raw_frame.img = raw_frame.img.split(',')[1]

        # Convert image
        original_img = imageio.imread(io.BytesIO(base64.b64decode(raw_frame.img)))
        img = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)

        # Padded resize
        img = letterbox(img, new_shape=self.img_size)[0]

        # Convert
        img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB, to 3x416x416
        img = np.ascontiguousarray(img)

        img = torch.from_numpy(img).to(self.device)
        img = img.float()  # uint8 to fp16/32
        img /= 255.0  # 0 - 255 to 0.0 - 1.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)

        # Inference
        pred = self.model(img, augment=self.augment)[0]

        # Apply NMS
        pred = non_max_suppression(pred, self.conf_thres, self.iou_thres, classes=False, agnostic=self.agnostic_nms)[0]

        # Create bounding boxes
        detected_objects = []

        classes = self.model.module.names if hasattr(
            self.model, 'module') else self.model.names

        if pred is not None:
            # Scale coordinates
            pred[:, :4] = scale_coords(img.shape[2:], pred[:, :4], original_img.shape).round()
            for i, det in enumerate(pred):
                detected_objects.append(self._create_output_json(det, classes))

        # Count objects
        counts = {x: 0 for x in classes}
        counts["total"] = 0
        for box in detected_objects:
            counts[box['detected_object_type']] += 1
            counts["total"] +=1

        # End timer
        end_time = datetime.now()
        time_taken = (end_time - start_time).total_seconds()

        # Build return object
        result = AnalyzedFrame(**raw_frame.dict())
        result.detected_objects = detected_objects
        result.object_count = counts
        result.analyser_meta = {
            'ml_start_at': start_time,
            'ml_done_at': end_time,
            'ml_time_taken': time_taken,
            'model_name': "todo",
            'model_version': "todo",
        }

        return result


if __name__ == "__main__":
    weights_location = "../../weights/garb_weights.pt"
    detector = YOLOv5Detector(weights_location)

    with open("../../images/garbage.jpg", "rb") as f:
        base64_img = base64.b64encode(f.read()).decode("utf-8")
        result = detector.detect(base64_img)
        print(result.detected_objects)
        print(result.object_count)
