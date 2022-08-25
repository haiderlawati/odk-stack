from typing import Dict
from datetime import datetime
import base64
import os

def create_file_name(lat_lng: Dict, taken_at: datetime):
    """Creates time and location based file name for storing incoming frames
    E.g. a frame taken at 01-02-2021 at 13:37:77.1234 at location 52.3679876, 4.8973929,
    will become: 2020-02-01_13:37:77.1234_52.3679876_4.8973929

    Args:
        lat_lng (Dict): E.g.: {'lat': 52.3679876, 'lng': 4.8973929}
        taken_at (datetime): Datetime stamp of when frame was taken
    """
    timestamp_str = datetime.strftime(taken_at, "%Y-%m-%d_%H:%M:%S.%f")
    lat_lng_str = f"{lat_lng['lat']}_{lat_lng['lng']}"
    file_name = f"{timestamp_str}_{lat_lng_str}"

    return file_name


def save_to_disk(
        org_img: str, file_name: str,
        edit_img: str = None,
        blur=False, bbox=False,
        o_location: str = "output",
        sub_location: str = None,
        file_type = "jpg"
    ):
    """Store a base64 image on disk with specific name.

    Optionally extra information can be added, when image is blurred and/or has bounding boxes:
    - 2020-02-01_13:37:77.1234_52.3679876_4.8973929_blur.jpg
    - 2020-02-01_13:37:77.1234_52.3679876_4.8973929_bbox.jpg
    - 2020-02-01_13:37:77.1234_52.3679876_4.8973929_blur_bbox.jpg

    Args:
        base64_img (str): A base64 image string
        blur (bool, optional): For adding '_blur' to filename. Defaults to False.
        bbox (bool, optional): For adding '_bbox' to filename. Defaults to False.
        o_location (str, optional): Folder where image will be written to. Defaults to "output".
    """
    def write_image(img, folder, name, type):
        name_location = f"{folder}/{name}.{type}"
        img = base64.b64decode(img)
        with open(name_location, "wb") as file:
            file.write(img)

    # Build and create output location
    output_folder = o_location
    if sub_location:
        output_folder = f"{output_folder}/{sub_location}"
        #print(output_folder)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Write image(s)
    if blur:
        file_name = f"{file_name}_blur"
    write_image(org_img, output_folder, file_name, file_type)

    if bbox:
        file_name = f"{file_name}_bbox"
        write_image(edit_img, output_folder, file_name, file_type)
