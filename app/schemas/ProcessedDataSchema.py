from datetime import datetime
from typing import Optional
from .CustomBaseModel import CustomBaseModel
from .RunSchema import RunResponse


class ProcessedDataResponse(CustomBaseModel):
    id: int
    run_id: int
    timestamp: datetime
    name: str
    value: Optional[str] = None
    unit: Optional[str] = None
    created_at: datetime

    class Config(CustomBaseModel.Config):
        from_attributes = True


class ProcessedDataInRun(CustomBaseModel):
    name: str
    value: Optional[str]
    unit: Optional[str]
    timestamp: datetime

    class Config(CustomBaseModel.Config):
        from_attributes = True

class ProcessedDataCreate(CustomBaseModel):
    run_id: int
    timestamp: datetime
    name: str
    value: Optional[str] = None
    unit: Optional[str] = None


class ProcessedDataUpdate(CustomBaseModel):
    timestamp: Optional[datetime] = None
    name: Optional[str] = None
    value: Optional[str] = None
    unit: Optional[str] = None

class ProcessedDataWithRunResponse(ProcessedDataResponse):
    run: Optional[RunResponse] = None

    class Config(CustomBaseModel.Config):
        from_attributes = True