"""Define public error types for the docport domain contract."""

from typing import ClassVar


# ========================================
# MOLEQL STORE ERROR
# ========================================
class DocPortError(Exception):
    """Define the base public error for docport.

    Args:
        message: Safe error text for callers.

    Attributes:
        error_code: Stable machine code for logs and transport mapping.
    """

    error_code: ClassVar[str] = "docport_error"

    def __init__(self, message: str) -> None:
        """Store the safe public message on the exception instance.

        Args:
            message: Safe error text for callers.
        """
        super().__init__(message)


# ========================================
# DUPLICATE ENTITY ERROR
# ========================================
class DuplicateEntityError(DocPortError):
    """Raise when the backing store rejects a duplicate entity write."""

    error_code = "duplicate_entity"


# ========================================
# ENTITY NOT FOUND ERROR
# ========================================
class EntityNotFoundError(DocPortError):
    """Raise when an entity is missing from the backing store."""

    error_code = "entity_not_found"


# ========================================
# ENTITY VERSION CONFLICT ERROR
# ========================================
class EntityVersionConflictError(DocPortError):
    """Raise when optimistic concurrency detects a stale entity version."""

    error_code = "entity_version_conflict"


# ========================================
# STORE CONFIGURATION ERROR
# ========================================
class StoreConfigurationError(DocPortError):
    """Raise when a store subclass is missing required configuration."""

    error_code = "store_configuration_error"
