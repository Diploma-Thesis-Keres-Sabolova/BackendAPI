from fastapi import Query
from typing import Optional
from datetime import date, datetime

class RunFilter:
    def __init__(
        self,
        provider_id: Optional[int] = Query(None, ge=1),
        provider_name: Optional[str] = Query(None),
        status: Optional[str] = Query(None),
        data_type: Optional[str] = Query(None),

        target_date_from: Optional[date] = Query(None),
        target_date_to: Optional[date] = Query(None),
        run_from: Optional[datetime] = Query(None),
        run_to: Optional[datetime] = Query(None),
    ):
        self.provider_id = provider_id
        self.provider_name = provider_name
        self.status = status
        self.data_type = data_type
        self.target_date_from = target_date_from
        self.target_date_to = target_date_to
        self.run_from = run_from
        self.run_to = run_to
