from sqlalchemy.orm import Query
from app.models.Provider import Provider
from app.dependencies.provider_get_filters import ProviderFilter

def apply_provider_filters(query: Query, filters: ProviderFilter) -> Query:
    if filters.name:
        query = query.filter(Provider.name.ilike(f"%{filters.name}%"))

    if filters.endpoint:
        query = query.filter(Provider.endpoint.ilike(f"%{filters.endpoint}%"))

    if filters.description:
        query = query.filter(Provider.description.ilike(f"%{filters.description}%"))

    return query
