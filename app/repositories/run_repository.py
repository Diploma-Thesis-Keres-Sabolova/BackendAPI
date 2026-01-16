from sqlalchemy.orm import Query
from app.models.Run import Run
from app.models.Provider import Provider
from app.dependencies.run_get_filters import RunFilter

def apply_run_filters(query: Query, filters: RunFilter) -> Query:
    if filters.provider_id:
        query = query.filter(Run.provider_id == filters.provider_id)

    if filters.provider_name:
        query = query.join(Run.provider).filter(
            Provider.name == filters.provider_name
        )

    if filters.status:
        query = query.filter(Run.status == filters.status)

    if filters.data_type:
        query = query.filter(Run.data_type == filters.data_type)

    if filters.target_date_from:
        query = query.filter(Run.target_date >= filters.target_date_from)

    if filters.target_date_to:
        query = query.filter(Run.target_date <= filters.target_date_to)

    if filters.run_from:
        query = query.filter(Run.run_timestamp >= filters.run_from)

    if filters.run_to:
        query = query.filter(Run.run_timestamp <= filters.run_to)

    return query
