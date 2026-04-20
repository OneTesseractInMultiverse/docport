"""Define an opt-in hook for store boundary observations."""

from typing import Protocol

from docport.domain.observability import StoreObservation


# ========================================
# STORE OBSERVABILITY HOOK
# ========================================
class StoreObservabilityHook(Protocol):
    """Receive one structured store observation at a boundary point."""

    def record(self, observation: StoreObservation) -> None:
        """Handle one store observation.

        Args:
            observation: Structured boundary event with safe field names.
        """


# ========================================
# NO OP STORE OBSERVABILITY HOOK
# ========================================
class NoOpStoreObservabilityHook:
    """Ignore store observations when the caller does not attach a hook."""

    def record(self, observation: StoreObservation) -> None:
        """Drop the observation.

        Args:
            observation: Structured boundary event with safe field names.
        """
        _ = observation
