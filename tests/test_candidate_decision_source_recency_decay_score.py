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


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_source_recency_decay_score"
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
            module.DEFAULT_CANDIDATE_DECISION_SOURCE_RECENCY_DECAY_SCORE_CONFIG_VERSION
        ),
        "min_pass_recency_decay_score": d("0.750000"),
        "min_watch_recency_decay_score": d("0.500000"),
        "max_pass_newest_source_age_minutes": d("60.000000"),
        "max_watch_newest_source_age_minutes": d("240.000000"),
        "max_pass_average_source_age_minutes": d("180.000000"),
        "max_watch_average_source_age_minutes": d("720.000000"),
        "max_pass_oldest_source_age_minutes": d("1440.000000"),
        "max_watch_oldest_source_age_minutes": d("2880.000000"),
        "min_pass_source_count": d("3"),
        "min_watch_source_count": d("1"),
        "min_pass_independent_source_ratio": d("0.670000"),
        "min_watch_independent_source_ratio": d("0.340000"),
    }
    values.update(overrides)
    return module.CandidateDecisionSourceRecencyDecayScoreConfig(**values)


def score_input(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "generated_at": GENERATED_AT,
        "newest_source_at": GENERATED_AT - timedelta(minutes=30),
        "oldest_source_at": GENERATED_AT - timedelta(minutes=180),
        "source_count": d("4"),
        "average_source_age_minutes": d("90.000000"),
        "independent_source_ratio": d("0.750000"),
        "reason_codes": ("local_recency_facts_present",),
    }
    values.update(overrides)
    return module.CandidateDecisionSourceRecencyDecayScoreInput(**values)


def report(subject: object | None = None, cfg: object | None = None):
    module = api()
    return module.build_candidate_decision_source_recency_decay_score_report(
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
    if isinstance(value, datetime):
        raise AssertionError(f"unexpected datetime value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numbers_or_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_numbers_or_float_values(item)


def assert_sha256(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def test_fresh_multi_source_evidence_passes_with_quantized_report() -> None:
    module = api()

    recency_report = report()

    assert type(recency_report) is module.CandidateDecisionSourceRecencyDecayScoreReport
    assert recency_report.generated_at == GENERATED_AT
    assert recency_report.newest_source_at == GENERATED_AT - timedelta(minutes=30)
    assert recency_report.oldest_source_at == GENERATED_AT - timedelta(minutes=180)
    assert recency_report.source_count == d("4")
    assert recency_report.newest_source_age_minutes == d("30.000000")
    assert recency_report.oldest_source_age_minutes == d("180.000000")
    assert recency_report.source_age_span_minutes == d("150.000000")
    assert recency_report.average_source_age_minutes == d("90.000000")
    assert recency_report.newest_source_recency_component == d("1.000000")
    assert recency_report.average_source_recency_component == d("1.000000")
    assert recency_report.oldest_source_recency_component == d("1.000000")
    assert recency_report.source_count_coverage_component == d("1.000000")
    assert recency_report.independence_coverage_component == d("1.000000")
    assert recency_report.recency_decay_score == d("1.000000")
    assert recency_report.recency_status == "pass"
    assert recency_report.hard_blocker_codes == ()
    assert recency_report.reason_codes == (
        "local_recency_facts_present",
        "source_recency_decay_pass",
        "newest_source_age_pass",
        "average_source_age_pass",
        "oldest_source_age_pass",
        "source_count_pass",
        "independent_source_ratio_pass",
        "recency_decay_score_pass",
    )
    assert recency_report.paper_only is True
    assert recency_report.report_only is True
    assert recency_report.readonly is True
    assert_sha256(recency_report.derived_validation_digest)


def test_watch_thresholds_apply_linear_decay_without_float_arithmetic() -> None:
    subject = score_input(
        newest_source_at=GENERATED_AT - timedelta(minutes=120),
        oldest_source_at=GENERATED_AT - timedelta(minutes=1500),
        source_count=d("2"),
        average_source_age_minutes=d("360.000000"),
        independent_source_ratio=d("0.500000"),
        reason_codes=(),
    )
    recency_report = report(subject)

    assert recency_report.recency_status == "watch"
    assert recency_report.newest_source_age_minutes == d("120.000000")
    assert recency_report.oldest_source_age_minutes == d("1500.000000")
    assert recency_report.source_age_span_minutes == d("1380.000000")
    assert recency_report.newest_source_recency_component == d("0.666667")
    assert recency_report.average_source_recency_component == d("0.666667")
    assert recency_report.oldest_source_recency_component == d("0.958333")
    assert recency_report.source_count_coverage_component == d("0.500000")
    assert recency_report.independence_coverage_component == d("0.484848")
    assert recency_report.recency_decay_score == d("0.655303")
    assert recency_report.hard_blocker_codes == ()
    assert recency_report.reason_codes == (
        "source_recency_decay_watch",
        "newest_source_age_watch",
        "average_source_age_watch",
        "oldest_source_age_watch",
        "source_count_watch",
        "independent_source_ratio_watch",
        "recency_decay_score_watch",
    )


def test_stale_or_undercovered_evidence_blocks() -> None:
    recency_report = report(
        score_input(
            newest_source_at=GENERATED_AT - timedelta(minutes=300),
            oldest_source_at=GENERATED_AT - timedelta(minutes=3000),
            source_count=d("1"),
            average_source_age_minutes=d("900.000000"),
            independent_source_ratio=d("0.200000"),
            reason_codes=(),
        ),
    )

    assert recency_report.recency_status == "block"
    assert recency_report.recency_decay_score == d("0.000000")
    assert recency_report.hard_blocker_codes == (
        "newest_source_age_block",
        "average_source_age_block",
        "oldest_source_age_block",
        "independent_source_ratio_block",
        "recency_decay_score_block",
    )
    assert recency_report.reason_codes == (
        "source_recency_decay_block",
        "newest_source_age_block",
        "average_source_age_block",
        "oldest_source_age_block",
        "source_count_watch",
        "independent_source_ratio_block",
        "recency_decay_score_block",
    )


def test_age_calculation_quantizes_subminute_datetimes_and_ignores_ambient_context() -> None:
    newest = GENERATED_AT - timedelta(seconds=60, microseconds=500000)
    oldest = GENERATED_AT - timedelta(seconds=90, microseconds=250000)
    subject = score_input(
        newest_source_at=newest,
        oldest_source_at=oldest,
        average_source_age_minutes=d("1.250000"),
    )
    expected = report(subject)

    assert expected.newest_source_age_minutes == d("1.008333")
    assert expected.oldest_source_age_minutes == d("1.504167")
    assert expected.source_age_span_minutes == d("0.495834")

    with localcontext() as context:
        context.prec = 2
        context.rounding = "ROUND_UP"
        actual = report(subject)

    assert actual.payload == expected.payload


def test_payload_is_json_ready_redacted_and_tamper_checked() -> None:
    module = api()
    recency_report = report(
        score_input(
            generated_at=datetime(2026, 7, 7, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
            newest_source_at=datetime(2026, 7, 7, 4, 30, tzinfo=timezone(timedelta(hours=-7))),
            oldest_source_at=datetime(2026, 7, 7, 2, 0, tzinfo=timezone(timedelta(hours=-7))),
        ),
    )

    payload = module.candidate_decision_source_recency_decay_score_payload(
        recency_report,
    )
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()

    assert payload == recency_report.payload
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["newest_source_at"] == "2026-07-07T11:30:00+00:00"
    assert payload["oldest_source_at"] == "2026-07-07T09:00:00+00:00"
    assert payload["source_count"] == "4"
    assert payload["recency_decay_score"] == "1.000000"
    assert payload["reason_codes"] == list(recency_report.reason_codes)
    assert payload["derived_validation_digest"] == recency_report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_numbers_or_float_values(payload)

    for forbidden in (
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_refs",
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

    object.__setattr__(recency_report, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.candidate_decision_source_recency_decay_score_payload(recency_report)


def test_public_payload_validator_rejects_leaks_status_aliases_and_numbers() -> None:
    module = api()

    unsafe_payloads = (
        ({"market_id": "redacted"}, "raw market"),
        ({"market_slug": "redacted"}, "raw market"),
        ({"question": "will this resolve"}, "raw market"),
        ({"source_ref": "source-ref:abc123"}, "source refs"),
        ({"source_url": "https://example.test/source"}, "source refs"),
        ({"source_text": "raw source text"}, "source refs"),
        ({"safe_key": "https://example.test/source"}, "source refs"),
        ({"safe_key": "source-ref:abc123"}, "source refs"),
        ({"safe_key": "orders_table"}, "unsafe live surface"),
        ({"safe_key": "api-token"}, "unsafe live surface"),
        ({"safe_key": "wallet order trade"}, "unsafe live surface"),
        ({"safe_key": "buy sell recommendation"}, "unsafe live surface"),
        ({"safe_key": "position_size"}, "unsafe live surface"),
        ({"recency_status": "blocked"}, "public status"),
        ({"recency_status": "ready"}, "public status"),
        ({"safe_key": "matched"}, "public status"),
        ({"source_count": 1}, "decimal strings"),
        ({"source_count": 1.0}, "decimal strings"),
        (["not", "object"], "public payload must be a JSON object"),
    )

    for payload, match in unsafe_payloads:
        with pytest.raises(ValueError, match=match):
            module.validate_candidate_decision_source_recency_decay_score_public_payload(
                payload,
            )


def test_dataclasses_are_frozen_final_decimal_only_and_flagged() -> None:
    module = api()
    cfg = config()
    subject = score_input()
    recency_report = report(subject, cfg)

    assert is_dataclass(cfg)
    assert is_dataclass(subject)
    assert is_dataclass(recency_report)
    assert module.CandidateDecisionSourceRecencyDecayScoreConfig.__dataclass_params__.frozen
    assert module.CandidateDecisionSourceRecencyDecayScoreInput.__dataclass_params__.frozen
    assert module.CandidateDecisionSourceRecencyDecayScoreReport.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.source_count = d("9")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        recency_report.recency_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(module.CandidateDecisionSourceRecencyDecayScoreConfig):
            pass

    for instance in (cfg, subject, recency_report):
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

    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        score_input(source_count=4)
    with pytest.raises(ValueError, match="independent_source_ratio must be a Decimal"):
        score_input(independent_source_ratio=0.75)
    with pytest.raises(ValueError, match="independent_source_ratio must be a Decimal"):
        score_input(independent_source_ratio=DecimalSubclass("0.750000"))
    with pytest.raises(ValueError, match="source_count must be integral"):
        score_input(source_count=d("2.500000"))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        score_input(generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="newest_source_at must not be after generated_at"):
        score_input(newest_source_at=GENERATED_AT + timedelta(minutes=1))
    with pytest.raises(ValueError, match="oldest_source_at must not be after newest_source_at"):
        score_input(
            newest_source_at=GENERATED_AT - timedelta(minutes=60),
            oldest_source_at=GENERATED_AT - timedelta(minutes=30),
        )
    with pytest.raises(ValueError, match="average_source_age_minutes must be between"):
        score_input(average_source_age_minutes=d("1.000000"))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        score_input(reason_codes=["local_recency_facts_present"])
    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(recency_report, readonly=False)
    with pytest.raises(ValueError, match="Input"):
        report(object())
    with pytest.raises(ValueError, match="Config"):
        report(score_input(), object())
    with pytest.raises(ValueError, match="supported version"):
        config(config_version="candidate-decision-source-recency-decay-score-next")

    rebuilt_input = module.CandidateDecisionSourceRecencyDecayScoreInput(
        **public_field_values(subject),
    )
    assert rebuilt_input == subject
    rebuilt_report = module.CandidateDecisionSourceRecencyDecayScoreReport(
        **public_field_values(recency_report),
    )
    assert rebuilt_report == recency_report


def test_report_consistency_rejects_mutated_derived_fields_and_status_vocabulary() -> None:
    module = api()
    recency_report = report()

    with pytest.raises(ValueError, match="recency_decay_score"):
        replace(recency_report, recency_decay_score=d("0.500000"), derived_validation_digest="")
    with pytest.raises(ValueError, match="recency_status"):
        replace(recency_report, recency_status="watch", derived_validation_digest="")
    with pytest.raises(ValueError, match="hard_blocker_codes"):
        replace(
            recency_report,
            hard_blocker_codes=("recency_decay_score_block",),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="recency_status"):
        module.CandidateDecisionSourceRecencyDecayScoreReport(
            **{
                **public_field_values(recency_report),
                "recency_status": "blocked",
                "derived_validation_digest": "",
            },
        )

    assert module.RECENCY_STATUSES == ("pass", "watch", "block")
    for public_status in module.RECENCY_STATUSES:
        assert public_status in {"pass", "watch", "block"}
    assert "ready" not in module.RECENCY_STATUSES
    assert "blocked" not in module.RECENCY_STATUSES
    assert "matched" not in module.RECENCY_STATUSES
    assert "supported" not in module.RECENCY_STATUSES


def test_no_unsafe_runtime_surface_or_io_is_added() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_CANDIDATE_DECISION_SOURCE_RECENCY_DECAY_SCORE_CONFIG_VERSION",
        "RECENCY_STATUSES",
        "CandidateDecisionSourceRecencyDecayScoreConfig",
        "CandidateDecisionSourceRecencyDecayScoreInput",
        "CandidateDecisionSourceRecencyDecayScoreReport",
        "build_candidate_decision_source_recency_decay_score_report",
        "candidate_decision_source_recency_decay_score_payload",
        "validate_candidate_decision_source_recency_decay_score_public_payload",
        "reject_candidate_decision_source_recency_decay_score_unsafe_payload",
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
