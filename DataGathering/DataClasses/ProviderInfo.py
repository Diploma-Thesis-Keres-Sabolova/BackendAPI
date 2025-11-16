from dataclasses import dataclass
from typing import Optional


@dataclass
class ProviderInfo:
    id: int
    name: str
    endpoint: str
    params: dict
    description: Optional[str] = None