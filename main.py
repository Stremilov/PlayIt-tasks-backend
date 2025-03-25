import asyncio
import uvicorn
import logging

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.api.routers import all_routers
from src.core.utils.config import settings

logging.basicConfig(
    level=settings.logging.log_level_value,
    format=settings.logging.log_format
)


app = FastAPI(root_path="/playit/tasks")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in all_routers:
    app.include_router(router)


async def main():
    uvicorn.run(
        "main:app",
        host=settings.run.host,
        port=settings.run.port,
        reload=True)


if __name__ == "__main__":
    asyncio.run(main())
