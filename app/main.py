import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.database import Base, engine
from app.core.scheduler import start_scheduler, stop_scheduler
from app.controllers import alerts, pages, rates, reports

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Dollar Tracker",
    description=(
        "Tracks Argentine dollar exchange rates automatically. "
        "Stores history, fires email alerts on threshold breaches, "
        "and sends periodic reports."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

for router in [pages.router, rates.router, alerts.router, reports.router]:
    app.include_router(router)
