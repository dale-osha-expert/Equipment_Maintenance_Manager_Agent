from __future__ import annotations
import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from routers import auth, calendar, export, process, spreadsheet

app = FastAPI(title="Equipment Maintenance Manager", version="1.0.0")

# Session middleware (must be added before CORS)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET_KEY", "change-me-in-production"),
    max_age=86400,  # 24 hours
    https_only=False,  # Set True in production with HTTPS
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
