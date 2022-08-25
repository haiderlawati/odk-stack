# ODK frame analyzer updated

**THE CONTENT OF THIS FILE IS MOST LIKELY OUTDATED!**

This documentation serves as background for developers, which decisions are made during development and how the design generally looks like. In this updated version of the frame analyzer the different layers of the application will be more clearly seperated.

## Design

### Detection

The core of the application handles the detection of objects on a given image. Most code is based on previous implementations of YOLO in Python, therefor some functions from the [YOLOv5](https://github.com/ultralytics/yolov5) project are imported. Detection is responsible for:

- Detecting the available device, i.e. CPU or CUDA supported GPU
- Loading in the weights model file (e.g. `weights.pt`)
- Taking in a base64 formatted image, e.g.:

```
iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=
```

- Detecting objects (based on loaded model)
- Creating bounding boxes for objects
- Creating list of objects counts
- Calculating time taken
- Returning output, `DetectionResult` model:
```json
{
    "base64_img": "iVBORw0KGgoAAAA...",
    "detected_objects": [{}, ...],
    "counts": {"type": 1, ...},
    "ml_start_at": "datetime",
    "ml_done_at": "datetime",
    "ml_time_taken  ": "datetime",
    "model_name": "garbage-amsterdam",
    "model_version": "YYYY.MM.DD",
}
```

### Utils

- Returning image size, based on base64 formatted image
- Blurring privacy sensitive bounding boxes, based on `DetectionResult` object, returns base64
- Add bounding boxes on image, returns base64
- Save image files to disk
  - Add `_blur` or `_bbox` to file name when image is blurred or has bounding boxes?

### CLI

- Importing image file(s) from local directory
- Call detection logic with these images
- Collect `DetectionResult` objects and
    - output in JSON formatted text file or
    - send to outgoing analysed frame RMQ connection
- Output images to disk, including bounding boxes and/or blurred

### RMQ

- Establish robust connection with RMQ server
- Create a queue and bind it to the "raw frame"-exchange (ODK API should declare exchange)

`RawFrame` model:
```json
{
    "img": "",
    "etc": "more_meta_data"
}
```

- Call detection logic incoming messages

Next to a base64 image, these messages include meta data from the ODK app and/or api. This information must be preserved.

- Collect results from detection logic and combine it again with `IncomingFrame` data
- Send combined message to outgoing analysed frame exchange/queue

`AnalyzedFrameData` model:
```json
{
    "detect_data": "more_meta_data"
}
```

### Saving frames

There are different options and combinations when it comes to saving frames. This flow is independent from where you would want to store the frames. Currently (07-03-2021) the frames are stored on disk. In the near future frames will be stored on a cloud service.

These are the most likely scenarios when it comes to saving frames:

1. Not saving any frames, the detected objects will be saved as text data but the frames are not persisted anywhere.
2. Storing frames with detected objects, only when objects (but not just privacy 'objects' like faces and license plates!) are detected a frame is persisted.
3. Stored frame with objects and without, 

### System Configuration and Stability

- Daemonize the code handling RMQ connections and object detection for increased stability

Supervisord is a good option for this. It's in this APT repositories for easy installation and integration with the OS. It's easy to set up auto(re)start for applications, with just a few lines of ini style configuration. As always, DigitalOcean provides a [useful guide](https://www.digitalocean.com/community/tutorials/how-to-install-and-manage-supervisor-on-ubuntu-and-debian-vps) to get started.

## Installation

### Poetry

Make sure to install your dependencies using the [Poetry](https://python-poetry.org/) dependency manager when setting up a worker node. Feel free to choose either Poetry or pip when working locally.

```
$ poetry install [--no-dev]
```

It is possible to generate `requirements.txt` files with Poetry:

```
$ poetry export -f requirements.txt --output requirements.txt
```

### Pip

Create a virtual environment in your preferred manner, activate it, and run
```
$ pip install -r requirements.txt
```

### Worker Node

Make sure you have `supervisor` installed:

```
$ apt install supervisor
```

Edit the `frame_analyzer_worker.conf` file to set the correct user, and the _absolute_ paths to
- The Python binary belonging to the environment where your dependencies are installed in,
- The project directory.

Create a symlink to the `frame_analyzer_worker.conf` file in `/etc/supevisor/conf.d/`, or make a copy there. Edit the paths to match those on the machine you are running on.

```
$ ln -s /full/path/to/frame_analyzer_worker.conf /etc/supervisor/conf.d/frame_analyzer_worker.conf
```

Next, run the following commands for your changes to take effect, and to start the newly daemonized program:

```
$ supervisorctl reread
$ supervisorctl update
```

### Docker

Make sure you have access to a RabbitMQ service, and its IP address. Then build and run the Frame Analyzer worker container, substituting `$QUEUE_NAME` for your desired queue name, `$RMQ_IP` for your RabbitMQ host's IP, `$RMQ_USER` for its username, and `$RMQ_PASS` for its matching password.

```
$ docker build -t oor/frame-analyzer-worker --target production .
$ docker run -ti oor/frame-analyzer-worker \
  --add-host rmq:$RMQ_IP \
  --volume output:/srv/frame_analyzer/output:rw \
  $QUEUE_NAME weights/garb_weights.pt rmq $RMQ_USER $RMQ_PASS 5672
```

Image files will be available in your Docker mount directory:
```
$ docker volume inspect frame_analyzer_output
```

## Testing

The included test suite is written in the `pytest` framework. Make sure to install the
development dependencies to be able to run the tests.

```
# pip
$ pip install -r requirements-dev.txt

# poetry
$ poetry install

$ ./runtests.sh
```

An HTML formatted coverage report will be generated in the `htmlcov` directory after a
successful test run.


## Background

### YoloV5

The most current version while creating this document is `v4.0` which can be checked out in using `git checkout tags/v4.0`.

BUT the current model is only working properly, this means e.g. that is blurs license plates, when sticking to a specific (outdated) commit of the `yolov5` repository: `git checkout 15a10609fe0e0f1fd3a03b11bf631a053cf001ca`.

- GitHub repo: https://github.com/ultralytics/yolov5
- Hacker News thread about relationship with other YOLO implementations: https://news.ycombinator.com/item?id=23478151

### RabbitMQ

Exchanges can be seen as as post offices, queues are the service the delivery service offers.

- https://www.rabbitmq.com/definitions.html
- https://stackoverflow.com/questions/59193789/unknown-variable-management-load-definitions-in-rabbitmq-rabbit-conf-file
- https://stackoverflow.com/questions/22992057/rabbitmq-declare-exchange-on-start#23010774