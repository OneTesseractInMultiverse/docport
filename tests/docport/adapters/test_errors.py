from docport import StoreDependencyError, StoreInfrastructureError


class TestAdapterErrors:
    def test_store_dependency_error_exposes_stable_error_code(self) -> None:
        assert StoreDependencyError("dependency").error_code == "store_dependency_error"

    def test_store_infrastructure_error_exposes_stable_error_code(self) -> None:
        assert StoreInfrastructureError("infra").error_code == "store_infrastructure_error"
