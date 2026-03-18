from __future__ import annotations
import re

import httpx
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from models import SheetsImportRequest
from services.spreadsheet_parser import parse_csv_bytes, parse_xlsx_bytes

router = APIRouter(tags=["spreadsheet"])


@router.post("/upload-xlsx")
async def upload_xlsx(file: UploadFile = File(...)):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only .xlsx / .xls files are accepted")
    data = await file.read()
    try:
        items = parse_xlsx_bytes(data)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Failed to parse spreadsheet: {exc}")
    return JSONResponse([item.model_dump(mode="json") for item in items])


@router.post("/import-sheets")
async def import_sheets(body: SheetsImportRequest):
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", body.sheet_url)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid Google Sheets URL")
    spreadsheet_id = match.group(1)

    export_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv"
    try:
        resp = httpx.get(export_url, follow_redirects=True, timeout=15.0)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch spreadsheet: {exc}")

    if resp.status_code != 200 or "text/csv" not in resp.headers.get("content-type", ""):
        raise HTTPException(
            status_code=400,
            detail="Could not access the spreadsheet. Make sure it is shared as 'Anyone with the link can view'.",
        )

    try:
        items = parse_csv_bytes(resp.content)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Failed to parse sheet: {exc}")

    return JSONResponse([item.model_dump(mode="json") for item in items])
