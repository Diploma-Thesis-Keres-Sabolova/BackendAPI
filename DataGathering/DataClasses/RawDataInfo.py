from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class RawDataInfo:
    id: int
    run_id: int
    data: Any
    data_format: str
    created_at: datetime