"""Define the asyncio-native store port for persisted document entities."""

from __future__ import annotations

import builtins
from abc import abstractmethod
from typing import Generic, TypeVar, overload

from pydantic import BaseModel

from docport.domain.observability import StoreOperationContext
from docport.domain.query import FindOptions
from docport.domain.types import DocumentId, ProjectionDocument, StoreFilter
from docport.ports.base import EntityT, StorePort

ProjectionModelT = TypeVar("ProjectionModelT", bound=BaseModel)


# ========================================
# ASYNC STORE
# ========================================
class AsyncStore(StorePort[EntityT], Generic[EntityT]):
    """Define the asyncio-native repository port for persisted document entities."""

    @abstractmethod
    async def get(
        self,
        entity_id: DocumentId,
        *,
        context: StoreOperationContext | None = None,
    ) -> EntityT | None:
        """Return an entity by its cross-system id."""

    @abstractmethod
    async def list(
        self,
        options: FindOptions | None = None,
        *,
        context: StoreOperationContext | None = None,
    ) -> builtins.list[EntityT]:
        """Return entities from the configured collection."""

    @abstractmethod
    async def add(
        self,
        entity: EntityT,
        *,
        actor: str | None = None,
        context: StoreOperationContext | None = None,
    ) -> EntityT:
        """Persist a new entity."""

    @abstractmethod
    async def update(
        self,
        entity: EntityT,
        *,
        actor: str | None = None,
        context: StoreOperationContext | None = None,
    ) -> EntityT:
        """Persist a full entity replacement with optimistic concurrency."""

    @abstractmethod
    async def delete(
        self,
        entity_id: DocumentId,
        *,
        context: StoreOperationContext | None = None,
    ) -> None:
        """Delete one entity by id."""

    @abstractmethod
    async def count(
        self,
        criteria: StoreFilter | None = None,
        *,
        context: StoreOperationContext | None = None,
    ) -> int:
        """Return a document count for the given criteria."""

    @abstractmethod
    async def find(
        self,
        criteria: StoreFilter | None = None,
        options: FindOptions | None = None,
        *,
        context: StoreOperationContext | None = None,
    ) -> builtins.list[EntityT]:
        """Return fully hydrated entities that match the given criteria."""

    @abstractmethod
    async def find_one(
        self,
        criteria: StoreFilter,
        options: FindOptions | None = None,
        *,
        context: StoreOperationContext | None = None,
    ) -> EntityT | None:
        """Return the first hydrated entity that matches the given criteria."""

    @overload
    async def find_projected(
        self,
        criteria: StoreFilter | None = None,
        *,
        options: FindOptions,
        context: StoreOperationContext | None = None,
        result_type: None = None,
    ) -> builtins.list[ProjectionDocument]: ...

    @overload
    async def find_projected(
        self,
        criteria: StoreFilter | None = None,
        *,
        options: FindOptions,
        context: StoreOperationContext | None = None,
        result_type: type[ProjectionModelT],
    ) -> builtins.list[ProjectionModelT]: ...

    @abstractmethod
    async def find_projected(
        self,
        criteria: StoreFilter | None = None,
        *,
        options: FindOptions,
        context: StoreOperationContext | None = None,
        result_type: type[ProjectionModelT] | None = None,
    ) -> builtins.list[ProjectionDocument] | builtins.list[ProjectionModelT]:
        """Return partial documents or typed projection models."""
