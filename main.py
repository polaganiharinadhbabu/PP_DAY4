import asyncio
import logging
from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from routers.products import router as products_router
from routers.users import router as users_router


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.ready = True
    logger.info("Application started")

    yield

    app.state.ready = False
    logger.info("Application stopped")


app = FastAPI(
    title="Day 4 FastAPI Assignment",
    description="Async, Middleware, Dependencies and APIRouter",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Authorization", "Content-Type"]
)


@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    start = perf_counter()
    response = await call_next(request)

    elapsed = perf_counter() - start
    response.headers["X-Process-Time"] = f"{elapsed:.6f}"

    return response


app.include_router(products_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")


@app.get("/status", tags=["health"])
async def status():
    await asyncio.sleep(0.1)
    return {"status": "ready", "application_ready": app.state.ready}


def write_audit_log(message: str):
    logger.info("Audit event: %s", message)


@app.post("/orders", tags=["orders"])
def create_order(background_tasks: BackgroundTasks):
    background_tasks.add_task(write_audit_log, "Order created")
    return {"message": "Order accepted"}
