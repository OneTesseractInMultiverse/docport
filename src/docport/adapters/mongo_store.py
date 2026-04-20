"""Implement the sync MongoDB store adapter with safe errors and telemetry hooks."""

from __future__ import annotations

import builtins
from collections.abc import Callable, Mapping
from time import perf_counter
from typing import Any, Generic, TypeVar, cast, overload

from pydantic import BaseModel
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError, PyMongoError

from docport.adapters.errors import StoreDependencyError
from docport.adapters.mongo_document_mapper import MongoDocumentMapper
from docport.domain.entity import DocPortEntity
from docport.domain.errors import (
    DocPortError,
    DuplicateEntityError,
    EntityNotFoundError,
    EntityVersionConflictError,
)
from docport.domain.observability import (
    ObservationOutcome,
    StoreObservation,
    StoreOperationContext,
)
from docport.domain.query import FindOptions
from docport.domain.types import ProjectionDocument, StoreFilter
from docport.ports.observability import NoOpStoreObservabilityHook, StoreObservabilityHook
from docport.ports.store import Store

EntityT = TypeVar("EntityT", bound=DocPortEntity)
ProjectionModelT = TypeVar("ProjectionModelT", bound=BaseModel)
ResultT = TypeVar("ResultT")


# ========================================
# MONGO STORE
# ========================================
class MongoStore(Store[EntityT], Generic[EntityT]):
    """Implement the sync store port with PyMongo.

    Args:
        database: PyMongo database instance passed in by the caller.
        entity_type: Optional explicit entity type for the store instance.
        collection_name: Optional explicit collection name for the store instance.
        mapper: Optional document mapper override.
        observability_hook: Optional hook for structured store observations.
    """

    def __init__(
        self,
        database: Database,
        *,
        entity_type: type[EntityT] | None = None,
        collection_name: str | None = None,
        mapper: MongoDocumentMapper[EntityT] | None = None,
        observability_hook: StoreObservabilityHook | None = None,
    ) -> None:
        super().__init__(entity_type=entity_type, collection_name=collection_name)
        self._entity_type = cast(type[EntityT], self.entity_type)
        self._collection_name = cast(str, self.collection_name)
        self.database = database
        self.collection: Collection = self.database[self._collection_name]
        self.mapper = mapper or MongoDocumentMapper(self._entity_type)
        self.observability_hook = observability_hook or NoOpStoreObservabilityHook()

    def get(
        self,
        entity_id: str,
        *,
        context: StoreOperationContext | None = None,
    ) -> EntityT | None:
        """Return one entity by id.

        Args:
            entity_id: Cross-system entity identifier.
            context: Optional correlation and actor data for the call.

        Returns:
            The matching entity or ``None``.
        """
        resolved_context = self._resolve_context(context=context)
        return self._execute_operation(
            action="get",
            target=entity_id,
            context=resolved_context,
            operation=lambda: self._find_one_internal({"id": entity_id}, options=None),
        )

    def list(
        self,
        options: FindOptions | None = None,
        *,
        context: StoreOperationContext | None = None,
    ) -> builtins.list[EntityT]:
        """Return entities from the configured collection.

        Args:
            options: Optional paging and sort data.
            context: Optional correlation and actor data for the call.

        Returns:
            Hydrated entities from the store.
        """
        resolved_context = self._resolve_context(context=context)
        return self._execute_operation(
            action="list",
            target=self._collection_name,
            context=resolved_context,
            operation=lambda: self._find_internal(criteria={}, options=options),
        )

    def add(
        self,
        entity: EntityT,
        *,
        actor: str | None = None,
        context: StoreOperationContext | None = None,
    ) -> EntityT:
        """Insert one entity into MongoDB.

        Args:
            entity: Entity to persist.
            actor: Optional service, system, or user id for audit fields.
            context: Optional correlation and actor data for the call.

        Returns:
            The stored entity value.

        Raises:
            DuplicateEntityError: If the entity id already exists.
            StoreDependencyError: If the MongoDB driver fails.
        """
        resolved_context = self._resolve_context(context=context, actor=actor)
        return self._execute_operation(
            action="add",
            target=entity.id,
            context=resolved_context,
            operation=lambda: self._add_internal(entity, actor=resolved_context.actor),
        )

    def update(
        self,
        entity: EntityT,
        *,
        actor: str | None = None,
        context: StoreOperationContext | None = None,
    ) -> EntityT:
        """Replace one entity by id and version.

        Args:
            entity: Entity to persist.
            actor: Optional service, system, or user id for audit fields.
            context: Optional correlation and actor data for the call.

        Returns:
            The stored entity value with the new version.

        Raises:
            EntityNotFoundError: If the entity no longer exists.
            EntityVersionConflictError: If the entity version is stale.
            StoreDependencyError: If the MongoDB driver fails.
        """
        resolved_context = self._resolve_context(context=context, actor=actor)
        return self._execute_operation(
            action="update",
            target=entity.id,
            context=resolved_context,
            operation=lambda: self._update_internal(entity, actor=resolved_context.actor),
        )

    def delete(
        self,
        entity_id: str,
        *,
        context: StoreOperationContext | None = None,
    ) -> None:
        """Delete one entity by id.

        Args:
            entity_id: Cross-system entity identifier.
            context: Optional correlation and actor data for the call.
        """
        resolved_context = self._resolve_context(context=context)
        self._execute_operation(
            action="delete",
            target=entity_id,
            context=resolved_context,
            operation=lambda: self._delete_internal(entity_id),
        )

    def count(
        self,
        criteria: StoreFilter | None = None,
        *,
        context: StoreOperationContext | None = None,
    ) -> int:
        """Return a count for the given criteria.

        Args:
            criteria: Optional MongoDB-style filter document.
            context: Optional correlation and actor data for the call.

        Returns:
            Number of matching documents.
        """
        resolved_context = self._resolve_context(context=context)
        return self._execute_operation(
            action="count",
            target=self._collection_name,
            context=resolved_context,
            operation=lambda: self._count_internal(criteria),
        )

    def find(
        self,
        criteria: StoreFilter | None = None,
        options: FindOptions | None = None,
        *,
        context: StoreOperationContext | None = None,
    ) -> builtins.list[EntityT]:
        """Return hydrated entities for the given criteria.

        Args:
            criteria: Optional MongoDB-style filter document.
            options: Optional paging and sort data.
            context: Optional correlation and actor data for the call.

        Returns:
            Hydrated entities from the store.
        """
        resolved_context = self._resolve_context(context=context)
        return self._execute_operation(
            action="find",
            target=self._collection_name,
            context=resolved_context,
            operation=lambda: self._find_internal(criteria=criteria, options=options),
        )

    def find_one(
        self,
        criteria: StoreFilter,
        options: FindOptions | None = None,
        *,
        context: StoreOperationContext | None = None,
    ) -> EntityT | None:
        """Return the first hydrated entity for the given criteria.

        Args:
            criteria: MongoDB-style filter document.
            options: Optional paging and sort data.
            context: Optional correlation and actor data for the call.

        Returns:
            The first hydrated entity or ``None``.
        """
        resolved_context = self._resolve_context(context=context)
        return self._execute_operation(
            action="find_one",
            target=self._collection_name,
            context=resolved_context,
            operation=lambda: self._find_one_internal(criteria, options=options),
        )

    @overload
    def find_projected(
        self,
        criteria: StoreFilter | None = None,
        *,
        options: FindOptions,
        context: StoreOperationContext | None = None,
        result_type: None = None,
    ) -> builtins.list[ProjectionDocument]: ...

    @overload
    def find_projected(
        self,
        criteria: StoreFilter | None = None,
        *,
        options: FindOptions,
        context: StoreOperationContext | None = None,
        result_type: type[ProjectionModelT],
    ) -> builtins.list[ProjectionModelT]: ...

    def find_projected(
        self,
        criteria: StoreFilter | None = None,
        *,
        options: FindOptions,
        context: StoreOperationContext | None = None,
        result_type: type[ProjectionModelT] | None = None,
    ) -> builtins.list[ProjectionDocument] | builtins.list[ProjectionModelT]:
        """Return projected documents or typed projection models.

        Args:
            criteria: Optional MongoDB-style filter document.
            options: Projection, paging, and sort data.
            context: Optional correlation and actor data for the call.
            result_type: Optional Pydantic model for typed projection rows.

        Returns:
            Detached projection dictionaries or typed projection models.
        """
        resolved_context = self._resolve_context(context=context)
        return self._execute_operation(
            action="find_projected",
            target=self._collection_name,
            context=resolved_context,
            operation=lambda: self._find_projected_internal(
                criteria=criteria,
                options=options,
                result_type=result_type,
            ),
        )

    def _add_internal(self, entity: EntityT, *, actor: str | None) -> EntityT:
        """Insert one prepared entity without boundary telemetry.

        Args:
            entity: Entity to persist.
            actor: Optional actor for audit fields.

        Returns:
            The stored entity value.

        Raises:
            DuplicateEntityError: If the entity id already exists.
        """
        entity_to_insert = entity.prepare_for_insert(actor=actor)
        try:
            self.collection.insert_one(self.mapper.to_document(entity_to_insert))
        except DuplicateKeyError as error:
            error_message = f"entity with id '{entity_to_insert.id}' already exists"
            raise DuplicateEntityError(error_message) from error
        return entity_to_insert

    def _update_internal(self, entity: EntityT, *, actor: str | None) -> EntityT:
        """Replace one entity without boundary telemetry.

        Args:
            entity: Entity to persist.
            actor: Optional actor for audit fields.

        Returns:
            The stored entity value with the new version.

        Raises:
            EntityNotFoundError: If the entity no longer exists.
            EntityVersionConflictError: If the entity version is stale.
        """
        entity_to_store = entity.touch(actor=actor)
        result = self.collection.replace_one(
            {"id": entity.id, "version": entity.version},
            self.mapper.to_document(entity_to_store),
        )
        if result.matched_count == 0:
            self._raise_update_error(entity.id)
        return entity_to_store

    def _delete_internal(self, entity_id: str) -> None:
        """Delete one entity without boundary telemetry.

        Args:
            entity_id: Cross-system entity identifier.
        """
        self.collection.delete_one({"id": entity_id})

    def _count_internal(self, criteria: StoreFilter | None = None) -> int:
        """Return a count without boundary telemetry.

        Args:
            criteria: Optional MongoDB-style filter document.

        Returns:
            Number of matching documents.
        """
        return self.collection.count_documents(dict(criteria or {}))

    def _find_internal(
        self,
        *,
        criteria: StoreFilter | None,
        options: FindOptions | None,
    ) -> builtins.list[EntityT]:
        """Return hydrated entities without boundary telemetry.

        Args:
            criteria: Optional MongoDB-style filter document.
            options: Optional paging and sort data.

        Returns:
            Hydrated entities from the store.
        """
        documents = self._find_documents(
            criteria=criteria,
            options=options,
            require_projection=False,
        )
        return self.mapper.from_documents(documents)

    def _find_one_internal(
        self,
        criteria: StoreFilter,
        options: FindOptions | None,
    ) -> EntityT | None:
        """Return one hydrated entity without boundary telemetry.

        Args:
            criteria: MongoDB-style filter document.
            options: Optional paging and sort data.

        Returns:
            The first hydrated entity or ``None``.
        """
        query_options = options.with_limit(1) if options is not None else FindOptions(limit=1)
        results = self._find_internal(criteria=criteria, options=query_options)
        return results[0] if results else None

    @overload
    def _find_projected_internal(
        self,
        *,
        criteria: StoreFilter | None,
        options: FindOptions,
        result_type: None,
    ) -> builtins.list[ProjectionDocument]: ...

    @overload
    def _find_projected_internal(
        self,
        *,
        criteria: StoreFilter | None,
        options: FindOptions,
        result_type: type[ProjectionModelT],
    ) -> builtins.list[ProjectionModelT]: ...

    def _find_projected_internal(
        self,
        *,
        criteria: StoreFilter | None,
        options: FindOptions,
        result_type: type[ProjectionModelT] | None,
    ) -> builtins.list[ProjectionDocument] | builtins.list[ProjectionModelT]:
        """Return projected data without boundary telemetry.

        Args:
            criteria: Optional MongoDB-style filter document.
            options: Projection, paging, and sort data.
            result_type: Optional Pydantic model for typed projection rows.

        Returns:
            Detached projection dictionaries or typed projection models.
        """
        documents = self._find_documents(
            criteria=criteria,
            options=options,
            require_projection=True,
        )
        if result_type is None:
            return self.mapper.to_projection_documents(documents)
        return self.mapper.decode_projections(result_type, documents)

    def _find_documents(
        self,
        *,
        criteria: Mapping[str, Any] | None,
        options: FindOptions | None,
        require_projection: bool,
    ) -> builtins.list[dict[str, Any]]:
        """Return detached Mongo documents from a query.

        Args:
            criteria: Optional MongoDB-style filter document.
            options: Optional paging, sort, and projection data.
            require_projection: Flag that enforces projection use for the call.

        Returns:
            Detached Mongo documents.

        Raises:
            ValueError: If projection rules are violated.
        """
        self._validate_projection_usage(options=options, require_projection=require_projection)
        projection = options.projection_document() if options is not None else None
        cursor = self.collection.find(dict(criteria or {}), projection=projection)
        if options is not None:
            sort_pairs = options.sort_pairs()
            if sort_pairs is not None:
                cursor = cursor.sort(sort_pairs)
            if options.skip:
                cursor = cursor.skip(options.skip)
            if options.limit:
                cursor = cursor.limit(options.limit)
        return [dict(document) for document in cursor]

    def _raise_update_error(self, entity_id: str) -> None:
        """Raise the domain error that explains a failed replacement match.

        Args:
            entity_id: Cross-system entity identifier.

        Raises:
            EntityNotFoundError: If the entity no longer exists.
            EntityVersionConflictError: If the entity version is stale.
        """
        existing_document = self.collection.find_one({"id": entity_id}, projection={"version": 1})
        if existing_document is None:
            error_message = f"entity with id '{entity_id}' does not exist"
            raise EntityNotFoundError(error_message)
        current_version = existing_document["version"]
        error_message = (
            f"entity with id '{entity_id}' has a stale version and the current version is "
            f"'{current_version}'"
        )
        raise EntityVersionConflictError(error_message)

    def _execute_operation(
        self,
        *,
        action: str,
        target: str,
        context: StoreOperationContext,
        operation: Callable[[], ResultT],
    ) -> ResultT:
        """Run one store boundary operation with safe telemetry and error mapping.

        Args:
            action: Store action name.
            target: Stable target name such as a record id or collection name.
            context: Correlation and actor data for the call.
            operation: Internal store computation to run.

        Returns:
            The operation result.

        Raises:
            DocPortError: Domain or infrastructure error from the store boundary.
        """
        started_at = perf_counter()
        self._record_observation(
            action=action,
            target=target,
            context=context,
            outcome="start",
            duration_ms=0,
            error_code=None,
        )
        try:
            result = operation()
        except DocPortError as error:
            self._record_observation(
                action=action,
                target=target,
                context=context,
                outcome="failure",
                duration_ms=self._duration_ms(started_at),
                error_code=error.error_code,
            )
            raise
        except PyMongoError as error:
            dependency_error = StoreDependencyError(f"store dependency failed during {action}")
            self._record_observation(
                action=action,
                target=target,
                context=context,
                outcome="failure",
                duration_ms=self._duration_ms(started_at),
                error_code=dependency_error.error_code,
            )
            raise dependency_error from error
        except Exception:
            self._record_observation(
                action=action,
                target=target,
                context=context,
                outcome="failure",
                duration_ms=self._duration_ms(started_at),
                error_code="unexpected_error",
            )
            raise
        self._record_observation(
            action=action,
            target=target,
            context=context,
            outcome="success",
            duration_ms=self._duration_ms(started_at),
            error_code=None,
        )
        return result

    def _record_observation(
        self,
        *,
        action: str,
        target: str,
        context: StoreOperationContext,
        outcome: ObservationOutcome,
        duration_ms: int,
        error_code: str | None,
    ) -> None:
        """Emit one structured store observation through the configured hook.

        Args:
            action: Store action name.
            target: Stable target name such as a record id or collection name.
            context: Correlation and actor data for the call.
            outcome: Boundary result state.
            duration_ms: Call duration in milliseconds.
            error_code: Stable machine code for failures.
        """
        observation = StoreObservation(
            correlation_id=context.correlation_id,
            causation_id=context.causation_id,
            actor=context.actor,
            action=action,
            target=target,
            outcome=outcome,
            error_code=error_code,
            duration_ms=duration_ms,
            entity_type=self._entity_type.__name__,
            collection_name=self._collection_name,
        )
        self.observability_hook.record(observation)

    @staticmethod
    def _duration_ms(started_at: float) -> int:
        """Return elapsed time in milliseconds.

        Args:
            started_at: Start time captured from ``perf_counter``.

        Returns:
            Elapsed milliseconds rounded down to an integer.
        """
        return int((perf_counter() - started_at) * 1000)

    @staticmethod
    def _resolve_context(
        *,
        context: StoreOperationContext | None,
        actor: str | None = None,
    ) -> StoreOperationContext:
        """Return the context used for one public store call.

        Args:
            context: Optional caller-supplied operation context.
            actor: Optional service, system, or user id for audit fields.

        Returns:
            A validated operation context with a stable correlation id.
        """
        resolved_context = context or StoreOperationContext.create()
        return resolved_context.with_actor(actor)

    @staticmethod
    def _validate_projection_usage(
        *,
        options: FindOptions | None,
        require_projection: bool,
    ) -> None:
        """Enforce the public split between full entities and projected reads.

        Args:
            options: Optional paging, sort, and projection data.
            require_projection: Flag that enforces projection use for the call.

        Raises:
            ValueError: If projection rules are violated.
        """
        has_projection = options is not None and options.projection is not None
        if require_projection and not has_projection:
            raise ValueError("find_projected requires a projection")
        if not require_projection and has_projection:
            raise ValueError("projection is only valid with find_projected")
