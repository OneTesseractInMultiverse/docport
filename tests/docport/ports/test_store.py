from __future__ import annotations

import pytest

from docport import (
    AsyncStore,
    DocPortEntity,
    FindOptions,
    Projection,
    Store,
    StoreConfigurationError,
    StoreOperationContext,
)


class User(DocPortEntity):
    name: str


class ConfiguredStore(Store[User]):
    entity_type = User

    def get(self, entity_id: str, *, context: StoreOperationContext | None = None) -> User | None:
        _ = entity_id
        _ = context
        return None

    def list(
        self,
        options: FindOptions | None = None,
        *,
        context: StoreOperationContext | None = None,
    ) -> list[User]:
        _ = options
        _ = context
        return []

    def add(
        self,
        entity: User,
        *,
        actor: str | None = None,
        context: StoreOperationContext | None = None,
    ) -> User:
        _ = actor
        _ = context
        return entity

    def update(
        self,
        entity: User,
        *,
        actor: str | None = None,
        context: StoreOperationContext | None = None,
    ) -> User:
        _ = actor
        _ = context
        return entity

    def delete(self, entity_id: str, *, context: StoreOperationContext | None = None) -> None:
        _ = entity_id
        _ = context

    def count(
        self,
        criteria=None,
        *,
        context: StoreOperationContext | None = None,
    ) -> int:  # type: ignore[no-untyped-def]
        _ = criteria
        _ = context
        return 0

    def find(
        self,
        criteria=None,
        options: FindOptions | None = None,
        *,
        context: StoreOperationContext | None = None,
    ) -> list[User]:  # type: ignore[no-untyped-def]
        _ = criteria
        _ = options
        _ = context
        return []

    def find_one(
        self,
        criteria,
        options: FindOptions | None = None,
        *,
        context: StoreOperationContext | None = None,
    ) -> User | None:  # type: ignore[no-untyped-def]
        _ = criteria
        _ = options
        _ = context
        return None

    def find_projected(  # type: ignore[no-untyped-def]
        self,
        criteria=None,
        *,
        options: FindOptions,
        context: StoreOperationContext | None = None,
        result_type=None,
    ):
        _ = criteria
        _ = options
        _ = context
        _ = result_type
        return []


class NamedStore(ConfiguredStore):
    collection_name = "people"


class MissingConfigStore(Store[User]):
    def get(self, entity_id: str, *, context: StoreOperationContext | None = None) -> User | None:
        _ = entity_id
        _ = context
        return None

    def list(
        self,
        options: FindOptions | None = None,
        *,
        context: StoreOperationContext | None = None,
    ) -> list[User]:
        _ = options
        _ = context
        return []

    def add(
        self,
        entity: User,
        *,
        actor: str | None = None,
        context: StoreOperationContext | None = None,
    ) -> User:
        _ = actor
        _ = context
        return entity

    def update(
        self,
        entity: User,
        *,
        actor: str | None = None,
        context: StoreOperationContext | None = None,
    ) -> User:
        _ = actor
        _ = context
        return entity

    def delete(self, entity_id: str, *, context: StoreOperationContext | None = None) -> None:
        _ = entity_id
        _ = context

    def count(
        self,
        criteria=None,
        *,
        context: StoreOperationContext | None = None,
    ) -> int:  # type: ignore[no-untyped-def]
        _ = criteria
        _ = context
        return 0

    def find(
        self,
        criteria=None,
        options: FindOptions | None = None,
        *,
        context: StoreOperationContext | None = None,
    ) -> list[User]:  # type: ignore[no-untyped-def]
        _ = criteria
        _ = options
        _ = context
        return []

    def find_one(
        self,
        criteria,
        options: FindOptions | None = None,
        *,
        context: StoreOperationContext | None = None,
    ) -> User | None:  # type: ignore[no-untyped-def]
        _ = criteria
        _ = options
        _ = context
        return None

    def find_projected(  # type: ignore[no-untyped-def]
        self,
        criteria=None,
        *,
        options: FindOptions,
        context: StoreOperationContext | None = None,
        result_type=None,
    ):
        _ = criteria
        _ = options
        _ = context
        _ = result_type
        return []


class ConfiguredAsyncStore(AsyncStore[User]):
    entity_type = User

    async def get(
        self,
        entity_id: str,
        *,
        context: StoreOperationContext | None = None,
    ) -> User | None:
        _ = entity_id
        _ = context
        return None

    async def list(
        self,
        options: FindOptions | None = None,
        *,
        context: StoreOperationContext | None = None,
    ) -> list[User]:
        _ = options
        _ = context
        return []

    async def add(
        self,
        entity: User,
        *,
        actor: str | None = None,
        context: StoreOperationContext | None = None,
    ) -> User:
        _ = actor
        _ = context
        return entity

    async def update(
        self,
        entity: User,
        *,
        actor: str | None = None,
        context: StoreOperationContext | None = None,
    ) -> User:
        _ = actor
        _ = context
        return entity

    async def delete(
        self,
        entity_id: str,
        *,
        context: StoreOperationContext | None = None,
    ) -> None:
        _ = entity_id
        _ = context

    async def count(
        self,
        criteria=None,
        *,
        context: StoreOperationContext | None = None,
    ) -> int:  # type: ignore[no-untyped-def]
        _ = criteria
        _ = context
        return 0

    async def find(
        self,
        criteria=None,
        options: FindOptions | None = None,
        *,
        context: StoreOperationContext | None = None,
    ) -> list[User]:  # type: ignore[no-untyped-def]
        _ = criteria
        _ = options
        _ = context
        return []

    async def find_one(
        self,
        criteria,
        options: FindOptions | None = None,
        *,
        context: StoreOperationContext | None = None,
    ) -> User | None:  # type: ignore[no-untyped-def]
        _ = criteria
        _ = options
        _ = context
        return None

    async def find_projected(  # type: ignore[no-untyped-def]
        self,
        criteria=None,
        *,
        options: FindOptions,
        context: StoreOperationContext | None = None,
        result_type=None,
    ):
        _ = criteria
        _ = options
        _ = context
        _ = result_type
        return []


class TestStorePortConfiguration:
    def test_sync_store_resolves_entity_type_and_collection_name(self) -> None:
        store = ConfiguredStore()

        assert (store.entity_type, store.collection_name) == (User, "users")

    def test_sync_store_respects_explicit_collection_name(self) -> None:
        store = NamedStore()

        assert store.collection_name == "people"

    def test_sync_store_raises_for_missing_entity_configuration(self) -> None:
        with pytest.raises(StoreConfigurationError, match="define entity_type"):
            MissingConfigStore()

    def test_async_store_resolves_entity_type_and_collection_name(self) -> None:
        store = ConfiguredAsyncStore()

        assert (store.entity_type, store.collection_name) == (User, "users")

    def test_projection_type_is_available_in_store_signature(self) -> None:
        store = ConfiguredStore()
        options = FindOptions(projection=Projection.include("name"))

        assert store.find_projected(options=options) == []
