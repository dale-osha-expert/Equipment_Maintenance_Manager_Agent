from __future__ import annotations
import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from routers import auth, calendar, export, process, spreadsheet

# Validate required env vars at startup
_REQUIRED_ENV = [
    "GEMINI_API_KEY",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "SESSION_SECRET_KEY",
    "GOOGLE_REDIRECT_URI",
    "FRONTEND_URL",
]
_missing = [v for v in _REQUIRED_ENV if not os.environ.get(v)]
if _missing:
    raise RuntimeError(
        f"Missing required environment variables: {', '.join(_missing)}. "
        "Copy backend/.env.example to backend/.env and fill in all values."
    )

app = FastAPI(title="Equipment Maintenance Manager", version="1.0.0")

_https_only = os.getenv("HTTPS_ONLY", "false").lower() == "true"

# Session middleware (must be added before CORS)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ["SESSION_SECRET_KEY"],
    max_age=86400,  # 24 hours
    https_only=_https_only,
    same_site="lax",
)

# CORS
frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(spreadsheet.router)
app.include_router(process.router)
app.include_router(export.router)
app.include_router(calendar.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
