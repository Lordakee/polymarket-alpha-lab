from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_source_revision_frequency_score"
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


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
            module.DEFAULT_CANDIDATE_DECISION_SOURCE_REVISION_FREQUENCY_SCORE_CONFIG_VERSION
        ),
        "max_pass_source_revision_frequency_score": d("0.300000"),
        "max_watch_source_revision_frequency_score": d("0.600000"),
        "max_revision_count_for_component": d("6"),
        "high_impact_revision_block_ratio": d("0.500000"),
        "contradictory_revision_block_ratio": d("0.400000"),
        "same_day_revision_block_ratio": d("0.700000"),
        "source_stability_block_score": d("0.200000"),
        "min_pass_observation_window_days": d("7.000000"),
        "min_watch_observation_window_days": d("1.000000"),
        "revision_frequency_weight": d("0.250000"),
        "high_impact_revision_weight": d("0.200000"),
        "contradictory_revision_weight": d("0.200000"),
        "same_day_revision_weight": d("0.150000"),
        "source_instability_weight": d("0.150000"),
        "short_observation_window_weight": d("0.050000"),
    }
    values.update(overrides)
    return module.CandidateDecisionSourceRevisionFrequencyScoreConfig(**values)


def score_input(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "generated_at": GENERATED_AT,
        "redacted_candidate_ref": "candidate_ref_0123456789abcdef",
        "revision_count": d("0"),
        "high_impact_revision_ratio": d("0.000000"),
        "contradictory_revision_ratio": d("0.000000"),
        "same_day_revision_ratio": d("0.000000"),
        "source_stability_score": d("0.950000"),
        "observation_window_days": d("14.000000"),
        "reason_codes": ("local_revision_frequency_facts_present",),
    }
    values.update(overrides)
    return module.CandidateDecisionSourceRevisionFrequencyScoreInput(**values)


def report(subject: object | None = None, cfg: object | None = None):
    module = api()
    return module.build_candidate_decision_source_revision_frequency_score_report(
        score_input() if subject is None else subject,
        config=config() if cfg is None else cfg,
    )


def public_field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_json_ready_no_numbers(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, int) and not isinstance(value, bool):
        raise AssertionError(f"unexpected int value {value!r}")
    if isinstance(value, Decimal):
        raise AssertionError(f"unexpected Decimal value {value!r}")
    if isinstance(value, datetime):
        raise AssertionError(f"unexpected datetime value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_json_ready_no_numbers(item)
    if isinstance(value, list):
        for item in value:
            assert_json_ready_no_numbers(item)


def assert_sha256(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def test_stable_sources_pass_with_low_revision_frequency() -> None:
    module = api()

    frequency_report = report()

    assert type(frequency_report) is module.CandidateDecisionSourceRevisionFrequencyScoreReport
    assert frequency_report.generated_at == GENERATED_AT
    assert frequency_report.redacted_candidate_ref == "candidate_ref_0123456789abcdef"
    assert frequency_report.revision_count == d("0")
    assert frequency_report.revision_frequency_component == d("0.000000")
    assert frequency_report.high_impact_revision_component == d("0.000000")
    assert frequency_report.contradictory_revision_component == d("0.000000")
    assert frequency_report.same_day_revision_component == d("0.000000")
    assert frequency_report.source_instability_component == d("0.050000")
    assert frequency_report.short_observation_window_component == d("0.000000")
    assert frequency_report.source_revision_frequency_score == d("0.007500")
    assert frequency_report.source_revision_frequency_status == "pass"
    assert frequency_report.hard_blocker_codes == ()
    assert frequency_report.reason_codes == (
        "local_revision_frequency_facts_present",
        "source_revision_frequency_pass",
        "revision_count_pass",
        "high_impact_revision_ratio_pass",
        "contradictory_revision_ratio_pass",
        "same_day_revision_ratio_pass",
        "source_stability_pass",
        "short_observation_window_pass",
    )
    assert frequency_report.paper_only is True
    assert frequency_report.report_only is True
    assert frequency_report.readonly is True
    assert_sha256(frequency_report.derived_validation_digest)


def test_watch_status_captures_frequent_revisions_without_hard_blockers() -> None:
    frequency_report = report(
        score_input(
            revision_count=d("3"),
            high_impact_revision_ratio=d("0.200000"),
            contradictory_revision_ratio=d("0.100000"),
            same_day_revision_ratio=d("0.300000"),
            source_stability_score=d("0.600000"),
            observation_window_days=d("4.000000"),
            reason_codes=(),
        ),
    )

    assert frequency_report.source_revision_frequency_status == "watch"
    assert frequency_report.revision_frequency_component == d("0.500000")
    assert frequency_report.source_instability_component == d("0.400000")
    assert frequency_report.short_observation_window_component == d("0.500000")
    assert frequency_report.source_revision_frequency_score == d("0.315000")
    assert frequency_report.hard_blocker_codes == ()
    assert "source_revision_frequency_watch" in frequency_report.reason_codes
    assert "revision_count_watch" in frequency_report.reason_codes
    assert "high_impact_revision_ratio_pass" in frequency_report.reason_codes

    module = api()
    assert module.SOURCE_REVISION_FREQUENCY_STATUSES == ("pass", "watch", "block")
    assert set(module.SOURCE_REVISION_FREQUENCY_STATUSES) == {"pass", "watch", "block"}


def test_block_status_captures_unstable_revision_pattern() -> None:
    frequency_report = report(
        score_input(
            revision_count=d("8"),
            high_impact_revision_ratio=d("0.700000"),
            contradictory_revision_ratio=d("0.500000"),
            same_day_revision_ratio=d("0.800000"),
            source_stability_score=d("0.100000"),
            observation_window_days=d("0.500000"),
            reason_codes=(),
        ),
    )

    assert frequency_report.source_revision_frequency_status == "block"
    assert frequency_report.revision_frequency_component == d("1.000000")
    assert frequency_report.source_instability_component == d("0.900000")
    assert frequency_report.short_observation_window_component == d("1.000000")
    assert frequency_report.source_revision_frequency_score == d("0.795000")
    assert frequency_report.hard_blocker_codes == (
        "revision_count_block",
        "high_impact_revision_ratio_block",
        "contradictory_revision_ratio_block",
        "same_day_revision_ratio_block",
        "source_stability_block",
        "short_observation_window_block",
        "source_revision_frequency_score_block",
    )
    assert "source_revision_frequency_block" in frequency_report.reason_codes


def test_decimal_exact_type_rejection_and_canonical_inputs() -> None:
    module = api()

    with pytest.raises(ValueError, match="revision_count must be a Decimal"):
        score_input(revision_count=0)
    with pytest.raises(ValueError, match="source_stability_score must be a Decimal"):
        score_input(source_stability_score=0.1)
    with pytest.raises(ValueError, match="source_stability_score must be a Decimal"):
        score_input(source_stability_score=DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="revision_count must be integral"):
        score_input(revision_count=d("1.500000"))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        score_input(generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="redacted_candidate_ref must be redacted"):
        score_input(redacted_candidate_ref="raw-candidate-123")
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        score_input(reason_codes=["local_revision_frequency_facts_present"])
    with pytest.raises(ValueError, match="weights must sum to one"):
        config(short_observation_window_weight=d("0.060000"))
    with pytest.raises(ValueError, match="pass threshold must not exceed watch"):
        config(max_pass_source_revision_frequency_score=d("0.700000"))
    with pytest.raises(ValueError, match="watch observation window must not exceed pass"):
        config(min_watch_observation_window_days=d("8.000000"))
    with pytest.raises(ValueError, match="supported version"):
        config(config_version="candidate-decision-source-revision-frequency-score-next")
    with pytest.raises(ValueError, match="Input"):
        report(object())
    with pytest.raises(ValueError, match="Config"):
        report(score_input(), object())

    subject = score_input()
    rebuilt = module.CandidateDecisionSourceRevisionFrequencyScoreInput(
        **public_field_values(subject),
    )
    assert rebuilt == subject


def test_public_payload_rejects_leaks_status_aliases_numbers_and_missing_flags() -> None:
    module = api()

    unsafe_payloads = (
        ({"candidate_id": "abc"}, "raw market or candidate"),
        ({"market_id": "abc"}, "raw market or candidate"),
        ({"market_slug": "slug"}, "raw market or candidate"),
        ({"question": "will this resolve"}, "raw market or candidate"),
        ({"safe_key": "candidate_id=abc"}, "raw market or candidate"),
        ({"source_ref": "source-ref:abc123"}, "source references"),
        ({"source_url": "https://example.test/source"}, "source references"),
        ({"source_text": "raw source text"}, "source references"),
        ({"safe_key": "https://example.test/source"}, "source references"),
        ({"safe_key": "orders_table"}, "unsafe live surface"),
        ({"safe_key": "api-token"}, "unsafe live surface"),
        ({"safe_key": "wallet order trade"}, "unsafe live surface"),
        ({"safe_key": "buy sell recommendation"}, "unsafe live surface"),
        ({"safe_key": "position_size"}, "unsafe live surface"),
        ({"source_revision_frequency_status": "blocked"}, "public status"),
        ({"safe_key": "ready"}, "public status"),
        ({"safe_key": "matched"}, "public status"),
        ({"safe_key": "supported"}, "public status"),
        ({"revision_count": 1}, "decimal strings"),
        ({"revision_count": 1.0}, "decimal strings"),
        ({"paper_only": True, "report_only": True}, "readonly"),
        (["not", "object"], "public payload must be a JSON object"),
    )

    for payload, match in unsafe_payloads:
        with pytest.raises(ValueError, match=match):
            module.validate_candidate_decision_source_revision_frequency_score_public_payload(
                payload,
            )


def test_hard_flags_frozen_dataclasses_and_report_only_scope() -> None:
    module = api()
    cfg = config()
    subject = score_input()
    frequency_report = report(subject, cfg)

    assert is_dataclass(cfg)
    assert is_dataclass(subject)
    assert is_dataclass(frequency_report)
    assert module.CandidateDecisionSourceRevisionFrequencyScoreConfig.__dataclass_params__.frozen
    assert module.CandidateDecisionSourceRevisionFrequencyScoreInput.__dataclass_params__.frozen
    assert module.CandidateDecisionSourceRevisionFrequencyScoreReport.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.revision_count = d("9")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        frequency_report.source_revision_frequency_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(module.CandidateDecisionSourceRevisionFrequencyScoreConfig):
            pass

    for instance in (cfg, subject, frequency_report):
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

    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(frequency_report, readonly=False)


def test_deterministic_payload_is_json_ready_and_redacted() -> None:
    module = api()
    subject = score_input(
        generated_at=datetime(2026, 7, 7, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    expected = report(subject)

    with localcontext() as context:
        context.prec = 2
        context.rounding = "ROUND_UP"
        actual = report(subject)

    assert actual.payload == expected.payload
    payload = module.candidate_decision_source_revision_frequency_score_payload(actual)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()

    assert payload == actual.payload
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["redacted_candidate_ref"] == "candidate_ref_0123456789abcdef"
    assert payload["revision_count"] == "0"
    assert payload["source_revision_frequency_score"] == "0.007500"
    assert payload["source_revision_frequency_status"] == "pass"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == actual.derived_validation_digest
    assert_json_ready_no_numbers(payload)
    assert_sha256(payload["derived_validation_digest"])

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
        "blocked",
        "ready",
        "matched",
        "supported",
    ):
        assert forbidden not in rendered


def test_report_consistency_rejects_mutated_derived_fields() -> None:
    module = api()
    frequency_report = report()

    with pytest.raises(ValueError, match="source_revision_frequency_score"):
        replace(
            frequency_report,
            source_revision_frequency_score=d("0.500000"),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="source_revision_frequency_status"):
        replace(
            frequency_report,
            source_revision_frequency_status="watch",
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="hard_blocker_codes"):
        replace(
            frequency_report,
            hard_blocker_codes=("source_revision_frequency_score_block",),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        object.__setattr__(frequency_report, "derived_validation_digest", "0" * 64)
        module.candidate_decision_source_revision_frequency_score_payload(frequency_report)

    rebuilt = module.CandidateDecisionSourceRevisionFrequencyScoreReport(
        **public_field_values(report()),
    )
    assert rebuilt == report()


def test_no_unsafe_runtime_surface_or_io_is_added() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_CANDIDATE_DECISION_SOURCE_REVISION_FREQUENCY_SCORE_CONFIG_VERSION",
        "SOURCE_REVISION_FREQUENCY_STATUSES",
        "CandidateDecisionSourceRevisionFrequencyScoreConfig",
        "CandidateDecisionSourceRevisionFrequencyScoreInput",
        "CandidateDecisionSourceRevisionFrequencyScoreReport",
        "build_candidate_decision_source_revision_frequency_score_report",
        "candidate_decision_source_revision_frequency_score_payload",
        "validate_candidate_decision_source_revision_frequency_score_public_payload",
        "reject_candidate_decision_source_revision_frequency_score_unsafe_payload",
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
