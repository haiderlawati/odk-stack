import os
import argparse
import base64
from io import BytesIO
import csv
from typing import Tuple

from PIL import Image
from loguru import logger

from imageio import imread
import io

from frame_analyzer.utils.image_util import blur_privacy_objects, draw_bounding_boxes
from frame_analyzer.utils.persist_util import save_to_disk
from frame_analyzer.schemas.frame import AnalyzedFrame
from frame_analyzer.detection.yolov5_detector import YOLOv5Detector


DEFAULT_WEIGHTS_FILE = "./weights/garb_weights.pt"


def _handle_image(yolo: YOLOv5Detector, image_path: str, blur_on: bool, bbox_on: bool, save_on: bool, show_on: bool = False) -> Tuple[str, AnalyzedFrame]:
    with open(image_path, "rb") as f:
        basename = os.path.basename(image_path)
        filename, ext = os.path.splitext(basename)

        try:
            base64_img = base64.b64encode(f.read()).decode("utf-8")
            result: AnalyzedFrame = yolo.detect(base64_img=base64_img)
        except ValueError as e:
            logger.error(f"Could not process '{basename}': {e}")
            return None, None
        except TypeError as e:
            logger.error(f"Could not process '{basename}': {e}")
            return None, None
        
        output_image = result.img

        if blur_on:
            blurred_img = blur_privacy_objects(
                base64_img=output_image,
                detected_objects=result.detected_objects
            )
            print ('detected objects = ',result.detected_objects)
            output_image = blurred_img
        
        if bbox_on:
            bbox_img = draw_bounding_boxes(
                base64_img=output_image,
                detected_objects=result.detected_objects
            )
            output_image = bbox_img
        
        if save_on:
            save_to_disk(
                org_img=result.img,
                edit_img=output_image,
                file_name=filename,
                bbox=bbox_on,
                blur=blur_on
            )

        if show_on:
            img = Image.open(BytesIO(base64.b64decode(output_image)))
            img.show()
            # These are debugging statemenst by Haider Al-Lawati
            
            '''
            img = imread(BytesIO(base64.b64decode(base64_img)))
            width = img.shape[1]
            height = img.shape[0]
            print("width, height types are: ", width, height)
            '''
        logger.info(f"Processed results for '{basename}'")
        return basename, result

def _write_to_dict(_dict, filename, result: AnalyzedFrame):
    if filename and result:
        _dict.append({
            'filename': filename, 
            'detected_objects': str(result.detected_objects),
            'object_count': str(result.object_count)
        })


def _handle_input(image_path: str, weights_path: str, blur_on: bool, bbox_on: bool, save_on: bool):
    if not os.path.isfile(weights_path):
        logger.error("Weights file not found")
        return

    yolo = YOLOv5Detector(weights_path)    
    all_results = []

    if os.path.isfile(image_path):
        filename, result = _handle_image(yolo, image_path, blur_on, bbox_on, save_on, show_on=True)
        _write_to_dict(all_results, filename, result)
    elif os.path.isdir(image_path):
        for root, directories, files in os.walk(image_path):
            for name in files:
                single_image_path = os.path.join(root, name)
                filename, result = _handle_image(yolo, single_image_path, blur_on, bbox_on, save_on, show_on=False)
                _write_to_dict(all_results, filename, result)
    else:
        logger.error("Image path not found")
        return

    return all_results


def _create_results_output(results_dict):
    labels = ['filename', 'detected_objects', 'object_count']
    results_file = 'output/results.csv'

    with open(results_file, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=labels)
        writer.writeheader()
        for element in results_dict:
            writer.writerow(element)

    logger.info(f"Saved results to '{results_file}'")


def _cli():
    parser = argparse.ArgumentParser(
        description="Tool for detecting objects on images"
    )
    parser.add_argument("-i", "--images", dest="image_path",
                        help="Image(s) to be analyzed", required=True)
    parser.add_argument("-w", "--weights", dest="weights_path",
                        help="Location of weights file", default=DEFAULT_WEIGHTS_FILE)
    parser.add_argument("--blur", action="store_true", help="Blur output image")
    parser.add_argument("--bbox", action="store_true", help="Draw bounding boxes")
    parser.add_argument("--save", action="store_true", help="Save to disk")

    args = parser.parse_args()
    image_path = args.image_path
    weights_path = args.weights_path
    blur_on = args.blur
    bbox_on = args.bbox
    save_on = args.save

    results = _handle_input(image_path, weights_path, blur_on, bbox_on, save_on)
    _create_results_output(results)


if __name__ == "__main__":
    _cli()
