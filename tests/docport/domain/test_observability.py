from uuid import UUID

import pytest

from docport import StoreObservation, StoreOperationContext, new_correlation_id


class TestStoreObservability:
    def test_new_correlation_id_returns_uuid_text(self) -> None:
        correlation_id = new_correlation_id()

        assert UUID(correlation_id).version == 4

    def test_operation_context_create_keeps_supplied_values(self) -> None:
        context = StoreOperationContext.create(
            correlation_id="corr-1",
            causation_id="cause-1",
            actor="api-gateway",
        )

        assert context == StoreOperationContext(
            correlation_id="corr-1",
            causation_id="cause-1",
            actor="api-gateway",
        )

    def test_operation_context_with_actor_returns_updated_copy(self) -> None:
        context = StoreOperationContext(correlation_id="corr-1")

        assert context.with_actor("writer") == StoreOperationContext(
            correlation_id="corr-1",
            actor="writer",
        )

    def test_operation_context_rejects_blank_actor(self) -> None:
        with pytest.raises(ValueError, match="actor must not be blank"):
            StoreOperationContext(correlation_id="corr-1", actor=" ")

    def test_store_observation_as_log_fields_returns_stable_names(self) -> None:
        observation = StoreObservation(
            correlation_id="corr-1",
            causation_id="cause-1",
            actor="worker",
            action="add",
            target="user-1",
            outcome="success",
            error_code=None,
            duration_ms=12,
            entity_type="User",
            collection_name="users",
        )

        assert observation.as_log_fields() == {
            "correlation_id": "corr-1",
            "causation_id": "cause-1",
            "actor": "worker",
            "action": "add",
            "target": "user-1",
            "outcome": "success",
            "error_code": None,
            "duration_ms": 12,
            "entity_type": "User",
            "collection_name": "users",
        }

    def test_store_observation_rejects_negative_duration(self) -> None:
        with pytest.raises(ValueError, match="duration_ms must be greater than or equal to 0"):
            StoreObservation(
                correlation_id="corr-1",
                causation_id=None,
                actor=None,
                action="find",
                target="users",
                outcome="failure",
                error_code="unexpected_error",
                duration_ms=-1,
                entity_type="User",
                collection_name="users",
            )
