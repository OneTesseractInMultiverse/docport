"""Define the shared base class used by sync and async store ports."""

from __future__ import annotations

from abc import ABC
from typing import Generic, TypeVar

from docport.domain.entity import DocPortEntity
from docport.domain.errors import StoreConfigurationError

EntityT = TypeVar("EntityT", bound=DocPortEntity)


# ========================================
# STORE PORT
# ========================================
class StorePort(ABC, Generic[EntityT]):
    """Resolve the entity type and collection name for a store."""

    entity_type: type[DocPortEntity] | None = None
    collection_name: str | None = None

    def __init__(
        self,
        *,
        entity_type: type[EntityT] | None = None,
        collection_name: str | None = None,
    ) -> None:
        """Resolve and store the entity type and collection name.

        Args:
            entity_type: Optional explicit entity type for the store instance.
            collection_name: Optional explicit collection name for the store instance.

        Raises:
            StoreConfigurationError: If the store has no entity type.
        """
        self.entity_type: type[EntityT] = entity_type or self._resolve_entity_type()
        self.collection_name = collection_name or self._resolve_collection_name(self.entity_type)

    @classmethod
    def _resolve_entity_type(cls) -> type[EntityT]:
        """Return the configured entity type for the store subclass.

        Returns:
            The entity type bound to the store.

        Raises:
            StoreConfigurationError: If the store has no entity type.
        """
        configured_entity_type = cls.entity_type
        if configured_entity_type is None:
            raise StoreConfigurationError(
                "store subclasses must define entity_type or pass it to the constructor"
            )
        return configured_entity_type  # type: ignore[return-value]

    @classmethod
    def _resolve_collection_name(cls, entity_type: type[EntityT]) -> str:
        """Return the collection name for the store subclass.

        Args:
            entity_type: Entity type bound to the store.

        Returns:
            The explicit collection name or the entity default.
        """
        if cls.collection_name is not None:
            return cls.collection_name
        return entity_type.collection_name()
