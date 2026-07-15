from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Context, Decimal, localcontext
from hashlib import sha256
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 8, 13, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt):  # type: ignore[no-untyped-def]
        return None

    def dst(self, dt):  # type: ignore[no-untyped-def]
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_edge_persistence_monitor_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def redacted_source_ref(value: str) -> str:
    return f"source_ref_{sha256(value.encode('utf-8')).hexdigest()[:16]}"


def resign_payload(payload: dict[str, object]) -> dict[str, object]:
    unsigned = {
        key: value for key, value in payload.items() if key != "payload_sha256"
    }
    payload["payload_sha256"] = sha256(
        json.dumps(
            unsigned,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()
    return payload


def config(**overrides: object):
    monitor = api()
    values = {
        "config_version": "research-strategy-edge-persistence-monitor-report-v0",
        "persisted_edge_floor": d("0.050000"),
        "watch_edge_floor": d("0.015000"),
        "max_evidence_age_hours": d("24.000000"),
        "evidence_age_drag_cap": d("0.040000"),
        "market_movement_watch_probability": d("0.040000"),
        "cost_drag_watch_probability": d("0.020000"),
        "liquidity_watch_floor": d("0.500000"),
        "liquidity_block_floor": d("0.200000"),
        "liquidity_drag_cap": d("0.020000"),
        "confidence_haircut_watch_probability": d("0.030000"),
        "resolution_ambiguity_watch_score": d("0.500000"),
        "resolution_ambiguity_block_score": d("0.750000"),
        "resolution_ambiguity_drag_cap": d("0.030000"),
    }
    values.update(overrides)
    return monitor.ResearchStrategyEdgePersistenceMonitorConfig(**values)


def observation(**overrides: object):
    monitor = api()
    values = {
        "source_ref": "candidate-raw-alpha-market-slug-secret-token",
        "observed_at": GENERATED_AT - timedelta(hours=6),
        "baseline_edge_probability": d("0.120000"),
        "current_edge_probability": d("0.100000"),
        "evidence_age_hours": d("6.000000"),
        "cost_drag_probability": d("0.010000"),
        "liquidity_quality_score": d("0.850000"),
        "confidence_haircut_probability": d("0.005000"),
        "resolution_ambiguity_score": d("0.100000"),
    }
    values.update(overrides)
    return monitor.ResearchStrategyEdgePersistenceObservation(**values)


def report(*rows, cfg=None, generated_at: datetime = GENERATED_AT):
    monitor = api()
    return monitor.build_research_strategy_edge_persistence_monitor_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_report_monitors_edge_persistence_drivers_without_raw_public_refs() -> None:
    blocked_ref = "candidate-raw-block-market-question-url-token"
    watch_ref = "candidate-raw-watch-market-question-url-token"
    pass_ref = "candidate-raw-pass-market-question-url-token"

    monitor_report = report(
        observation(
            source_ref=pass_ref,
            baseline_edge_probability=d("0.120000"),
            current_edge_probability=d("0.100000"),
            evidence_age_hours=d("6.000000"),
            cost_drag_probability=d("0.010000"),
            liquidity_quality_score=d("0.850000"),
            confidence_haircut_probability=d("0.005000"),
            resolution_ambiguity_score=d("0.100000"),
        ),
        observation(
            source_ref=watch_ref,
            observed_at=GENERATED_AT - timedelta(hours=30),
            baseline_edge_probability=d("0.140000"),
            current_edge_probability=d("0.120000"),
            evidence_age_hours=d("30.000000"),
            cost_drag_probability=d("0.005000"),
            liquidity_quality_score=d("0.900000"),
            confidence_haircut_probability=d("0.005000"),
            resolution_ambiguity_score=d("0.100000"),
        ),
        observation(
            source_ref=blocked_ref,
            observed_at=GENERATED_AT - timedelta(hours=20),
            baseline_edge_probability=d("0.090000"),
            current_edge_probability=d("0.050000"),
            evidence_age_hours=d("20.000000"),
            cost_drag_probability=d("0.020000"),
            liquidity_quality_score=d("0.100000"),
            confidence_haircut_probability=d("0.000000"),
            resolution_ambiguity_score=d("0.000000"),
        ),
    )

    assert is_dataclass(monitor_report)
    assert monitor_report.generated_at == GENERATED_AT
    assert monitor_report.source_row_count == d("3")
    assert monitor_report.pass_count == d("1")
    assert monitor_report.watch_count == d("1")
    assert monitor_report.block_count == d("1")
    assert monitor_report.persisted_edge_count == d("2")
    assert monitor_report.mean_adjusted_edge_probability == d("0.037556")
    assert monitor_report.min_adjusted_edge_probability == d("-0.021333")
    assert monitor_report.status == "block"
    assert monitor_report.reason_codes == (
        "edge_persistence_block",
        "edge_persistence_watch",
        "evidence_aging_watch",
        "edge_movement_watch",
        "cost_drag_watch",
        "liquidity_quality_block",
    )
    assert monitor_report.paper_only is True
    assert monitor_report.report_only is True
    assert monitor_report.readonly is True

    first, second, third = monitor_report.rows
    assert first.redacted_source_ref == redacted_source_ref(blocked_ref)
    assert first.persistence_status == "block"
    assert first.adjusted_edge_probability == d("-0.021333")
    assert first.reason_codes == (
        "edge_not_persistent",
        "edge_movement_watch",
        "cost_drag_watch",
        "liquidity_quality_block",
    )
    assert second.redacted_source_ref == redacted_source_ref(watch_ref)
    assert second.persistence_status == "watch"
    assert second.adjusted_edge_probability == d("0.065000")
    assert second.reason_codes == (
        "edge_persistent",
        "evidence_aging_watch",
    )
    assert third.redacted_source_ref == redacted_source_ref(pass_ref)
    assert third.persistence_status == "pass"
    assert third.adjusted_edge_probability == d("0.069000")
    assert third.reason_codes == ("edge_persistent",)

    payload = api().research_strategy_edge_persistence_monitor_report_payload(
        monitor_report,
    )
    public_text = repr(payload).lower()
    for raw_ref in (blocked_ref, watch_ref, pass_ref):
        assert raw_ref not in public_text
    for forbidden in ("market-question", "url", "token"):
        assert forbidden not in public_text


def test_report_serializes_deterministic_json_and_validates_sha256_digest() -> None:
    monitor = api()
    monitor_report = report(
        observation(),
        generated_at=datetime(2026, 7, 8, 6, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = monitor.research_strategy_edge_persistence_monitor_report_payload(
        monitor_report,
    )
    canonical_json = monitor.research_strategy_edge_persistence_monitor_report_json(
        monitor_report,
    )
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "payload_sha256"
    }
    expected_digest = sha256(
        json.dumps(
            payload_without_digest,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()

    assert monitor_report.generated_at == GENERATED_AT
    assert json.loads(canonical_json) == payload
    assert canonical_json == monitor.research_strategy_edge_persistence_monitor_report_json(
        monitor_report,
    )
    assert payload["payload_sha256"] == expected_digest
    assert monitor_report.payload_sha256 == expected_digest
    assert payload["rows"][0]["redacted_source_ref"] == redacted_source_ref(
        "candidate-raw-alpha-market-slug-secret-token",
    )
    assert "Decimal(" not in repr(payload)
    assert "datetime" not in repr(payload).lower()

    tampered_payload = dict(payload)
    tampered_payload["status"] = "watch"
    with pytest.raises(ValueError, match="payload_sha256 does not match"):
        monitor.validate_research_strategy_edge_persistence_monitor_report_payload(
            tampered_payload,
        )

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        monitor.research_strategy_edge_persistence_monitor_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "payload_sha256": "0" * 64,
                "mean_adjusted_edge_probability": 0.1,
            },
        )


def test_report_validates_decimals_flags_time_statuses_and_frozen_outputs() -> None:
    monitor = api()
    monitor_report = report(observation())

    with pytest.raises(FrozenInstanceError):
        monitor_report.rows[0].persistence_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="current_edge_probability must be a Decimal"):
        observation(current_edge_probability=0.1)

    with pytest.raises(ValueError, match="current_edge_probability"):
        observation(current_edge_probability=_DecimalSubclass("0.100000"))

    with pytest.raises(ValueError, match="current_edge_probability must be finite"):
        observation(current_edge_probability=Decimal("NaN"))

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report(observation(), generated_at="bad")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(
            observation(),
            generated_at=datetime(2026, 7, 8, 13, 0, tzinfo=_NoneOffsetTimezone()),
        )

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        monitor.ResearchStrategyEdgePersistenceMonitorReport(
            generated_at=_DatetimeSubclass(2026, 7, 8, 13, 0, tzinfo=UTC),
            config_version="research-strategy-edge-persistence-monitor-report-v0",
            source_row_count=d("0"),
            pass_count=d("0"),
            watch_count=d("0"),
            block_count=d("0"),
            persisted_edge_count=d("0"),
            mean_adjusted_edge_probability=d("0.000000"),
            min_adjusted_edge_probability=d("0.000000"),
            status="pass",
            reason_codes=("edge_persistence_clear",),
            reason_code_counts=(),
            rows=(),
        )

    with pytest.raises(ValueError, match="config must be paper_only"):
        config(paper_only=False)

    with pytest.raises(ValueError, match="observation must be readonly"):
        observation(readonly=False)

    with pytest.raises(ValueError, match="status"):
        replace(monitor_report, status="review")

    with pytest.raises(ValueError, match="source_row_count"):
        replace(monitor_report, source_row_count=d("2"))

    with pytest.raises(ValueError, match="payload_sha256 does not match"):
        replace(monitor_report, payload_sha256="0" * 64)


def test_public_payload_rejects_raw_surfaces_and_module_has_no_live_connectors() -> None:
    monitor = api()

    with pytest.raises(ValueError, match="unsafe public field"):
        monitor.research_strategy_edge_persistence_monitor_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "market_slug": "raw-market",
            },
        )

    with pytest.raises(ValueError, match="unsafe public value"):
        monitor.research_strategy_edge_persistence_monitor_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "payload_sha256": "0" * 64,
                "summary": "https://example.test/raw-question",
            },
        )

    source = Path(
        "src/polymarket_alpha_lab/research_strategy_edge_persistence_monitor_report.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "wallet",
        "dsn",
        "table_name",
        "submit",
        "cancel",
        "place_order",
        "position_size",
        "recommend_trade",
        "execute_trade",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"


def test_public_dataclasses_are_frozen_slotted_and_final() -> None:
    monitor = api()

    public_types = (
        monitor.ResearchStrategyEdgePersistenceMonitorConfig,
        monitor.ResearchStrategyEdgePersistenceObservation,
        monitor.ResearchStrategyEdgePersistenceMonitorRow,
        monitor.ResearchStrategyEdgePersistenceMonitorReport,
    )
    for public_type in public_types:
        assert "__dict__" not in public_type.__dict__
        assert "__slots__" in public_type.__dict__

    with pytest.raises(TypeError):
        class ChildConfig(monitor.ResearchStrategyEdgePersistenceMonitorConfig):
            pass


def test_builder_revalidates_tampered_config_and_observation_objects() -> None:
    monitor = api()

    tampered_config = config()
    object.__setattr__(tampered_config, "watch_edge_floor", d("0.900000"))
    with pytest.raises(ValueError, match="watch_edge_floor"):
        report(observation(), cfg=tampered_config)

    tampered_observation = observation()
    object.__setattr__(tampered_observation, "current_edge_probability", 0.1)
    with pytest.raises(ValueError, match="current_edge_probability must be a Decimal"):
        report(tampered_observation)

    object.__setattr__(tampered_observation, "current_edge_probability", d("0.100000"))
    object.__setattr__(tampered_observation, "readonly", False)
    with pytest.raises(ValueError, match="observation must be readonly"):
        report(tampered_observation)


def test_payload_schema_rejects_resigned_shape_and_noncanonical_values() -> None:
    monitor = api()
    payload = monitor.research_strategy_edge_persistence_monitor_report_payload(
        report(observation()),
    )

    extra_field = json.loads(json.dumps(payload))
    extra_field["unexpected"] = "value"
    resign_payload(extra_field)
    with pytest.raises(ValueError, match="canonical report payload schema"):
        monitor.validate_research_strategy_edge_persistence_monitor_report_payload(
            extra_field,
        )

    missing_row_field = json.loads(json.dumps(payload))
    missing_row_field["rows"][0].pop("adjusted_edge_probability")
    resign_payload(missing_row_field)
    with pytest.raises(ValueError, match="canonical report payload schema"):
        monitor.validate_research_strategy_edge_persistence_monitor_report_payload(
            missing_row_field,
        )

    noncanonical_decimal = json.loads(json.dumps(payload))
    noncanonical_decimal["rows"][0]["current_edge_probability"] = "0.1"
    resign_payload(noncanonical_decimal)
    with pytest.raises(ValueError, match="canonical report payload schema"):
        monitor.validate_research_strategy_edge_persistence_monitor_report_payload(
            noncanonical_decimal,
        )

    signed_zero = json.loads(json.dumps(payload))
    signed_zero["rows"][0]["evidence_age_drag_probability"] = "-0.000000"
    resign_payload(signed_zero)
    with pytest.raises(ValueError, match="signed zero"):
        monitor.validate_research_strategy_edge_persistence_monitor_report_payload(
            signed_zero,
        )


def test_payload_validator_rejects_resigned_derived_row_and_report_tampering() -> None:
    monitor = api()
    payload = monitor.research_strategy_edge_persistence_monitor_report_payload(
        report(observation()),
    )

    forged_row = json.loads(json.dumps(payload))
    forged_row["rows"][0]["edge_movement_probability"] = "0.000000"
    resign_payload(forged_row)
    with pytest.raises(ValueError, match="edge_movement_probability"):
        monitor.validate_research_strategy_edge_persistence_monitor_report_payload(
            forged_row,
        )

    forged_report = json.loads(json.dumps(payload))
    forged_report["mean_adjusted_edge_probability"] = "0.999999"
    resign_payload(forged_report)
    with pytest.raises(ValueError, match="mean_adjusted_edge_probability"):
        monitor.validate_research_strategy_edge_persistence_monitor_report_payload(
            forged_report,
        )

    forged_status = json.loads(json.dumps(payload))
    forged_status["status"] = "block"
    resign_payload(forged_status)
    with pytest.raises(ValueError, match="status"):
        monitor.validate_research_strategy_edge_persistence_monitor_report_payload(
            forged_status,
        )


def test_numeric_normalization_is_fixed_context_and_canonical_signed_zero() -> None:
    monitor = api()
    with pytest.raises(ValueError, match="signed zero"):
        observation(cost_drag_probability=d("-0.000000"))

    with localcontext(Context(prec=4)):
        constrained = report(
            observation(
                baseline_edge_probability=d("0.123457"),
                current_edge_probability=d("0.234568"),
                cost_drag_probability=d("0.012345"),
                liquidity_quality_score=d("0.678912"),
                confidence_haircut_probability=d("0.023456"),
                resolution_ambiguity_score=d("0.034567"),
            ),
        )
    assert constrained.rows[0].adjusted_edge_probability == d("0.181308")
    assert constrained.rows[0].adjusted_edge_probability == d("0.181308")
    assert monitor.research_strategy_edge_persistence_monitor_report_payload(
        constrained,
    )["rows"][0]["adjusted_edge_probability"] == "0.181308"

    payload = monitor.research_strategy_edge_persistence_monitor_report_payload(
        report(observation()),
    )
    signed_zero = json.loads(json.dumps(payload))
    signed_zero["rows"][0]["cost_drag_probability"] = "-0.000000"
    resign_payload(signed_zero)
    with pytest.raises(ValueError, match="signed zero"):
        monitor.validate_research_strategy_edge_persistence_monitor_report_payload(
            signed_zero,
        )


def test_builder_rejects_observations_after_report_generation() -> None:
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(
            observation(observed_at=GENERATED_AT + timedelta(microseconds=1)),
        )


def test_payload_validator_rejects_rows_after_report_generation() -> None:
    monitor = api()
    payload = monitor.research_strategy_edge_persistence_monitor_report_payload(
        report(observation()),
    )
    future_payload = json.loads(json.dumps(payload))
    future_payload["rows"][0]["observed_at"] = (
        GENERATED_AT + timedelta(seconds=1)
    ).isoformat()
    resign_payload(future_payload)
    with pytest.raises(ValueError, match="observed_at"):
        monitor.validate_research_strategy_edge_persistence_monitor_report_payload(
            future_payload,
        )


def test_report_rejects_non_deterministically_ordered_rows() -> None:
    monitor_report = report(
        observation(source_ref="candidate-raw-alpha"),
        observation(source_ref="candidate-raw-beta", current_edge_probability=d("0.050000")),
    )
    with pytest.raises(ValueError, match="deterministic"):
        replace(monitor_report, rows=tuple(reversed(monitor_report.rows)))
