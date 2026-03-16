from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from models import ProcessRequest
from services.gemini_service import analyze_equipment

router = APIRouter(tags=["process"])


@router.post("/process")
async def process_equipment(body: ProcessRequest):
    if not body.equipment:
        raise HTTPException(status_code=400, detail="No equipment items provided")
    try:
        results = await analyze_equipment(body.equipment)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return JSONResponse([r.model_dump(mode="json") for r in results])
