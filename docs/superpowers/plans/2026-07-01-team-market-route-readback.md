# Team Market Route Readback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add local Supabase/Postgres readback helpers for persisted `team_market_routes` rows so later team research assignment DB-source work can consume routed market history without re-reading files.

**Architecture:** Mirror the existing team forecast/evidence/outcome persistence pattern in `team_forecast_store.py` and `team_forecast_psycopg.py`. Keep this node limited to store-level and psycopg readback helpers; do not add a CLI or team research assignment DB-source in this node.

**Tech Stack:** Python 3, DB-API compatible connections, optional `psycopg`, pytest, local Supabase/Postgres DSN validation from existing env modules.

## Global Constraints

- Use CodeGraph before grep/find/raw reads because `.codegraph/` exists at the repo root.
- Use TDD: write failing tests before production code for behavior changes.
- Durable project data must use local Supabase/Postgres only.
- Do not add SQLite, Redis, Mongo, SQLAlchemy, hosted DB assumptions, generic DB layers, or file durable substitutes.
- Preserve Phase 1 boundary: `paper_only=True`, `report_only=True`, `readonly=True`.
- No live trading/auth/wallet/key material/account reads/order signing/submission/cancel/replace/exchange mutation.
- No investment recommendation, ranking, trade instruction, strategy-weight tuning, or position sizing.
- Do not add CLI flags named `--dsn` or `--table`; this node adds no CLI.
- DB/CLI errors must not echo DSNs, table names, market slugs/questions/payload/hash/raw_filter details.
- Keep route readback newest-first: `ORDER BY generated_at DESC, inserted_at DESC, payload_sha256 DESC`.
- Reuse `_DEFAULT_ROUTE_TABLE_NAME = "team_market_routes"` and `_ROUTE_COLUMNS` exactly.
- Use `team_route_from_db_row(row)` to restore `TeamMarketRouteReport`; do not manually unpack route payload JSON.
- Do not export the route store API from `polymarket_alpha_lab.__init__`.

---

### Task 1: DB-API Route Readback

**Files:**
- Modify: `tests/test_team_forecast_store.py`
- Modify: `src/polymarket_alpha_lab/team_forecast_store.py`

**Interfaces:**
- Consumes: `TeamMarketRouteDbRow`, `team_route_from_db_row(row)`, `_ROUTE_COLUMNS`, `_filter_params`, `_limit_clause`, `_execute_load`, `_db_row_from_record`.
- Produces: `load_team_market_route_rows(connection, *, team_id=None, market_slug=None, limit=None, table_name=_DEFAULT_ROUTE_TABLE_NAME) -> tuple[TeamMarketRouteDbRow, ...]`.
- Produces: `load_team_market_routes(connection, *, team_id=None, market_slug=None, limit=None, table_name=_DEFAULT_ROUTE_TABLE_NAME) -> tuple[TeamMarketRouteReport, ...]`.

- [ ] **Step 1: Write the failing packet-loader test**

Add a fake route report and converter to `tests/test_team_forecast_store.py`:

```python
@dataclass(frozen=True)
class FakeTeamMarketRouteReport:
    team_id: str
    market_slug: str
    category_id: str
```

In the `store_module` fixture, add:

```python
def team_route_from_db_row(row: FakeTeamMarketRouteDbRow) -> FakeTeamMarketRouteReport:
    return FakeTeamMarketRouteReport(
        team_id=row.team_id,
        market_slug=row.market_slug,
        category_id=row.category_id,
    )

companion.team_route_from_db_row = team_route_from_db_row
```

Add this test:

```python
def test_load_team_market_routes_filters_limits_newest_first_and_restores_reports(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection(rows=(route_row(),))

    routes = store_module.load_team_market_routes(
        connection,
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        limit=25,
        table_name="research.team_market_routes",
    )

    assert routes == (
        FakeTeamMarketRouteReport(
            team_id="crypto_btc",
            market_slug="bitcoin-above-120k",
            category_id="finance.crypto.btc",
        ),
    )
    assert connection.commit_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        SELECT
            payload_sha256,
            generated_at,
            team_id,
            market_slug,
            config_version,
            condition_id,
            category_id,
            event_template,
            routing_confidence,
            payload_json,
            paper_only,
            report_only,
            readonly
        FROM research.team_market_routes
        WHERE team_id = %s AND market_slug = %s
        ORDER BY generated_at DESC, inserted_at DESC, payload_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("crypto_btc", "bitcoin-above-120k", 25)
```

- [ ] **Step 2: Verify RED**

Run:

```bash
pytest tests/test_team_forecast_store.py::test_load_team_market_routes_filters_limits_newest_first_and_restores_reports -q
```

Expected: fail because `load_team_market_routes` is not implemented.

- [ ] **Step 3: Implement store helpers**

Modify `src/polymarket_alpha_lab/team_forecast_store.py`:

```python
from polymarket_alpha_lab.team_forecast_db_row import (
    TeamForecastDbRow,
    TeamForecastEvidenceDbRow,
    TeamForecastOutcomeDbRow,
    TeamMarketRouteDbRow,
    team_forecast_evidence_from_db_row,
    team_forecast_from_db_row,
    team_forecast_outcome_from_db_row,
    team_route_from_db_row,
)
```

Add exports:

```python
    "load_team_market_routes",
    "load_team_market_route_rows",
```

Add helpers after `insert_team_forecast_outcome` and before `load_team_forecasts`:

```python
def load_team_market_routes(
    connection: Any,
    *,
    team_id: str | None = None,
    market_slug: str | None = None,
    limit: int | None = None,
    table_name: str = _DEFAULT_ROUTE_TABLE_NAME,
) -> tuple[TeamMarketRouteReport, ...]:
    rows = load_team_market_route_rows(
        connection,
        team_id=team_id,
        market_slug=market_slug,
        limit=limit,
        table_name=table_name,
    )
    return tuple(team_route_from_db_row(row) for row in rows)


def load_team_market_route_rows(
    connection: Any,
    *,
    team_id: str | None = None,
    market_slug: str | None = None,
    limit: int | None = None,
    table_name: str = _DEFAULT_ROUTE_TABLE_NAME,
) -> tuple[TeamMarketRouteDbRow, ...]:
    table_name = _validate_table_name(table_name)
    where_clause, params = _filter_params(
        team_id=team_id,
        market_slug=market_slug,
        limit=limit,
    )
    limit_clause = _limit_clause(limit)
    columns = ",\n            ".join(_ROUTE_COLUMNS)
    sql = f"""
        SELECT
            {columns}
        FROM {table_name}
        {where_clause}
        ORDER BY generated_at DESC, inserted_at DESC, payload_sha256 DESC
        {limit_clause}
        """
    records = _execute_load(connection, sql, tuple(params))
    return tuple(
        _db_row_from_record(record, TeamMarketRouteDbRow, _ROUTE_COLUMNS)
        for record in records
    )
```

- [ ] **Step 4: Verify GREEN**

Run:

```bash
pytest tests/test_team_forecast_store.py::test_load_team_market_routes_filters_limits_newest_first_and_restores_reports -q
```

Expected: pass.

- [ ] **Step 5: Expand validation coverage**

Add route inputs to invalid-query coverage in `tests/test_team_forecast_store.py` with a new test:

```python
@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "schema.too.many.parts"}, "table_name"),
        ({"table_name": "_team_market_routes"}, "table_name"),
        ({"table_name": "team_market_routes_"}, "table_name"),
        ({"team_id": ""}, "team_id"),
        ({"team_id": " crypto_btc"}, "team_id"),
        ({"market_slug": ""}, "market_slug"),
        ({"market_slug": " bitcoin-above-120k"}, "market_slug"),
        ({"limit": 0}, "limit"),
        ({"limit": True}, "limit"),
    ),
)
def test_load_team_market_routes_rejects_invalid_query_inputs_without_executing_sql(
    store_module: types.ModuleType,
    kwargs: dict[str, Any],
    message: str,
) -> None:
    connection = FakeConnection()
    kwargs.setdefault("table_name", "team_market_routes")

    with pytest.raises(ValueError, match=message):
        store_module.load_team_market_routes(connection, **kwargs)

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []
```

- [ ] **Step 6: Run task tests**

Run:

```bash
pytest tests/test_team_forecast_store.py -q
```

Expected: pass.

### Task 2: Raw Route Row Readback Coverage

**Files:**
- Modify: `tests/test_team_forecast_store_raw_rows.py`
- May rely on production changes from Task 1.

**Interfaces:**
- Consumes: `load_team_market_route_rows(...)` and `load_team_market_routes(...)` from Task 1.
- Produces: raw-row tests that prove route rows are selected using `_ROUTE_COLUMNS`, restored as `TeamMarketRouteDbRow`, and packet loaders delegate through raw row loaders.

- [ ] **Step 1: Write route-row fixtures and failing tests**

Add:

```python
@dataclass(frozen=True)
class FakeTeamMarketRouteReport:
    team_id: str
    payload_json: dict[str, Any]
```

Add a `route_row` helper matching `FakeTeamMarketRouteDbRow`:

```python
def route_row(**overrides: Any) -> FakeTeamMarketRouteDbRow:
    values = {
        "payload_sha256": "a" * 64,
        "generated_at": GENERATED_AT,
        "team_id": "crypto_btc",
        "market_slug": "bitcoin-above-120k",
        "config_version": "team-router-v0",
        "condition_id": "condition-btc",
        "category_id": "finance.crypto.btc",
        "event_template": "btc_hit_price",
        "routing_confidence": Decimal("0.900000"),
        "payload_json": {"kind": "route", "extra_recovery_field": "kept"},
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return FakeTeamMarketRouteDbRow(**values)
```

In `store_module`, add:

```python
def team_route_from_db_row(row: FakeTeamMarketRouteDbRow) -> FakeTeamMarketRouteReport:
    return FakeTeamMarketRouteReport(row.team_id, {"converted": row.payload_json})

companion.team_route_from_db_row = team_route_from_db_row
```

Add:

```python
def test_load_team_market_route_rows_returns_db_rows_with_filters_order_and_limit(
    store_module: types.ModuleType,
) -> None:
    row = route_row()
    connection = FakeConnection((row,))

    loaded = store_module.load_team_market_route_rows(
        connection,
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        limit=5,
        table_name="research.team_market_routes",
    )

    assert loaded == (row,)
    assert loaded[0].routing_confidence == Decimal("0.900000")
    assert loaded[0].payload_json == {"kind": "route", "extra_recovery_field": "kept"}
    assert connection.commit_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        SELECT
            payload_sha256,
            generated_at,
            team_id,
            market_slug,
            config_version,
            condition_id,
            category_id,
            event_template,
            routing_confidence,
            payload_json,
            paper_only,
            report_only,
            readonly
        FROM research.team_market_routes
        WHERE team_id = %s AND market_slug = %s
        ORDER BY generated_at DESC, inserted_at DESC, payload_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("crypto_btc", "bitcoin-above-120k", 5)
```

- [ ] **Step 2: Verify RED**

Run:

```bash
pytest tests/test_team_forecast_store_raw_rows.py::test_load_team_market_route_rows_returns_db_rows_with_filters_order_and_limit -q
```

Expected: fail because `load_team_market_route_rows` is not implemented until Task 1 lands.

- [ ] **Step 3: Extend delegation test**

Update `test_existing_packet_loaders_delegate_through_raw_row_loaders` to include:

```python
route = route_row()

def fake_route_rows(
    connection_arg: object,
    *,
    team_id: str | None,
    market_slug: str | None,
    limit: int | None,
    table_name: str,
) -> tuple[FakeTeamMarketRouteDbRow, ...]:
    calls.append(("route", connection_arg, team_id, market_slug, limit, table_name))
    return (route,)

monkeypatch.setattr(store_module, "load_team_market_route_rows", fake_route_rows)

assert store_module.load_team_market_routes(
    connection,
    team_id="crypto_btc",
    market_slug="bitcoin-above-120k",
    limit=6,
    table_name="team_market_routes",
) == (
    FakeTeamMarketRouteReport(
        "crypto_btc",
        {"converted": {"kind": "route", "extra_recovery_field": "kept"}},
    ),
)
```

Expected final call list includes:

```python
("route", connection, "crypto_btc", "bitcoin-above-120k", 6, "team_market_routes")
```

- [ ] **Step 4: Verify GREEN**

Run:

```bash
pytest tests/test_team_forecast_store_raw_rows.py -q
```

Expected: pass after Task 1 implementation is present.

### Task 3: Psycopg Route Readback Wrappers

**Files:**
- Modify: `tests/test_team_forecast_psycopg.py`
- Modify: `src/polymarket_alpha_lab/team_forecast_psycopg.py`

**Interfaces:**
- Consumes: `load_team_market_routes(...)` and `load_team_market_route_rows(...)` from Task 1.
- Produces: `load_team_market_routes_with_psycopg(dsn, *, team_id=None, market_slug=None, limit=None, table_name) -> tuple[TeamMarketRouteReport, ...]`.
- Produces: `load_team_market_route_rows_with_psycopg(dsn, *, team_id=None, market_slug=None, limit=None, table_name) -> tuple[TeamMarketRouteDbRow, ...]`.

- [ ] **Step 1: Write failing wrapper tests**

Add fake route types:

```python
@dataclass(frozen=True)
class FakeRouteReport:
    team_id: str


@dataclass(frozen=True)
class FakeRouteDbRow:
    payload_sha256: str
```

Add tests mirroring existing forecast read wrapper tests:

```python
def test_load_routes_opens_psycopg_connection_delegates_query_options_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    route = FakeRouteReport(team_id="crypto_btc")
    connect_calls: list[str] = []
    store_calls: list[tuple[Any, str | None, str | None, int | None, str]] = []

    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn: connect_calls.append(dsn) or connection,
    )

    def fake_load(
        connection_arg: Any,
        *,
        team_id: str | None,
        market_slug: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeRouteReport, ...]:
        store_calls.append((connection_arg, team_id, market_slug, limit, table_name))
        return (route,)

    monkeypatch.setattr(adapter_module, "load_team_market_routes", fake_load, raising=False)

    loaded = adapter_module.load_team_market_routes_with_psycopg(
        LOCAL_DSN,
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        limit=10,
        table_name="team_market_routes_archive",
    )

    assert loaded == (route,)
    assert connect_calls == [LOCAL_DSN]
    store_connection, team_id, market_slug, limit, table_name = store_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert team_id == "crypto_btc"
    assert market_slug == "bitcoin-above-120k"
    assert limit == 10
    assert table_name == "team_market_routes_archive"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1
```

```python
def test_load_route_rows_opens_psycopg_connection_delegates_query_options_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    row = FakeRouteDbRow(payload_sha256="a" * 64)
    connect_calls: list[str] = []
    store_calls: list[tuple[Any, str | None, str | None, int | None, str]] = []

    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn: connect_calls.append(dsn) or connection,
    )

    def fake_load(
        connection_arg: Any,
        *,
        team_id: str | None,
        market_slug: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeRouteDbRow, ...]:
        store_calls.append((connection_arg, team_id, market_slug, limit, table_name))
        return (row,)

    monkeypatch.setattr(adapter_module, "load_team_market_route_rows", fake_load, raising=False)

    loaded = adapter_module.load_team_market_route_rows_with_psycopg(
        LOCAL_DSN,
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        limit=10,
        table_name="team_market_routes_archive",
    )

    assert loaded == (row,)
    assert connect_calls == [LOCAL_DSN]
    store_connection, team_id, market_slug, limit, table_name = store_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert team_id == "crypto_btc"
    assert market_slug == "bitcoin-above-120k"
    assert limit == 10
    assert table_name == "team_market_routes_archive"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1
```

- [ ] **Step 2: Verify RED**

Run:

```bash
pytest tests/test_team_forecast_psycopg.py::test_load_routes_opens_psycopg_connection_delegates_query_options_commits_and_closes tests/test_team_forecast_psycopg.py::test_load_route_rows_opens_psycopg_connection_delegates_query_options_commits_and_closes -q
```

Expected: fail because wrappers are missing.

- [ ] **Step 3: Implement psycopg wrappers and fallback stubs**

Modify import list in `team_forecast_psycopg.py` to import:

```python
        load_team_market_route_rows,
        load_team_market_routes,
```

Add fallback stubs in the `except ModuleNotFoundError` block:

```python
    def load_team_market_routes(
        connection: Any,
        *,
        team_id: str | None = None,
        market_slug: str | None = None,
        limit: int | None = None,
        table_name: str,
    ) -> tuple[Any, ...]:
        raise RuntimeError("team forecast store module is required")

    def load_team_market_route_rows(
        connection: Any,
        *,
        team_id: str | None = None,
        market_slug: str | None = None,
        limit: int | None = None,
        table_name: str,
    ) -> tuple[Any, ...]:
        raise RuntimeError("team forecast store module is required")
```

Add wrappers after `insert_team_market_route_with_psycopg`:

```python
def load_team_market_routes_with_psycopg(
    dsn: str,
    *,
    team_id: str | None = None,
    market_slug: str | None = None,
    limit: int | None = None,
    table_name: str,
) -> tuple[TeamMarketRouteReport, ...]:
    return _with_owned_connection(
        dsn,
        lambda connection: load_team_market_routes(
            connection,
            team_id=team_id,
            market_slug=market_slug,
            limit=limit,
            table_name=table_name,
        ),
    )


def load_team_market_route_rows_with_psycopg(
    dsn: str,
    *,
    team_id: str | None = None,
    market_slug: str | None = None,
    limit: int | None = None,
    table_name: str,
) -> tuple[TeamMarketRouteDbRow, ...]:
    return _with_owned_connection(
        dsn,
        lambda connection: load_team_market_route_rows(
            connection,
            team_id=team_id,
            market_slug=market_slug,
            limit=limit,
            table_name=table_name,
        ),
    )
```

Add both names to `__all__`.

- [ ] **Step 4: Expand exports and missing-store tests**

Update `test_public_exports_include_all_team_forecast_psycopg_wrappers` to include:

```python
"load_team_market_routes_with_psycopg",
"load_team_market_route_rows_with_psycopg",
```

Update `test_missing_store_module_public_wrappers_raise_clean_runtime_error` calls to include:

```python
lambda: module.load_team_market_routes_with_psycopg(
    LOCAL_DSN,
    table_name="team_market_routes",
),
lambda: module.load_team_market_route_rows_with_psycopg(
    LOCAL_DSN,
    table_name="team_market_routes",
),
```

- [ ] **Step 5: Verify GREEN**

Run:

```bash
pytest tests/test_team_forecast_psycopg.py -q
```

Expected: pass.

### Task 4: Documentation And Integration Verification

**Files:**
- Modify: `docs/team-research-assignment-db-source-gap.md`
- Modify: `.superpowers/sdd/progress.md`
- Optional modify: `README.md` only if existing team route persistence docs need a single readback sentence.

**Interfaces:**
- Consumes: completed route readback helpers from Tasks 1-3.
- Produces: documentation that says store/psycopg route readback is now available, while team research assignment DB-source/CLI remains deferred to a later node.

- [ ] **Step 1: Update docs after code lands**

In `docs/team-research-assignment-db-source-gap.md`, state that the low-level `team_market_routes` readback prerequisite is now implemented through `load_team_market_routes`, `load_team_market_route_rows`, `load_team_market_routes_with_psycopg`, and `load_team_market_route_rows_with_psycopg`.

Keep the remaining gap explicit: the user-facing team research assignment DB-source/CLI is still not part of this node.

- [ ] **Step 2: Run focused verification**

Run:

```bash
pytest tests/test_team_forecast_store.py tests/test_team_forecast_store_raw_rows.py tests/test_team_forecast_psycopg.py tests/test_team_forecast_db_row.py -q
```

Expected: pass.

- [ ] **Step 3: Run repository verification**

Run:

```bash
python3 -m compileall -q src/polymarket_alpha_lab tests
pytest -q
codegraph sync
git diff --check
```

Expected: all pass.

- [ ] **Step 4: Review and push**

Request Claude Code review only:

```bash
claude --model claude-opus-4-8 --thinking max
```

Review scope: current diff against `origin/main`, plan compliance, tests, Phase 1 safety, local Supabase/Postgres-only persistence.

If Claude reports Critical or Important findings, fix them, rerun focused verification, and request re-review.

When clean:

```bash
git add src/polymarket_alpha_lab/team_forecast_store.py src/polymarket_alpha_lab/team_forecast_psycopg.py tests/test_team_forecast_store.py tests/test_team_forecast_store_raw_rows.py tests/test_team_forecast_psycopg.py docs/team-research-assignment-db-source-gap.md docs/superpowers/plans/2026-07-01-team-market-route-readback.md
git commit -m "feat: add team market route readback"
git push origin main
```
