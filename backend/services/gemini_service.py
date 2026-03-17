from __future__ import annotations
import asyncio
import json
import os
import re
from datetime import date, timedelta
from typing import Optional

import google.generativeai as genai
from google.generativeai import protos

from models import EquipmentItem, ProcessedEquipment


def _init_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash-lite",
        tools=[protos.Tool(
            google_search_retrieval=protos.GoogleSearchRetrieval()
        )],
    )


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

For each of the following {len(items)} equipment items, use Google Search to find the manufacturer's recommended maintenance interval from official manuals or guidelines. Then calculate the next maintenance date.

Date calculation rules:
- If last maintenance date is known: next_date = last_maintenance_date + interval_months
- If only installation date is known: next_date = installation_date + interval_months
- If neither is known: next_date = today + interval_months

{equipment_list}

Respond ONLY with a valid JSON array containing exactly {len(items)} objects, one per item in the same order. Each object must use this exact format:
{{
  "interval_months": <integer>,
  "next_maintenance_date": "<YYYY-MM-DD>",
  "manual_source": "<URL or description of the manual/guideline found>",
  "reasoning": "<1-2 sentence explanation>"
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
    model = _init_client()
    prompt = _build_batch_prompt(items)
    loop = asyncio.get_event_loop()

    try:
        # Single request for all items; 120s timeout to cover larger batches
        response = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: model.generate_content(prompt)),
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
