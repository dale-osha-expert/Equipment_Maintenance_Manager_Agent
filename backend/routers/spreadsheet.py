from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from models import SheetsImportRequest
from services.spreadsheet_parser import parse_xlsx_bytes, parse_sheets_values

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
async def import_sheets(body: SheetsImportRequest, request: Request):
    creds = request.session.get("google_credentials")
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated with Google")

    # Extract spreadsheet ID from URL
    import re
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", body.sheet_url)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid Google Sheets URL")
    spreadsheet_id = match.group(1)

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        google_creds = Credentials(
            token=creds["token"],
            refresh_token=creds.get("refresh_token"),
            token_uri=creds.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=creds.get("client_id"),
            client_secret=creds.get("client_secret"),
            scopes=creds.get("scopes"),
        )
        service = build("sheets", "v4", credentials=google_creds)
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range="A1:Z1000",
        ).execute()
        values = result.get("values", [])
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch Google Sheet: {exc}")

    try:
        items = parse_sheets_values(values)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Failed to parse sheet data: {exc}")

    return JSONResponse([item.model_dump(mode="json") for item in items])
