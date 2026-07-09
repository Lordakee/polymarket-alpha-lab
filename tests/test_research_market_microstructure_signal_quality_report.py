from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_market_microstructure_signal_quality_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_market_microstructure_signal_quality_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 11, 58, tzinfo=UTC)


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def cfg(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": "research-market-microstructure-signal-quality-report-v0",
        "watch_spread_instability_score": d("0.300000"),
        "block_spread_instability_score": d("0.650000"),
        "watch_depth_imbalance_score": d("0.300000"),
        "block_depth_imbalance_score": d("0.650000"),
        "watch_update_age_seconds": d("60.000000"),
        "block_update_age_seconds": d("300.000000"),
        "watch_unattributed_movement_score": d("0.250000"),
        "block_unattributed_movement_score": d("0.600000"),
        "block_signal_count_threshold": d("3"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchMarketMicrostructureSignalQualityConfig(**values)


def observation(
    *,
    observed_at: datetime = OBSERVED_AT,
    spread_stability_score: Decimal = d("0.900000"),
    depth_balance_score: Decimal = d("0.950000"),
    update_age_seconds: Decimal = d("20.000000"),
    movement_magnitude_score: Decimal = d("0.200000"),
    movement_attribution_score: Decimal = d("0.900000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketMicrostructureSignalObservation(
        observed_at=observed_at,
        spread_stability_score=spread_stability_score,
        depth_balance_score=depth_balance_score,
        update_age_seconds=update_age_seconds,
        movement_magnitude_score=movement_magnitude_score,
        movement_attribution_score=movement_attribution_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*observations: object, generated_at: datetime = GENERATED_AT, config: object | None = None):
    module = api()
    return module.build_research_market_microstructure_signal_quality_report(
        observations,
        generated_at=generated_at,
        config=config or cfg(),
    )


def assert_no_public_number_payload(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"payload numeric was not serialized as string: {value!r}")
    if isinstance(value, dict):
        for item_value in value.values():
            assert_no_public_number_payload(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_public_number_payload(item_value)


def assert_no_forbidden_public_surface(value: Any) -> None:
    forbidden_fragments = (
        "raw",
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "private",
        "auth",
        "wallet",
        "network",
        "database",
        "order",
        "buy",
        "sell",
        "trade",
        "position",
        "recommend",
        "sizing",
        "live",
    )
    if isinstance(value, dict):
        for key, item_value in value.items():
            lowered = key.lower()
            for fragment in forbidden_fragments:
                assert fragment not in lowered, key
            assert_no_forbidden_public_surface(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_forbidden_public_surface(item_value)
        return
    if isinstance(value, str):
        lowered = value.lower()
        assert "://" not in lowered
        for fragment in forbidden_fragments:
            assert fragment not in lowered, value


def assert_decimal_public_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {"rows", "reason_codes"}:
            continue
        if any(
            marker in field.name
            for marker in (
                "count",
                "score",
                "seconds",
                "age",
                "imbalance",
            )
        ):
            assert type(getattr(value, field.name)) is Decimal, field.name


def resign_payload(payload: dict[str, Any]) -> None:
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    canonical = json.dumps(
        unsigned_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    payload["derived_validation_digest"] = hashlib.sha256(
        canonical.encode("utf-8"),
    ).hexdigest()


def test_empty_input_blocks_research_triage_with_report_only_decimal_digest() -> None:
    module = api()
    empty_report = report()

    assert is_dataclass(empty_report)
    assert empty_report.generated_at == GENERATED_AT
    assert empty_report.config_version == (
        "research-market-microstructure-signal-quality-report-v0"
    )
    assert empty_report.status == "block"
    assert empty_report.reason_codes == ("no_microstructure_signal_quality_observations",)
    assert empty_report.observation_count == d("0.000000")
    assert empty_report.pass_count == d("0.000000")
    assert empty_report.watch_count == d("0.000000")
    assert empty_report.block_count == d("0.000000")
    assert empty_report.max_spread_instability_score == d("0.000000")
    assert empty_report.max_depth_imbalance_score == d("0.000000")
    assert empty_report.max_update_age_seconds == d("0.000000")
    assert empty_report.max_unattributed_movement_score == d("0.000000")
    assert empty_report.rows == ()
    assert empty_report.paper_only is True
    assert empty_report.report_only is True
    assert empty_report.readonly is True
    assert_decimal_public_fields(empty_report)

    payload = module.research_market_microstructure_signal_quality_report_payload(
        empty_report,
    )
    digest_value = module.research_market_microstructure_signal_quality_report_digest(
        empty_report,
    )
    json.dumps(payload, sort_keys=True)
    assert_no_public_number_payload(payload)
    assert_no_forbidden_public_surface(payload)
    assert payload["status"] == "block"
    assert payload["observation_count"] == "0.000000"
    assert payload["derived_validation_digest"] == digest_value
    assert len(digest_value) == 64


def test_report_scores_spread_depth_update_age_and_movement_attribution() -> None:
    passed = observation(observed_at=GENERATED_AT - timedelta(seconds=20))
    watched = observation(
        observed_at=GENERATED_AT - timedelta(seconds=120),
        spread_stability_score=d("0.550000"),
        depth_balance_score=d("0.800000"),
        update_age_seconds=d("120.000000"),
        movement_magnitude_score=d("0.300000"),
        movement_attribution_score=d("0.900000"),
    )
    blocked = observation(
        observed_at=GENERATED_AT - timedelta(seconds=10),
        spread_stability_score=d("0.250000"),
        depth_balance_score=d("0.200000"),
        update_age_seconds=d("400.000000"),
        movement_magnitude_score=d("0.800000"),
        movement_attribution_score=d("0.100000"),
    )

    built = report(passed, watched, blocked)

    assert built.status == "block"
    assert built.observation_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.spread_inconsistent_count == d("2.000000")
    assert built.depth_unbalanced_count == d("1.000000")
    assert built.update_stale_count == d("2.000000")
    assert built.movement_unattributed_count == d("1.000000")
    assert built.max_spread_instability_score == d("0.750000")
    assert built.max_depth_imbalance_score == d("0.800000")
    assert built.max_update_age_seconds == d("400.000000")
    assert built.max_unattributed_movement_score == d("0.720000")
    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")

    blocked_row, watched_row, passed_row = built.rows
    assert blocked_row.quality_signal_count == d("4.000000")
    assert blocked_row.status == "block"
    assert blocked_row.spread_inconsistent is True
    assert blocked_row.depth_unbalanced is True
    assert blocked_row.update_stale is True
    assert blocked_row.movement_unattributed is True
    assert blocked_row.reason_codes == (
        "spread_instability_block",
        "depth_imbalance_block",
        "update_age_block",
        "movement_attribution_block",
        "microstructure_signal_quality_block",
    )

    assert watched_row.quality_signal_count == d("2.000000")
    assert watched_row.status == "watch"
    assert watched_row.reason_codes == (
        "spread_instability_watch",
        "update_age_watch",
        "microstructure_signal_quality_watch",
    )
    assert passed_row.status == "pass"
    assert passed_row.reason_codes == ("microstructure_signal_quality_pass",)


def test_payload_is_decimal_string_sanitized_deterministic_and_digest_checked() -> None:
    module = api()
    observations = (
        observation(spread_stability_score=d("0.550000")),
        observation(
            observed_at=GENERATED_AT - timedelta(seconds=30),
            depth_balance_score=d("0.200000"),
            update_age_seconds=d("360.000000"),
            movement_magnitude_score=d("0.800000"),
            movement_attribution_score=d("0.900000"),
        ),
    )
    first = report(*observations)
    second = report(*reversed(observations))

    payload = first.payload
    json.dumps(payload, sort_keys=True)
    assert payload["observation_count"] == "2.000000"
    assert payload["rows"][0]["status"] == "block"
    assert payload["rows"][0]["depth_imbalance_score"] == "0.800000"
    assert payload["rows"][1]["spread_instability_score"] == "0.450000"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert first.derived_validation_digest == second.derived_validation_digest
    assert module.research_market_microstructure_signal_quality_report_digest(first) == (
        first.derived_validation_digest
    )
    assert_no_public_number_payload(payload)
    assert_no_forbidden_public_surface(payload)
    assert_decimal_public_fields(first)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)

    tampered = dict(payload)
    tampered["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_market_microstructure_signal_quality_public_payload(
            tampered,
        )

    decimal_payload = dict(payload)
    decimal_payload["observation_count"] = d("2.000000")
    decimal_payload["derived_validation_digest"] = first.derived_validation_digest
    with pytest.raises(ValueError, match="JSON-ready"):
        module.validate_research_market_microstructure_signal_quality_public_payload(
            decimal_payload,
        )

    unsafe_payload = dict(payload)
    unsafe_payload["market_slug"] = "leaky-market"
    unsafe_payload["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="unsafe"):
        module.validate_research_market_microstructure_signal_quality_public_payload(
            unsafe_payload,
        )


def test_public_payload_requires_exact_report_and_row_schemas() -> None:
    module = api()
    payload = report(observation()).payload

    mutations = (
        lambda value: value.__setitem__("note", "pass"),
        lambda value: value.pop("reason_codes"),
        lambda value: value["rows"][0].__setitem__("memo", "pass"),
        lambda value: value["rows"][0].pop("reason_codes"),
    )
    for mutate in mutations:
        candidate = json.loads(json.dumps(payload))
        mutate(candidate)
        resign_payload(candidate)
        with pytest.raises(ValueError, match="exact schema"):
            module.validate_research_market_microstructure_signal_quality_public_payload(
                candidate,
            )


@pytest.mark.parametrize(
    ("mutate", "error_match"),
    (
        (
            lambda value: value["rows"][0].__setitem__("report_only", False),
            "report_only",
        ),
        (
            lambda value: value.__setitem__("observation_count", "1"),
            "observation_count",
        ),
        (
            lambda value: value.__setitem__("observation_count", "2.000000"),
            "observation_count",
        ),
        (
            lambda value: value.__setitem__(
                "generated_at",
                "2026-07-08T12:00:00Z",
            ),
            "generated_at",
        ),
        (
            lambda value: value["rows"][0].__setitem__(
                "reason_codes",
                ["microstructure_signal_quality_watch"],
            ),
            "reason_codes",
        ),
    ),
)
def test_public_payload_rejects_resigned_canonical_and_semantic_drift(
    mutate: Any,
    error_match: str,
) -> None:
    module = api()
    candidate = json.loads(json.dumps(report(observation()).payload))
    mutate(candidate)
    resign_payload(candidate)

    with pytest.raises(ValueError, match=error_match):
        module.validate_research_market_microstructure_signal_quality_public_payload(
            candidate,
        )


def test_dataclasses_are_frozen_and_reject_subclassing_and_bad_flags() -> None:
    module = api()
    built = report(observation())

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(module.ResearchMarketMicrostructureSignalQualityConfig):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        observation(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(built.rows[0], readonly=False)


def test_strict_types_unsafe_inputs_and_live_surfaces_are_rejected() -> None:
    module = api()
    with pytest.raises(ValueError, match="spread_stability_score must be exactly Decimal"):
        observation(spread_stability_score=_DecimalSubclass("0.400000"))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="depth_balance_score must be a Decimal"):
        observation(depth_balance_score=0.4)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="movement_attribution_score"):
        observation(movement_attribution_score=d("1.100000"))

    with pytest.raises(ValueError, match="timezone-aware"):
        observation(observed_at=datetime(2026, 7, 8, 11, 58))

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report(observation(), generated_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC))

    with pytest.raises(ValueError, match="utcoffset"):
        observation(observed_at=datetime(2026, 7, 8, 11, 58, tzinfo=_NoneOffsetTz()))

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="block_spread_instability_score"):
        cfg(block_spread_instability_score=d("0.300000"))

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    forbidden_imports = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "web3",
        "py_clob_client",
    }
    assert imported_roots.isdisjoint(forbidden_imports)

    forbidden_field_fragments = {
        "raw",
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "position",
        "recommend",
        "sizing",
        "live",
    }
    for cls in (
        module.ResearchMarketMicrostructureSignalQualityConfig,
        module.ResearchMarketMicrostructureSignalObservation,
        module.ResearchMarketMicrostructureSignalQualityRow,
        module.ResearchMarketMicrostructureSignalQualityReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in forbidden_field_fragments)

    public_names = set(module.__all__)
    forbidden_public_name_fragments = {
        "client",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "recommend",
        "sizing",
        "live",
    }
    for name in public_names:
        lowered = name.lower()
        assert not any(fragment in lowered for fragment in forbidden_public_name_fragments)
