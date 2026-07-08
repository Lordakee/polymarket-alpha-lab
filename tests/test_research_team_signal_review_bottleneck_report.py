from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_signal_review_bottleneck_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 14, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_signal_review_bottleneck_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(**overrides: object):
    module = api()
    values = {
        "team_key": "macro_research",
        "domain_key": "rates_policy",
        "aggregate_pending_signals": d("4.000000"),
        "review_capacity_slots": d("10.000000"),
        "confidence_min": d("0.720000"),
        "confidence_max": d("0.810000"),
        "mean_evidence_age_seconds": d("900.000000"),
        "contradiction_pressure": d("0.100000"),
        "domain_expertise": d("0.900000"),
    }
    values.update(overrides)
    return module.ResearchTeamSignalReviewBottleneckInput(**values)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-team-signal-review-bottleneck-report-v0",
        "pass_bottleneck_score_threshold": d("0.350000"),
        "block_bottleneck_score_threshold": d("0.750000"),
        "watch_capacity_load_ratio": d("0.650000"),
        "block_capacity_load_ratio": d("1.000000"),
        "watch_confidence_dispersion": d("0.200000"),
        "block_confidence_dispersion": d("0.400000"),
        "watch_evidence_age_seconds": d("3600.000000"),
        "block_evidence_age_seconds": d("7200.000000"),
        "watch_contradiction_pressure": d("0.300000"),
        "block_contradiction_pressure": d("0.600000"),
        "watch_min_domain_expertise": d("0.650000"),
        "block_min_domain_expertise": d("0.400000"),
    }
    values.update(overrides)
    return module.ResearchTeamSignalReviewBottleneckConfig(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_signal_review_bottleneck_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def walk_payload(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(walk_payload(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(walk_payload(item))
        return tuple(nested)
    return (value,)


def assert_no_unsafe_public_surface(value: object) -> None:
    forbidden = (
        "raw",
        "event",
        "market",
        "source",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "buy",
        "sell",
        "recommendation",
        "sizing",
        "position",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lower_key = key.lower()
            assert not any(fragment in lower_key for fragment in forbidden), lower_key
            assert_no_unsafe_public_surface(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_unsafe_public_surface(item)
        return
    if isinstance(value, str):
        lower_value = value.lower()
        assert not any(fragment in lower_value for fragment in forbidden), lower_value


def assert_decimal_fields_are_plain(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if isinstance(item, Decimal):
            assert type(item) is Decimal, field.name


def test_public_api_declares_report_only_signal_review_bottleneck_contract() -> None:
    module = api()

    assert module.DEFAULT_RESEARCH_TEAM_SIGNAL_REVIEW_BOTTLENECK_REPORT_CONFIG_VERSION == (
        "research-team-signal-review-bottleneck-report-v0"
    )
    assert module.STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_SIGNAL_REVIEW_BOTTLENECK_REPORT_CONFIG_VERSION",
        "STATUSES",
        "ResearchTeamSignalReviewBottleneckConfig",
        "ResearchTeamSignalReviewBottleneckInput",
        "ResearchTeamSignalReviewBottleneckReasonCodeCount",
        "ResearchTeamSignalReviewBottleneckReport",
        "ResearchTeamSignalReviewBottleneckRow",
        "build_research_team_signal_review_bottleneck_report",
        "research_team_signal_review_bottleneck_report_payload",
    )

    defaults = {
        field.name: field.default
        for field in fields(module.ResearchTeamSignalReviewBottleneckConfig)
    }
    assert defaults["paper_only"] is True
    assert defaults["report_only"] is True
    assert defaults["readonly"] is True


def test_summarizes_team_signal_review_bottlenecks_with_public_safe_aggregates() -> None:
    report = build_report(
        observation(),
        observation(
            team_key="sports_research",
            domain_key="football_injuries",
            aggregate_pending_signals=d("8.000000"),
            review_capacity_slots=d("10.000000"),
            confidence_min=d("0.430000"),
            confidence_max=d("0.710000"),
            mean_evidence_age_seconds=d("4500.000000"),
            contradiction_pressure=d("0.420000"),
            domain_expertise=d("0.610000"),
        ),
        observation(
            team_key="crypto_research",
            domain_key="stablecoin_policy",
            aggregate_pending_signals=d("13.000000"),
            review_capacity_slots=d("10.000000"),
            confidence_min=d("0.150000"),
            confidence_max=d("0.840000"),
            mean_evidence_age_seconds=d("9000.000000"),
            contradiction_pressure=d("0.750000"),
            domain_expertise=d("0.350000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "research-team-signal-review-bottleneck-report-v0"
    )
    assert report.status == "block"
    assert report.team_domain_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.total_pending_signals == d("25.000000")
    assert report.total_review_capacity_slots == d("30.000000")
    assert report.average_capacity_load_ratio == d("0.833333")
    assert report.average_confidence_dispersion == d("0.353333")
    assert report.average_evidence_age_seconds == d("4800.000000")
    assert report.average_contradiction_pressure == d("0.423333")
    assert report.average_domain_expertise == d("0.620000")
    assert report.max_bottleneck_score == d("0.998500")
    assert report.reason_codes == (
        "signal_review_bottleneck_report_block_rows",
        "signal_review_bottleneck_report_watch_rows",
    )
    assert len(report.public_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.team_key, row.domain_key) for row in report.rows) == (
        ("crypto_research", "stablecoin_policy"),
        ("sports_research", "football_injuries"),
        ("macro_research", "rates_policy"),
    )
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.capacity_load_ratio for row in report.rows) == (
        d("1.300000"),
        d("0.800000"),
        d("0.400000"),
    )
    assert tuple(row.confidence_dispersion for row in report.rows) == (
        d("0.690000"),
        d("0.280000"),
        d("0.090000"),
    )
    assert tuple(row.bottleneck_score for row in report.rows) == (
        d("0.998500"),
        d("0.613000"),
        d("0.176500"),
    )
    assert report.rows[0].reason_codes == (
        "capacity_load_block",
        "confidence_dispersion_block",
        "evidence_age_block",
        "contradiction_pressure_block",
        "domain_expertise_block",
    )
    assert report.rows[1].reason_codes == (
        "capacity_load_watch",
        "confidence_dispersion_watch",
        "evidence_age_watch",
        "contradiction_pressure_watch",
        "domain_expertise_watch",
    )
    assert report.rows[2].reason_codes == ("signal_review_bottleneck_pass",)

    reason_counts = {item.reason_code: item for item in report.reason_code_counts}
    assert reason_counts["capacity_load_block"].count == d("1.000000")
    assert reason_counts["capacity_load_block"].team_domain_ratio == d("0.333333")
    assert reason_counts["signal_review_bottleneck_pass"].count == d("1.000000")
    for value in (report, *report.rows, *report.reason_code_counts):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
        assert_decimal_fields_are_plain(value)


def test_payload_and_digest_are_deterministic_and_json_safe() -> None:
    inputs = (
        observation(
            team_key="sports_research",
            domain_key="football_injuries",
            aggregate_pending_signals=d("8.000000"),
            confidence_min=d("0.430000"),
            confidence_max=d("0.710000"),
            mean_evidence_age_seconds=d("4500.000000"),
            contradiction_pressure=d("0.420000"),
            domain_expertise=d("0.610000"),
        ),
        observation(),
    )

    first = build_report(*inputs)
    second = build_report(*reversed(inputs), generated_at=GENERATED_AT)
    first_payload = api().research_team_signal_review_bottleneck_report_payload(first)
    second_payload = api().research_team_signal_review_bottleneck_report_payload(second)

    assert first == second
    assert first.public_digest == second.public_digest
    assert first_payload == second_payload
    assert json.loads(json.dumps(first_payload, sort_keys=True)) == first_payload
    assert first_payload["public_digest"] == first.public_digest
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert "8.000000" in walk_payload(first_payload)
    assert all(type(value) is not Decimal for value in walk_payload(first_payload))
    assert_no_unsafe_public_surface(first_payload)

    assert api().research_team_signal_review_bottleneck_report_payload(first_payload) == (
        first_payload
    )


def test_empty_input_returns_report_only_block_without_raw_identifiers() -> None:
    report = build_report()

    assert report.status == "block"
    assert report.team_domain_count == ZERO
    assert report.pass_count == ZERO
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.rows == ()
    assert report.reason_codes == ("signal_review_bottleneck_no_inputs",)
    assert report.reason_code_counts[0].reason_code == (
        "signal_review_bottleneck_no_inputs"
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert_no_unsafe_public_surface(
        api().research_team_signal_review_bottleneck_report_payload(report),
    )


def test_statuses_are_exactly_pass_watch_block_and_config_thresholds_are_respected() -> None:
    module = api()

    assert module.STATUSES == ("pass", "watch", "block")
    assert build_report(observation()).status == "pass"
    assert build_report(
        observation(
            aggregate_pending_signals=d("8.000000"),
            confidence_min=d("0.430000"),
            confidence_max=d("0.710000"),
            mean_evidence_age_seconds=d("4500.000000"),
            contradiction_pressure=d("0.420000"),
            domain_expertise=d("0.610000"),
        ),
    ).status == "watch"
    assert build_report(
        observation(
            aggregate_pending_signals=d("13.000000"),
            confidence_min=d("0.150000"),
            confidence_max=d("0.840000"),
            mean_evidence_age_seconds=d("9000.000000"),
            contradiction_pressure=d("0.750000"),
            domain_expertise=d("0.350000"),
        ),
    ).status == "block"

    relaxed = config(
        pass_bottleneck_score_threshold=d("0.650000"),
        block_bottleneck_score_threshold=d("0.950000"),
        watch_capacity_load_ratio=d("0.900000"),
        block_capacity_load_ratio=d("1.500000"),
        watch_confidence_dispersion=d("0.350000"),
        block_confidence_dispersion=d("0.800000"),
        watch_evidence_age_seconds=d("5000.000000"),
        block_evidence_age_seconds=d("10000.000000"),
        watch_contradiction_pressure=d("0.500000"),
        block_contradiction_pressure=d("0.900000"),
        watch_min_domain_expertise=d("0.500000"),
        block_min_domain_expertise=d("0.200000"),
    )
    report = build_report(
        observation(
            aggregate_pending_signals=d("8.000000"),
            confidence_min=d("0.430000"),
            confidence_max=d("0.710000"),
            mean_evidence_age_seconds=d("4500.000000"),
            contradiction_pressure=d("0.420000"),
            domain_expertise=d("0.610000"),
        ),
        cfg=relaxed,
    )

    assert report.status == "pass"
    assert report.rows[0].status == "pass"
    assert report.rows[0].reason_codes == ("signal_review_bottleneck_pass",)
    assert report.reason_codes == ("signal_review_bottleneck_report_pass",)


def test_validation_rejects_non_decimal_subclasses_flags_and_raw_identifiers() -> None:
    module = api()
    report = build_report(observation())

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.reason_code_counts[0].count = d("2.000000")  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclass"):
        type("BadInput", (module.ResearchTeamSignalReviewBottleneckInput,), {})
    with pytest.raises(ValueError, match="Decimal"):
        observation(aggregate_pending_signals=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        observation(contradiction_pressure=0.2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        observation(review_capacity_slots=_DecimalSubclass("10.000000"))
    with pytest.raises(ValueError, match="plain str"):
        observation(team_key=_StringSubclass("macro_research"))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(observation(), generated_at=_DatetimeSubclass(2026, 7, 8, 14, 30))
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="inputs must contain"):
        build_report("not-an-input")
    with pytest.raises(ValueError, match="duplicate team_key/domain_key"):
        build_report(observation(), observation())
    with pytest.raises(ValueError, match="raw identifiers"):
        observation(team_key="raw_event_42")
    with pytest.raises(ValueError, match="raw identifiers"):
        observation(domain_key="source_reference")
    with pytest.raises(ValueError, match="pass_bottleneck_score_threshold"):
        config(
            pass_bottleneck_score_threshold=d("0.800000"),
            block_bottleneck_score_threshold=d("0.700000"),
        )

    valid_row = report.rows[0]
    with pytest.raises(ValueError, match="bottleneck_score must match"):
        replace(valid_row, bottleneck_score=d("0.900000"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(valid_row, reason_codes=("capacity_load_watch",))


def test_module_has_no_write_network_wallet_order_or_execution_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    banned_import_roots = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "web3",
        "subprocess",
    }
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert imports.isdisjoint(banned_import_roots)

    banned_call_names = {
        "connect",
        "execute",
        "executemany",
        "commit",
        "rollback",
        "send",
        "post",
        "put",
        "patch",
        "delete",
        "request",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in banned_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in banned_call_names

    lowered = source.lower()
    for term in (
        "wallet",
        "auth",
        "order",
        "trade",
        "live execution",
        "buy",
        "sell",
        "recommendation",
        "position sizing",
    ):
        assert term not in lowered
