import io
import base64
from typing import Tuple, List, Dict

from imageio import imread
import cv2

from frame_analyzer.detection.yolov5_utils import plot_one_box

def get_image_size(base64_img: str) -> Tuple[str, str]:
    """Gets width and height of base64 image

    Args:
        base64_img (str): A base64 image

    Returns:
        Tuple[str, str]: First width, then height
    """
    img = imread(io.BytesIO(base64.b64decode(base64_img)))
    width = img.shape[1]
    height = img.shape[0]

    return (width, height)


def blur_privacy_objects(base64_img: str, detected_objects: List[Dict]) -> str:
    """Given a base64 image and a list of detected objects (as returned by `yolov5_detector.detect`)
    a new base64 image will be created where all the privacy objects are blurred with a black box.

    Args:
        base64_img (str): Base64 image corresponding to the coordinates of the detected objects
        detected_objects (List[Dict]): Detected objects corresponding to the base64 image

    Returns:
        str: An base64 image with, if present, blacked out privacy objects
    """
    img = imread(io.BytesIO(base64.b64decode(base64_img)))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    blur_color = (0, 0, 0)
    for i, obj in enumerate(detected_objects):
        if "privacy" in obj["detected_object_type"]:
            cv2.rectangle(
                img, obj["bbox"]["coordinate1"], obj["bbox"]["coordinate2"],
                blur_color, -1
            )

    retval, buffer = cv2.imencode(".jpg", img)
    b64_result = base64.b64encode(buffer)

    return b64_result


def draw_bounding_boxes(base64_img: str, detected_objects: List[Dict], include_privacy_objects = True) -> str:
    """Given a base64 image and a list of detected objects (as returned by `yolov5_detector.detect`)
    a new base64 image will be created with a colored outline of every detected object

    Args:
        base64_img (str): Base64 image corresponding to the coordinates of the detected objects
        detected_objects (List[Dict]): Detected objects corresponding to the base64 image
        include_privacy_objects (bool, optional): If True will also draw boxes for privacy objects.
        Can be set to false in combination with blurring an image. Defaults to True.

    Returns:
        str: An base64 image with the outline bounding boxes for every detected object 
    """
    img = imread(io.BytesIO(base64.b64decode(base64_img)))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    if include_privacy_objects == False:
        detected_objects = [obj for obj in detected_objects if "privacy" not in obj["detected_object_type"]]

    for i, obj in enumerate(detected_objects):
        conf = obj['confidence']
        bbox = obj['bbox']
        xyxy = [
            bbox['coordinate1'][0], bbox['coordinate1'][1],
            bbox['coordinate2'][0], bbox['coordinate2'][1]
        ]
        label = f"{obj['detected_object_type']} {conf/100}"
        plot_one_box(xyxy, img, label=label, line_thickness=1)

    retval, buffer = cv2.imencode(".jpg", img)
    b64_result = base64.b64encode(buffer)

    return b64_result
