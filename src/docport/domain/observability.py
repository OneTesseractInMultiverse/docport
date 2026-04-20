"""Define correlation context and safe telemetry records for store calls."""

from dataclasses import dataclass, field, replace
from typing import Literal, Self
from uuid import uuid4

type ObservationOutcome = Literal["start", "success", "failure"]


# ------------------------------------------------------
# NEW CORRELATION ID
# ------------------------------------------------------
def new_correlation_id() -> str:
    """Return a new correlation identifier.

    Returns:
        A UUID string that can stay stable through one flow.
    """
    return str(uuid4())


# ------------------------------------------------------
# NORMALIZE REQUIRED TEXT
# ------------------------------------------------------
def normalize_required_text(value: str, *, field_name: str) -> str:
    """Strip and validate a required text value.

    Args:
        value: Raw text to validate.
        field_name: Field name used in the error message.

    Returns:
        The stripped text value.

    Raises:
        ValueError: If the text is blank.
    """
    normalized_value = value.strip()
    if not normalized_value:
        raise ValueError(f"{field_name} must not be blank")
    return normalized_value


# ------------------------------------------------------
# NORMALIZE OPTIONAL TEXT
# ------------------------------------------------------
def normalize_optional_text(value: str | None, *, field_name: str) -> str | None:
    """Strip and validate an optional text value.

    Args:
        value: Raw text to validate.
        field_name: Field name used in the error message.

    Returns:
        The stripped text value or ``None``.

    Raises:
        ValueError: If the text is blank.
    """
    if value is None:
        return None
    return normalize_required_text(value, field_name=field_name)


# ========================================
# STORE OPERATION CONTEXT
# ========================================
@dataclass(frozen=True, slots=True)
class StoreOperationContext:
    """Carry stable identifiers and actor data through one store call.

    Attributes:
        correlation_id: Stable identifier for the full flow.
        causation_id: Identifier for the prior event that caused this work.
        actor: Service, system, or user that triggered the call.
    """

    correlation_id: str = field(default_factory=new_correlation_id)
    causation_id: str | None = None
    actor: str | None = None

    def __post_init__(self) -> None:
        """Validate and normalize the context fields.

        Raises:
            ValueError: If any identifier or actor value is blank.
        """
        object.__setattr__(
            self,
            "correlation_id",
            normalize_required_text(self.correlation_id, field_name="correlation_id"),
        )
        object.__setattr__(
            self,
            "causation_id",
            normalize_optional_text(self.causation_id, field_name="causation_id"),
        )
        object.__setattr__(self, "actor", normalize_optional_text(self.actor, field_name="actor"))

    @classmethod
    def create(
        cls,
        *,
        correlation_id: str | None = None,
        causation_id: str | None = None,
        actor: str | None = None,
    ) -> Self:
        """Create a new operation context.

        Args:
            correlation_id: Optional caller-supplied correlation identifier.
            causation_id: Optional identifier for upstream work.
            actor: Optional service, system, or user id.

        Returns:
            A validated operation context.
        """
        return cls(
            correlation_id=correlation_id or new_correlation_id(),
            causation_id=causation_id,
            actor=actor,
        )

    def with_actor(self, actor: str | None) -> Self:
        """Return a copy with a caller-supplied actor when one is present.

        Args:
            actor: Optional service, system, or user id.

        Returns:
            The current context or a copied context with the new actor value.
        """
        if actor is None:
            return self
        return replace(self, actor=actor)


# ========================================
# STORE OBSERVATION
# ========================================
@dataclass(frozen=True, slots=True)
class StoreObservation:
    """Describe one structured store boundary event.

    Attributes:
        correlation_id: Stable identifier for the full flow.
        causation_id: Identifier for the prior event that caused this work.
        actor: Service, system, or user that triggered the call.
        action: Store action name such as ``add`` or ``find``.
        target: Stable target name such as a record id or collection name.
        outcome: Boundary result state.
        error_code: Stable machine code for failures.
        duration_ms: Call duration in milliseconds.
        entity_type: Entity type name for the store.
        collection_name: Collection name for the store.
    """

    correlation_id: str
    causation_id: str | None
    actor: str | None
    action: str
    target: str
    outcome: ObservationOutcome
    error_code: str | None
    duration_ms: int
    entity_type: str
    collection_name: str

    def __post_init__(self) -> None:
        """Validate the observation fields.

        Raises:
            ValueError: If a required text field is blank or timing is negative.
        """
        object.__setattr__(
            self,
            "correlation_id",
            normalize_required_text(self.correlation_id, field_name="correlation_id"),
        )
        object.__setattr__(
            self,
            "causation_id",
            normalize_optional_text(self.causation_id, field_name="causation_id"),
        )
        object.__setattr__(self, "actor", normalize_optional_text(self.actor, field_name="actor"))
        object.__setattr__(
            self,
            "action",
            normalize_required_text(self.action, field_name="action"),
        )
        object.__setattr__(
            self,
            "target",
            normalize_required_text(self.target, field_name="target"),
        )
        object.__setattr__(
            self,
            "error_code",
            normalize_optional_text(self.error_code, field_name="error_code"),
        )
        object.__setattr__(
            self,
            "entity_type",
            normalize_required_text(self.entity_type, field_name="entity_type"),
        )
        object.__setattr__(
            self,
            "collection_name",
            normalize_required_text(self.collection_name, field_name="collection_name"),
        )
        if self.duration_ms < 0:
            raise ValueError("duration_ms must be greater than or equal to 0")

    def as_log_fields(self) -> dict[str, str | int | None]:
        """Return stable field names for structured logs and audit events.

        Returns:
            A detached mapping with stable telemetry field names.
        """
        return {
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "actor": self.actor,
            "action": self.action,
            "target": self.target,
            "outcome": self.outcome,
            "error_code": self.error_code,
            "duration_ms": self.duration_ms,
            "entity_type": self.entity_type,
            "collection_name": self.collection_name,
        }
