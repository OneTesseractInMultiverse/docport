"""Define typed query options for store reads and projections."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Any, Self

from docport.domain.types import ProjectionDocument, SortDirection, StoreSort


# ========================================
# SORT FIELD
# ========================================
@dataclass(frozen=True, slots=True)
class SortField:
    """Describe one field and direction in a query sort."""

    field: str
    direction: SortDirection = 1

    def __post_init__(self) -> None:
        """Validate the field name and the sort direction."""
        if not self.field.strip():
            raise ValueError("sort field must not be blank")
        if self.direction not in (-1, 1):
            raise ValueError("sort direction must be 1 or -1")

    @classmethod
    def ascending(cls, field: str) -> Self:
        """Build an ascending sort definition."""
        return cls(field=field, direction=1)

    @classmethod
    def descending(cls, field: str) -> Self:
        """Build a descending sort definition."""
        return cls(field=field, direction=-1)

    def as_pair(self) -> tuple[str, int]:
        """Return the sort definition in driver-friendly form."""
        return (self.field, self.direction)


# ========================================
# PROJECTION
# ========================================
@dataclass(frozen=True, slots=True)
class Projection:
    """Represent a projection document for partial reads."""

    document: ProjectionDocument

    def __post_init__(self) -> None:
        """Reject empty projections and detach the mapping value."""
        if not self.document:
            raise ValueError("projection must not be empty")
        object.__setattr__(self, "document", dict(self.document))

    @classmethod
    def from_mapping(cls, document: Mapping[str, Any]) -> Self:
        """Create a projection from a mapping."""
        return cls(document=dict(document))

    @classmethod
    def include(cls, *fields: str, include_id: bool = False) -> Self:
        """Create an inclusion projection."""
        if not fields:
            raise ValueError("at least one projection field is required")
        document = {field_name: 1 for field_name in fields}
        if not include_id:
            document["_id"] = 0
        return cls(document=document)

    @classmethod
    def exclude(cls, *fields: str) -> Self:
        """Create an exclusion projection."""
        if not fields:
            raise ValueError("at least one projection field is required")
        return cls(document={field_name: 0 for field_name in fields})

    def as_document(self) -> ProjectionDocument:
        """Return a shallow copy of the projection document."""
        return dict(self.document)


# ========================================
# FIND OPTIONS
# ========================================
@dataclass(frozen=True, slots=True)
class FindOptions:
    """Capture sort, paging, and projection settings for a query."""

    sort: tuple[SortField, ...] = field(default_factory=tuple)
    skip: int = 0
    limit: int = 0
    projection: Projection | None = None

    def __post_init__(self) -> None:
        """Reject negative paging values."""
        if self.skip < 0:
            raise ValueError("skip must be greater than or equal to 0")
        if self.limit < 0:
            raise ValueError("limit must be greater than or equal to 0")

    @classmethod
    def from_values(
        cls,
        *,
        sort: Sequence[tuple[str, SortDirection]] | None = None,
        skip: int = 0,
        limit: int = 0,
        projection: Mapping[str, Any] | None = None,
    ) -> Self:
        """Create options from plain Python values."""
        sort_fields = tuple(
            SortField(field=field_name, direction=direction)
            for field_name, direction in (sort or [])
        )
        projection_value = Projection.from_mapping(projection) if projection is not None else None
        return cls(sort=sort_fields, skip=skip, limit=limit, projection=projection_value)

    def sort_pairs(self) -> StoreSort | None:
        """Return sort pairs that the MongoDB driver accepts."""
        if not self.sort:
            return None
        return [sort_field.as_pair() for sort_field in self.sort]

    def projection_document(self) -> ProjectionDocument | None:
        """Return the raw projection document."""
        if self.projection is None:
            return None
        return self.projection.as_document()

    def with_limit(self, limit: int) -> Self:
        """Return a copy with a new limit value."""
        return replace(self, limit=limit)
