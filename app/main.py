from sqlmodel import Session, select 
from app.models.event import Event
from app.data.db import engine 
from app.config import config
from datetime import datetime
from app.models.user import User
from app.models.registration import Registration

from pathlib import Path
import os

if Path(__file__).parent == Path(os.getcwd()):
    config.root_dir = "."

from fastapi import FastAPI, HTTPException, Response, status

from app.routers import frontend, events, users, registrations
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.data.db import init_database


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