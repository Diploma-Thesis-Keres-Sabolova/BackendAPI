from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class RawDataInfo:
    id: int
    run_id: int
    data: Dict[str, Any]
    created_at: datetime