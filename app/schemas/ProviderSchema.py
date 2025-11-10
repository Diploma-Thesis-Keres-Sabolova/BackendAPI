from typing import List, Optional
from datetime import datetime, date
from pydantic import Field
from .CustomBaseModel import CustomBaseModel

class RunInProvider(CustomBaseModel):
    id: int
    run_timestamp: datetime
    data_type: str
    target_date: date
    status: str
    message: str

    class Config(CustomBaseModel.Config):
        from_attributes = True

class ProviderResponse(CustomBaseModel):
    id: int
    name: str
    endpoint: str
    description: Optional[str]
    params: Optional[str]
    runs: Optional[List[RunInProvider]] = []

    class Config(CustomBaseModel.Config):
        from_attributes = True

class ProviderCreate(CustomBaseModel):
    name: str
    endpoint: str
    description: Optional[str] = None
    params: Optional[str] = None

class ProviderUpdate(CustomBaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    params: Optional[str] = None