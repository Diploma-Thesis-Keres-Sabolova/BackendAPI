from sqlalchemy.orm import Query
from app.models.RawData import RawData
from app.models.Run import Run
from app.dependencies.raw_data_get_filters import RawDataFilter

def apply_raw_data_filters(query: Query, filters: RawDataFilter) -> Query:
    if filters.run_id:
        query = query.filter(RawData.run_id == filters.run_id)

    if filters.provider_id:
        query = query.join(RawData.run).filter(Run.provider_id == filters.provider_id)
    if filters.created_from:
        query = query.filter(RawData.created_at >= filters.created_from)
    if filters.created_to:
        query = query.filter(RawData.created_at <= filters.created_to)

    return query