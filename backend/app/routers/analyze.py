from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.analytics import (
    build_allocations,
    build_performance_and_risk,
    build_positions_with_market_data,
    build_summary,
)
from app.parser import CsvParseError, parse_statement_csv
from app.portfolio import build_positions
from app.schemas import AnalysisResponse

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_statement(file: UploadFile = File(...)) -> AnalysisResponse:
    if not file.filename or not file.filename.lower().endswith((".csv", ".txt")):
        raise HTTPException(status_code=400, detail="Le fichier doit être un CSV (.csv).")

    content = await file.read()
    try:
        transactions, parse_warnings = parse_statement_csv(content)
    except CsvParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    state = build_positions(transactions)
    positions, market_warnings = build_positions_with_market_data(state)
    summary = build_summary(transactions, state, positions)
    sector_alloc, country_alloc, ticker_alloc = build_allocations(positions)
    performance, risk, perf_warnings = build_performance_and_risk(transactions)

    return AnalysisResponse(
        summary=summary,
        positions=positions,
        allocation_by_sector=sector_alloc,
        allocation_by_country=country_alloc,
        allocation_by_ticker=ticker_alloc,
        performance=performance,
        risk=risk,
        warnings=[*parse_warnings, *market_warnings, *perf_warnings],
    )
