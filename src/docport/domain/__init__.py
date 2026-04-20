"""Expose the public domain contract for docport."""

from docport.domain.constants import (
    DEFAULT_ENTITY_VERSION,
    DEFAULT_TIME_SERIES_FIELD_NAME,
    METADATA_FIELD_NAMES,
)
from docport.domain.entity import (
    DocPortEntity,
    DocPortTimeSeriesEntity,
    new_entity_id,
    utc_now,
)
from docport.domain.errors import (
    DocPortError,
    DuplicateEntityError,
    EntityNotFoundError,
    EntityVersionConflictError,
    StoreConfigurationError,
)
from docport.domain.observability import (
    ObservationOutcome,
    StoreObservation,
    StoreOperationContext,
    new_correlation_id,
)
from docport.domain.query import FindOptions, Projection, SortField
from docport.domain.types import (
    DocumentId,
    ProjectionDocument,
    SortDirection,
    StoreDocument,
    StoreFilter,
    StoreSort,
)

__all__ = [
    "DEFAULT_ENTITY_VERSION",
    "DEFAULT_TIME_SERIES_FIELD_NAME",
    "METADATA_FIELD_NAMES",
    "DocPortEntity",
    "DocPortTimeSeriesEntity",
    "new_entity_id",
    "utc_now",
    "DuplicateEntityError",
    "EntityNotFoundError",
    "EntityVersionConflictError",
    "StoreConfigurationError",
    "DocPortError",
    "ObservationOutcome",
    "StoreObservation",
    "StoreOperationContext",
    "new_correlation_id",
    "FindOptions",
    "Projection",
    "SortField",
    "DocumentId",
    "ProjectionDocument",
    "SortDirection",
    "StoreDocument",
    "StoreFilter",
    "StoreSort",
]
