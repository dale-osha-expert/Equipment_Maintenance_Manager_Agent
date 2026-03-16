from __future__ import annotations
from datetime import date
from typing import Optional
from pydantic import BaseModel


class EquipmentItem(BaseModel):
    id: str
    equipment_type: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    installation_date: Optional[date] = None
    last_maintenance_date: Optional[date] = None
    raw_row: dict = {}


class ProcessedEquipment(EquipmentItem):
    next_maintenance_date: Optional[date] = None
    maintenance_interval_months: Optional[int] = None
    manual_source: Optional[str] = None
    gemini_reasoning: Optional[str] = None
    calendar_event_id: Optional[str] = None


class ProcessRequest(BaseModel):
    equipment: list[EquipmentItem]


class CalendarAddRequest(BaseModel):
    equipment: ProcessedEquipment


class CalendarAddAllRequest(BaseModel):
    equipment: list[ProcessedEquipment]


class ExportRequest(BaseModel):
    equipment: list[ProcessedEquipment]


class SheetsImportRequest(BaseModel):
    sheet_url: str
