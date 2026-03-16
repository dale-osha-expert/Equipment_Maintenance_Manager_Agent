from __future__ import annotations
from typing import Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from models import ProcessedEquipment


def _build_service(credentials_dict: dict):
    creds = Credentials(
        token=credentials_dict["token"],
        refresh_token=credentials_dict.get("refresh_token"),
        token_uri=credentials_dict.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=credentials_dict.get("client_id"),
        client_secret=credentials_dict.get("client_secret"),
        scopes=credentials_dict.get("scopes"),
    )
    return build("calendar", "v3", credentials=creds)


def _build_event(item: ProcessedEquipment) -> dict:
    name_parts = [p for p in [item.brand, item.model] if p]
    equipment_label = " ".join(name_parts) if name_parts else "Equipment"
    if item.equipment_type:
        equipment_label += f" ({item.equipment_type})"

    description_parts = []
    if item.gemini_reasoning:
        description_parts.append(item.gemini_reasoning)
    if item.manual_source:
        description_parts.append(f"Source: {item.manual_source}")
    if item.maintenance_interval_months:
        description_parts.append(f"Recommended interval: every {item.maintenance_interval_months} month(s)")
    if item.last_maintenance_date:
        description_parts.append(f"Last maintenance: {item.last_maintenance_date.isoformat()}")

    date_str = item.next_maintenance_date.isoformat() if item.next_maintenance_date else None

    return {
        "summary": f"Maintenance Due: {equipment_label}",
        "description": "\n".join(description_parts),
        "start": {"date": date_str},
        "end": {"date": date_str},
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 7 * 24 * 60},  # 1 week before
                {"method": "popup", "minutes": 24 * 60},       # 1 day before
            ],
        },
    }


def add_calendar_event(item: ProcessedEquipment, credentials_dict: dict) -> str:
    """Add a single event. Returns the created event ID."""
    if not item.next_maintenance_date:
        raise ValueError("No next_maintenance_date set for this equipment item")
    service = _build_service(credentials_dict)
    event = _build_event(item)
    created = service.events().insert(calendarId="primary", body=event).execute()
    return created.get("id", "")


def add_calendar_events_bulk(
    items: list[ProcessedEquipment], credentials_dict: dict
) -> dict[str, Optional[str]]:
    """Add multiple events. Returns {item_id: event_id_or_error}."""
    service = _build_service(credentials_dict)
    results: dict[str, Optional[str]] = {}
    for item in items:
        if not item.next_maintenance_date:
            results[item.id] = None
            continue
        try:
            event = _build_event(item)
            created = service.events().insert(calendarId="primary", body=event).execute()
            results[item.id] = created.get("id")
        except Exception as exc:
            results[item.id] = f"error: {exc}"
    return results
