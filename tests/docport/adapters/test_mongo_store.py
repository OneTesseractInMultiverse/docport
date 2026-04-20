from datetime import UTC, datetime

import mongomock
import pytest
from pydantic import BaseModel, ConfigDict
from pymongo.errors import PyMongoError

from docport import (
    DocPortEntity,
    DuplicateEntityError,
    EntityNotFoundError,
    EntityVersionConflictError,
    FindOptions,
    MongoStore,
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
    email: str


class UserStore(MongoStore[User]):
    entity_type = User
    collection_name = "users"

    def get_by_email(self, email: str) -> User | None:
        return self.find_one({"email": email})


@pytest.fixture
def database():
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


class TestMongoStore:
    def test_add_sets_missing_actor_fields(self, database) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=database)

        stored = store.add(
            User(id="user-1", name="Ana", email="ana@example.com"),
            actor="identity-service",
        )

        assert (stored.created_by, stored.updated_by) == (
            "identity-service",
            "identity-service",
        )

    def test_get_returns_stored_entity(self, database) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=database)
        stored = store.add(User(id="user-1", name="Ana", email="ana@example.com"))

        assert store.get("user-1") == stored

    def test_duplicate_id_raises_domain_error(self, database) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=database)
        store.collection.create_index("id", unique=True)
        user = User(id="user-1", name="Ana", email="ana@example.com")

        store.add(user)

        with pytest.raises(DuplicateEntityError, match="already exists"):
            store.add(user)

    def test_list_applies_find_options(self, database) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=database)
        store.add(User(id="user-1", name="Brisa", email="brisa@example.com"))
        store.add(User(id="user-2", name="Ana", email="ana@example.com"))

        results = store.list(
            FindOptions(
                sort=(SortField.ascending("name"),),
                skip=1,
                limit=1,
            )
        )

        assert [user.name for user in results] == ["Brisa"]

    def test_count_returns_matching_document_total(self, database) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=database)
        store.add(User(id="user-1", name="Brisa", email="brisa@example.com"))
        store.add(User(id="user-2", name="Ana", email="ana@example.com"))

        assert store.count({"name": {"$in": ["Ana", "Brisa"]}}) == 2

    def test_find_one_returns_none_when_missing(self, database) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=database)

        assert store.find_one({"email": "missing@example.com"}) is None

    def test_find_one_respects_sort(self, database) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=database)
        store.add(
            User(
                id="user-1",
                name="Ana",
                email="ana-older@example.com",
                created_at=datetime(2026, 4, 13, 8, 0, tzinfo=UTC),
                updated_at=datetime(2026, 4, 13, 8, 0, tzinfo=UTC),
            )
        )
        store.add(
            User(
                id="user-2",
                name="Ana",
                email="ana-newer@example.com",
                created_at=datetime(2026, 4, 13, 9, 0, tzinfo=UTC),
                updated_at=datetime(2026, 4, 13, 9, 0, tzinfo=UTC),
            )
        )

        found = store.find_one(
            {"name": "Ana"},
            options=FindOptions(sort=(SortField.descending("created_at"),)),
        )

        assert found == store.get_by_email("ana-newer@example.com")

    def test_update_increments_version_and_sets_actor(
        self,
        database,
    ) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=database)
        original = store.add(User(id="user-1", name="Ana", email="ana@example.com"))

        updated = store.update(original, actor="profile-service")

        assert (updated.version, updated.updated_by) == (2, "profile-service")

    def test_update_persists_replacement(self, database) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=database)
        original = store.add(User(id="user-1", name="Ana", email="ana@example.com"))

        updated = store.update(original, actor="profile-service")

        assert store.get("user-1") == updated

    def test_update_raises_not_found_for_missing_entity(
        self,
        database,
    ) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=database)

        with pytest.raises(EntityNotFoundError, match="does not exist"):
            store.update(User(id="user-1", name="Ana", email="ana@example.com"))

    def test_update_raises_version_conflict_for_stale_entity(
        self,
        database,
    ) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=database)
        original = store.add(User(id="user-1", name="Ana", email="ana@example.com"))
        store.update(original)

        with pytest.raises(EntityVersionConflictError, match="stale version"):
            store.update(original)

    def test_delete_removes_entity(self, database) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=database)
        store.add(User(id="user-1", name="Ana", email="ana@example.com"))

        store.delete("user-1")

        assert store.get("user-1") is None

    def test_find_accepts_empty_find_options(self, database) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=database)
        stored = store.add(User(id="user-1", name="Ana", email="ana@example.com"))

        assert store.find() == [stored]
        assert store.find(options=FindOptions()) == [stored]

    def test_find_rejects_projection_usage(self, database) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=database)

        with pytest.raises(ValueError, match="projection is only valid with find_projected"):
            store.find(options=FindOptions(projection=Projection.include("name")))

    def test_find_projected_requires_projection(self, database) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=database)

        with pytest.raises(ValueError, match="find_projected requires a projection"):
            store.find_projected(options=FindOptions())

    def test_find_projected_returns_raw_documents(self, database) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=database)
        store.add(User(id="user-1", name="Ana", email="ana@example.com"))

        projected = store.find_projected(options=FindOptions(projection=Projection.include("name")))

        assert projected == [{"name": "Ana"}]

    def test_find_projected_returns_typed_projection_models(
        self,
        database,
    ) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=database)
        store.add(User(id="user-1", name="Ana", email="ana@example.com"))

        projected = store.find_projected(
            options=FindOptions(projection=Projection.include("name", "email")),
            result_type=UserSummary,
        )

        assert projected == [UserSummary(name="Ana", email="ana@example.com")]

    def test_add_uses_context_actor_when_actor_is_missing(
        self,
        database,
    ) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=database)
        context = StoreOperationContext.create(
            correlation_id="corr-1",
            causation_id="cause-1",
            actor="api-gateway",
        )

        stored = store.add(User(id="user-1", name="Ana", email="ana@example.com"), context=context)

        assert stored.created_by == "api-gateway"

    def test_add_records_observation_events(self, database) -> None:  # type: ignore[no-untyped-def]
        hook = ObservationCollector()
        store = UserStore(database=database, observability_hook=hook)
        context = StoreOperationContext.create(
            correlation_id="corr-1",
            causation_id="cause-1",
            actor="api-gateway",
        )

        store.add(User(id="user-1", name="Ana", email="ana@example.com"), context=context)

        assert observation_trace(hook) == [
            ("start", "corr-1", "cause-1", "api-gateway", "add", "user-1"),
            ("success", "corr-1", "cause-1", "api-gateway", "add", "user-1"),
        ]

    def test_count_maps_driver_error_to_dependency_error(
        self,
        database,
        monkeypatch,
    ) -> None:  # type: ignore[no-untyped-def]
        store = UserStore(database=database)

        def broken_count_documents(criteria):  # type: ignore[no-untyped-def]
            _ = criteria
            raise PyMongoError("driver failed")

        monkeypatch.setattr(store.collection, "count_documents", broken_count_documents)

        with pytest.raises(StoreDependencyError, match="store dependency failed during count"):
            store.count(context=StoreOperationContext(correlation_id="corr-2"))

    def test_count_records_dependency_failure_observation(
        self,
        database,
        monkeypatch,
    ) -> None:  # type: ignore[no-untyped-def]
        hook = ObservationCollector()
        store = UserStore(database=database, observability_hook=hook)

        def broken_count_documents(criteria):  # type: ignore[no-untyped-def]
            _ = criteria
            raise PyMongoError("driver failed")

        monkeypatch.setattr(store.collection, "count_documents", broken_count_documents)

        with pytest.raises(StoreDependencyError):
            store.count(context=StoreOperationContext(correlation_id="corr-2"))

        assert observation_view(hook) == [
            ("start", None),
            ("failure", "store_dependency_error"),
        ]
