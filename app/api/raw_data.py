from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.RawData import RawData
from app.schemas.RawDataSchema import RawDataResponse, RawDataCreate, RawDataUpdate

router = APIRouter(
    prefix="/raw_data",
    tags=["RawData"]
)

@router.get("/", response_model=List[RawDataResponse])
def read_weather(limit: int = 10, db: Session = Depends(get_db)):
    return db.query(RawData).all()

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