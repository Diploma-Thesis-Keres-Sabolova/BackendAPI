from typing import Optional, List
from datetime import datetime, date
from .CustomBaseModel import CustomBaseModel
from .WeatherDataSchema import WeatherDataInRun
from .ProviderSchema import ProviderResponse

class RunResponse(CustomBaseModel):
    id: int
    provider_id: int
    run_timestamp: datetime
    data_type: str
    target_date: date
    status: str
    message: str
    provider: Optional[ProviderResponse]
    weather_data: Optional[List[WeatherDataInRun]] = []

    class Config(CustomBaseModel.Config):
        from_attributes = True
