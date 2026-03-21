from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.database import get_db
from app.dependencies.auth import get_api_key
from app.dependencies.processed_data_get_filters import ProcessedDataFilter
from app.models.ProcessedData import ProcessedData
from app.models.Run import Run
from app.repositories.processed_data_repository import apply_processed_data_filters
from app.schemas.ProcessedDataSchema import ProcessedDataResponse, ProcessedDataCreate, ProcessedDataUpdate, \
    ProcessedDataWithRunResponse

router = APIRouter(
    prefix="/processed_data",
    tags=["ProcessedData"],
    dependencies=[Depends(get_api_key)]
)

@router.get("/latest", response_model=List[ProcessedDataWithRunResponse])
def get_latest_data_for_model(
    db: Session = Depends(get_db),
    provider_id: Optional[int] = Query(None)
):
    latest_run = (
        db.query(Run)
        .filter(Run.provider_id == provider_id)
        .filter(Run.status == "SUCCESS PROCESSED")
        .order_by(Run.run_timestamp.desc())
        .first()
    )

    if not latest_run:
        raise HTTPException(
            status_code=404,
            detail=f"There are no runs for provider with ID {provider_id}."
        )

    processed_data = (
        db.query(ProcessedData)
        .filter(ProcessedData.run_id == latest_run.id)
        .options(joinedload(ProcessedData.run))
        .all()
    )

    return processed_data


@router.get("/range", response_model=List[ProcessedDataWithRunResponse])
def get_data_by_date_range(
        start_date: datetime = Query(..., description="Start Interval"),
        end_date: datetime = Query(..., description="End Interval"),
        provider_id: Optional[int] = Query(None, description="Provider"),
        limit: int = Query(3000, le=50000, description="Max cnumber of returned data"),
        offset: int = Query(0, description="Offset"),
        db: Session = Depends(get_db)
):

    query = db.query(ProcessedData)

    query = query.filter(
        ProcessedData.timestamp >= start_date,
        ProcessedData.timestamp <= end_date
    )

    if provider_id is not None:
        query = query.join(Run).filter(Run.provider_id == provider_id)

    query = query.options(joinedload(ProcessedData.run))

    return (
        query
        .order_by(ProcessedData.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

@router.get("/", response_model=List[ProcessedDataResponse])
def read_processed_data(
    filters: ProcessedDataFilter = Depends(),
    db: Session = Depends(get_db),
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
):
    query = db.query(ProcessedData)
    query = apply_processed_data_filters(query, filters)

    return (
        query
        .order_by(ProcessedData.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

@router.post("/", response_model=ProcessedDataResponse)
def create_processed_data(processed_data: ProcessedDataCreate, db: Session = Depends(get_db)):
    new_data = ProcessedData(**processed_data.model_dump())
    db.add(new_data)
    db.commit()
    db.refresh(new_data)
    db.refresh(new_data)
    return new_data

@router.put("/{processed_data_id}", response_model=ProcessedDataResponse)
def update_processed_data(processed_data_id: int, processed_data: ProcessedDataUpdate, db: Session = Depends(get_db)):
    db_data = db.query(ProcessedData).filter(ProcessedData.id == processed_data_id).first()

    for key, value in processed_data.model_dump(exclude_unset=True).items():
        setattr(db_data, key, value)

    db.commit()
    db.refresh(db_data)
    return db_data