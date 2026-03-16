from __future__ import annotations
import asyncio
import json
import os
import re
from datetime import date, timedelta
from typing import Optional

import google.generativeai as genai

from models import EquipmentItem, ProcessedEquipment

_SEMAPHORE = asyncio.Semaphore(3)


def _init_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config={"response_mime_type": "application/json"},
    )


def _build_prompt(item: EquipmentItem) -> str:
    parts = []
    if item.equipment_type:
        parts.append(f"- Equipment Type: {item.equipment_type}")
    if item.brand:
        parts.append(f"- Brand: {item.brand}")
    if item.model:
        parts.append(f"- Model: {item.model}")
    if item.installation_date:
        parts.append(f"- Installation Date: {item.installation_date.isoformat()}")
    if item.last_maintenance_date:
        parts.append(f"- Last Maintenance Date: {item.last_maintenance_date.isoformat()}")

    equipment_desc = "\n".join(parts) if parts else "Unknown equipment"

    return f"""You are a warehouse equipment maintenance scheduling expert.

Given the following warehouse equipment:
{equipment_desc}

Your task:
1. Search for and reference the official maintenance manual or manufacturer maintenance guidelines for this specific equipment (brand + model if available, otherwise equipment type).
2. Determine the recommended preventive maintenance interval in months based on the manual/guidelines.
3. Calculate the estimated next maintenance date:
   - If last maintenance date is known: next_date = last_maintenance_date + interval_months
   - If only installation date is known: next_date = installation_date + interval_months
   - If neither is known, estimate from today's date
4. Provide a brief note on what manual or source you referenced.

Today's date is: {date.today().isoformat()}

Respond ONLY with valid JSON in this exact format:
{{
  "interval_months": <integer>,
  "next_maintenance_date": "<YYYY-MM-DD>",
  "manual_source": "<URL or description of the manual/guideline found>",
  "reasoning": "<1-2 sentence explanation of what maintenance schedule was found and why>"
}}"""


def _extract_json(text: str) -> dict:
    """Extract JSON from Gemini response, handling markdown code blocks."""
    # Strip markdown fences
    text = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
    return json.loads(text)


def _fallback_result(item: EquipmentItem) -> dict:
    """Return a conservative 12-month default when Gemini fails."""
    base = item.last_maintenance_date or item.installation_date or date.today()
    next_date = base + timedelta(days=365)
    return {
        "interval_months": 12,
        "next_maintenance_date": next_date.isoformat(),
        "manual_source": "Default estimate (manual not found)",
        "reasoning": "Could not retrieve specific maintenance guidelines. Applied a conservative 12-month default interval.",
    }


async def _analyze_one(item: EquipmentItem, model) -> ProcessedEquipment:
    async with _SEMAPHORE:
        try:
            prompt = _build_prompt(item)
            # Run synchronous Gemini call in executor; enforce 60s timeout
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: model.generate_content(
                        prompt,
                        tools=[{"google_search": {}}],
                    ),
                ),
                timeout=60.0,
            )
            raw_text = response.text
            data = _extract_json(raw_text)
        except asyncio.TimeoutError:
            print(f"[Gemini] Timeout for {item.brand} {item.model}")
            data = _fallback_result(item)
        except Exception as exc:
            print(f"[Gemini] Error for {item.brand} {item.model}: {exc}")
            data = _fallback_result(item)

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
    tasks = [_analyze_one(item, model) for item in items]
    return await asyncio.gather(*tasks)
