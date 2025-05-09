from fastapi import FastAPI
from contextlib import asynccontextmanager
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from pipeline.truck_loader.pipeline import start_truck_loader_thread
from config.db import connect_db
from routes import routes

@asynccontextmanager
async def lifespan(app: FastAPI):
    connect_db()
    start_truck_loader_thread()
    yield
    print("Shutting down pipeline...")

app = FastAPI(lifespan=lifespan)
app.include_router(routes.router)