"""Define shared type aliases used by docport public contracts."""

from typing import Any, Literal

type DocumentId = str
type ProjectionDocument = dict[str, Any]
type StoreDocument = dict[str, Any]
type StoreFilter = dict[str, Any]
type StoreSort = list[tuple[str, int]]
type SortDirection = Literal[1, -1]
