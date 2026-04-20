import mongomock
import pytest
from pydantic import BaseModel, ConfigDict
from pymongo.errors import PyMongoError

from docport import (
    AsyncMongoStore,
    DocPortEntity,
    DuplicateEntityError,
    EntityNotFoundError,
    EntityVersionConflictError,
    FindOptions,
    Projection,
    SortField,
    StoreDependencyError,
    StoreObservation,
    StoreOperationContext,
)


class User(DocPortEntity):
    name: str
    email: str


class UserSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str


class AsyncCursorDouble:
    def __init__(self, cursor) -> None:  # type: ignore[no-untyped-def]
        self._cursor = cursor

    def sort(self, sort_spec):  # type: ignore[no-untyped-def]
        self._cursor = self._cursor.sort(sort_spec)
        return self

    def skip(self, value: int):  # type: ignore[no-untyped-def]
        self._cursor = self._cursor.skip(value)
        return self

    def limit(self, value: int):  # type: ignore[no-untyped-def]
        self._cursor = self._cursor.limit(value)
        return self

    def __aiter__(self):
        return self

    async def __anext__(self):  # type: ignore[no-untyped-def]
        try:
            return next(self._cursor)
        except StopIteration as error:
            raise StopAsyncIteration from error


class AsyncCollectionDouble:
    def __init__(self, collection) -> None:  # type: ignore[no-untyped-def]
        self._collection = collection

    async def insert_one(self, document):  # type: ignore[no-untyped-def]
        return self._collection.insert_one(document)

    async def replace_one(self, filter_data, document):  # type: ignore[no-untyped-def]
        return self._collection.replace_one(filter_data, document)

    async def delete_one(self, filter_data):  # type: ignore[no-untyped-def]
        return self._collection.delete_one(filter_data)

    async def count_documents(self, criteria):  # type: ignore[no-untyped-def]
        return self._collection.count_documents(criteria)

    async def find_one(self, criteria, projection=None):  # type: ignore[no-untyped-def]
        return self._collection.find_one(criteria, projection=projection)

    def find(self, criteria, projection=None):  # type: ignore[no-untyped-def]
        return AsyncCursorDouble(self._collection.find(criteria, projection=projection))


class AsyncDatabaseDouble:
    def __init__(self, database) -> None:  # type: ignore[no-untyped-def]
        self._database = database

    def __getitem__(self, collection_name: str) -> AsyncCollectionDouble:
        return AsyncCollectionDouble(self._database[collection_name])


class UserStore(AsyncMongoStore[User]):
    entity_type = User
    collection_name = "users"


@pytest.fixture
def backing_database():
    return mongomock.MongoClient().get_database("app")


class ObservationCollector:
    def __init__(self) -> None:
        self.records: list[StoreObservation] = []

    def record(self, observation: StoreObservation) -> None:
        self.records.append(observation)


def observation_view(hook: ObservationCollector) -> list[tuple[str, str | None]]:
    return [(record.outcome, record.error_code) for record in hook.records]


def observation_trace(
    hook: ObservationCollector,
) -> list[tuple[str, str, str | None, str | None, str, str]]:
    return [
        (
            record.outcome,
            record.correlation_id,
            record.causation_id,
            record.actor,
            record.action,
            record.target,
        )
        for record in hook.records
    ]


class TestAsyncMongoStore:
    @pytest.mark.asyncio
    async def test_add_returns_stored_entity(self, backing_database) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=AsyncDatabaseDouble(backing_database))
        stored = await store.add(User(id="user-1", name="Ana", email="ana@example.com"))

        assert await store.get("user-1") == stored

    @pytest.mark.asyncio
    async def test_duplicate_id_raises_domain_error(self, backing_database) -> None:  # type: ignore[no-untyped-def]
        backing_database["users"].create_index("id", unique=True)
        store = UserStore(database=AsyncDatabaseDouble(backing_database))
        user = User(id="user-1", name="Ana", email="ana@example.com")

        await store.add(user)

        with pytest.raises(DuplicateEntityError, match="already exists"):
            await store.add(user)

    @pytest.mark.asyncio
    async def test_update_increments_version_and_sets_actor(
        self,
        backing_database,
    ) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=AsyncDatabaseDouble(backing_database))
        original = await store.add(User(id="user-1", name="Ana", email="ana@example.com"))

        updated = await store.update(original, actor="profile-service")

        assert (updated.version, updated.updated_by) == (2, "profile-service")

    @pytest.mark.asyncio
    async def test_update_raises_not_found(self, backing_database) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=AsyncDatabaseDouble(backing_database))

        with pytest.raises(EntityNotFoundError, match="does not exist"):
            await store.update(User(id="user-1", name="Ana", email="ana@example.com"))

    @pytest.mark.asyncio
    async def test_update_raises_version_conflict(
        self,
        backing_database,
    ) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=AsyncDatabaseDouble(backing_database))
        original = await store.add(User(id="user-1", name="Ana", email="ana@example.com"))
        await store.update(original)

        with pytest.raises(EntityVersionConflictError, match="stale version"):
            await store.update(original)

    @pytest.mark.asyncio
    async def test_count_returns_document_total(self, backing_database) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=AsyncDatabaseDouble(backing_database))
        await store.add(User(id="user-1", name="Ana", email="ana@example.com"))

        assert await store.count() == 1

    @pytest.mark.asyncio
    async def test_delete_removes_entity(self, backing_database) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=AsyncDatabaseDouble(backing_database))
        await store.add(User(id="user-1", name="Ana", email="ana@example.com"))

        await store.delete("user-1")

        assert await store.get("user-1") is None

    @pytest.mark.asyncio
    async def test_list_returns_entities(self, backing_database) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=AsyncDatabaseDouble(backing_database))
        await store.add(User(id="user-1", name="Ana", email="ana@example.com"))
        await store.add(User(id="user-2", name="Luz", email="luz@example.com"))

        listed = await store.list()

        assert len(listed) == 2

    @pytest.mark.asyncio
    async def test_find_one_returns_matching_entity(self, backing_database) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=AsyncDatabaseDouble(backing_database))
        await store.add(User(id="user-1", name="Ana", email="ana@example.com"))
        await store.add(User(id="user-2", name="Luz", email="luz@example.com"))

        found = await store.find_one({"email": "luz@example.com"})

        assert found is not None and (found.id, found.name, found.email) == (
            "user-2",
            "Luz",
            "luz@example.com",
        )

    @pytest.mark.asyncio
    async def test_find_applies_sort_skip_and_limit(self, backing_database) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=AsyncDatabaseDouble(backing_database))
        await store.add(User(id="user-1", name="Brisa", email="brisa@example.com"))
        await store.add(User(id="user-2", name="Ana", email="ana@example.com"))

        listed = await store.find(
            options=FindOptions(
                sort=(SortField.ascending("name"),),
                skip=1,
                limit=1,
            )
        )

        assert [user.name for user in listed] == ["Brisa"]

    @pytest.mark.asyncio
    async def test_find_rejects_projection_usage(self, backing_database) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=AsyncDatabaseDouble(backing_database))

        with pytest.raises(ValueError, match="projection is only valid with find_projected"):
            await store.find(options=FindOptions(projection=Projection.include("name")))

    @pytest.mark.asyncio
    async def test_find_projected_requires_projection(
        self,
        backing_database,
    ) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=AsyncDatabaseDouble(backing_database))

        with pytest.raises(ValueError, match="find_projected requires a projection"):
            await store.find_projected(options=FindOptions())

    @pytest.mark.asyncio
    async def test_find_projected_returns_raw_documents(
        self,
        backing_database,
    ) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=AsyncDatabaseDouble(backing_database))
        await store.add(User(id="user-1", name="Ana", email="ana@example.com"))

        projected = await store.find_projected(
            options=FindOptions(projection=Projection.include("name")),
        )

        assert projected == [{"name": "Ana"}]

    @pytest.mark.asyncio
    async def test_find_projected_returns_typed_models(
        self,
        backing_database,
    ) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=AsyncDatabaseDouble(backing_database))
        await store.add(User(id="user-1", name="Ana", email="ana@example.com"))

        projected = await store.find_projected(
            options=FindOptions(projection=Projection.include("name")),
            result_type=UserSummary,
        )

        assert projected == [UserSummary(name="Ana")]

    @pytest.mark.asyncio
    async def test_add_uses_context_actor_when_actor_is_missing(
        self,
        backing_database,
    ) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=AsyncDatabaseDouble(backing_database))
        context = StoreOperationContext.create(
            correlation_id="corr-1",
            causation_id="cause-1",
            actor="worker",
        )

        stored = await store.add(
            User(id="user-1", name="Ana", email="ana@example.com"),
            context=context,
        )

        assert stored.created_by == "worker"

    @pytest.mark.asyncio
    async def test_add_records_observation_events(
        self,
        backing_database,
    ) -> None:  # type: ignore[no-untyped-def]
        hook = ObservationCollector()
        store = UserStore(database=AsyncDatabaseDouble(backing_database), observability_hook=hook)
        context = StoreOperationContext.create(
            correlation_id="corr-1",
            causation_id="cause-1",
            actor="worker",
        )

        await store.add(User(id="user-1", name="Ana", email="ana@example.com"), context=context)

        assert observation_trace(hook) == [
            ("start", "corr-1", "cause-1", "worker", "add", "user-1"),
            ("success", "corr-1", "cause-1", "worker", "add", "user-1"),
        ]

    @pytest.mark.asyncio
    async def test_count_maps_driver_error_to_dependency_error(
        self,
        backing_database,
        monkeypatch,
    ) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=AsyncDatabaseDouble(backing_database))

        async def broken_count_documents(criteria):  # type: ignore[no-untyped-def]
            _ = criteria
            raise PyMongoError("driver failed")

        monkeypatch.setattr(store.collection, "count_documents", broken_count_documents)

        with pytest.raises(StoreDependencyError, match="store dependency failed during count"):
            await store.count(context=StoreOperationContext(correlation_id="corr-2"))

    @pytest.mark.asyncio
    async def test_count_records_dependency_failure_observation(
        self,
        backing_database,
        monkeypatch,
    ) -> None:  # type: ignore[no-untyped-def]
        hook = ObservationCollector()
        store = UserStore(database=AsyncDatabaseDouble(backing_database), observability_hook=hook)

        async def broken_count_documents(criteria):  # type: ignore[no-untyped-def]
            _ = criteria
            raise PyMongoError("driver failed")

        monkeypatch.setattr(store.collection, "count_documents", broken_count_documents)

        with pytest.raises(StoreDependencyError):
            await store.count(context=StoreOperationContext(correlation_id="corr-2"))

        assert observation_view(hook) == [
            ("start", None),
            ("failure", "store_dependency_error"),
        ]
