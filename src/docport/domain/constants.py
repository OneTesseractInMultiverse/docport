"""Define stable constants shared across the docport domain layer."""

DEFAULT_ENTITY_VERSION: int = 1
DEFAULT_TIME_SERIES_FIELD_NAME: str = "observed_at"

METADATA_FIELD_NAMES: frozenset[str] = frozenset(
    {
        "id",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "version",
    }
)
