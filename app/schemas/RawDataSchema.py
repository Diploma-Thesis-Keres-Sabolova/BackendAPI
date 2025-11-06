from datetime import datetime
from typing import Optional
from .CustomBaseModel import CustomBaseModel


class RawDataResponse(CustomBaseModel):
    id: int
    run_id: int
    timestamp: datetime
    name: str
    value: Optional[float] = None
    unit: Optional[str] = None
    created_at: datetime

    class Config(CustomBaseModel.Config):
        from_attributes = True


class RawDataInRun(CustomBaseModel):
    name: str
    value: Optional[float]
    unit: Optional[str]
    timestamp: datetime

    class Config(CustomBaseModel.Config):
        from_attributes = True

class RawDataCreate(CustomBaseModel):
    run_id: int
    timestamp: datetime
    name: str
    value: Optional[float] = None
    unit: Optional[str] = None


class RawDataUpdate(CustomBaseModel):
    timestamp: Optional[datetime] = None
    name: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None