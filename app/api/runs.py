from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import SessionLocal
from app.models.Run import Run
from app.schemas.RunSchema import RunResponse


router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[RunResponse])
def read_runs(db: Session = Depends(get_db)):
    return db.query(Run).all()