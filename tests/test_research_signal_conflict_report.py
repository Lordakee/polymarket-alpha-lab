from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 7, 11, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    module_name = "polymarket_alpha_lab.research_signal_conflict_report"
    assert importlib.util.find_spec(module_name) is not None
    return importlib.import_module(module_name)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": module.DEFAULT_RESEARCH_SIGNAL_CONFLICT_REPORT_CONFIG_VERSION,
        "watch_source_disagreement_count": d("1"),
        "block_source_disagreement_count": d("3"),
        "watch_evidence_conflict_count": d("1"),
        "block_evidence_conflict_count": d("2"),
        "watch_probability_gap": d("0.050000"),
        "block_probability_gap": d("0.150000"),
        "watch_rule_risk_score": d("0.300000"),
        "block_rule_risk_score": d("0.700000"),
    }
    values.update(overrides)
    return module.ResearchSignalConflictConfig(**values)


def record(**overrides: object):
    module = api()
    values = {
        "candidate_reference": "candidate-alpha",
        "market_reference": "market-alpha",
        "origin_reference": "origin-alpha",
        "origin_family": "official",
        "observed_at": OBSERVED_AT,
        "model_probability": d("0.520000"),
        "source_probability": d("0.500000"),
        "source_disagreement_count": d("0"),
        "evidence_conflict_count": d("0"),
        "rule_risk_score": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchSignalConflictRecord(**values)


def report(*records: object, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_research_signal_conflict_report(
        records,
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


def test_scores_pass_watch_and_block_signal_conflicts() -> None:
    result = report(
        record(
            candidate_reference="secret-pass-candidate",
            market_reference="secret-pass-market",
            origin_reference="secret-pass-origin",
            source_disagreement_count=d("0"),
            evidence_conflict_count=d("0"),
            model_probability=d("0.520000"),
            source_probability=d("0.500000"),
            rule_risk_score=d("0.100000"),
        ),
        record(
            candidate_reference="watch-candidate",
            market_reference="watch-market",
            origin_reference="watch-origin",
            origin_family="proxy",
            source_disagreement_count=d("1"),
            evidence_conflict_count=d("1"),
            model_probability=d("0.580000"),
            source_probability=d("0.500000"),
            rule_risk_score=d("0.400000"),
        ),
        record(
            candidate_reference="block-candidate",
            market_reference="block-market",
            origin_reference="block-origin",
            origin_family="rules",
            source_disagreement_count=d("3"),
            evidence_conflict_count=d("2"),
            model_probability=d("0.700000"),
            source_probability=d("0.500000"),
            rule_risk_score=d("0.800000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.signal_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.max_probability_gap == d("0.200000")
    assert result.max_source_disagreement_count == d("3")
    assert result.max_evidence_conflict_count == d("2")
    assert result.max_rule_risk_score == d("0.800000")
    assert result.status == "block"
    assert result.reason_codes == (
        "source_disagreement_block",
        "evidence_conflict_block",
        "probability_gap_block",
        "rule_risk_block",
        "source_disagreement_watch",
        "evidence_conflict_watch",
        "probability_gap_watch",
        "rule_risk_watch",
    )
    assert result.review_prompts == (
        "review_origin_family_disagreement",
        "review_conflicting_evidence",
        "review_probability_gap_explanation",
        "review_rule_risk_controls",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")
    blocked, watched, passed = result.rows
    assert blocked.probability_gap == d("0.200000")
    assert blocked.probability_gap_explanation == "block_probability_gap"
    assert blocked.reason_codes == (
        "evidence_conflict_block",
        "probability_gap_block",
        "rule_risk_block",
        "source_disagreement_block",
    )
    assert blocked.review_prompts == (
        "review_origin_family_disagreement",
        "review_conflicting_evidence",
        "review_probability_gap_explanation",
        "review_rule_risk_controls",
    )
    assert watched.probability_gap == d("0.080000")
    assert watched.probability_gap_explanation == "watch_probability_gap"
    assert passed.probability_gap_explanation == "aligned_probability_gap"
    assert passed.reason_codes == ("research_signal_conflict_pass",)
    assert passed.review_prompts == ("no_conflict_review_required",)
    assert passed.redacted_candidate_marker.startswith("candidate_marker_")
    assert passed.redacted_market_marker.startswith("market_marker_")
    assert passed.redacted_origin_marker.startswith("origin_marker_")


def test_payload_redacts_raw_values_and_rejects_public_leaks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = api()
    result = report(
        record(
            candidate_reference="raw-candidate-id-token-wallet",
            market_reference="market-id-slug-question-auth",
            origin_reference="https://example.invalid/source/ref/text/token",
            origin_family="official",
            model_probability=d("0.700000"),
            source_probability=d("0.500000"),
            source_disagreement_count=d("3"),
            evidence_conflict_count=d("2"),
            rule_risk_score=d("0.800000"),
        ),
    )

    payload = module.research_signal_conflict_report_payload(result)
    rendered = json.dumps(payload, sort_keys=True).lower()
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["probability_gap"] == "0.200000"
    assert payload["rows"][0]["result_integrity_digest"] == (
        result.rows[0].result_integrity_digest
    )
    assert payload["report_integrity_digest"] == result.report_integrity_digest
    for forbidden in (
        "raw-candidate-id",
        "market-id",
        "slug",
        "question",
        "https",
        "example.invalid",
        "source/ref/text",
        "token",
        "wallet",
        "auth",
    ):
        assert forbidden not in rendered
        assert forbidden not in repr(result).lower()
    assert_no_int_or_float_values(payload)

    def unsafe_json_ready_key(value: object) -> dict[str, object]:
        assert value is result
        return {"paper_only": True, "report_only": True, "readonly": True, "market_id": "x"}

    monkeypatch.setattr(module, "json_ready_no_floats", unsafe_json_ready_key)
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_signal_conflict_report_payload(result)

    def unsafe_json_ready_value(value: object) -> dict[str, object]:
        assert value is result
        return {
            "paper_only": True,
            "report_only": True,
            "readonly": True,
            "operator_note": "place buy order",
        }

    monkeypatch.setattr(module, "json_ready_no_floats", unsafe_json_ready_value)
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_signal_conflict_report_payload(result)


def test_rejects_non_decimal_exact_types_and_invalid_times() -> None:
    module = api()
    valid_record = record()
    cfg = config()

    with pytest.raises(ValueError, match="records"):
        module.build_research_signal_conflict_report(
            "bad-records",
            config=cfg,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="Decimal"):
        record(model_probability=0.5)
    with pytest.raises(ValueError, match="exact Decimal"):
        record(source_probability=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="timezone-aware"):
        record(observed_at=datetime(2026, 7, 7, 11, 30))
    with pytest.raises(ValueError, match="timezone-aware"):
        record(observed_at=datetime(2026, 7, 7, 11, 30, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="observed_at"):
        report(record(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="block_probability_gap"):
        config(watch_probability_gap=d("0.200000"), block_probability_gap=d("0.150000"))
    with pytest.raises(ValueError, match="config"):
        module.build_research_signal_conflict_report(
            (valid_record,),
            config=object(),
            generated_at=GENERATED_AT,
        )


def test_hard_flags_and_frozen_dataclasses_are_enforced() -> None:
    module = api()
    cfg = config()
    item = record()
    result = report(item, cfg=cfg)

    for value in (cfg, item, result, *result.rows):
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False
        assert getattr(value, "paper_only") is True
        assert getattr(value, "report_only") is True
        assert getattr(value, "readonly") is True
        for field in fields(value):
            field_value = getattr(value, field.name)
            if field.name.endswith(("_count", "_probability", "_gap", "_score")):
                assert type(field_value) is Decimal

    with pytest.raises(ValueError, match="readonly"):
        replace(cfg, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(item, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        module.research_signal_conflict_report_payload(replace(result, readonly=False))


def test_output_is_deterministic_and_module_stays_pure_readonly() -> None:
    module = api()
    first = report(
        record(candidate_reference="b", market_reference="m2", origin_reference="o2"),
        record(candidate_reference="a", market_reference="m1", origin_reference="o1"),
    )
    second = report(
        record(candidate_reference="a", market_reference="m1", origin_reference="o1"),
        record(candidate_reference="b", market_reference="m2", origin_reference="o2"),
    )

    assert first == second
    assert module.research_signal_conflict_report_payload(first) == (
        module.research_signal_conflict_report_payload(second)
    )
    assert json.dumps(first.report_integrity_digest, sort_keys=True) == json.dumps(
        second.report_integrity_digest,
        sort_keys=True,
    )

    source_path = Path(module.__file__)
    assert source_path.name == "research_signal_conflict_report.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))

    forbidden_imports = {
        "http.client",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    forbidden_calls = {
        "connect",
        "create_order",
        "delete",
        "execute",
        "get",
        "open",
        "patch",
        "place_order",
        "post",
        "put",
        "request",
        "run",
        "send",
        "write",
        "write_text",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name for alias in node.names}
            assert imported.isdisjoint(forbidden_imports)
        if isinstance(node, ast.ImportFrom):
            assert node.module not in forbidden_imports
            assert not (node.module or "").startswith(("urllib", "http"))
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls

    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if is_dataclass(exported):
            assert getattr(exported, "__dataclass_params__").frozen is True
