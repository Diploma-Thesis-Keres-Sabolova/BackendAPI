from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class RawDataInfo:
    id: int
    run_id: int
    data: Any
    created_at: datetime