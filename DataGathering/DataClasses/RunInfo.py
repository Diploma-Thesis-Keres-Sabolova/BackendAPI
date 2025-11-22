from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class RunInfo:
    id: int
    provider_id: int
    run_timestamp: datetime
    params: dict
    data_type: str
    target_date: date
    status: str
    message: str
