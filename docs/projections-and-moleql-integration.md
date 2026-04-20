# Projections and [MoleQL](https://github.com/OneTesseractInMultiverse/moleql) Integration

This page explains how `docport` handles partial reads and how [MoleQL](https://github.com/OneTesseractInMultiverse/moleql) can feed the store layer without a package dependency.

## Partial reads are not entities

A projected query returns part of a document.
That result should not become a `DocPortEntity`.
A missing field can hide an invariant or a domain rule.
`docport` makes that boundary explicit.

Use `find()` and `find_one()` for full entity hydration.
Use `find_projected()` for partial reads.
That rule gives the caller a clear signal about what came back from the database.

## Two projection return styles

`find_projected()` supports two return styles.

The first style returns raw dictionaries.
This is a good fit for generic endpoints, export code, and query layers that want to stay close to JSON.

The second style returns a Pydantic model that describes the projected shape.
This is a good fit for stable list rows, API response models, and internal read models that need validation.

```python
from pydantic import BaseModel
from docport import FindOptions, Projection


class UserRow(BaseModel):
    name: str
    email: str


rows = store.find_projected(
    {"status": "active"},
    options=FindOptions(projection=Projection.include("name", "email")),
    result_type=UserRow,
)
```

## Raw dictionary projections

Raw dictionary projections are the most flexible return type.
They preserve driver-shaped values and keep the caller free to reshape data later in the flow.

```python
rows = store.find_projected(
    {"status": "active"},
    options=FindOptions(projection=Projection.include("name", "email")),
)
```

The adapter returns detached copies.
The caller can transform them without mutating cursor-backed objects.

## Projection models

A projection model makes the read shape explicit.
That pays off in service contracts, typed response builders, and tests that want strict field checks.

If a projection model needs Mongo `_id`, define a Pydantic alias for that field.
The mapper will keep `_id` in that case.
If the model does not ask for `_id`, the mapper drops it.

```python
from pydantic import BaseModel, ConfigDict, Field


class UserMongoRow(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    mongo_id: str = Field(alias="_id")
```

## [MoleQL](https://github.com/OneTesseractInMultiverse/moleql) Handoff

[MoleQL](https://github.com/OneTesseractInMultiverse/moleql) returns plain Python data.
That makes the handoff to `docport` very small.
No adapter object is needed in either package.

```python
from moleql import parse
from docport import FindOptions


query = parse("team=platform&sort=-updated_at&limit=25&fields=id,name,email")

rows = store.find_projected(
    query["filter"],
    options=FindOptions.from_values(
        sort=query["sort"],
        skip=query["skip"],
        limit=query["limit"],
        projection=query["projection"],
    ),
)
```

This line between packages is healthy.
[MoleQL](https://github.com/OneTesseractInMultiverse/moleql) parses query text.
`docport` owns persistence contracts.
Each package stays small and easy to reason about.

## Projection and pagination

[MoleQL](https://github.com/OneTesseractInMultiverse/moleql) already gives the parts needed for page reads.
`skip` and `limit` map to `FindOptions`.
`projection` decides if the store call should return entities or projected rows.

```python
from typing import Any

from moleql import parse
from docport import FindOptions


def list_user_rows(store, raw_query: str) -> dict[str, Any]:
    parsed = parse(raw_query)
    options = FindOptions.from_values(
        sort=parsed["sort"],
        skip=parsed["skip"],
        limit=parsed["limit"],
        projection=parsed["projection"],
    )

    rows = store.find_projected(
        parsed["filter"],
        options=options,
    )
    total = store.count(parsed["filter"])

    return {
        "rows": rows,
        "skip": parsed["skip"],
        "limit": parsed["limit"],
        "total": total,
    }
```

This pattern keeps the paging contract in the service layer.
The store applies the filter, sort, skip, limit, and projection.
The service owns page totals and response shape.

Use a query such as:

```text
status=active&sort=-updated_at,name&skip=20&limit=10&fields=id,name,email
```

This query asks for ten projected rows after the first twenty matches.
The sort is newest first, then name.
The count call uses the same parsed `filter`, so the total stays in sync with the page query.

## Choosing `find()` or `find_projected()`

Use `find()` when `projection` is `None`.
Use `find_projected()` when `projection` has a value.
This branch keeps the read type honest.

```python
from moleql import parse
from docport import FindOptions


def run_user_query(store, raw_query: str):
    parsed = parse(raw_query)
    options = FindOptions.from_values(
        sort=parsed["sort"],
        skip=parsed["skip"],
        limit=parsed["limit"],
        projection=parsed["projection"],
    )

    if parsed["projection"] is None:
        return store.find(parsed["filter"], options=options)
    return store.find_projected(parsed["filter"], options=options)
```

## Typed Projection Rows with [MoleQL](https://github.com/OneTesseractInMultiverse/moleql)

Typed projection rows work well for list endpoints.
The [MoleQL](https://github.com/OneTesseractInMultiverse/moleql) query still owns `fields`, `skip`, `limit`, and `sort`.
The service chooses the row model.

```python
from pydantic import BaseModel
from moleql import parse
from docport import FindOptions


class UserRow(BaseModel):
    id: str
    name: str
    email: str


parsed = parse(
    "status=active"
    "&sort=-updated_at"
    "&skip=0"
    "&limit=25"
    "&fields=id,name,email"
)

rows = store.find_projected(
    parsed["filter"],
    options=FindOptions.from_values(
        sort=parsed["sort"],
        skip=parsed["skip"],
        limit=parsed["limit"],
        projection=parsed["projection"],
    ),
    result_type=UserRow,
)
```

The same rule still applies.
Projection queries return read shapes.
They do not return `DocPortEntity`.

## Picking the right return type

Use raw dictionaries for open-ended query paths and export work.
Use projection models for stable read shapes that deserve validation.
Use full entities for aggregate work and domain behavior.
