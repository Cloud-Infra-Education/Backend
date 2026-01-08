# Backend/main.py (최상위 main)
from fastapi import FastAPI
from users.main import router as user_router
from videos.main import router as video_router

app = FastAPI()

# 두 마을(Prefix)을 모두 연결해줘요
app.include_router(user_router)
app.include_router(video_router)


# Backend/main.py
from users.database import init_db
import asyncio

