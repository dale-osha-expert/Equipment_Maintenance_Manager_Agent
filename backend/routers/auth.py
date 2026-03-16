from __future__ import annotations
import os

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

router = APIRouter(prefix="/auth", tags=["auth"])

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/calendar.events",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
]


def _build_flow(redirect_uri: str) -> Flow:
    client_config = {
        "web": {
            "client_id": os.environ["GOOGLE_CLIENT_ID"],
            "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }
    flow = Flow.from_client_config(client_config, scopes=SCOPES)
    flow.redirect_uri = redirect_uri
    return flow


@router.get("/google")
async def auth_google(request: Request):
    redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")
    flow = _build_flow(redirect_uri)
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    request.session["oauth_state"] = state
    return RedirectResponse(auth_url)


@router.get("/callback")
async def auth_callback(request: Request, code: str = None, state: str = None, error: str = None):
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    if error:
        return RedirectResponse(f"{frontend_url}?auth=error&reason={error}")

    redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")
    flow = _build_flow(redirect_uri)
    flow.fetch_token(code=code)

    credentials: Credentials = flow.credentials

    # Store credentials in session
    request.session["google_credentials"] = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes or SCOPES),
    }

    # Try to get user email
    try:
        import httpx
        resp = httpx.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {credentials.token}"},
        )
        user_info = resp.json()
        request.session["user_email"] = user_info.get("email", "")
    except Exception:
        request.session["user_email"] = ""

    return RedirectResponse(f"{frontend_url}?auth=success")


@router.get("/status")
async def auth_status(request: Request):
    creds = request.session.get("google_credentials")
    authenticated = creds is not None and bool(creds.get("token"))
    return JSONResponse({
        "authenticated": authenticated,
        "email": request.session.get("user_email", ""),
    })


@router.post("/logout")
async def auth_logout(request: Request):
    request.session.pop("google_credentials", None)
    request.session.pop("user_email", None)
    request.session.pop("oauth_state", None)
    return JSONResponse({"status": "logged out"})
