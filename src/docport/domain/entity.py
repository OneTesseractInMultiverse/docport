"""Define shared entity classes and time helpers for persisted records."""

import re
from datetime import UTC, datetime
from typing import Any, ClassVar, Self
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from docport.domain.constants import DEFAULT_ENTITY_VERSION, DEFAULT_TIME_SERIES_FIELD_NAME
from docport.domain.types import StoreDocument


# ------------------------------------------------------
# UTC NOW
# ------------------------------------------------------
def utc_now() -> datetime:
    """Return the current time in UTC.

    Returns:
        A timezone-aware UTC timestamp.
    """
    return datetime.now(UTC)


# ------------------------------------------------------
# NEW ENTITY ID
# ------------------------------------------------------
def new_entity_id() -> str:
    """Return a new cross-system identifier.

    Returns:
        A UUID string for service-visible record identity.
    """
    return str(uuid4())


# ------------------------------------------------------
# NORMALIZE DATETIME
# ------------------------------------------------------
def normalize_datetime(value: datetime) -> datetime:
    """Reject naive datetimes and normalize aware values to UTC.

    Args:
        value: Input datetime to normalize.

    Returns:
        A timezone-aware UTC datetime at BSON millisecond precision.

    Raises:
        ValueError: If the datetime is naive.
    """
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime fields must be timezone-aware")
    normalized_value = value.astimezone(UTC)
    bson_microseconds = (normalized_value.microsecond // 1000) * 1000
    return normalized_value.replace(microsecond=bson_microseconds)


# ------------------------------------------------------
# CAMEL TO SNAKE
# ------------------------------------------------------
def camel_to_snake(value: str) -> str:
    """Convert a class name into snake_case.

    Args:
        value: Class name to convert.

    Returns:
        A snake_case string.
    """
    first_pass = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", value)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", first_pass).lower()


# ========================================
# MOLEQL STORE ENTITY
# ========================================
class DocPortEntity(BaseModel):
    """Define shared identity and audit metadata for persisted store entities."""

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)

    __collection_name__: ClassVar[str | None] = None

    id: str = Field(default_factory=new_entity_id)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    created_by: str | None = None
    updated_by: str | None = None
    version: int = DEFAULT_ENTITY_VERSION

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        """Reject blank identifiers."""
        normalized = value.strip()
        if not normalized:
            raise ValueError("id must not be blank")
        return normalized

    @field_validator("created_by", "updated_by")
    @classmethod
    def validate_actor(cls, value: str | None) -> str | None:
        """Reject blank actor fields."""
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("actor fields must not be blank")
        return normalized

    @field_validator("created_at", "updated_at")
    @classmethod
    def validate_datetime(cls, value: datetime) -> datetime:
        """Normalize datetimes to UTC."""
        return normalize_datetime(value)

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: int) -> int:
        """Reject invalid entity versions."""
        if value < DEFAULT_ENTITY_VERSION:
            raise ValueError("version must be greater than or equal to 1")
        return value

    @model_validator(mode="after")
    def validate_timestamps(self) -> Self:
        """Reject timestamp order that moves backward."""
        if self.updated_at < self.created_at:
            raise ValueError("updated_at must be greater than or equal to created_at")
        return self

    @classmethod
    def collection_name(cls) -> str:
        """Return the default collection name for this entity."""
        if cls.__collection_name__ is not None:
            return cls.__collection_name__
        return f"{camel_to_snake(cls.__name__)}s"

    def to_document(self) -> StoreDocument:
        """Return the entity as a plain Python document."""
        return self.model_dump(mode="python")

    def prepare_for_insert(
        self,
        *,
        actor: str | None = None,
        at: datetime | None = None,
    ) -> Self:
        """Fill actor fields for a first insert without mutating the entity in place."""
        updates: dict[str, Any] = {}
        if at is not None:
            normalized_at = normalize_datetime(at)
            updates["created_at"] = normalized_at
            updates["updated_at"] = normalized_at
        if actor is not None and self.created_by is None:
            updates["created_by"] = actor
        if actor is not None and self.updated_by is None:
            updates["updated_by"] = actor
        if not updates:
            return self
        return self._validated_copy(**updates)

    def touch(
        self,
        *,
        actor: str | None = None,
        at: datetime | None = None,
    ) -> Self:
        """Return a new entity with updated audit fields and the next version."""
        updated_at = normalize_datetime(at) if at is not None else utc_now()
        updates: dict[str, Any] = {
            "updated_at": updated_at,
            "version": self.version + 1,
        }
        if actor is not None:
            updates["updated_by"] = actor
        return self._validated_copy(**updates)

    def _validated_copy(self, **updates: Any) -> Self:
        """Return a strict validated copy with field updates.

        Args:
            **updates: Field values to merge into the copied entity.

        Returns:
            A validated entity copy.
        """
        entity_data = self.model_dump(mode="python")
        entity_data.update(updates)
        return type(self).model_validate(entity_data, strict=True)


# ========================================
# MOLEQL STORE TIME SERIES ENTITY
# ========================================
class DocPortTimeSeriesEntity(DocPortEntity):
    """Define the common fields for time-series records."""

    time_field_name: ClassVar[str] = DEFAULT_TIME_SERIES_FIELD_NAME

    observed_at: datetime = Field(default_factory=utc_now)

    @field_validator("observed_at")
    @classmethod
    def validate_observed_at(cls, value: datetime) -> datetime:
        """Normalize the time-series timestamp to UTC."""
        return normalize_datetime(value)
