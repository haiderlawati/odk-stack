import asyncio
import os

from frame_analyzer.rmq.worker import RabbitMQWorker

if __name__ == "__main__":
    from loguru import logger
    logger.info("Starting worker...")

    host = os.environ.get("HOST", "rabbitmq.default.svc.cluster.local")
    username = os.environ.get("RMQ_USERNAME")
    password = os.environ.get("RMQ_PASSWORD")
    port = os.environ.get("PORT", 5672)

    weights_location = os.environ.get("WEIGHTS_LOCATION", "weights/garb_weights_l.pt")
    savewith = os.environ.get("SAVEWITH", True)
    includepriv = os.environ.get("INCLUDEPRIV", True)
    savewithout = os.environ.get("SAVEWITHOUT", True)
    blur = os.environ.get("BLUR", True)
    bbox = os.environ.get("BBOX", True)
    in_exchange_name = os.environ.get("IN_EXCHANGE", "exchange_raw_frames")
    in_queue_name = os.environ.get("IN_QUEUE", "queue_raw_frames")
    in_routing_key = os.environ.get("IN_ROUTING_KEY", "frame")
    out_exchange_name = os.environ.get("OUT_EXCHANGE", "exchange_analysed_frames")
    out_routing_key = os.environ.get("OUT_ROUTING_KEY", "frame")

    loop = asyncio.get_event_loop()
    w = RabbitMQWorker(
        weights_location=weights_location,
        savewith=savewith,
        includepriv=includepriv,
        savewithout=savewithout,
        blur=blur,
        bbox=bbox,
        in_exchange_name=in_exchange_name,
        in_queue_name=in_queue_name,
        in_routing_key=in_routing_key,
        out_exchange_name=out_exchange_name,
        out_routing_key=out_routing_key,
    )
    w.connect(host, username, password, port)

    loop.create_task(w.start_consuming())
    loop.run_forever()
