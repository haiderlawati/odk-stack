import argparse
import asyncio
import sys
import aio_pika
from frame_analyzer.rmq.worker import RabbitMQWorker


parser = argparse.ArgumentParser(description="Start a Frame Analyzer worker")
# YOLOv5 arguments
parser.add_argument("-w", "--weights", dest="weights_location", type=str, default="weights/garb_weights.pt", help="Path to weights file")
# Persistment rules
parser.add_argument("--savewith", action="store_true", help="Save frames with detected objects (to disk)")
parser.add_argument("--includepriv", action="store_true", help="Also accept frames with just privacy objects")
parser.add_argument("--savewithout", action="store_true", help="Save frames without detected objects (to disk)")
parser.add_argument("--blur", action="store_true", help="Blur privacy objects on original image")
parser.add_argument("--bbox", action="store_true", help="Save a separate image with bounding boxes")
# Incoming traffic arguments
parser.add_argument("-ie", "--inexchange", dest="in_exchange_name", type=str, default="exchange_raw_frames",  help="RabbitMQ exchange where raw frames are posted")
parser.add_argument("-iq", "--inqueue", dest="in_queue_name", type=str, default="incoming_frames", help="RabbitMQ queue that is bound to exchange")
parser.add_argument("-ir", "--inkey", dest="in_routing_key", type=str, default="frame", help="RabbitMQ incoming routing key")
# Outgoing traffic arguments
parser.add_argument("-oe", "--outexchange", dest="out_exchange_name", type=str, default="exchange_analysed_frames", help="RabbitMQ exchange to send results to")
parser.add_argument("-or", "--outkey", dest="out_routing_key", type=str, default="frame", help="RabbitMQ outgoing routing key")
# Connection arguments
parser.add_argument("--host", dest="host", type=str, default="172.19.0.2", help="RabbitMQ host address")
parser.add_argument("--port", dest="port", type=int, default=5672, help="RabbitMQ port: 5672")
parser.add_argument("-u", "--username", dest="username", type=str, default="odk", help="RabbitMQ username")
parser.add_argument("-p", "--password", dest="password", type=str, default="development", help="RabbitMQ password")

args = parser.parse_args()


if __name__ == "__main__":
    from loguru import logger
    logger.info("Starting worker...")
    logger.info("Python version ...")
    print(sys.version)

    loop = asyncio.get_event_loop()
    w = RabbitMQWorker(
        weights_location=args.weights_location,
        savewith=args.savewith,
        includepriv=args.includepriv,
        savewithout=args.savewithout,
        blur=args.blur,
        bbox=args.bbox,
        in_exchange_name=args.in_exchange_name,
        in_queue_name=args.in_queue_name,
        in_routing_key=args.in_routing_key,
        out_exchange_name=args.out_exchange_name,
        out_routing_key=args.out_routing_key,
    )
    w.connect(args.host, args.username, args.password, args.port)

    loop.create_task(w.start_consuming())
    loop.run_forever()
