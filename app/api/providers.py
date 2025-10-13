from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import SessionLocal
from app.models.Provider import Provider
from app.schemas.ProviderSchema import ProviderResponse

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[ProviderResponse])
def read_providers(db: Session = Depends(get_db)):
    return db.query(Provider).all()
