from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.database import get_db
from app.dependencies.auth import get_api_key
from app.dependencies.run_get_filters import RunFilter
from app.models.Run import Run
from app.repositories.run_repository import apply_run_filters
from app.schemas.RunSchema import RunResponse, RunCreate, RunUpdate

router = APIRouter(
    prefix="/run",
    tags=["Run"],
    dependencies=[Depends(get_api_key)]
)

@router.get("/", response_model=List[RunResponse])
def read_runs(
    filters: RunFilter = Depends(),
    db: Session = Depends(get_db),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
):
    query = db.query(Run).options(joinedload(Run.provider))
    query = apply_run_filters(query, filters)

    return (
        query
        .order_by(Run.run_timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

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