from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from starseek.api.dependencies import get_settings, get_db_path
from starseek.config import Settings
from starseek.models.chart import SynastryReport
from starseek.core.synastry import calculate_synastry
from starseek.services.storage import load_chart

router = APIRouter(prefix="/api/v1", tags=["synastry"])


class SynastryRequest(BaseModel):
    chart_a_id: int = Field(..., description="ID of the first saved chart")
    chart_b_id: int = Field(..., description="ID of the second saved chart")
    include_minor_aspects: bool = Field(False, description="Include minor aspects")


@router.post("/synastry", response_model=SynastryReport)
def create_synastry(
    body: SynastryRequest,
    settings: Settings = Depends(get_settings),
    db_path: str = Depends(get_db_path),
):
    chart_a = load_chart(db_path, body.chart_a_id)
    if chart_a is None:
        raise HTTPException(status_code=404, detail=f"Chart {body.chart_a_id} not found")

    chart_b = load_chart(db_path, body.chart_b_id)
    if chart_b is None:
        raise HTTPException(status_code=404, detail=f"Chart {body.chart_b_id} not found")

    report = calculate_synastry(
        chart_a, chart_b, include_minor_aspects=body.include_minor_aspects
    )
    return report
