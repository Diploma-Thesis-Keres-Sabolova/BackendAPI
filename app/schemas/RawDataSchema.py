from datetime import datetime
from typing import Optional, Dict, Any
from .CustomBaseModel import CustomBaseModel

class RawDataResponse(CustomBaseModel):
    id: int
    run_id: int
    data: Dict[str, Any]
    created_at: datetime

    class Config(CustomBaseModel.Config):
        from_attributes = True


class RawDataInRun(CustomBaseModel):
    id: int
    data: Dict[str, Any]

    class Config(CustomBaseModel.Config):
        from_attributes = True

class RawDataCreate(CustomBaseModel):
    run_id: int
    data: Dict[str, Any]


class RawDataUpdate(CustomBaseModel):
    data: Optional[Dict[str, Any]] = None