from datetime import datetime
from typing import Optional
from .CustomBaseModel import CustomBaseModel

class WeatherDataResponse(CustomBaseModel):
    id: int
    run_id: int
    timestamp: datetime
    temperature: Optional[float] = None
    dew_point: Optional[float] = None
    precipitation: Optional[float] = None
    rain: Optional[float] = None
    snowfall: Optional[float] = None
    wind_speed: Optional[float] = None
    global_tilted_irradiance: Optional[float] = None
    created_at: datetime

class WeatherDataInRun(CustomBaseModel):
    id: int
    run_id: int
    timestamp: datetime
    temperature: Optional[float]
    dew_point: Optional[float]
    precipitation: Optional[float]
    rain: Optional[float]
    snowfall: Optional[float]
    wind_speed: Optional[float]
    global_tilted_irradiance: Optional[float]
    created_at: datetime

    class Config(CustomBaseModel.Config):
        from_attributes = True
