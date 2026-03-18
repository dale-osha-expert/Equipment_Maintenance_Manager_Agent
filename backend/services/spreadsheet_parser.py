from __future__ import annotations
import uuid
from datetime import date, datetime
from difflib import SequenceMatcher
from typing import Optional
import pandas as pd
import io

from models import EquipmentItem


COLUMN_KEYWORDS: dict[str, list[str]] = {
    "equipment_type": ["type", "equipment type", "equipment", "machine", "asset", "category"],
    "brand": ["brand", "manufacturer", "make", "vendor", "supplier"],
    "model": ["model", "model number", "model no", "part number", "part"],
    "installation_date": ["install date", "installation date", "installed", "start date", "purchase date", "commissioned"],
    "last_maintenance_date": ["last maintenance", "last service", "last serviced", "serviced", "maintenance date", "last check"],
}

THRESHOLD = 0.55


def _similarity(a: str, b: str) -> float:
    a, b = a.lower().strip(), b.lower().strip()
    if b in a or a in b:
        return 0.9
    return SequenceMatcher(None, a, b).ratio()


def _detect_column(header: str, used: set[str]) -> Optional[str]:
    """Return the best matching field name for a column header, or None."""
    best_field = None
    best_score = THRESHOLD
    for field, keywords in COLUMN_KEYWORDS.items():
        if field in used:
            continue
        score = max(_similarity(header, kw) for kw in keywords)
        if score > best_score:
            best_score = score
            best_field = field
    return best_field


def _parse_date(value) -> Optional[date]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (date, datetime)):
        return value.date() if isinstance(value, datetime) else value
    s = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def parse_dataframe(df: pd.DataFrame) -> list[EquipmentItem]:
    """Auto-detect columns and return list of EquipmentItem."""
    # Drop fully-empty rows
    df = df.dropna(how="all").reset_index(drop=True)

    # Map detected field -> column name in dataframe
    column_map: dict[str, str] = {}
    used_fields: set[str] = set()

    for col in df.columns:
        field = _detect_column(str(col), used_fields)
        if field:
            column_map[field] = col
            used_fields.add(field)

    items: list[EquipmentItem] = []
    for _, row in df.iterrows():
        raw = {str(k): (None if pd.isna(v) else str(v)) for k, v in row.items()
               if not (isinstance(v, float) and pd.isna(v))}

        def get(field: str):
            col = column_map.get(field)
            if col is None:
                return None
            val = row.get(col)
            if val is None or (isinstance(val, float) and pd.isna(val)):
                return None
            return val

        items.append(EquipmentItem(
            id=str(uuid.uuid4()),
            equipment_type=str(get("equipment_type")).strip() if get("equipment_type") else None,
            brand=str(get("brand")).strip() if get("brand") else None,
            model=str(get("model")).strip() if get("model") else None,
            installation_date=_parse_date(get("installation_date")),
            last_maintenance_date=_parse_date(get("last_maintenance_date")),
            raw_row=raw,
        ))
    return items


def parse_xlsx_bytes(data: bytes) -> list[EquipmentItem]:
    df = pd.read_excel(io.BytesIO(data), engine="openpyxl")
    return parse_dataframe(df)


def parse_csv_bytes(data: bytes) -> list[EquipmentItem]:
    df = pd.read_csv(io.BytesIO(data))
    return parse_dataframe(df)


def parse_sheets_values(values: list[list]) -> list[EquipmentItem]:
    """Parse raw values from Google Sheets API (list of rows)."""
    if not values:
        return []
    headers = [str(h) for h in values[0]]
    rows = values[1:]
    records = []
    for row in rows:
        # Pad row to header length
        padded = row + [None] * (len(headers) - len(row))
        records.append(dict(zip(headers, padded)))
    df = pd.DataFrame(records)
    return parse_dataframe(df)
