from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.dependencies.auth import get_api_key
from app.models.Run import Run
from app.schemas.RunSchema import RunResponse, RunCreate, RunUpdate

router = APIRouter(
    prefix="/run",
    tags=["Run"],
    dependencies=[Depends(get_api_key)]
)

@router.get("/", response_model=List[RunResponse])
def read_runs(db: Session = Depends(get_db)):
    return db.query(Run).all()

@router.post("/", response_model=RunResponse)
def create_run(run: RunCreate, db: Session = Depends(get_db)):
    new_data = Run(**run.model_dump())
    db.add(new_data)
    db.commit()
    db.refresh(new_data)
    return new_data

@router.put("/{run_id}", response_model=RunResponse)
def update_provider(run_id: int, provider: RunUpdate, db: Session = Depends(get_db)):
    db_data = db.query(Run).filter(Run.id == run_id).first()

    for key, value in provider.model_dump(exclude_unset=True).items():
        setattr(db_data, key, value)

    db.commit()
    db.refresh(db_data)
    return db_data