from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.market_research_fed_dots_revision_digest"
GENERATED_AT = datetime(2026, 7, 3, 15, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
_UNSET = object()


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def test_fed_dots_revision_digest_public_api_exists() -> None:
    assert importlib.util.find_spec(MODULE_NAME) is not None


def test_fed_dots_revision_digest_reduces_rows_and_sorts_deterministically() -> None:
    digest = digest_module()

    summary = report(
        digest,
        (
            input_row(
                digest,
                "research.fed.dots.longer-run",
                condition_id="condition_fed_dots_longer_run",
                dot_key="fed.dots.longer_run",
                public_dot_reference="https://rates.example/fomc?token=secret-123",
                observed_at=GENERATED_AT - timedelta(hours=3),
                acknowledged_at=None,
                source_count=d("1.000000"),
                median_rate_before=d("3.100000"),
                median_rate_after=d("3.600000"),
                market_probability_before=d("0.620000"),
                market_probability_after=d("0.400000"),
                dot_config_version="fed-dots-v1",
            ),
            input_row(
                digest,
                "research.fed.dots.next-year",
                condition_id="condition_fed_dots_next_year",
                dot_key="fed.dots.next_year",
                public_dot_reference="private-fed-dots-feed",
                observed_at=GENERATED_AT - timedelta(hours=2, minutes=15),
                acknowledged_at=GENERATED_AT - timedelta(minutes=70),
                source_count=d("2.000000"),
                median_rate_before=d("4.100000"),
                median_rate_after=d("4.200000"),
                market_probability_before=d("0.510000"),
                market_probability_after=d("0.540000"),
                dot_config_version="fed-dots-v1",
            ),
            input_row(
                digest,
                "research.fed.dots.current-year",
                condition_id="condition_fed_dots_current_year",
                dot_key="fed.dots.current_year",
                public_dot_reference="fomc-dot-plot-calendar",
                observed_at=GENERATED_AT - timedelta(minutes=30),
                acknowledged_at=GENERATED_AT - timedelta(minutes=20),
                source_count=d("3.000000"),
                median_rate_before=d("4.500000"),
                median_rate_after=d("4.520000"),
                market_probability_before=d("0.480000"),
                market_probability_after=d("0.490000"),
                dot_config_version="fed-dots-v0",
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        digest.DEFAULT_MARKET_RESEARCH_FED_DOTS_REVISION_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_fed_dots_revision_digest"
    )
    assert summary.dot_count == d("3.000000")
    assert summary.ready_dot_count == d("1.000000")
    assert summary.watch_dot_count == d("1.000000")
    assert summary.blocked_dot_count == d("1.000000")
    assert summary.material_revision_count == d("1.000000")
    assert summary.stale_dot_count == d("2.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.missing_acknowledgement_count == d("1.000000")
    assert summary.slow_acknowledgement_count == d("1.000000")
    assert summary.probability_repricing_count == d("1.000000")
    assert summary.average_median_rate_revision_abs == d("0.206667")
    assert summary.average_probability_delta_abs == d("0.086667")
    assert summary.max_signal_age_seconds == d("10800.000000")
    assert summary.average_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.dot_key, row.research_key) for row in summary.rows) == (
        ("fed.dots.longer_run", "research.fed.dots.longer-run"),
        ("fed.dots.next_year", "research.fed.dots.next-year"),
        ("fed.dots.current_year", "research.fed.dots.current-year"),
    )

    longer_run = summary.rows[0]
    assert longer_run.revision_status == "blocked"
    assert longer_run.signal_age_seconds == d("10800.000000")
    assert longer_run.acknowledgement_lag_seconds is None
    assert longer_run.median_rate_revision_delta == d("0.500000")
    assert longer_run.median_rate_revision_abs == d("0.500000")
    assert longer_run.probability_delta == d("-0.220000")
    assert longer_run.redacted_public_dot_reference == redacted(
        "https://rates.example/fomc?token=secret-123",
    )
    assert longer_run.reason_codes == (
        "market_research_fed_dots_revision_digest_material_revision",
        "market_research_fed_dots_revision_digest_probability_repricing",
        "market_research_fed_dots_revision_digest_missing_acknowledgement",
        "market_research_fed_dots_revision_digest_stale_dot",
        "market_research_fed_dots_revision_digest_thin_sources",
    )

    next_year = summary.rows[1]
    assert next_year.revision_status == "watch"
    assert next_year.signal_age_seconds == d("8100.000000")
    assert next_year.acknowledgement_lag_seconds == d("3900.000000")
    assert next_year.median_rate_revision_delta == d("0.100000")
    assert next_year.median_rate_revision_abs == d("0.100000")
    assert next_year.probability_delta == d("0.030000")
    assert next_year.redacted_public_dot_reference == redacted("private-fed-dots-feed")
    assert next_year.reason_codes == (
        "market_research_fed_dots_revision_digest_slow_acknowledgement",
        "market_research_fed_dots_revision_digest_stale_dot",
    )

    current_year = summary.rows[2]
    assert current_year.revision_status == "ready"
    assert current_year.signal_age_seconds == d("1800.000000")
    assert current_year.acknowledgement_lag_seconds == d("600.000000")
    assert current_year.median_rate_revision_delta == d("0.020000")
    assert current_year.median_rate_revision_abs == d("0.020000")
    assert current_year.probability_delta == d("0.010000")
    assert current_year.redacted_public_dot_reference == "fomc-dot-plot-calendar"
    assert current_year.reason_codes == (
        "market_research_fed_dots_revision_digest_ready",
    )

    assert summary.reason_code_counts == (
        digest.MarketResearchFedDotsRevisionDigestReasonCodeCount(
            reason_code="market_research_fed_dots_revision_digest_stale_dot",
            count=d("2.000000"),
            dot_ratio=d("0.666667"),
        ),
        digest.MarketResearchFedDotsRevisionDigestReasonCodeCount(
            reason_code="market_research_fed_dots_revision_digest_material_revision",
            count=d("1.000000"),
            dot_ratio=d("0.333333"),
        ),
        digest.MarketResearchFedDotsRevisionDigestReasonCodeCount(
            reason_code=(
                "market_research_fed_dots_revision_digest_probability_repricing"
            ),
            count=d("1.000000"),
            dot_ratio=d("0.333333"),
        ),
        digest.MarketResearchFedDotsRevisionDigestReasonCodeCount(
            reason_code=(
                "market_research_fed_dots_revision_digest_missing_acknowledgement"
            ),
            count=d("1.000000"),
            dot_ratio=d("0.333333"),
        ),
        digest.MarketResearchFedDotsRevisionDigestReasonCodeCount(
            reason_code="market_research_fed_dots_revision_digest_ready",
            count=d("1.000000"),
            dot_ratio=d("0.333333"),
        ),
        digest.MarketResearchFedDotsRevisionDigestReasonCodeCount(
            reason_code=(
                "market_research_fed_dots_revision_digest_slow_acknowledgement"
            ),
            count=d("1.000000"),
            dot_ratio=d("0.333333"),
        ),
        digest.MarketResearchFedDotsRevisionDigestReasonCodeCount(
            reason_code="market_research_fed_dots_revision_digest_thin_sources",
            count=d("1.000000"),
            dot_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )
    assert summary.dot_config_versions == (
        ("fed.dots.current_year", "fed-dots-v0"),
        ("fed.dots.longer_run", "fed-dots-v1"),
        ("fed.dots.next_year", "fed-dots-v1"),
    )

    public = repr(summary).lower()
    for token in (
        "secret-123",
        "rates.example",
        "https://",
        "private-fed-dots-feed",
        "auth",
        "broker",
        "signing",
        "submit",
        "cancel",
        "wallet",
        "account",
        "advice",
        "network",
        "database",
        "token",
        "secret",
        "private",
    ):
        assert token not in public


def test_empty_fed_dots_revision_digest_is_blocked_and_report_only() -> None:
    digest = digest_module()
    summary = report(digest, ())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_fed_dots_revision_digest"
    )
    assert summary.dot_count == ZERO
    assert summary.ready_dot_count == ZERO
    assert summary.watch_dot_count == ZERO
    assert summary.blocked_dot_count == ZERO
    assert summary.average_median_rate_revision_abs == ZERO
    assert summary.average_probability_delta_abs == ZERO
    assert summary.max_signal_age_seconds == ZERO
    assert summary.average_source_count == ZERO
    assert summary.rows == ()
    assert summary.dot_config_versions == ()
    assert summary.reason_code_counts == (
        digest.MarketResearchFedDotsRevisionDigestReasonCodeCount(
            reason_code="market_research_fed_dots_revision_digest_no_inputs",
            count=d("1.000000"),
            dot_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_fed_dots_revision_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_fed_dots_revision_digest_payload_uses_decimal_strings() -> None:
    digest = digest_module()
    summary = report(digest, (input_row(digest),))
    payload = digest.market_research_fed_dots_revision_digest_payload(summary)
    json.dumps(payload, sort_keys=True)

    assert payload["dot_count"] == "1.000000"
    assert payload["average_median_rate_revision_abs"] == "0.020000"
    assert payload["rows"][0]["source_count"] == "3.000000"
    assert payload["rows"][0]["median_rate_revision_abs"] == "0.020000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert not any(isinstance(value, Decimal) for value in walk_values(payload))
    assert "'public_dot_reference':" not in repr(payload)
    assert "private" not in repr(payload).lower()


def test_fed_dots_revision_digest_validates_public_contracts_and_flags() -> None:
    digest = digest_module()

    assert digest.MarketResearchFedDotsRevisionDigestConfig.__dataclass_params__.frozen
    assert digest.MarketResearchFedDotsRevisionDigestInputRow.__dataclass_params__.frozen
    assert digest.MarketResearchFedDotsRevisionDigestRow.__dataclass_params__.frozen
    assert digest.MarketResearchFedDotsRevisionDigestReport.__dataclass_params__.frozen

    summary = report(digest, (input_row(digest),))
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].source_count = d("4.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(digest, config_version=_StringSubclass("fed-dots-revision-v0"))
    with pytest.raises(ValueError, match="max_dot_signal_age_seconds"):
        config(digest, max_dot_signal_age_seconds=_DecimalSubclass("7200.000000"))
    with pytest.raises(ValueError, match="material_median_rate_revision_threshold"):
        config(
            digest,
            material_median_rate_revision_threshold=0.25,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="research_key"):
        input_row(digest, research_key=" bad")
    with pytest.raises(ValueError, match="dot_key"):
        input_row(digest, dot_key="fed.private.dots")
    with pytest.raises(ValueError, match="observed_at"):
        input_row(digest, observed_at=datetime(2026, 7, 3, 15, 0))
    with pytest.raises(ValueError, match="acknowledged_at"):
        input_row(
            digest,
            acknowledged_at=_DateTimeSubclass(2026, 7, 3, 15, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="source_count"):
        input_row(digest, source_count=Decimal("1.5"))
    with pytest.raises(ValueError, match="median_rate_before"):
        input_row(digest, median_rate_before=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="median_rate_after"):
        input_row(digest, median_rate_after=Decimal("Infinity"))
    with pytest.raises(ValueError, match="market_probability_before"):
        input_row(digest, market_probability_before=d("1.000001"))
    with pytest.raises(ValueError, match="market_probability_after"):
        input_row(digest, market_probability_after=d("-0.000001"))
    with pytest.raises(ValueError, match="future"):
        report(
            digest,
            (input_row(digest, observed_at=GENERATED_AT + timedelta(seconds=1)),),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_row(digest), paper_only=False)
    with pytest.raises(ValueError, match="config"):
        digest.build_market_research_fed_dots_revision_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(TypeError, match="does not support subclassing"):
        type(
            "BadConfig",
            (digest.MarketResearchFedDotsRevisionDigestConfig,),
            {},
        )


def test_fed_dots_revision_digest_rejects_false_phase1_flags() -> None:
    digest = digest_module()
    summary = report(digest, (input_row(digest),))
    row = summary.rows[0]
    reason_count = summary.reason_code_counts[0]

    with pytest.raises(ValueError, match="paper_only"):
        config(digest, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(digest, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(digest, readonly=False)

    with pytest.raises(ValueError, match="paper_only"):
        input_row(digest, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        input_row(digest, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        input_row(digest, readonly=False)

    with pytest.raises(ValueError, match="paper_only"):
        replace(row, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(row, readonly=False)

    with pytest.raises(ValueError, match="paper_only"):
        replace(reason_count, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(reason_count, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(reason_count, readonly=False)

    with pytest.raises(ValueError, match="paper_only"):
        replace(summary, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(summary, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)


def test_fed_dots_revision_digest_rejects_duplicates_and_bad_consistency() -> None:
    digest = digest_module()

    with pytest.raises(ValueError, match="unique"):
        report(
            digest,
            (
                input_row(digest, dot_key="fed.dots.duplicate"),
                input_row(
                    digest,
                    "research.fed.dots.duplicate-2",
                    dot_key="fed.dots.duplicate",
                ),
            ),
        )

    ready = report(digest, (input_row(digest),)).rows[0]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "market_research_fed_dots_revision_digest_ready",
                "market_research_fed_dots_revision_digest_stale_dot",
            ),
        )
    with pytest.raises(ValueError, match="revision_status"):
        replace(ready, revision_status="blocked")
    with pytest.raises(ValueError, match="median_rate_revision_delta"):
        replace(ready, median_rate_revision_delta=d("9.999999"))
    with pytest.raises(ValueError, match="redacted_public_dot_reference"):
        replace(ready, redacted_public_dot_reference="https://host?token=secret")

    with pytest.raises(ValueError, match="ready_dot_count"):
        replace(report(digest, (input_row(digest),)), ready_dot_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            digest,
            (
                input_row(digest, "research.fed.dots.z", dot_key="fed.dots.z"),
                input_row(digest),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))


def test_public_numeric_count_ratio_fields_are_decimals() -> None:
    digest = digest_module()
    summary = report(digest, (input_row(digest),))

    assert_decimal_public_numeric_fields(digest.MarketResearchFedDotsRevisionDigestConfig())
    assert_decimal_public_numeric_fields(input_row(digest))
    assert_decimal_public_numeric_fields(summary)
    assert_decimal_public_numeric_fields(summary.rows[0])
    assert_decimal_public_numeric_fields(summary.reason_code_counts[0])


def test_module_has_no_io_durable_store_or_execution_surfaces() -> None:
    module_path = Path(
        "src/polymarket_alpha_lab/market_research_fed_dots_revision_digest.py",
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: set[str] = set()
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    forbidden_import_fragments = (
        "db",
        "env",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "websocket",
        "aiohttp",
        "psycopg",
        "supabase",
        "sqlite",
        "sqlalchemy",
        "pathlib",
        "openai",
        "boto",
        "ccxt",
        "subprocess",
    )
    forbidden_call_or_attribute_names = (
        "connect",
        "execute",
        "fetch",
        "get",
        "post",
        "put",
        "delete",
        "request",
        "open",
        "read",
        "write",
        "mkdir",
        "unlink",
        "rename",
        "submit",
        "cancel",
        "order",
        "trade",
        "wallet",
        "broker",
        "account",
        "sign",
        "auth",
    )

    lowered_imports = tuple(name.lower() for name in imported_modules)
    lowered_surface = tuple(name.lower() for name in (*call_names, *attribute_names))
    assert not any(
        fragment in module_name
        for module_name in lowered_imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in lowered_surface)
    for forbidden in (
        "live trading",
        "wallet",
        "broker",
        "signing",
        "submit_order",
        "cancel_order",
        "account",
        "advice",
    ):
        assert forbidden not in source.lower()


def d(value: str) -> Decimal:
    return Decimal(value)


def redacted(value: str) -> str:
    import hashlib

    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def digest_module() -> Any:
    return importlib.import_module(MODULE_NAME)


def config(digest: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            digest.DEFAULT_MARKET_RESEARCH_FED_DOTS_REVISION_DIGEST_CONFIG_VERSION
        ),
        "max_dot_signal_age_seconds": d("7200.000000"),
        "material_median_rate_revision_threshold": d("0.250000"),
        "min_probability_repricing_abs": d("0.050000"),
        "min_source_count": d("2.000000"),
        "max_acknowledgement_lag_seconds": d("1800.000000"),
    }
    values.update(overrides)
    return digest.MarketResearchFedDotsRevisionDigestConfig(**values)


def input_row(
    digest: Any,
    research_key: str = "research.fed.dots.current-year",
    *,
    condition_id: str = "condition_fed_dots_current_year",
    dot_key: str = "fed.dots.current_year",
    central_bank: str = "fed",
    policy_event_key: str = "fomc.statement",
    public_dot_reference: str = "fomc-dot-plot-calendar",
    observed_at: datetime | None = None,
    acknowledged_at: object = _UNSET,
    source_count: Decimal = d("3.000000"),
    median_rate_before: Decimal = d("4.500000"),
    median_rate_after: Decimal = d("4.520000"),
    market_probability_before: Decimal = d("0.480000"),
    market_probability_after: Decimal = d("0.490000"),
    dot_config_version: str = "fed-dots-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return digest.MarketResearchFedDotsRevisionDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        dot_key=dot_key,
        central_bank=central_bank,
        policy_event_key=policy_event_key,
        public_dot_reference=public_dot_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        acknowledged_at=(
            GENERATED_AT - timedelta(minutes=20)
            if acknowledged_at is _UNSET
            else acknowledged_at
        ),
        source_count=source_count,
        median_rate_before=median_rate_before,
        median_rate_after=median_rate_after,
        market_probability_before=market_probability_before,
        market_probability_after=market_probability_after,
        dot_config_version=dot_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    digest: Any,
    rows: tuple[object, ...],
    *,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return digest.build_market_research_fed_dots_revision_digest(
        rows,
        config=cfg or config(digest),
        generated_at=generated_at,
    )


def walk_values(value: object) -> list[object]:
    if isinstance(value, dict):
        return [item for child in value.values() for item in walk_values(child)]
    if isinstance(value, list):
        return [item for child in value for item in walk_values(child)]
    return [value]


def assert_decimal_public_numeric_fields(value: object) -> None:
    assert is_dataclass(value)
    numeric_markers = (
        "age_seconds",
        "average",
        "count",
        "delta",
        "lag_seconds",
        "max_",
        "median_rate",
        "min_",
        "probability",
        "ratio",
        "threshold",
    )
    for field in fields(value):
        if field.name in ("rows", "dot_config_versions", "reason_code_counts"):
            continue
        field_value = getattr(value, field.name)
        if any(marker in field.name for marker in numeric_markers):
            if field_value is None:
                continue
            assert type(field_value) is Decimal, field.name
