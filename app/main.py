from app.config import config
from pathlib import Path
import os

if Path(__file__).parent == Path(os.getcwd()):
    config.root_dir = "."

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.data.db import init_database
from app.routers import frontend, events, users, registrations


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    yield


app = FastAPI(lifespan=lifespan)

app.mount(
    "/static",
    StaticFiles(directory=config.root_dir / "static"),
    name="static"
)

app.include_router(frontend.router)
app.include_router(events.router)
app.include_router(users.router)
app.include_router(registrations.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True)