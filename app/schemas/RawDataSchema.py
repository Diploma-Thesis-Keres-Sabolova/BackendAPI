from datetime import datetime
from typing import Optional, Dict, Any
from .CustomBaseModel import CustomBaseModel

class RawDataResponse(CustomBaseModel):
    id: int
    run_id: int
    data: Any
    created_at: datetime

    class Config(CustomBaseModel.Config):
        from_attributes = True


class RawDataInRun(CustomBaseModel):
    id: int
    data: Any

    class Config(CustomBaseModel.Config):
        from_attributes = True

class RawDataCreate(CustomBaseModel):
    run_id: int
    data: Any


class RawDataUpdate(CustomBaseModel):
    data: Any = None