from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.dependencies.auth import get_api_key
from app.dependencies.processed_data_get_filters import ProcessedDataFilter
from app.models.ProcessedData import ProcessedData
from app.repositories.processed_data_repository import apply_processed_data_filters
from app.schemas.ProcessedDataSchema import ProcessedDataResponse, ProcessedDataCreate, ProcessedDataUpdate

router = APIRouter(
    prefix="/processed_data",
    tags=["ProcessedData"],
    dependencies=[Depends(get_api_key)]
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