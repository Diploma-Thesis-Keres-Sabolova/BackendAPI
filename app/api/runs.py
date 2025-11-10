from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.dependencies.auth import get_api_key
from app.models.Run import Run
from app.schemas.RunSchema import RunResponse


router = APIRouter(
    prefix="/run",
    tags=["Run"],
    dependencies=[Depends(get_api_key)]
)

@router.get("/", response_model=List[RunResponse])
def read_runs(db: Session = Depends(get_db)):
    return db.query(Run).all()