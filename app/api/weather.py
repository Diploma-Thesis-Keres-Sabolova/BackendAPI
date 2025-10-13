from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import SessionLocal
from app.models.WeatherData import WeatherData
from app.schemas.WeatherDataSchema import WeatherDataResponse


router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[WeatherDataResponse])
def read_weather(limit: int = 10, db: Session = Depends(get_db)):
    return db.query(WeatherData).all()