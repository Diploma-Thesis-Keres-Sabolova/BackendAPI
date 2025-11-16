from typing import Optional, List
from datetime import datetime, date
from .CustomBaseModel import CustomBaseModel
from .RawDataSchema import RawDataInRun
from .ProviderSchema import ProviderResponse

class RunResponse(CustomBaseModel):
    id: int
    provider_id: int
    run_timestamp: datetime
    data_type: str
    target_date: date
    status: str
    message: str

    class Config(CustomBaseModel.Config):
        from_attributes = True

class RunWithDataResponse(CustomBaseModel):
    id: int
    provider_id: int
    run_timestamp: datetime
    data_type: str
    target_date: date
    status: str
    message: str
    provider: Optional[ProviderResponse]
    data: Optional[List[RawDataInRun]] = []

    class Config(CustomBaseModel.Config):
        from_attributes = True

class RunCreate(CustomBaseModel):
    provider_id: int
    run_timestamp: datetime
    data_type: str
    target_date: datetime
    status: str
    message: Optional[str] = None


class RunUpdate(CustomBaseModel):
    status: Optional[str] = None
    message: Optional[str] = None