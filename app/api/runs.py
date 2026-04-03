from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.database import get_db
from app.dependencies.auth import get_api_key
from app.dependencies.run_get_filters import RunFilter
from app.models.ProcessedData import ProcessedData
from app.models.Provider import Provider
from app.models.RawData import RawData
from app.models.Run import Run
from app.repositories.run_repository import apply_run_filters
from app.schemas.RunSchema import RunResponse, RunCreate, RunUpdate
from app.schemas.RawDataSchema import RawDataCreate
from app.schemas.ProcessedDataSchema import ProcessedDataCreate

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

@router.post("/impute-missing", tags=["Imputation"])
def impute_missing_runs(target_date: date = None, db: Session = Depends(get_db)):

    if not target_date:
        target_date = date.today()

    all_providers = db.query(Provider).all()
    all_provider_ids = {p.id for p in all_providers}

    todays_runs = db.query(Run).filter(Run.target_date == target_date).all()
    providers_with_runs = {run.provider_id for run in todays_runs}

    missing_provider_ids = all_provider_ids - providers_with_runs

    if not missing_provider_ids:
        return {"message": "There is no imputation needed.", "imputed_count": 0}

    imputed_providers = []

    for provider_id in missing_provider_ids:
        last_success_run = db.query(Run).filter(
            Run.provider_id == provider_id,
            Run.target_date < target_date,
            Run.status.in_(['SUCCESS PROCESSED'])
        ).order_by(Run.target_date.desc()).first()

        if not last_success_run:
            continue

        run_schema = RunCreate(
            provider_id=provider_id,
            run_timestamp=datetime.now(),
            data_type=last_success_run.data_type,
            target_date=datetime.combine(target_date, datetime.min.time()),
            params=last_success_run.params,
            status="IMPUTED",
            message=f"Data imputed from Run ID: {last_success_run.id}"
        )
        new_run = Run(**run_schema.model_dump())
        db.add(new_run)
        db.flush()

        last_raw_data = db.query(RawData).filter(RawData.run_id == last_success_run.id).first()
        if last_raw_data:
            raw_schema = RawDataCreate(
                run_id=new_run.id,
                data=last_raw_data.data,
                data_format=last_raw_data.data_format
            )
            new_raw = RawData(**raw_schema.model_dump())
            db.add(new_raw)

        last_processed_data = db.query(ProcessedData).filter(ProcessedData.run_id == last_success_run.id).all()

        for p_data in last_processed_data:
            processed_schema = ProcessedDataCreate(
                run_id=new_run.id,
                timestamp=p_data.timestamp,
                name=p_data.name,
                value=p_data.value,
                unit=p_data.unit
            )

            new_processed = ProcessedData(**processed_schema.model_dump())
            db.add(new_processed)

        imputed_providers.append(provider_id)

    db.commit()

    return {
        "message": f"Data impuded for  {len(imputed_providers)} providers.",
        "imputed_provider_ids": imputed_providers
    }