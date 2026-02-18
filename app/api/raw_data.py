from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.dependencies.auth import get_api_key
from app.dependencies.raw_data_get_filters import RawDataFilter
from app.models.RawData import RawData
from app.repositories.raw_data_repository import apply_raw_data_filters
from app.schemas.RawDataSchema import RawDataResponse, RawDataCreate, RawDataUpdate

router = APIRouter(
    prefix="/raw_data",
    tags=["RawData"],
    dependencies=[Depends(get_api_key)]
)

@router.get("/", response_model=List[RawDataResponse])
def read_raw_data(
    filters: RawDataFilter = Depends(),
    db: Session = Depends(get_db),
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
):
    query = db.query(RawData)
    query = apply_raw_data_filters(query, filters)

    return (
        query
        .order_by(RawData.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

@router.post("/", response_model=RawDataResponse)
def create_raw_data(raw_data: RawDataCreate, db: Session = Depends(get_db)):
    new_data = RawData(**raw_data.model_dump())
    db.add(new_data)
    db.commit()
    db.refresh(new_data)
    return new_data

@router.put("/{raw_data_id}", response_model=RawDataResponse)
def update_raw_data(raw_data_id: int, raw_data: RawDataUpdate, db: Session = Depends(get_db)):
    db_data = db.query(RawData).filter(RawData.id == raw_data_id).first()

    for key, value in raw_data.model_dump(exclude_unset=True).items():
        setattr(db_data, key, value)

    db.commit()
    db.refresh(db_data)
    return db_data