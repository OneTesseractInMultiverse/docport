import docport
import docport.adapters
import docport.domain
import docport.ports


class TestPackageExports:
    def test_top_level_exports_sync_store(self) -> None:
        assert docport.Store is docport.ports.Store

    def test_top_level_exports_async_store(self) -> None:
        assert docport.AsyncStore is docport.ports.AsyncStore

    def test_top_level_exports_entity(self) -> None:
        assert docport.DocPortEntity is docport.domain.DocPortEntity

    def test_top_level_exports_timeseries_entity(self) -> None:
        assert docport.DocPortTimeSeriesEntity is docport.domain.DocPortTimeSeriesEntity

    def test_top_level_exports_find_options(self) -> None:
        assert docport.FindOptions is docport.domain.FindOptions

    def test_top_level_exports_operation_context(self) -> None:
        assert docport.StoreOperationContext is docport.domain.StoreOperationContext

    def test_top_level_exports_observation_type(self) -> None:
        assert docport.StoreObservation is docport.domain.StoreObservation

    def test_adapters_package_exports_mongo_store(self) -> None:
        assert docport.adapters.MongoStore is docport.MongoStore

    def test_adapters_package_exports_async_mongo_store(self) -> None:
        assert docport.adapters.AsyncMongoStore is docport.AsyncMongoStore

    def test_adapters_package_exports_mapper(self) -> None:
        assert docport.adapters.MongoDocumentMapper is docport.MongoDocumentMapper

    def test_adapters_package_exports_dependency_error(self) -> None:
        assert docport.adapters.StoreDependencyError is docport.StoreDependencyError

    def test_domain_package_exports_error_types(self) -> None:
        assert docport.domain.EntityVersionConflictError is docport.EntityVersionConflictError

    def test_ports_package_exports_base_port(self) -> None:
        assert docport.ports.StorePort is docport.StorePort

    def test_ports_package_exports_observability_hook(self) -> None:
        assert docport.ports.StoreObservabilityHook is docport.StoreObservabilityHook
