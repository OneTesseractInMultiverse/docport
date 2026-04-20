"""Define safe infrastructure errors raised by store adapters."""

from docport.domain.errors import DocPortError


# ========================================
# STORE INFRASTRUCTURE ERROR
# ========================================
class StoreInfrastructureError(DocPortError):
    """Raise for non-domain faults at the adapter boundary."""

    error_code = "store_infrastructure_error"


# ========================================
# STORE DEPENDENCY ERROR
# ========================================
class StoreDependencyError(StoreInfrastructureError):
    """Raise for driver, dependency, or transport faults in a store adapter."""

    error_code = "store_dependency_error"
