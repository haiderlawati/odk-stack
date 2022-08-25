import json
import typing
from unittest import mock

import aio_pika
import pytest

from frame_analyzer.rmq.worker import AbstractRabbitMQWorker, RabbitMQWorker
from frame_analyzer.schemas.frame import RawFrame


class DummyRabbitMQWorker(AbstractRabbitMQWorker):
    async def on_message(
            self, message: aio_pika.IncomingMessage, *args, **kwargs
    ) -> typing.Any:
        pass


@mock.patch("frame_analyzer.rmq.worker.aio_pika.connect_robust")
class TestAbstractRabbitMQWorker:
    def test_raises_when_instantiated(self, _) -> None:
        with pytest.raises(TypeError):
            AbstractRabbitMQWorker("test")

    @pytest.mark.asyncio
    async def test_sets_private_method_connect(self, connect_robust) -> None:
        worker = DummyRabbitMQWorker("test")
        worker.connect("test", "user", "password")
        await worker.start_consuming()

        connect_robust.assert_called_once_with(
            "amqp://user:password@test:5672",
            loop=worker.loop
        )

    @pytest.mark.asyncio
    async def test_opens_channel(self, _) -> None:
        worker = DummyRabbitMQWorker("test")
        worker.connect("test", "user", "password")
        await worker.start_consuming()

        worker.connection.channel.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_connects_to_queue(self, _) -> None:
        worker = DummyRabbitMQWorker("test")
        worker.connect("test", "user", "password")
        await worker.start_consuming()

        worker.channel.declare_queue.assert_called_once_with(worker.in_queue_name)


@mock.patch("frame_analyzer.rmq.worker.RabbitMQWorker.send_message")
@mock.patch("frame_analyzer.rmq.worker.aio_pika.connect_robust")
@mock.patch("frame_analyzer.rmq.worker.YOLOv5Detector")
@mock.patch("frame_analyzer.rmq.worker.image_util.blur_privacy_objects")
@mock.patch("frame_analyzer.rmq.worker.image_util.draw_bounding_boxes")
@mock.patch("frame_analyzer.rmq.worker.persist_util.create_file_name")
@mock.patch("frame_analyzer.rmq.worker.persist_util.save_to_disk")
@mock.patch("frame_analyzer.rmq.worker.RabbitMQWorker.push_result")
class TestRabbitMQWorker:
    # TODO: Write tests for the different parameter options

    message_body = {
        "img": "/9j/i/am/a/base64/encoded/image==",
        "taken_at": "2021-01-31 12:34:56",
        "lat_lng": {"lat": "52.367527", "lng": "4.901257"},
        "stream_id": "1",
        "stream_meta": {},
    }

    message = mock.Mock(body=json.dumps(message_body).encode("utf-8"))
    frame = RawFrame(**message_body)

    worker = None

    @pytest.mark.asyncio
    async def base_test(self):
        self.worker = RabbitMQWorker(
            weights_location="/path/to/weights",
            savewith=True,
            includepriv=True,
            savewithout=True,
            blur=True,
            bbox=True,
            in_exchange_name="in_ex",
            in_queue_name="in_q",
            in_routing_key="in_rk"
        )
        self.worker.connect("test", "user", "password")
        await self.worker.start_consuming()

    @pytest.mark.asyncio
    async def test_calls_detect(self, *args) -> None:
        await self.base_test()
        await self.worker.on_message(self.message)
        self.worker.yolov5_detector.detect.assert_called_once_with(raw_frame=self.frame)

    @pytest.mark.asyncio
    async def test_calls_blur_privacy_objects(
            self, _, __, ___, ____, blur_privacy_objects, *args
    ) -> None:
        await self.base_test()
        await self.worker.on_message(self.message)
        blur_privacy_objects.assert_called_once_with(
            self.worker.yolov5_detector.detect.return_value.img,
            self.worker.yolov5_detector.detect.return_value.detected_objects,
        )

    @pytest.mark.asyncio
    async def test_calls_draw_bounding_boxes(
            self, _, __, ___, draw_bounding_boxes, blur, *args
    ) -> None:
        await self.base_test()
        await self.worker.on_message(self.message)
        draw_bounding_boxes.assert_called_once_with(
            blur.return_value,
            self.worker.yolov5_detector.detect.return_value.detected_objects,
            include_privacy_objects=True,
        )

    @pytest.mark.asyncio
    async def test_calls_create_file_name(self, _, __, create_file_name, *args) -> None:
        await self.base_test()
        await self.worker.on_message(self.message)
        create_file_name.assert_called_once_with(
            self.worker.yolov5_detector.detect.return_value.lat_lng,
            self.worker.yolov5_detector.detect.return_value.taken_at,
        )

    @pytest.mark.asyncio
    async def test_calls_save_to_disk(self, _, save_to_disk, create_file_name, draw, blur, *args) -> None:
        await self.base_test()
        await self.worker.on_message(self.message)
        save_to_disk.assert_called_once_with(
            org_img=blur.return_value,
            edit_img=draw.return_value,
            file_name=create_file_name.return_value,
            bbox=self.worker.bbox,
            blur=self.worker.blur,
            o_location=self.worker.output_location,
            stream_id=self.worker.yolov5_detector.detect.return_value.stream_id,
        )

    # TODO: Decide whether a use case remains for the test below
    # @pytest.mark.asyncio
    # async def test_calls_detect_blur_draw_file_save_in_order(
    #         self, push_result, save_to_disk, create_file_name, draw_bounding_boxes, blur_privacy_objects, *args
    # ) -> None:
    #     await self.base_test()
    #
    #     manager = mock.Mock()
    #     manager.attach_mock(self.worker.yolov5_detector.detect, "detect")
    #     manager.attach_mock(blur_privacy_objects, "blur_privacy_objects")
    #     manager.attach_mock(draw_bounding_boxes, "draw_bounding_boxes")
    #     manager.attach_mock(create_file_name, "create_file_name")
    #     manager.attach_mock(save_to_disk, "save_to_disk")
    #     manager.attach_mock(push_result, "push_result")
    #
    #     await self.worker.on_message(self.message)
    #
    #     assert manager.mock_calls == [
    #         mock.call.detect(raw_frame=self.frame),
    #         mock.call.blur_privacy_objects(
    #             manager.detect.return_value.img,
    #             manager.detect.return_value.detected_objects,
    #         ),
    #         mock.call.draw_bounding_boxes(
    #             manager.blur_privacy_objects.return_value,
    #             manager.detect.return_value.detected_objects,
    #             include_privacy_objects=True,
    #         ),
    #         mock.call.create_file_name(
    #             manager.detect.return_value.lat_lng,
    #             manager.detect.return_value.taken_at,
    #         ),
    #         mock.call.save_to_disk(
    #             manager.draw_bounding_boxes.return_value,
    #             manager.create_file_name.return_value,
    #             bbox=True,
    #             blur=True,
    #             o_location=self.worker.output_location,
    #         ),
    #         mock.call.push_result(
    #             manager.detect.return_value
    #         )
    #     ]
