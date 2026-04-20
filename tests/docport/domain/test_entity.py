from datetime import UTC, datetime, timedelta, timezone

import pytest

from docport import DocPortEntity, DocPortTimeSeriesEntity


class User(DocPortEntity):
    name: str


class CpuSample(DocPortTimeSeriesEntity):
    host: str
    cpu: float


class TestDocPortEntity:
    def test_assigns_default_metadata(self) -> None:
        entity = User(name="Ana")

        assert (
            bool(entity.id),
            entity.version,
            entity.created_at.tzinfo,
            entity.updated_at.tzinfo,
        ) == (True, 1, UTC, UTC)

    def test_prepare_for_insert_sets_missing_actor_fields(self) -> None:
        entity = User(name="Ana")

        prepared = entity.prepare_for_insert(actor="identity-service")

        assert (prepared.created_by, prepared.updated_by) == (
            "identity-service",
            "identity-service",
        )

    def test_prepare_for_insert_returns_same_entity_without_changes(self) -> None:
        entity = User(name="Ana", created_by="seed", updated_by="seed")

        assert entity.prepare_for_insert() is entity

    def test_prepare_for_insert_accepts_explicit_timestamp(self) -> None:
        entity = User(name="Ana")
        inserted_at = datetime(2026, 4, 13, 8, 0, tzinfo=UTC)

        prepared = entity.prepare_for_insert(at=inserted_at)

        assert (prepared.created_at, prepared.updated_at) == (inserted_at, inserted_at)

    def test_touch_returns_entity_with_updated_metadata(self) -> None:
        entity = User(
            name="Ana",
            created_at=datetime(2026, 4, 13, 8, 0, tzinfo=UTC),
            updated_at=datetime(2026, 4, 13, 8, 0, tzinfo=UTC),
        )
        touched_at = datetime(2026, 4, 13, 9, 0, tzinfo=UTC)

        touched = entity.touch(actor="store-service", at=touched_at)

        assert (touched.version, touched.updated_by, touched.updated_at) == (
            2,
            "store-service",
            touched_at,
        )

    def test_touch_does_not_mutate_source_entity(self) -> None:
        entity = User(
            name="Ana",
            created_at=datetime(2026, 4, 13, 8, 0, tzinfo=UTC),
            updated_at=datetime(2026, 4, 13, 8, 0, tzinfo=UTC),
        )

        _ = entity.touch(actor="store-service", at=datetime(2026, 4, 13, 9, 0, tzinfo=UTC))

        assert (entity.version, entity.updated_by, entity.updated_at) == (
            1,
            None,
            datetime(2026, 4, 13, 8, 0, tzinfo=UTC),
        )

    def test_collection_name_defaults_to_pluralized_snake_case(self) -> None:
        class SecurityCodeFinding(DocPortEntity):
            finding_id: str

        assert SecurityCodeFinding.collection_name() == "security_code_findings"

    def test_collection_name_can_be_overridden(self) -> None:
        class UserProfile(DocPortEntity):
            __collection_name__ = "profiles"

            display_name: str

        assert UserProfile.collection_name() == "profiles"

    def test_to_document_returns_python_values(self) -> None:
        entity = User(name="Ana")

        document = entity.to_document()

        assert (document["name"], document["id"]) == ("Ana", entity.id)

    def test_rejects_blank_id(self) -> None:
        with pytest.raises(ValueError, match="id must not be blank"):
            User(id=" ", name="Ana")

    def test_rejects_blank_actor(self) -> None:
        with pytest.raises(ValueError, match="actor fields must not be blank"):
            User(name="Ana", created_by=" ")

    def test_rejects_naive_datetime(self) -> None:
        with pytest.raises(ValueError, match="timezone-aware"):
            User(
                name="Ana",
                created_at=datetime(2026, 4, 13, 8, 0),
                updated_at=datetime(2026, 4, 13, 8, 0, tzinfo=UTC),
            )

    def test_rejects_invalid_version(self) -> None:
        with pytest.raises(ValueError, match="version must be greater than or equal to 1"):
            User(name="Ana", version=0)

    def test_rejects_updated_at_before_created_at(self) -> None:
        with pytest.raises(
            ValueError,
            match="updated_at must be greater than or equal to created_at",
        ):
            User(
                name="Ana",
                created_at=datetime(2026, 4, 13, 9, 0, tzinfo=UTC),
                updated_at=datetime(2026, 4, 13, 8, 0, tzinfo=UTC),
            )


class TestDocPortTimeSeriesEntity:
    def test_normalizes_observed_at_to_utc(self) -> None:
        sample = CpuSample(
            host="edge-1",
            cpu=0.42,
            observed_at=datetime(2026, 4, 13, 6, 0, tzinfo=timezone(-timedelta(hours=6))),
        )

        assert (sample.observed_at.tzinfo, sample.time_field_name) == (UTC, "observed_at")
