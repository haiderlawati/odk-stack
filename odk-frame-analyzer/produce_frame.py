import asyncio
import base64
from datetime import datetime

import aio_pika

from frame_analyzer.rmq.worker import AbstractRabbitMQWorker
from frame_analyzer.schemas.frame import RawFrame


class RawFrameProducer(AbstractRabbitMQWorker):
    async def on_message(self, message: aio_pika.IncomingMessage, *args, **kwargs) -> None:
        pass

    async def send_message(self, *args, **kwargs) -> None:
        await super().send_message(*args, **kwargs)
        loop.stop()


def create_raw_frame():
    with open("images/garbage.jpg", "rb") as f:
        base64_img = base64.b64encode(f.read()).decode("utf-8")
        return RawFrame(
            img=base64_img,
            taken_at=datetime.now(),
            lat_lng={'lat': 1, 'lng': 2},
            stream_id="foobar",
            stream_meta={"user_type": "demo"}
        )


if __name__ == "__main__":
    producer = RawFrameProducer(
        out_exchange_name="raw_frames",
        out_routing_key="frame"
    )
    producer.connect("localhost", "odk", "development")

    loop = asyncio.get_event_loop()
    raw_frame = create_raw_frame()
    message = aio_pika.Message(raw_frame.json().encode("utf8"))
    loop.create_task(producer.send_message(message))
    loop.run_forever()
