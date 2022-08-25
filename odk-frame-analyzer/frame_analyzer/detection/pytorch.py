import base64
import io
import sys

# for running from `main,py`
sys.path.append("yolov5")
# for running from current file
sys.path.append("../../yolov5")

import torch
import torch.nn as nn
import torchvision.models as models
from PIL import Image
from loguru import logger
from torchvision.transforms import transforms
from utils.torch_utils import select_device


class PyTorchDetector:
    categories = ['garbage', 'bulkywaste', 'garbagebag', 'cardboard', 'litter']
    prediction_threshold = 0.5
    size = 448

    def __init__(self, weights_location):
        self.device = select_device()
        self.image_loader = self.build_image_loader()
        self.weights_location = weights_location

        logger.info(f"Using device: {self.device}")
        self.model = self.load_model()

    def load_model(self):
        model = models.resnet18(pretrained=True)
        model.fc = nn.Sequential(nn.Linear(512, 5), nn.Sigmoid())
        #model.load_state_dict(torch.load(self.weights_location, map_location=self.device))

        if torch.cuda.is_available():
            model = model.cuda()

        model.eval()

        for param in model.parameters():
            param.requires_grad = True

        return model

    def build_image_loader(self):
        return transforms.Compose([
            transforms.Resize(self.size),
            transforms.CenterCrop(self.size),
            transforms.ToTensor(),
        ])

    def detect(self, analyzed_frame):
        image = analyzed_frame.blurred_image if analyzed_frame.blurred_image else analyzed_frame.img
        with torch.no_grad(), Image.open(io.BytesIO(base64.b64decode(image))) as img:
            img = self.image_loader(img).float()
            if torch.cuda.is_available():
                img = img.cuda()

            img = img.unsqueeze(0)
            prediction = self.model(img)
            prediction = prediction.squeeze()

        analyzed_frame.classification = dict(
            zip(self.categories, [p > self.prediction_threshold for p in prediction.tolist()]))
        return analyzed_frame
