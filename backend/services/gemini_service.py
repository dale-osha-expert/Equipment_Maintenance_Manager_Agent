from __future__ import annotations
import asyncio
import json
import os
import re
from datetime import date, timedelta
from typing import Optional

from google import genai
from google.genai import types

from models import EquipmentItem, ProcessedEquipment


def _init_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    return genai.Client(api_key=api_key)


def _build_batch_prompt(items: list[EquipmentItem]) -> str:
    today = date.today().isoformat()

    item_blocks = []
    for i, item in enumerate(items, 1):
        parts = [f"Item {i}:"]
        if item.equipment_type:
            parts.append(f"  - Equipment Type: {item.equipment_type}")
        if item.brand:
            parts.append(f"  - Brand: {item.brand}")
        if item.model:
            parts.append(f"  - Model: {item.model}")
        if item.installation_date:
            parts.append(f"  - Installation Date: {item.installation_date.isoformat()}")
        if item.last_maintenance_date:
            parts.append(f"  - Last Maintenance Date: {item.last_maintenance_date.isoformat()}")
        item_blocks.append("\n".join(parts))

    equipment_list = "\n\n".join(item_blocks)

    return f"""You are a warehouse equipment maintenance scheduling expert. Today's date is {today}.

For each equipment item below, search for the manufacturer's official recommended PERIODIC maintenance interval (calendar-based, e.g. every 6 months or every 12 months). Use the primary scheduled service interval from the official service manual or the manufacturer's maintenance schedule page — not the most frequent minor check (e.g. daily/weekly inspections) and not hour-based intervals. Convert hour-based intervals to months assuming 8-hour workdays and 22 working days per month.

Date calculation rules:
- If last maintenance date is known: next_date = last_maintenance_date + interval_months
- If only installation date is known: next_date = installation_date + interval_months
- If neither is known: next_date = today + interval_months

{equipment_list}

For manual_source, provide the exact name/title of the official source document or page where this interval is documented (e.g. "Toyota 8FGCU25 Series Forklift Periodic Maintenance Guide"). Do not provide URLs.

Respond ONLY with a valid JSON array containing exactly {len(items)} objects, one per item in the same order:
{{
  "interval_months": <integer>,
  "next_maintenance_date": "<YYYY-MM-DD>",
  "manual_source": "<exact document or source title>",
  "reasoning": "<cite the specific interval found, e.g. 'Toyota 8FGCU25 service manual specifies 250-hour / 6-month periodic inspection'>"
}}

Return only the JSON array, no other text."""


def _extract_json_array(text: str) -> list[dict]:
    text = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
    return json.loads(text)


def _fallback_result(item: EquipmentItem) -> dict:
    base = item.last_maintenance_date or item.installation_date or date.today()
    next_date = base + timedelta(days=365)
    return {
        "interval_months": 12,
        "next_maintenance_date": next_date.isoformat(),
        "manual_source": "Default estimate (manual not found)",
        "reasoning": "Could not retrieve specific maintenance guidelines. Applied a conservative 12-month default interval.",
    }


def _to_processed(item: EquipmentItem, data: dict) -> ProcessedEquipment:
    next_date: Optional[date] = None
    try:
        next_date = date.fromisoformat(data["next_maintenance_date"])
    except Exception:
        pass
    return ProcessedEquipment(
        **item.model_dump(),
        next_maintenance_date=next_date,
        maintenance_interval_months=data.get("interval_months"),
        manual_source=data.get("manual_source"),
        gemini_reasoning=data.get("reasoning"),
    )


async def analyze_equipment(items: list[EquipmentItem]) -> list[ProcessedEquipment]:
    client = _init_client()
    prompt = _build_batch_prompt(items)
    loop = asyncio.get_event_loop()

    try:
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                        temperature=0,
                    ),
                ),
            ),
            timeout=120.0,
        )
        results_data = _extract_json_array(response.text)

        if len(results_data) != len(items):
            raise ValueError(f"Expected {len(items)} results, got {len(results_data)}")

        return [_to_processed(item, data) for item, data in zip(items, results_data)]

    except asyncio.TimeoutError:
        print(f"[Gemini] Batch timeout for {len(items)} items")
        return [_to_processed(item, _fallback_result(item)) for item in items]
    except Exception as exc:
        print(f"[Gemini] Batch error: {exc}")
        return [_to_processed(item, _fallback_result(item)) for item in items]
