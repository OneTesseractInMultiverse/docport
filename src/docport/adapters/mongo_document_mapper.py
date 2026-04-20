"""Convert between DocPort entities, Mongo documents, and projection models."""

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from docport.domain.entity import DocPortEntity
from docport.domain.types import ProjectionDocument, StoreDocument

EntityT = TypeVar("EntityT", bound=DocPortEntity)
ProjectionModelT = TypeVar("ProjectionModelT", bound=BaseModel)


# ========================================
# MONGO DOCUMENT MAPPER
# ========================================
class MongoDocumentMapper(Generic[EntityT]):
    """Convert between DocPort entities and MongoDB documents."""

    def __init__(self, entity_type: type[EntityT]) -> None:
        self.entity_type = entity_type

    def to_document(self, entity: EntityT) -> StoreDocument:
        """Convert an entity into a MongoDB-ready document."""
        return entity.to_document()

    def from_document(self, document: Mapping[str, Any]) -> EntityT:
        """Convert a MongoDB document into a hydrated entity."""
        document_data = self._normalize_bson_dates(dict(document))
        document_data.pop("_id", None)
        return self.entity_type.model_validate(document_data, strict=True)

    def from_documents(self, documents: Iterable[Mapping[str, Any]]) -> list[EntityT]:
        """Convert many MongoDB documents into entities."""
        return [self.from_document(document) for document in documents]

    @staticmethod
    def to_projection_document(document: Mapping[str, Any]) -> ProjectionDocument:
        """Return a detached copy of a projected document."""
        return dict(document)

    @classmethod
    def to_projection_documents(
        cls,
        documents: Iterable[Mapping[str, Any]],
    ) -> list[ProjectionDocument]:
        """Return detached copies of projected documents."""
        return [cls.to_projection_document(document) for document in documents]

    @staticmethod
    def decode_projection(
        projection_type: type[ProjectionModelT],
        document: Mapping[str, Any],
    ) -> ProjectionModelT:
        """Convert a projected document into a typed Pydantic model."""
        document_data = MongoDocumentMapper._normalize_bson_dates(dict(document))
        field_aliases = {
            field_info.alias or field_name
            for field_name, field_info in projection_type.model_fields.items()
        }
        if "_id" not in field_aliases:
            document_data.pop("_id", None)
        return projection_type.model_validate(document_data, strict=True)

    @classmethod
    def decode_projections(
        cls,
        projection_type: type[ProjectionModelT],
        documents: Iterable[Mapping[str, Any]],
    ) -> list[ProjectionModelT]:
        """Convert many projected documents into typed Pydantic models."""
        return [cls.decode_projection(projection_type, document) for document in documents]

    @staticmethod
    def _normalize_bson_dates(value: Any) -> Any:
        """Normalize BSON date values to timezone-aware UTC values.

        Args:
            value: Value loaded from the MongoDB driver.

        Returns:
            A detached value with nested date values normalized to UTC.
        """
        if isinstance(value, datetime):
            if value.tzinfo is None or value.utcoffset() is None:
                return value.replace(tzinfo=UTC)
            return value.astimezone(UTC)
        if isinstance(value, dict):
            return {
                key: MongoDocumentMapper._normalize_bson_dates(item) for key, item in value.items()
            }
        if isinstance(value, list):
            return [MongoDocumentMapper._normalize_bson_dates(item) for item in value]
        return value
