from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from typing import Optional

from starseek.api.dependencies import get_settings, get_db_path
from starseek.config import Settings
from starseek.models.chart import SynastryReport
from starseek.core.synastry import calculate_synastry
from starseek.services.storage import (
    load_chart, resolve_chart,
    save_synastry, load_synastry, list_synastries, delete_synastry,
)

router = APIRouter(prefix="/api/v1", tags=["synastry"])


class SynastryRequest(BaseModel):
    chart_a: str = Field(..., description="ID or name of the first saved chart")
    chart_b: str = Field(..., description="ID or name of the second saved chart")
    include_minor_aspects: bool = Field(False, description="Include minor aspects")
    save: bool = Field(True, description="Save the synastry report to database")


class SynastryListResponse(BaseModel):
    reports: list[dict]
    total: int


@router.post("/synastry", status_code=201, response_model=SynastryReport)
def create_synastry(
    body: SynastryRequest,
    settings: Settings = Depends(get_settings),
    db_path: str = Depends(get_db_path),
):
    chart_a = resolve_chart(db_path, body.chart_a)
    if chart_a is None:
        raise HTTPException(status_code=404, detail=f"Chart '{body.chart_a}' not found")

    chart_b = resolve_chart(db_path, body.chart_b)
    if chart_b is None:
        raise HTTPException(status_code=404, detail=f"Chart '{body.chart_b}' not found")

    report = calculate_synastry(
        chart_a, chart_b, include_minor_aspects=body.include_minor_aspects
    )

    if body.save:
        save_synastry(db_path, report)

    return report


@router.get("/synastry", response_model=SynastryListResponse)
def get_synastries(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db_path: str = Depends(get_db_path),
):
    items, total = list_synastries(db_path, limit=limit, offset=offset)
    reports = [
        {
            "id": item.id,
            "name_a": item.name_a,
            "name_b": item.name_b,
            "chart_a_id": item.chart_a_id,
            "chart_b_id": item.chart_b_id,
            "created_at": item.created_at,
        }
        for item in items
    ]
    return SynastryListResponse(reports=reports, total=total)


@router.get("/synastry/{report_id}", response_model=SynastryReport)
def get_synastry(report_id: int, db_path: str = Depends(get_db_path)):
    report = load_synastry(db_path, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Synastry report {report_id} not found")
    return report


@router.delete("/synastry/{report_id}", status_code=204)
def remove_synastry(report_id: int, db_path: str = Depends(get_db_path)):
    deleted = delete_synastry(db_path, report_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Synastry report {report_id} not found")
    return Response(status_code=204)
