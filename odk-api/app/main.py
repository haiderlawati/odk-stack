import time

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.core.config import PROJECT_NAME, DEBUG, VERSION, ALLOWED_HOSTS
from app.api.routes import router
from app.core.events import create_start_app_handler

# First things first, set timezone!
# Timezone is set to timezone specified in TZ environment variable
# https://docs.python.org/3/library/time.html#time.tzset
time.tzset()

app = FastAPI(title=PROJECT_NAME, debug=DEBUG, version=VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_HOSTS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_event_handler("startup", create_start_app_handler())


app.include_router(router)
