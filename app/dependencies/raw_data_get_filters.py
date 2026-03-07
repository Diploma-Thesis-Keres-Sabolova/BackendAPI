from datetime import datetime
from typing import Optional
from fastapi import Query

class RawDataFilter:
    def __init__(
        self,
        run_id: Optional[int] = Query(None, ge=1),
        provider_id: Optional[int] = Query(None, ge=1),
        data_format: Optional[str] = Query(None, ge=1),
        created_from: Optional[datetime] = Query(None),
        created_to: Optional[datetime] = Query(None),
    ):
        self.run_id = run_id
        self.provider_id = provider_id
        self.data_format = data_format
        self.created_from = created_from
        self.created_to = created_to