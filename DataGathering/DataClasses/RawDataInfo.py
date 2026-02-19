from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class RawDataInfo:
    id: int
    data: Dict[str, Any]