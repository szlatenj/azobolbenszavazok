from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.routes import carpool, contact, health, helprequest, signup

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Voting Guide API", docs_url="/api/docs", openapi_url="/api/openapi.json")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(health.router, prefix="/api")
app.include_router(signup.router, prefix="/api")
app.include_router(contact.router, prefix="/api")
app.include_router(helprequest.router, prefix="/api")
app.include_router(carpool.router, prefix="/api")

# Serve frontend static files (check Docker path first, then local dev path)
frontend_dir = Path("/frontend")
if not frontend_dir.is_dir():
    frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
