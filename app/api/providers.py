from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.dependencies.auth import get_api_key
from app.models.Provider import Provider
from app.schemas.ProviderSchema import ProviderResponse, ProviderCreate, ProviderUpdate

router = APIRouter(
    prefix="/provider",
    tags=["Provider"],
    dependencies=[Depends(get_api_key)]
)

@router.get("/", response_model=List[ProviderResponse])
def read_providers(name: str | None = None, endpoint: str | None = None, params: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Provider)
    if name:
        query = query.filter(Provider.name == name)
    if endpoint:
        query = query.filter(Provider.endpoint == endpoint)
    if params:
        query = query.filter(Provider.params == params)

    return query.all()

@router.post("/", response_model=ProviderResponse)
def create_provider(provider: ProviderCreate, db: Session = Depends(get_db)):
    new_data = Provider(**provider.model_dump())
    db.add(new_data)
    db.commit()
    db.refresh(new_data)
    return new_data

@router.put("/{provider_id}", response_model=ProviderResponse)
def update_provider(provider_id: int, provider: ProviderUpdate, db: Session = Depends(get_db)):
    db_data = db.query(Provider).filter(Provider.id == provider_id).first()

    for key, value in provider.model_dump(exclude_unset=True).items():
        setattr(db_data, key, value)

    db.commit()
    db.refresh(db_data)
    return db_data