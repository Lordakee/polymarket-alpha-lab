from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_event_freshness_decay_score"


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": (
            module.DEFAULT_CANDIDATE_DECISION_EVENT_FRESHNESS_DECAY_SCORE_CONFIG_VERSION
        ),
        "min_pass_event_freshness_decay_score": d("0.750000"),
        "min_watch_event_freshness_decay_score": d("0.500000"),
        "max_pass_latest_event_age_minutes": d("60.000000"),
        "max_watch_latest_event_age_minutes": d("240.000000"),
        "source_freshness_weight": d("0.250000"),
        "event_relevance_weight": d("0.250000"),
        "stale_context_weight": d("0.200000"),
        "update_frequency_weight": d("0.150000"),
        "evidence_quality_weight": d("0.150000"),
        "min_pass_source_freshness_score": d("0.700000"),
        "min_watch_source_freshness_score": d("0.400000"),
        "min_pass_event_relevance_score": d("0.700000"),
        "min_watch_event_relevance_score": d("0.400000"),
        "max_pass_stale_context_score": d("0.300000"),
        "max_watch_stale_context_score": d("0.700000"),
        "min_pass_update_frequency_score": d("0.600000"),
        "min_watch_update_frequency_score": d("0.300000"),
        "min_pass_evidence_quality_score": d("0.700000"),
        "min_watch_evidence_quality_score": d("0.400000"),
    }
    values.update(overrides)
    return module.CandidateDecisionEventFreshnessDecayScoreConfig(**values)


def score_input(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "redacted_candidate_ref": "candidate-ref-alpha",
        "latest_event_age_minutes": d("30.000000"),
        "source_freshness_score": d("0.900000"),
        "event_relevance_score": d("0.850000"),
        "stale_context_score": d("0.100000"),
        "update_frequency_score": d("0.800000"),
        "evidence_quality_score": d("0.900000"),
        "reason_codes": ("redacted_event_research_present",),
    }
    values.update(overrides)
    return module.CandidateDecisionEventFreshnessDecayScoreInput(**values)


def report(subject: object | None = None, cfg: object | None = None):
    module = api()
    return module.build_candidate_decision_event_freshness_decay_score_report(
        score_input() if subject is None else subject,
        config=config() if cfg is None else cfg,
    )


def public_field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_no_public_numbers_or_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, int) and not isinstance(value, bool):
        raise AssertionError(f"unexpected int value {value!r}")
    if isinstance(value, Decimal):
        raise AssertionError(f"unexpected Decimal value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numbers_or_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_numbers_or_float_values(item)


def assert_sha256(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def test_fresh_event_update_passes_with_redacted_report() -> None:
    module = api()

    freshness_report = report()

    assert type(freshness_report) is module.CandidateDecisionEventFreshnessDecayScoreReport
    assert freshness_report.redacted_candidate_ref == "candidate-ref-alpha"
    assert freshness_report.latest_event_age_minutes == d("30.000000")
    assert freshness_report.event_age_component == d("1.000000")
    assert freshness_report.source_freshness_component == d("1.000000")
    assert freshness_report.event_relevance_component == d("1.000000")
    assert freshness_report.stale_context_component == d("1.000000")
    assert freshness_report.update_frequency_component == d("1.000000")
    assert freshness_report.evidence_quality_component == d("1.000000")
    assert freshness_report.event_freshness_decay_score == d("1.000000")
    assert freshness_report.event_freshness_status == "pass"
    assert freshness_report.hard_flag_codes == ()
    assert freshness_report.reason_codes == (
        "redacted_event_research_present",
        "event_freshness_decay_pass",
        "latest_event_age_pass",
        "source_freshness_pass",
        "event_relevance_pass",
        "stale_context_pass",
        "update_frequency_pass",
        "evidence_quality_pass",
        "event_freshness_decay_score_pass",
    )
    assert freshness_report.paper_only is True
    assert freshness_report.report_only is True
    assert freshness_report.readonly is True
    assert_sha256(freshness_report.derived_validation_digest)


def test_stale_event_update_blocks_with_hard_flags() -> None:
    freshness_report = report(
        score_input(
            latest_event_age_minutes=d("300.000000"),
            source_freshness_score=d("0.200000"),
            event_relevance_score=d("0.300000"),
            stale_context_score=d("0.900000"),
            update_frequency_score=d("0.100000"),
            evidence_quality_score=d("0.300000"),
            reason_codes=(),
        ),
    )

    assert freshness_report.event_freshness_status == "block"
    assert freshness_report.event_age_component == d("0.000000")
    assert freshness_report.event_freshness_decay_score == d("0.000000")
    assert freshness_report.hard_flag_codes == (
        "latest_event_age_block",
        "source_freshness_block",
        "event_relevance_block",
        "stale_context_block",
        "update_frequency_block",
        "evidence_quality_block",
        "event_freshness_decay_score_block",
    )
    assert freshness_report.reason_codes == (
        "event_freshness_decay_block",
        "latest_event_age_block",
        "source_freshness_block",
        "event_relevance_block",
        "stale_context_block",
        "update_frequency_block",
        "evidence_quality_block",
        "event_freshness_decay_score_block",
    )


def test_moderate_event_decay_watches_with_decimal_linear_components() -> None:
    freshness_report = report(
        score_input(
            latest_event_age_minutes=d("120.000000"),
            source_freshness_score=d("0.550000"),
            event_relevance_score=d("0.550000"),
            stale_context_score=d("0.500000"),
            update_frequency_score=d("0.450000"),
            evidence_quality_score=d("0.550000"),
            reason_codes=(),
        ),
    )

    assert freshness_report.event_freshness_status == "watch"
    assert freshness_report.event_age_component == d("0.666667")
    assert freshness_report.source_freshness_component == d("0.500000")
    assert freshness_report.event_relevance_component == d("0.500000")
    assert freshness_report.stale_context_component == d("0.500000")
    assert freshness_report.update_frequency_component == d("0.500000")
    assert freshness_report.evidence_quality_component == d("0.500000")
    assert freshness_report.event_freshness_decay_score == d("0.541667")
    assert freshness_report.hard_flag_codes == ()
    assert freshness_report.reason_codes == (
        "event_freshness_decay_watch",
        "latest_event_age_watch",
        "source_freshness_watch",
        "event_relevance_watch",
        "stale_context_watch",
        "update_frequency_watch",
        "evidence_quality_watch",
        "event_freshness_decay_score_watch",
    )


def test_decimal_exact_type_rejection_and_phase_flags() -> None:
    module = api()
    cfg = config()
    subject = score_input()
    freshness_report = report(subject, cfg)

    assert is_dataclass(cfg)
    assert is_dataclass(subject)
    assert is_dataclass(freshness_report)
    assert module.CandidateDecisionEventFreshnessDecayScoreConfig.__dataclass_params__.frozen
    assert module.CandidateDecisionEventFreshnessDecayScoreInput.__dataclass_params__.frozen
    assert module.CandidateDecisionEventFreshnessDecayScoreReport.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.latest_event_age_minutes = d("90.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        freshness_report.event_freshness_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(module.CandidateDecisionEventFreshnessDecayScoreInput):
            pass

    for instance in (cfg, subject, freshness_report):
        assert instance.paper_only is True
        assert instance.report_only is True
        assert instance.readonly is True
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) is bool or field.name == "derived_validation_digest":
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(ValueError, match="latest_event_age_minutes must be a Decimal"):
        score_input(latest_event_age_minutes=30)
    with pytest.raises(ValueError, match="source_freshness_score must be a Decimal"):
        score_input(source_freshness_score=0.9)
    with pytest.raises(ValueError, match="event_relevance_score must be a Decimal"):
        score_input(event_relevance_score=DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="latest_event_age_minutes must be nonnegative"):
        score_input(latest_event_age_minutes=d("-1.000000"))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        score_input(reason_codes=["redacted_event_research_present"])
    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(freshness_report, readonly=False)
    with pytest.raises(ValueError, match="Input"):
        report(object())
    with pytest.raises(ValueError, match="Config"):
        report(score_input(), object())
    with pytest.raises(ValueError, match="supported version"):
        config(config_version="candidate-decision-event-freshness-decay-score-next")
    with pytest.raises(ValueError, match="weights must sum to 1.000000"):
        config(source_freshness_weight=d("0.300000"))


def test_public_payload_rejects_leaks_status_aliases_and_numbers() -> None:
    module = api()

    unsafe_payloads = (
        ({"candidate_id": "redacted"}, "raw market"),
        ({"market_slug": "redacted"}, "raw market"),
        ({"question": "will this resolve"}, "raw market"),
        ({"url": "https://example.test/source"}, "source refs"),
        ({"source_ref": "source-ref:abc123"}, "source refs"),
        ({"source_text": "raw source text"}, "source refs"),
        ({"safe_key": "https://example.test/source"}, "source refs"),
        ({"safe_key": "orders_table"}, "unsafe live surface"),
        ({"safe_key": "api-token"}, "unsafe live surface"),
        ({"safe_key": "wallet order trade"}, "unsafe live surface"),
        ({"safe_key": "buy sell recommendation"}, "unsafe live surface"),
        ({"safe_key": "position-sizing"}, "unsafe live surface"),
        ({"event_freshness_status": "blocked"}, "public status"),
        ({"event_freshness_status": "ready"}, "public status"),
        ({"safe_key": "matched"}, "public status"),
        ({"latest_event_age_minutes": 1}, "decimal strings"),
        ({"latest_event_age_minutes": 1.0}, "decimal strings"),
        (["not", "object"], "public payload must be a JSON object"),
    )

    for payload, match in unsafe_payloads:
        with pytest.raises(ValueError, match=match):
            module.validate_candidate_decision_event_freshness_decay_score_public_payload(
                payload,
            )


def test_hard_flags_are_threshold_driven() -> None:
    freshness_report = report(
        score_input(
            latest_event_age_minutes=d("120.000000"),
            source_freshness_score=d("0.390000"),
            event_relevance_score=d("0.410000"),
            stale_context_score=d("0.710000"),
            update_frequency_score=d("0.290000"),
            evidence_quality_score=d("0.410000"),
            reason_codes=(),
        ),
    )

    assert freshness_report.event_freshness_status == "block"
    assert freshness_report.hard_flag_codes == (
        "source_freshness_block",
        "stale_context_block",
        "update_frequency_block",
        "event_freshness_decay_score_block",
    )
    assert "latest_event_age_block" not in freshness_report.hard_flag_codes
    assert "event_relevance_block" not in freshness_report.hard_flag_codes
    assert "evidence_quality_block" not in freshness_report.hard_flag_codes


def test_payload_is_json_ready_deterministic_and_redacted() -> None:
    module = api()
    freshness_report = report()
    payload = module.candidate_decision_event_freshness_decay_score_payload(
        freshness_report,
    )
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()

    assert payload == freshness_report.payload
    assert payload["redacted_candidate_ref"] == "candidate-ref-alpha"
    assert payload["latest_event_age_minutes"] == "30.000000"
    assert payload["event_freshness_decay_score"] == "1.000000"
    assert payload["event_freshness_status"] == "pass"
    assert payload["reason_codes"] == list(freshness_report.reason_codes)
    assert payload["derived_validation_digest"] == freshness_report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_numbers_or_float_values(payload)

    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "raw_text",
        "http",
        "www.",
        "dsn",
        "table_name",
        "auth_token",
        "token",
        "secret",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommendation",
        "position_size",
        "position-sizing",
    ):
        assert forbidden not in rendered

    with localcontext() as context:
        context.prec = 2
        context.rounding = "ROUND_UP"
        assert report().payload == payload

    object.__setattr__(freshness_report, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.candidate_decision_event_freshness_decay_score_payload(freshness_report)


def test_report_consistency_rejects_mutated_fields_and_status_vocabulary() -> None:
    module = api()
    freshness_report = report()

    with pytest.raises(ValueError, match="event_freshness_decay_score"):
        replace(
            freshness_report,
            event_freshness_decay_score=d("0.500000"),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="event_freshness_status"):
        replace(
            freshness_report,
            event_freshness_status="watch",
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="hard_flag_codes"):
        replace(
            freshness_report,
            hard_flag_codes=("event_freshness_decay_score_block",),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="event_freshness_status"):
        module.CandidateDecisionEventFreshnessDecayScoreReport(
            **{
                **public_field_values(freshness_report),
                "event_freshness_status": "blocked",
                "derived_validation_digest": "",
            },
        )

    rebuilt_input = module.CandidateDecisionEventFreshnessDecayScoreInput(
        **public_field_values(score_input()),
    )
    assert rebuilt_input == score_input()
    rebuilt_report = module.CandidateDecisionEventFreshnessDecayScoreReport(
        **public_field_values(freshness_report),
    )
    assert rebuilt_report == freshness_report

    assert module.EVENT_FRESHNESS_STATUSES == ("pass", "watch", "block")
    for public_status in module.EVENT_FRESHNESS_STATUSES:
        assert public_status in {"pass", "watch", "block"}
    assert "ready" not in module.EVENT_FRESHNESS_STATUSES
    assert "blocked" not in module.EVENT_FRESHNESS_STATUSES
    assert "matched" not in module.EVENT_FRESHNESS_STATUSES
    assert "supported" not in module.EVENT_FRESHNESS_STATUSES


def test_no_unsafe_runtime_surface_or_io_is_added() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_CANDIDATE_DECISION_EVENT_FRESHNESS_DECAY_SCORE_CONFIG_VERSION",
        "EVENT_FRESHNESS_STATUSES",
        "CandidateDecisionEventFreshnessDecayScoreConfig",
        "CandidateDecisionEventFreshnessDecayScoreInput",
        "CandidateDecisionEventFreshnessDecayScoreReport",
        "build_candidate_decision_event_freshness_decay_score_report",
        "candidate_decision_event_freshness_decay_score_payload",
        "validate_candidate_decision_event_freshness_decay_score_public_payload",
        "reject_candidate_decision_event_freshness_decay_score_unsafe_payload",
    )

    source = Path(module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_import_roots = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "supabase",
        "web3",
        "ccxt",
        "os",
        "pathlib",
        "subprocess",
    }
    forbidden_call_names = {
        "open",
        "connect",
        "request",
        "post",
        "put",
        "delete",
        "submit",
        "execute",
        "commit",
        "rollback",
        "getenv",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Name):
                assert target.id not in forbidden_call_names
            if isinstance(target, ast.Attribute):
                assert target.attr not in forbidden_call_names
