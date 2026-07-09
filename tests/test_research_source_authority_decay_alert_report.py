from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_source_authority_decay_alert_report"
GENERATED_AT = datetime(2026, 7, 8, 12, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "stale_publication_watch_age_seconds": d("3600.000000"),
        "stale_publication_block_age_seconds": d("7200.000000"),
        "corroboration_pass_count": d("3.000000"),
        "corroboration_block_count": d("0.000000"),
        "contradiction_watch_threshold": d("0.300000"),
        "contradiction_block_threshold": d("0.600000"),
        "extraction_uncertainty_watch_threshold": d("0.250000"),
        "extraction_uncertainty_block_threshold": d("0.500000"),
        "resolution_watch_seconds_remaining": d("1800.000000"),
        "resolution_block_seconds_remaining": d("600.000000"),
    }
    values.update(overrides)
    return module.ResearchSourceAuthorityDecayAlertConfig(**values)


def source(
    source_family: str,
    *,
    source_authority_score: Decimal = d("0.900000"),
    publication_age_seconds: Decimal = d("900.000000"),
    corroboration_count: Decimal = d("3.000000"),
    contradiction_pressure_score: Decimal = d("0.050000"),
    extraction_uncertainty_score: Decimal = d("0.050000"),
    resolution_window_seconds: Decimal = d("3600.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceAuthorityDecayAlertInput(
        source_family=source_family,
        source_authority_score=source_authority_score,
        publication_age_seconds=publication_age_seconds,
        corroboration_count=corroboration_count,
        contradiction_pressure_score=contradiction_pressure_score,
        extraction_uncertainty_score=extraction_uncertainty_score,
        resolution_window_seconds=resolution_window_seconds,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_authority_decay_alert_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def test_empty_report_is_pass_readonly_digest_validated_and_decimal_only() -> None:
    module = api()
    result = build_report()

    assert type(result) is module.ResearchSourceAuthorityDecayAlertReport
    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.status == "pass"
    assert result.source_family_count == d("0.000000")
    assert result.pass_source_family_count == d("0.000000")
    assert result.watch_source_family_count == d("0.000000")
    assert result.block_source_family_count == d("0.000000")
    assert result.stale_publication_source_count == d("0.000000")
    assert result.missing_corroboration_source_count == d("0.000000")
    assert result.contradiction_pressure_source_count == d("0.000000")
    assert result.extraction_uncertainty_source_count == d("0.000000")
    assert result.resolution_window_source_count == d("0.000000")
    assert result.lowest_authority_usefulness_score == d("0.000000")
    assert result.highest_authority_decay_alert_score == d("0.000000")
    assert result.oldest_publication_age_seconds == d("0.000000")
    assert result.nearest_resolution_window_seconds == d("0.000000")
    assert result.reason_codes == ("research_source_authority_decay_alert_empty",)
    assert result.rows == ()
    assert len(result.derived_validation_digest) == 64
    int(result.derived_validation_digest, 16)
    assert (
        result.derived_validation_digest
        == module.research_source_authority_decay_alert_report_digest(result)
    )
    module.validate_research_source_authority_decay_alert_report_digest(result)
    payload = result.payload
    assert payload == module.research_source_authority_decay_alert_report_payload(result)
    assert payload["source_family_count"] == "0.000000"
    assert_no_numeric_objects(payload)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_alert_scores_stale_missing_contradictory_uncertain_and_near_resolution_inputs() -> None:
    result = build_report(
        source("official.filing"),
        source(
            "community.summary",
            source_authority_score=d("0.750000"),
            publication_age_seconds=d("4000.000000"),
            corroboration_count=d("2.000000"),
            contradiction_pressure_score=d("0.350000"),
            extraction_uncertainty_score=d("0.300000"),
            resolution_window_seconds=d("1200.000000"),
        ),
        source(
            "wire.disputed",
            source_authority_score=d("0.950000"),
            publication_age_seconds=d("8000.000000"),
            corroboration_count=d("0.000000"),
            contradiction_pressure_score=d("0.700000"),
            extraction_uncertainty_score=d("0.600000"),
            resolution_window_seconds=d("300.000000"),
        ),
    )

    assert result.status == "block"
    assert result.source_family_count == d("3.000000")
    assert result.pass_source_family_count == d("1.000000")
    assert result.watch_source_family_count == d("1.000000")
    assert result.block_source_family_count == d("1.000000")
    assert result.stale_publication_source_count == d("2.000000")
    assert result.missing_corroboration_source_count == d("2.000000")
    assert result.contradiction_pressure_source_count == d("2.000000")
    assert result.extraction_uncertainty_source_count == d("2.000000")
    assert result.resolution_window_source_count == d("2.000000")
    assert result.lowest_authority_usefulness_score == d("0.148833")
    assert result.highest_authority_decay_alert_score == d("0.851167")
    assert result.oldest_publication_age_seconds == d("8000.000000")
    assert result.nearest_resolution_window_seconds == d("300.000000")
    assert result.reason_codes == (
        "stale_publication_age_block",
        "missing_corroboration_block",
        "contradiction_pressure_block",
        "extraction_uncertainty_block",
        "resolution_window_block",
        "stale_publication_age_watch",
        "missing_corroboration_watch",
        "contradiction_pressure_watch",
        "extraction_uncertainty_watch",
        "resolution_window_watch",
    )

    assert tuple(row.source_family for row in result.rows) == (
        "wire.disputed",
        "community.summary",
        "official.filing",
    )
    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")

    blocked = result.rows[0]
    assert blocked.publication_age_band == "expired"
    assert blocked.corroboration_band == "missing"
    assert blocked.resolution_window_band == "immediate"
    assert blocked.authority_usefulness_score == d("0.148833")
    assert blocked.authority_decay_alert_score == d("0.851167")
    assert blocked.reason_codes == (
        "stale_publication_age_block",
        "missing_corroboration_block",
        "contradiction_pressure_block",
        "extraction_uncertainty_block",
        "resolution_window_block",
    )

    watched = result.rows[1]
    assert watched.publication_age_band == "stale"
    assert watched.corroboration_band == "thin"
    assert watched.resolution_window_band == "near"
    assert watched.authority_usefulness_score == d("0.460833")
    assert watched.authority_decay_alert_score == d("0.539167")
    assert watched.reason_codes == (
        "stale_publication_age_watch",
        "missing_corroboration_watch",
        "contradiction_pressure_watch",
        "extraction_uncertainty_watch",
        "resolution_window_watch",
    )

    passed = result.rows[2]
    assert passed.publication_age_band == "fresh"
    assert passed.corroboration_band == "corroborated"
    assert passed.resolution_window_band == "open"
    assert passed.authority_usefulness_score == d("0.853875")
    assert passed.authority_decay_alert_score == d("0.146125")
    assert passed.reason_codes == ("source_authority_usefulness_healthy",)


def test_payload_is_deterministic_public_safe_and_digest_validated() -> None:
    module = api()
    report_a = build_report(
        source("official.filing"),
        source(
            "wire.disputed",
            source_authority_score=d("0.950000"),
            publication_age_seconds=d("8000.000000"),
            corroboration_count=d("0.000000"),
            contradiction_pressure_score=d("0.700000"),
            extraction_uncertainty_score=d("0.600000"),
            resolution_window_seconds=d("300.000000"),
        ),
    )
    report_b = build_report(
        source(
            "wire.disputed",
            source_authority_score=d("0.950000"),
            publication_age_seconds=d("8000.000000"),
            corroboration_count=d("0.000000"),
            contradiction_pressure_score=d("0.700000"),
            extraction_uncertainty_score=d("0.600000"),
            resolution_window_seconds=d("300.000000"),
        ),
        source("official.filing"),
    )

    payload_a = module.research_source_authority_decay_alert_report_payload(report_a)
    payload_b = module.research_source_authority_decay_alert_report_payload(report_b)
    digest_a = module.research_source_authority_decay_alert_report_digest(report_a)
    digest_b = module.research_source_authority_decay_alert_report_digest(report_b)
    encoded = json.dumps(payload_a, sort_keys=True, allow_nan=False)

    assert payload_a == payload_b
    assert digest_a == digest_b
    assert payload_a["derived_validation_digest"] == digest_a
    assert len(digest_a) == 64
    int(digest_a, 16)
    assert payload_a["generated_at"] == "2026-07-08T12:30:00+00:00"
    assert payload_a["rows"][0]["authority_decay_alert_score"] == "0.851167"
    assert module.research_source_authority_decay_alert_report_payload(payload_a) == payload_a
    module.validate_research_source_authority_decay_alert_public_payload(payload_a)
    assert_no_numeric_objects(payload_a)

    unsafe_keys = {
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "url",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order_id",
        "trade_id",
        "live_surface",
    }
    public_fields = {
        field.name for cls in (type(report_a), type(report_a.rows[0])) for field in fields(cls)
    }
    assert unsafe_keys.isdisjoint(public_fields)
    assert_payload_has_no_leaked_values(payload_a)
    for forbidden in unsafe_keys | {"http://", "https://", "postgres://", "://"}:
        assert forbidden not in encoded.lower()

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_source_authority_decay_alert_report_payload(
            {**payload_a, "market_id": "hidden"},
        )
    with pytest.raises(ValueError, match="numeric values"):
        module.research_source_authority_decay_alert_report_payload(
            {**payload_a, "source_family_count": 2},
        )
    with pytest.raises(ValueError, match="readonly"):
        module.research_source_authority_decay_alert_report_payload(
            {**payload_a, "readonly": False},
        )


def test_validation_requires_decimal_inputs_hard_flags_statuses_and_safe_labels() -> None:
    module = api()

    with pytest.raises(ValueError, match="source_authority_score must be a Decimal"):
        source("official.filing", source_authority_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="publication_age_seconds must be a Decimal"):
        source("official.filing", publication_age_seconds=900)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_authority_score must be a Decimal"):
        source("official.filing", source_authority_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="publication_age_seconds must be nonnegative"):
        source("official.filing", publication_age_seconds=d("-1.000000"))
    with pytest.raises(ValueError, match="corroboration_count must be an integer Decimal"):
        source("official.filing", corroboration_count=d("1.500000"))
    with pytest.raises(ValueError, match="source_authority_score must be between zero and one"):
        source("official.filing", source_authority_score=d("1.000001"))
    with pytest.raises(ValueError, match="source_family contains unsafe text"):
        source("market.slug")
    with pytest.raises(ValueError, match="source_family contains unsafe text"):
        source("https://official.example/report")
    with pytest.raises(ValueError, match="paper_only"):
        source("official.filing", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        source("official.filing", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        source("official.filing", readonly=False)
    with pytest.raises(ValueError, match="stale_publication_watch_age_seconds"):
        config(stale_publication_watch_age_seconds=d("7200.000000"))
    with pytest.raises(ValueError, match="corroboration_block_count"):
        config(corroboration_block_count=d("3.000000"))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_source_authority_decay_alert_report(
            (),
            generated_at=datetime(2026, 7, 8, 12, 30),
        )
    with pytest.raises(ValueError, match="config must be"):
        module.build_research_source_authority_decay_alert_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    result = build_report(source("official.filing"))
    with pytest.raises(ValueError, match="status"):
        replace(result, status="ready")
    with pytest.raises(ValueError, match="status"):
        replace(result.rows[0], status="blocked")
    with pytest.raises(ValueError, match="authority_decay_alert_score"):
        replace(result.rows[0], authority_decay_alert_score=d("0.999999"))


def test_exports_frozen_dataclasses_and_status_vocabulary() -> None:
    module = api()
    result = build_report(source("official.filing"))

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_AUTHORITY_DECAY_ALERT_REPORT_CONFIG_VERSION",
        "RESEARCH_SOURCE_AUTHORITY_DECAY_ALERT_STATUSES",
        "ResearchSourceAuthorityDecayAlertConfig",
        "ResearchSourceAuthorityDecayAlertInput",
        "ResearchSourceAuthorityDecayAlertReport",
        "ResearchSourceAuthorityDecayAlertRow",
        "build_research_source_authority_decay_alert_report",
        "research_source_authority_decay_alert_report_digest",
        "research_source_authority_decay_alert_report_payload",
        "validate_research_source_authority_decay_alert_public_payload",
        "validate_research_source_authority_decay_alert_report_digest",
    )
    assert module.RESEARCH_SOURCE_AUTHORITY_DECAY_ALERT_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert is_dataclass(config())
    assert is_dataclass(source("official.filing"))
    assert is_dataclass(result)
    assert is_dataclass(result.rows[0])

    with pytest.raises(FrozenInstanceError):
        result.status = "watch"
    with pytest.raises(FrozenInstanceError):
        result.rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        config().stale_publication_watch_age_seconds = d("1.000000")


def test_module_scope_is_pure_public_safe_report_only() -> None:
    module = api()
    source_text = module.__loader__.get_source(module.__name__)
    assert source_text is not None
    tree = ast.parse(source_text)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
                "scrape",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def assert_no_numeric_objects(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_numeric_objects(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_numeric_objects(item)
    else:
        assert type(value) not in (Decimal, int, float)


def assert_payload_has_no_leaked_values(value: object) -> None:
    forbidden_fragments = (
        "http://",
        "https://",
        "postgres://",
        "candidate-",
        "candidate_id",
        "market-",
        "market_id",
        "market_slug",
        "question",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    )
    if isinstance(value, dict):
        for item in value.values():
            assert_payload_has_no_leaked_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_payload_has_no_leaked_values(item)
    elif isinstance(value, str):
        lowered = value.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)
