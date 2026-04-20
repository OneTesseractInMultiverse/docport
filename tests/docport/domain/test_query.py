import pytest

from docport import FindOptions, Projection, SortField


class TestSortField:
    def test_builds_ascending_pair(self) -> None:
        sort_field = SortField.ascending("created_at")

        assert sort_field.as_pair() == ("created_at", 1)

    def test_builds_descending_pair(self) -> None:
        sort_field = SortField.descending("created_at")

        assert sort_field.as_pair() == ("created_at", -1)

    def test_rejects_blank_field_name(self) -> None:
        with pytest.raises(ValueError, match="sort field must not be blank"):
            SortField(field=" ")

    def test_rejects_invalid_direction(self) -> None:
        with pytest.raises(ValueError, match="sort direction must be 1 or -1"):
            SortField(field="created_at", direction=0)  # type: ignore[arg-type]


class TestProjection:
    def test_include_defaults_to_hiding_mongo_id(self) -> None:
        projection = Projection.include("name", "email")

        assert projection.as_document() == {"name": 1, "email": 1, "_id": 0}

    def test_include_can_keep_mongo_id(self) -> None:
        projection = Projection.include("name", include_id=True)

        assert projection.as_document() == {"name": 1}

    def test_exclude_builds_exclusion_projection(self) -> None:
        projection = Projection.exclude("payload")

        assert projection.as_document() == {"payload": 0}

    def test_from_mapping_copies_the_input(self) -> None:
        source = {"name": 1}
        projection = Projection.from_mapping(source)
        source["email"] = 1

        assert projection.as_document() == {"name": 1}

    def test_rejects_empty_mapping(self) -> None:
        with pytest.raises(ValueError, match="projection must not be empty"):
            Projection.from_mapping({})

    def test_rejects_include_without_fields(self) -> None:
        with pytest.raises(ValueError, match="at least one projection field is required"):
            Projection.include()

    def test_rejects_exclude_without_fields(self) -> None:
        with pytest.raises(ValueError, match="at least one projection field is required"):
            Projection.exclude()


class TestFindOptions:
    def test_defaults_have_no_sort(self) -> None:
        options = FindOptions()

        assert options.sort_pairs() is None

    def test_defaults_have_no_projection(self) -> None:
        options = FindOptions()

        assert options.projection_document() is None

    def test_builds_from_plain_values(self) -> None:
        options = FindOptions.from_values(
            sort=[("updated_at", -1), ("name", 1)],
            skip=10,
            limit=20,
            projection={"name": 1, "_id": 0},
        )

        assert (
            options.sort_pairs(),
            options.skip,
            options.limit,
            options.projection_document(),
        ) == (
            [("updated_at", -1), ("name", 1)],
            10,
            20,
            {"name": 1, "_id": 0},
        )

    def test_with_limit_returns_new_options(self) -> None:
        options = FindOptions(limit=10)

        updated = options.with_limit(1)

        assert updated.limit == 1

    def test_with_limit_keeps_source_options_unchanged(self) -> None:
        options = FindOptions(limit=10)

        _ = options.with_limit(1)

        assert options.limit == 10

    def test_rejects_negative_skip(self) -> None:
        with pytest.raises(ValueError, match="skip must be greater than or equal to 0"):
            FindOptions(skip=-1)

    def test_rejects_negative_limit(self) -> None:
        with pytest.raises(ValueError, match="limit must be greater than or equal to 0"):
            FindOptions(limit=-1)
