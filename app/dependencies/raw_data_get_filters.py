from fastapi import Query
from typing import Optional
from datetime import datetime

class RawDataFilter:
    def __init__(
        self,
        run_id: Optional[int] = Query(None, ge=1),
        provider_id: Optional[int] = Query(None, ge=1),
        name: Optional[str] = Query(None),
        timestamp_from: Optional[datetime] = Query(None),
        timestamp_to: Optional[datetime] = Query(None),
        created_from: Optional[datetime] = Query(None),
        created_to: Optional[datetime] = Query(None),
    ):
        self.run_id = run_id
        self.provider_id = provider_id
        self.name = name
        self.timestamp_from = timestamp_from
        self.timestamp_to = timestamp_to
        self.created_from = created_from
        self.created_to = created_to
