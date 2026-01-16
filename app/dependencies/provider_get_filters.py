from fastapi import Query
from typing import Optional

class ProviderFilter:
    def __init__(
        self,
        name: Optional[str] = Query(None),
        endpoint: Optional[str] = Query(None),
        description: Optional[str] = Query(None),
    ):
        self.name = name
        self.endpoint = endpoint
        self.description = description
