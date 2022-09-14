import os
import abc
import asyncio
import json
from json.decoder import JSONDecodeError
import typing

import base64           # Added by Haider Al-Lawati for debugging
from io import BytesIO  # Added by Haider Al-Lawati for debugging
from PIL import Image   # Added by Haider Al-Lawati for debugging

import aio_pika
import httpx
from loguru import logger

from frame_analyzer.detection.pytorch import PyTorchDetector
from frame_analyzer.detection.yolov5_detector import YOLOv5Detector
from frame_analyzer.schemas.frame import RawFrame, AnalyzedFrame
from frame_analyzer.utils import image_util, persist_util, privacy_util


class AbstractRabbitMQWorker(abc.ABC):
    """
    Abstract class that defines a basic skeleton to derive RabbitMQ worker classes from

    Inherit from this class, and implement the on_message method to start processing
    messages from RabbitMQ

    Usage:

    # Initialize the worker with the queue is should consume from:
    worker = MyDerivedWorker(
        weights_location="../../weights/garb_weights.pt",
        in_exchange_name="raw_frames",
        in_queue_name="incoming_frames",
        in_routing_key="frame",
        out_exchange_name="analysed_frames",
        out_routing_key="frame",
        output_location="../../output"
    )

    # Initialize the event loop:
    import asyncio
    loop = asyncio.get_event_loop()

    # Supply your connection parameters:
    worker.connect("host", "username", "password", 5672)

    # Prepare to start processing messages:
    loop.create_task(worker.start())

    # Start the loop:
    loop.run_forever()
    """

    def __init__(
            self,
            in_exchange_name: str = None,
            in_queue_name: str = None,
            in_routing_key: str = None,
            out_exchange_name: str = None,
            out_routing_key: str = None,
    ):
        self.loop: typing.Optional[asyncio.base_events.BaseEventLoop] = None

        # Connection info
        self.host = None
        self.port = None

        # RabbitMQ connection
        self.connection: aio_pika.Connection = None
        self.channel: aio_pika.Channel = None

        # RabbitMQ incoming
        self.in_exchange_name = in_exchange_name
        self.in_exchange: aio_pika.Exchange = None
        self.in_queue_name = in_queue_name
        self.in_queue: aio_pika.Queue = None
        self.in_routing_key = in_routing_key

        # RabbitMQ outgoing
        self.out_exchange_name = out_exchange_name
        self.out_exchange: aio_pika.Exchange = None
        self.out_routing_key = out_routing_key

    async def _get_channel(self) -> aio_pika.RobustChannel:
        """Gets or opens a channel on the RabbitMQ host"""
        logger.info(f"Opening channel on {self.host}:{self.port}...")
        channel = await self.connection.channel()
        logger.info(f"Opened channel on {self.host}:{self.port}!")
        return channel

    async def _get_connection(
            self, host: str, username: str, password: str, port: int
    ) -> aio_pika.RobustConnection:
        """Gets a connection to the RabbitMQ host"""
        self.loop = asyncio.get_running_loop()
        connection_string = f"amqp://{username}:{password}@{host}:{port}"

        logger.info(f"Connecting to host {host}:{port}...")
        connection = await aio_pika.connect_robust(connection_string, loop=self.loop)
        logger.info(f"Connected to host {host}:{port}!")

        self.host = host
        self.port = port

        return connection

    async def _get_exchange(self, name) -> aio_pika.Exchange:
        """Connects to existing exchange on the RabbitMQ host"""
        logger.info(
            f"Connecting to exchange \"{name}\" on {self.host}:{self.port}..."
        )
        exchange = await self.channel.get_exchange(name)
        logger.info(
            f"Connected to exchange \"{name}\" on {self.host}:{self.port}!"
        )
        return exchange

    async def _get_queue(self) -> aio_pika.RobustQueue:
        """Connects to or creates a queue on the RabbitMQ host"""
        logger.info(
            f"Connecting to queue \"{self.in_queue_name}\" on {self.host}:{self.port}..."
        )
        queue: aio_pika.Queue = await self.channel.declare_queue(self.in_queue_name)
        logger.info(
            f"Connected to queue \"{self.in_queue_name}\" on {self.host}:{self.port}!"
        )
        return queue

    async def _bind_queue_exchange(self) -> None:
        """Binding queue to exchange on the RabbitMQ host"""
        logger.info(
            f"Binding queue \"{self.in_queue_name}\" to exchange \"{self.in_exchange}\"..."
        )
        await self.in_queue.bind(self.in_exchange, self.in_routing_key)
        logger.info(
            f"Bound queue \"{self.in_queue_name}\" to exchange \"{self.in_exchange}\"..."
        )

    async def _connect(self):
        raise ConnectionError("Call Worker.connect() first to connect")

    def connect(
            self, host: str, username: str, password: str, port: int = 5672
    ) -> None:
        """Obtain a connection to a RabbitMQ host and channel
        and setup queue and exchange for incoming traffic if `self.in_exchange_name` is set
        and/or connect to exchange for outgoing traffic if `self.out_exchange_name` is set
        """

        async def inner() -> None:
            self.connection = await self._get_connection(host, username, password, port)
            self.channel = await self._get_channel()

            if self.in_exchange_name:
                self.in_exchange = await self._get_exchange(self.in_exchange_name)
                self.in_queue = await self._get_queue()
                await self._bind_queue_exchange()
            if self.out_exchange_name:
                self.out_exchange = await self._get_exchange(self.out_exchange_name)

        self._connect = inner

    async def send_message(
            self, message: aio_pika.Message, *args, **kwargs
    ) -> None:
        """Sends message to outgoing exchange if it's set up 

        Args:
            message (aio_pika.Message): Message to be sent
        """
        if not self.out_exchange_name:
            logger.error("Set `out_exchange_name` in constructor in order to send messages")
            return
        if not self.out_exchange:
            await self._connect()
        await self.out_exchange.publish(
            message=message,
            routing_key=self.out_routing_key
        )
        logger.info(f"Message sent to exchange '{self.out_exchange_name}'")

    @abc.abstractmethod
    async def on_message(
            self, message: aio_pika.IncomingMessage, *args, **kwargs
    ) -> None:
        """
        Abstract method where any logic to handle incoming messages must be defined
        """
        pass

    async def start_consuming(self, no_ack=True) -> None:
        """Start consuming and processing messages"""
        if not self.in_queue:
            await self._connect()
        logger.info(
            f"Ready to start processing messages from queue {self.in_queue_name} "
            f"on host {self.host}:{self.port}..."
        )
        await self.in_queue.consume(self.on_message, no_ack=no_ack)


class EchoWorker(AbstractRabbitMQWorker):
    async def on_message(
            self, message: aio_pika.IncomingMessage, *args, **kwargs
    ) -> None:
        logger.info(f"Received message {message}")
        logger.info(message.body)


class RabbitMQWorker(AbstractRabbitMQWorker):
    def __init__(
            self, weights_location,
            savewith, includepriv, savewithout, blur, bbox,
            in_exchange_name, in_queue_name, in_routing_key,
            out_exchange_name=None, out_routing_key=None,
            output_location="output"
    ):
        self.yolov5_detector = YOLOv5Detector(weights_location)
        #self.pytorch_detector = PyTorchDetector(weights_location)
            #"weights/garb_weights.pt"
        #    "weights/resnet_18_multilabel_weighted_SGD.pt"
            # "weights/tut5-model_large_garbage_set_pretrained_448_img_size_resnet_152.pt"
        #)
        self.output_location = output_location
        self.savewith = savewith
        self.includepriv = includepriv
        self.savewithout = savewithout
        self.blur = blur
        self.bbox = bbox

        super().__init__(
            in_exchange_name=in_exchange_name,
            in_queue_name=in_queue_name,
            in_routing_key=in_routing_key,
            out_exchange_name=out_exchange_name,
            out_routing_key=out_routing_key
        )

    async def on_message(
            self, message: aio_pika.IncomingMessage, *args, **kwargs
    ) -> None:
        logger.info("Received message. Processing...")
        try:
            frame_data = json.loads(message.body.decode("utf-8"))
        except JSONDecodeError as e:
            logger.error(f"Message not JSON decodable: {message.body}")
            return

        raw_frame = RawFrame(**frame_data)
        analyzed_frame: AnalyzedFrame = self.yolov5_detector.detect(raw_frame=raw_frame)
        image_size = image_util.get_image_size(analyzed_frame.img)
        analyzed_frame.img_meta = {
            'width': image_size[0],
            'height': image_size[1],
            'file_hostname': os.uname()[1]
        }

        if analyzed_frame.detected_objects:
            analyzed_frame.blurred_image = image_util.blur_privacy_objects(
                analyzed_frame.img,
                analyzed_frame.detected_objects,
            )

            logger.info(f"Detected objects: {analyzed_frame.object_count}")
            #logger.info(f"Performing classification")
            #analyzed_frame = self.pytorch_detector.detect(analyzed_frame)
            #logger.info(f"Predicted categories present in image: {analyzed_frame.classification}")

            '''
            [Haider Al-Lawati]: This part must be updated with relevant information
            or url related to the client. It is currently connected to a url that 
            is managed and maintained by Municipality of Amsterdam. Be'ah has to 
            have its own similar version. The details of what this website does is
            not too clear as the main part of the website is not accessible except
            by the employees of the Municipality.
            
            # Post to SIA
            try:
                async with httpx.AsyncClient() as client:
                    logger.info(analyzed_frame.classification)
                    logger.info(str(analyzed_frame.classification))
                    response = await client.post(
                        "https://acc.api.data.amsterdam.nl/signals/v1/public/signals/",
                        json=analyzed_frame.to_signal(),
                    )
                    logger.info(response.content)

            except Exception as e:
                logger.error(e)
            '''
        await self.push_result(analyzed_frame)

        ###################
        # Save image logic:
        # When no objects detected and `savewithout` is off
        if bool(analyzed_frame.detected_objects) is False and self.savewithout is False:
            return
        
        # When no objects detected but `savewithout` is on 
        if bool(analyzed_frame.detected_objects) is False and self.savewithout is True:
            logger.info("Saving frame since `savewithout` is switched on")
            filename: str = persist_util.create_file_name(
                analyzed_frame.lat_lng,
                analyzed_frame.taken_at,
            )
            # Added by Haider for debugging [Working]
            #logger.info("showing the images before saving to disk")
            #output_image2 = analyzed_frame.img
            #img2 = Image.open(BytesIO(base64.b64decode(output_image2)))
            #img2.show()

            persist_util.save_to_disk(
                org_img=analyzed_frame.img,
                file_name=filename,
                o_location=f"{self.output_location}/no_objects",
            )
            return

        # When objects are detected but `savewith` is off
        if bool(analyzed_frame.detected_objects) is True and self.savewith is False:
            logger.info("Not saving frame since `savewith` is switched off")
            return

        # When objects are detected but `savewith` is on
        if bool(analyzed_frame.detected_objects) is True and self.savewith is True:
            
            # When there are only privacy objects and `includepriv` is off
            if privacy_util.not_only_privacy_objects(analyzed_frame.object_count) is False and self.includepriv is False:
                logger.info("Not storing frame, since only privacy objects are detected")
                return
            
            org_img = analyzed_frame.img
            edit_img = analyzed_frame.img

            # When blurring, override original image
            if self.blur:
                org_img: str = image_util.blur_privacy_objects(
                    org_img,
                    analyzed_frame.detected_objects,
                )

            # When bboxing, draw on separate image
            if self.bbox:
                edit_img: str = image_util.draw_bounding_boxes(
                    org_img,
                    analyzed_frame.detected_objects,
                    include_privacy_objects=True,
                )

            filename: str = persist_util.create_file_name(
                analyzed_frame.lat_lng,
                analyzed_frame.taken_at,
            )

            frame_date = analyzed_frame.taken_at.strftime("%Y-%m-%d")
            sub_location = f"{frame_date}/{analyzed_frame.stream_id}"
            persist_util.save_to_disk(
                org_img=org_img,
                edit_img=edit_img,
                file_name=filename,
                bbox=self.bbox,
                blur=self.blur,
                o_location=self.output_location,
                sub_location=sub_location,
            )

    async def push_result(self, frame: AnalyzedFrame) -> None:
        #frame.img = None
        result_body = frame.json().encode("utf8")
        result_message = aio_pika.Message(result_body)
        await self.send_message(result_message)


if __name__ == "__main__":
    import sys

    sys.path.insert(0, '../../yolov5')

    w = RabbitMQWorker(
        weights_location="../../weights/garb_weights.pt",
        output_location="../../output",
        in_exchange_name="raw_frames",
        in_queue_name="incoming_frames",
        in_routing_key="frame",
        out_exchange_name="analysed_frames",
        out_routing_key="frame",
    )
    w.connect("localhost", "odk", "development")

    loop = asyncio.get_event_loop()
    loop.create_task(w.start_consuming())
    loop.run_forever()
