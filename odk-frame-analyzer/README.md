
# Frame analyzer using PyTorch and YoloV5

For background information on the origin of this product, see [this](https://medium.com/maarten-sukel/garbage-object-detection-using-pytorch-and-yolov3-d6c4e0424a10) medium post.

All train and detection code comes directly from the [Yolov5 project](https://github.com/ultralytics/yolov5).

## Getting started

### Requirements

- Docker (docker-compose)
- Python 3 (python-venv, or other venv tool)
- [CUDA toolkit](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/) (optional for faster object detection, when you have a NVIDIA GPU)
- A trained model (you can find a model trained on garbage [here](https://drive.google.com/file/d/11s4WDwQkWdWpCfB_HTvQtRezZ3Xy4zUz/view?usp=sharing))

### Setup & installation

1. Clone repository with pull submodules:
```
$ git clone https://gitlab.com/odk/odk-frame-analyzer.git
$ cd odk-frame-analyzer
$ git submodule update --init --recursive
```

2. Setup Python venv & install packages:
```
$ python3 -m venv
$ source venv/bin/activate
$ (venv) pip install -r requirements.txt
```

3. Download garbage weights file:
```
$ cat weights/weights_drive_link.txt
```
Follow link and download the `*.pt` file into `weights` folder.

### CLI

**The easiest way to start experimenting is by using the CLI.**

Start of by getting familiar with the different arguments:
```
$ (venv) python cli.py --help
```

Example call:
```
$ (venv) python cli.py -i images/garbage.jpg --bbox --save
```

### Worker

The main responsibility in production is consuming frames from a queue.

Start by spinning up a local RabbitMQ instance using docker-compose:
```
$ cd dockerfiles
$ docker-compose up -d
```

Again, get familiar with the different arguments:
```
$ (venv) python start_worker.py --help
```

Start listining to a queue with a worker:
```
$ (venv) python start_worker.py -w weights/garb_weights.pt -ie raw_frames -iq incoming_frames -ir frame -oe analysed_frames -or frame -u odk -p development --savewithout --savewith --blur --bbox
```

To test the worker you can put a frame on the queue:
```
$ (venv) python produce_frame.py
```

## Hardware

Currently we are making the move to cloud computing, using Kubernetes. Previously we used custom build PCs for real-time inference of incoming frames.  

We build to PCs with the following components:
* Case: Cooler Master Elite 130 (Mini-ITX case)
* Board: Asus Prime A320I-K/CSM (Mini-ITX motherboard, AM4 Socket)
* CPU: AMD Ryzen 7 2700X (AM4)
* CPU fan: Xilence XC040 (Note: space for a fan is limited due to case)
* RAM: Corsair Vengeance LPX CMK16GX4M1D3000 (1 x 16GB & 3.000MT/s, 2 RAM slots availible (32GB is max))
* GPU: Gigabyte GeForce RTX 2070 Super Gaming OC 3X 8G (analyzes one frame in under 0.07 seconds!)
* Storage: Kingston A400 240GB (for running OS)
* PSU: be quiet! Pure Power 11 500W CM (80 Plus Gold)
