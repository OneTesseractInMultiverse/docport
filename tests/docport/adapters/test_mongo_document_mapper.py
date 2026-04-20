from datetime import UTC, datetime, timedelta, timezone

from pydantic import BaseModel, ConfigDict, Field

from docport import DocPortEntity, MongoDocumentMapper


class User(DocPortEntity):
    name: str
    email: str


class Timeline(DocPortEntity):
    events: list[datetime]


class UserSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    email: str


class ProjectionWithMongoId(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    mongo_id: str = Field(alias="_id")


class TimedProjection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observed_at: datetime


class TestMongoDocumentMapper:
    def test_round_trips_entity_documents(self) -> None:
        mapper = MongoDocumentMapper(User)
        entity = User(id="user-1", name="Ana", email="ana@example.com")
        document = mapper.to_document(entity) | {"_id": "mongo-1"}

        hydrated = mapper.from_document(document)

        assert hydrated == entity

    def test_returns_detached_projection_documents(self) -> None:
        projection = {"name": "Ana"}

        detached = MongoDocumentMapper[User].to_projection_document(projection)
        projection["name"] = "Luz"

        assert detached == {"name": "Ana"}

    def test_decodes_projection_models_and_hides_internal_id_by_default(self) -> None:
        decoded = MongoDocumentMapper[User].decode_projection(
            UserSummary,
            {"_id": "mongo-1", "name": "Ana", "email": "ana@example.com"},
        )

        assert decoded == UserSummary(name="Ana", email="ana@example.com")

    def test_keeps_internal_id_when_projection_model_uses_alias(self) -> None:
        decoded = MongoDocumentMapper[User].decode_projection(
            ProjectionWithMongoId,
            {"_id": "mongo-1"},
        )

        assert decoded.mongo_id == "mongo-1"

    def test_decodes_many_projection_models(self) -> None:
        decoded = MongoDocumentMapper[User].decode_projections(
            UserSummary,
            [
                {"name": "Ana", "email": "ana@example.com"},
                {"name": "Luz", "email": "luz@example.com"},
            ],
        )

        assert decoded == [
            UserSummary(name="Ana", email="ana@example.com"),
            UserSummary(name="Luz", email="luz@example.com"),
        ]

    def test_normalizes_bson_dates_for_entities_and_nested_lists(self) -> None:
        mapper = MongoDocumentMapper(Timeline)

        decoded = mapper.from_document(
            {
                "_id": "mongo-1",
                "id": "timeline-1",
                "events": [datetime(2026, 4, 13, 8, 0)],
                "created_at": datetime(2026, 4, 13, 8, 0),
                "updated_at": datetime(2026, 4, 13, 8, 0),
            }
        )

        assert (decoded.created_at.tzinfo, decoded.events[0].tzinfo) == (UTC, UTC)

    def test_normalizes_aware_projection_datetimes_to_utc(self) -> None:
        decoded = MongoDocumentMapper[User].decode_projection(
            TimedProjection,
            {
                "observed_at": datetime(
                    2026,
                    4,
                    13,
                    8,
                    0,
                    tzinfo=timezone(-timedelta(hours=6)),
                )
            },
        )

        assert decoded.observed_at.tzinfo == UTC
