from fastapi import APIRouter

from app.api.endpoints import login, objects, frames, users

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(objects.router, tags=["objects"])
api_router.include_router(frames.router, tags=["frames", "stream", "websocket"])
api_router.include_router(users.router, tags=["users"])