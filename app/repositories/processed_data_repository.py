from sqlalchemy.orm import Query
from app.models.ProcessedData import ProcessedData
from app.models.Run import Run
from app.dependencies.processed_data_get_filters import ProcessedDataFilter

def apply_processed_data_filters(query: Query, filters: ProcessedDataFilter) -> Query:
    if filters.run_id:
        query = query.filter(ProcessedData.run_id == filters.run_id)

    if filters.provider_id:
        query = query.join(ProcessedData.run).filter(
            Run.provider_id == filters.provider_id
        )

    if filters.name:
        query = query.filter(ProcessedData.name.ilike(f"%{filters.name}%"))

    if filters.timestamp_from:
        query = query.filter(ProcessedData.timestamp >= filters.timestamp_from)

    if filters.timestamp_to:
        query = query.filter(ProcessedData.timestamp <= filters.timestamp_to)

    if filters.created_from:
        query = query.filter(ProcessedData.created_at >= filters.created_from)

    if filters.created_to:
        query = query.filter(ProcessedData.created_at <= filters.created_to)

    return query
