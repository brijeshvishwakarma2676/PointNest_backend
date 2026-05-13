import logging
import platform
import uvicorn
import multiprocessing
from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi import status

from app.api.v1.router import api_router
from app.config.database import Base, engine
from app.config.settings import settings
from app.core.exception_handlers import add_exception_handlers

from contextlib import asynccontextmanager

import os

# Configure logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
handlers = [logging.StreamHandler()]

# Vercel has a read-only filesystem, use /tmp for logs there
log_file = "/tmp/app.log" if os.environ.get("VERCEL") else "app.log"
handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=handlers,
    force=True
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("DB : ", settings.DATABASE_URL)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# create tables (temporary for dev)
from app.models.notification import Notification
Base.metadata.create_all(bind=engine)

# register routers
app.include_router(api_router, prefix="/api/v1")

# register exception handlers
add_exception_handlers(app)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/")
def root():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    if platform.system() != "Linux":
        from gunicorn.app.wsgiapp import WSGIApplication

        class StandaloneApplication(WSGIApplication):
            def __init__(self, app_uri, options=None):
                self.options = options or {}
                self.app_uri = app_uri
                super().__init__()

            def load_config(self):
                config = {
                    key: value
                    for key, value in self.options.items()
                    if key in self.cfg.settings and value is not None
                }
                for key, value in config.items():
                    self.cfg.set(key.lower(), value)

        options = {
            "bind": f"0.0.0.0:{settings.PORT}",
            "workers": 8,
            "threads": 2,
            "worker_class": "uvicorn.workers.UvicornH11Worker",
            "timeout": 120,
            "keepalive": 10,
            "max_requests": 1000,
            "max_requests_jitter": 200,
            "graceful_timeout": 30,
            "limit_request_line": 8190,
        }
        StandaloneApplication("main:app", options).run()
    else:
        uvicorn.run(
            app="main:app",
            host="0.0.0.0",
            port=settings.PORT,
            reload=not settings.IS_PROD,
        )
