from docport import DuplicateEntityError, StoreConfigurationError


class TestDomainErrors:
    def test_duplicate_entity_error_exposes_stable_error_code(self) -> None:
        assert DuplicateEntityError("duplicate").error_code == "duplicate_entity"

    def test_store_configuration_error_exposes_stable_error_code(self) -> None:
        assert StoreConfigurationError("bad config").error_code == "store_configuration_error"
