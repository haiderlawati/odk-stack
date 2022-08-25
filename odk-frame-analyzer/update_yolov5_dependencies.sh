#/bin/bash
grep -v "#" yolov5/requirements.txt | xargs poetry add
