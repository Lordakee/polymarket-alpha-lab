from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 18, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 4, 17, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_candidate_recommendation_gate_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_STRATEGY_CANDIDATE_RECOMMENDATION_GATE_DIGEST_CONFIG_VERSION
        ),
        "min_pass_weighted_gate_score": d("0.800000"),
        "min_watch_weighted_gate_score": d("0.500000"),
        "max_block_gate_count": d("0"),
    }
    values.update(overrides)
    return module.StrategyCandidateRecommendationGateConfig(**values)


def signal(**overrides: object):
    module = api()
    values = {
        "candidate_reference": "candidate-alpha",
        "gate_name": "evidence_trace",
        "gate_status": "pass",
        "gate_score": d("0.900000"),
        "gate_weight": d("1.000000"),
        "observed_at": OBSERVED_AT,
        "source_reference": "evidence-trace-report",
        "reason_codes": ("evidence_trace_ready",),
    }
    values.update(overrides)
    return module.StrategyCandidateRecommendationGateSignal(**values)


def report(*signals: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_candidate_recommendation_gate_digest(
        signals,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_int_or_float_values(item)


def test_candidate_gate_combines_pass_watch_and_block_signals() -> None:
    result = report(
        signal(
            candidate_reference="candidate-pass",
            gate_name="evidence_trace",
            gate_status="pass",
            gate_score=d("0.950000"),
            reason_codes=("evidence_trace_ready",),
        ),
        signal(
            candidate_reference="candidate-pass",
            gate_name="tail_risk",
            gate_status="pass",
            gate_score=d("0.900000"),
            reason_codes=("tail_risk_pass",),
        ),
        signal(
            candidate_reference="candidate-watch",
            gate_name="category_rotation",
            gate_status="watch",
            gate_score=d("0.720000"),
            reason_codes=("category_volatility_watch",),
        ),
        signal(
            candidate_reference="candidate-watch",
            gate_name="team_memory",
            gate_status="pass",
            gate_score=d("0.780000"),
            reason_codes=("team_memory_ready",),
        ),
        signal(
            candidate_reference="candidate-block",
            gate_name="portfolio_correlation",
            gate_status="block",
            gate_score=d("0.200000"),
            reason_codes=("portfolio_correlation_block",),
            source_reference="https://example.invalid/report?token=secret",
        ),
        signal(
            candidate_reference="candidate-block",
            gate_name="expected_value",
            gate_status="watch",
            gate_score=d("0.600000"),
            reason_codes=("expected_value_buffer_watch",),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-candidate-recommendation-gate-digest-v0"
    assert result.signal_count == d("6")
    assert result.candidate_count == d("3")
    assert result.pass_candidate_count == d("1")
    assert result.watch_candidate_count == d("1")
    assert result.block_candidate_count == d("1")
    assert result.min_weighted_gate_score == d("0.400000")
    assert result.max_block_gate_count == d("1")
    assert result.gate_status == "block"
    assert result.reason_codes == ("candidate_recommendation_gate_blocked",)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    blocked, watched, passed = result.rows
    assert tuple(row.gate_status for row in result.rows) == ("block", "watch", "pass")
    assert blocked.gate_count == d("2")
    assert blocked.block_gate_count == d("1")
    assert blocked.watch_gate_count == d("1")
    assert blocked.weighted_gate_score == d("0.400000")
    assert blocked.gate_names == ("expected_value", "portfolio_correlation")
    assert blocked.reason_codes == (
        "gate_block_present",
        "gate_score_below_watch",
        "gate_watch_present",
        "expected_value_buffer_watch",
        "portfolio_correlation_block",
    )

    assert watched.gate_status == "watch"
    assert watched.weighted_gate_score == d("0.750000")
    assert watched.reason_codes == (
        "gate_watch_present",
        "gate_score_below_pass",
        "category_volatility_watch",
        "team_memory_ready",
    )

    assert passed.gate_status == "pass"
    assert passed.weighted_gate_score == d("0.925000")
    assert passed.reason_codes == (
        "candidate_recommendation_gate_pass",
        "evidence_trace_ready",
        "tail_risk_pass",
    )
    assert all(row.redacted_candidate_reference.startswith("candidate_ref_") for row in result.rows)
    assert "secret" not in repr(blocked).lower()
    assert "example.invalid" not in repr(blocked).lower()

    assert tuple(item.reason_code for item in result.reason_counts[:2]) == (
        "gate_watch_present",
        "gate_block_present",
    )
    assert result.reason_counts[0].candidate_count == d("2")
    assert result.reason_counts[0].candidate_ratio == d("0.666667")


def test_empty_report_is_pass_zeroed_decimal_and_readonly() -> None:
    result = report()

    assert result.signal_count == d("0")
    assert result.candidate_count == d("0")
    assert result.pass_candidate_count == d("0")
    assert result.watch_candidate_count == d("0")
    assert result.block_candidate_count == d("0")
    assert result.min_weighted_gate_score is None
    assert result.max_block_gate_count == ZERO
    assert result.gate_status == "pass"
    assert result.reason_codes == ("candidate_recommendation_gate_empty",)
    assert result.rows == ()
    assert result.reason_counts == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    populated = report(signal())
    for value in (result, populated, *populated.rows, *populated.reason_counts):
        for item in fields(value):
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            item_value = getattr(value, item.name)
            if item_value is None:
                continue
            if item.name.endswith(("_count", "_score", "_weight", "_ratio")):
                assert type(item_value) is Decimal


def test_payload_uses_decimal_strings_redacts_references_and_rejects_public_numbers() -> None:
    module = api()
    result = report(
        signal(
            candidate_reference="https://example.invalid/candidate?token=secret",
            source_reference="https://example.invalid/source?token=secret",
            gate_score=d("0.900000"),
        ),
        generated_at=datetime(2026, 7, 4, 11, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.strategy_candidate_recommendation_gate_digest_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()

    assert payload["generated_at"] == "2026-07-04T18:00:00+00:00"
    assert payload["signal_count"] == "1"
    assert payload["rows"][0]["weighted_gate_score"] == "0.900000"
    assert payload["rows"][0]["latest_observed_at"] == "2026-07-04T17:30:00+00:00"
    assert payload["rows"][0]["redacted_candidate_reference"].startswith("candidate_ref_")
    assert payload["rows"][0]["source_references"][0].startswith("source_ref_")
    assert "example.invalid" not in rendered
    assert "secret" not in rendered
    assert_no_int_or_float_values(payload)

    with pytest.raises(ValueError, match="numeric"):
        module.strategy_candidate_recommendation_gate_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "signal_count": 1,
            },
        )

    with pytest.raises(ValueError, match="readonly"):
        module.strategy_candidate_recommendation_gate_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": False,
            },
        )


def test_validation_rejects_bad_types_flags_duplicates_and_time_boundaries() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_strategy_candidate_recommendation_gate_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="gate_score"):
        signal(gate_score=0.9)
    with pytest.raises(ValueError, match="gate_weight"):
        signal(gate_weight=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="gate_status"):
        signal(gate_status="maybe")
    with pytest.raises(ValueError, match="observed_at"):
        signal(observed_at=datetime(2026, 7, 4, 17, 30))
    with pytest.raises(ValueError, match="observed_at"):
        signal(observed_at=datetime(2026, 7, 4, 17, 30, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="observed_at"):
        signal(observed_at=_DatetimeSubclass(2026, 7, 4, 17, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="paper_only"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="unique candidate and gate"):
        report(signal(), signal())

    result = report(signal())
    row = result.rows[0]
    with pytest.raises(FrozenInstanceError):
        row.gate_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="gate_status"):
        replace(row, gate_status="block")
    with pytest.raises(ValueError, match="signal_count"):
        replace(result, signal_count=d("2"))
    with pytest.raises(ValueError, match="latest_observed_at"):
        replace(result, rows=(replace(row, latest_observed_at=GENERATED_AT + timedelta(seconds=1)),))


def test_public_text_rejects_sensitive_values_without_echoing() -> None:
    sensitive_config = "api_key_secret"
    sensitive_gate = "wallet_surface"
    sensitive_reason = "token_leak"

    with pytest.raises(ValueError, match="config_version") as config_exc:
        config(config_version=sensitive_config)
    with pytest.raises(ValueError, match="gate_name") as gate_exc:
        signal(gate_name=sensitive_gate)
    with pytest.raises(ValueError, match="reason_codes") as reason_exc:
        signal(reason_codes=(sensitive_reason,))

    assert sensitive_config not in str(config_exc.value)
    assert sensitive_gate not in str(gate_exc.value)
    assert sensitive_reason not in str(reason_exc.value)


def test_module_scope_has_no_live_persistence_io_or_float_surface() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    forbidden_import_roots = {
        "http",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    forbidden_call_names = {
        "connect",
        "execute",
        "float",
        "open",
        "print",
        "request",
        "urlopen",
        "write",
    }

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.name for alias in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            for name in names:
                assert name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Name):
                assert target.id not in forbidden_call_names
            if isinstance(target, ast.Attribute):
                assert target.attr not in forbidden_call_names
        if isinstance(node, ast.Constant):
            assert not isinstance(node.value, float)

    lowered = source.lower()
    for forbidden in (
        "database",
        "network",
        "wallet",
        "broker",
        "cancel",
        "replace",
        "private_key",
    ):
        assert forbidden not in lowered


def test_expected_files_exist_without_package_or_cli_wiring() -> None:
    root = Path(__file__).resolve().parents[1]
    assert (root / "src/polymarket_alpha_lab/strategy_candidate_recommendation_gate_digest.py").exists()
