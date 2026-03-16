from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from models import CalendarAddAllRequest, CalendarAddRequest
from services.google_calendar import add_calendar_event, add_calendar_events_bulk

router = APIRouter(prefix="/calendar", tags=["calendar"])


def _get_creds(request: Request) -> dict:
    creds = request.session.get("google_credentials")
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated with Google")
    return creds


@router.post("/add")
async def calendar_add(body: CalendarAddRequest, request: Request):
    creds = _get_creds(request)
    if not body.equipment.next_maintenance_date:
        raise HTTPException(status_code=400, detail="Equipment has no next_maintenance_date")
    try:
        event_id = add_calendar_event(body.equipment, creds)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Google Calendar error: {exc}")
    return JSONResponse({"event_id": event_id, "equipment_id": body.equipment.id})


@router.post("/add-all")
async def calendar_add_all(body: CalendarAddAllRequest, request: Request):
    creds = _get_creds(request)
    eligible = [e for e in body.equipment if e.next_maintenance_date]
    if not eligible:
        raise HTTPException(status_code=400, detail="No equipment with next_maintenance_date to add")
    try:
        results = add_calendar_events_bulk(eligible, creds)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Google Calendar error: {exc}")
    return JSONResponse({"results": results})
