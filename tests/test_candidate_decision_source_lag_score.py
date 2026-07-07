from __future__ import annotations

import ast
import hashlib
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal, localcontext
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_source_lag_score"
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
        "config_version": module.DEFAULT_CANDIDATE_DECISION_SOURCE_LAG_SCORE_CONFIG_VERSION,
        "min_pass_source_lag_score": d("0.800000"),
        "min_watch_source_lag_score": d("0.500000"),
        "max_pass_publication_lag_minutes": d("30.000000"),
        "max_watch_publication_lag_minutes": d("240.000000"),
        "max_pass_source_after_signal_lag_minutes": d("15.000000"),
        "max_watch_source_after_signal_lag_minutes": d("180.000000"),
        "max_pass_research_signal_age_minutes": d("120.000000"),
        "max_watch_research_signal_age_minutes": d("720.000000"),
        "min_pass_critical_source_count": d("3"),
        "min_watch_critical_source_count": d("1"),
        "min_pass_independent_source_ratio": d("0.670000"),
        "min_watch_independent_source_ratio": d("0.340000"),
    }
    values.update(overrides)
    return module.CandidateDecisionSourceLagScoreConfig(**values)


def score_input(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "generated_at": GENERATED_AT,
        "information_event_at": GENERATED_AT - timedelta(minutes=120),
        "source_published_at": GENERATED_AT - timedelta(minutes=110),
        "research_signal_asof_at": GENERATED_AT - timedelta(minutes=90),
        "critical_source_count": d("4"),
        "independent_source_ratio": d("0.750000"),
        "reason_codes": ("local_source_lag_facts_present",),
    }
    values.update(overrides)
    return module.CandidateDecisionSourceLagScoreInput(**values)


def report(subject: object | None = None, cfg: object | None = None):
    return api().build_candidate_decision_source_lag_score_report(
        score_input() if subject is None else subject,
        config=config() if cfg is None else cfg,
    )


def public_field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def payload_digest(payload: dict[str, object]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded_payload = json.dumps(
        digest_payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded_payload.encode("utf-8")).hexdigest()


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


def test_fresh_incorporated_source_lag_passes_with_quantized_report() -> None:
    module = api()

    lag_report = report()

    assert type(lag_report) is module.CandidateDecisionSourceLagScoreReport
    assert lag_report.generated_at == GENERATED_AT
    assert lag_report.publication_lag_minutes == d("10.000000")
    assert lag_report.source_after_signal_lag_minutes == d("0.000000")
    assert lag_report.research_signal_age_minutes == d("90.000000")
    assert lag_report.critical_source_count == d("4")
    assert lag_report.independent_source_ratio == d("0.750000")
    assert lag_report.publication_lag_component == d("1.000000")
    assert lag_report.source_after_signal_lag_component == d("1.000000")
    assert lag_report.research_signal_freshness_component == d("1.000000")
    assert lag_report.source_count_coverage_component == d("1.000000")
    assert lag_report.independence_coverage_component == d("1.000000")
    assert lag_report.source_lag_score == d("1.000000")
    assert lag_report.lag_status == "pass"
    assert lag_report.hard_blocker_codes == ()
    assert lag_report.reason_codes == (
        "local_source_lag_facts_present",
        "source_lag_pass",
        "publication_lag_pass",
        "source_after_signal_lag_pass",
        "research_signal_age_pass",
        "critical_source_count_pass",
        "independent_source_ratio_pass",
        "source_lag_score_pass",
    )
    assert lag_report.paper_only is True
    assert lag_report.report_only is True
    assert lag_report.readonly is True
    assert_sha256(lag_report.derived_validation_digest)


def test_watch_thresholds_apply_decimal_linear_decay() -> None:
    subject = score_input(
        information_event_at=GENERATED_AT - timedelta(minutes=300),
        source_published_at=GENERATED_AT - timedelta(minutes=240),
        research_signal_asof_at=GENERATED_AT - timedelta(minutes=270),
        critical_source_count=d("2"),
        independent_source_ratio=d("0.500000"),
        reason_codes=(),
    )

    lag_report = report(subject)

    assert lag_report.lag_status == "watch"
    assert lag_report.publication_lag_minutes == d("60.000000")
    assert lag_report.source_after_signal_lag_minutes == d("30.000000")
    assert lag_report.research_signal_age_minutes == d("270.000000")
    assert lag_report.publication_lag_component == d("0.857143")
    assert lag_report.source_after_signal_lag_component == d("0.909091")
    assert lag_report.research_signal_freshness_component == d("0.750000")
    assert lag_report.source_count_coverage_component == d("0.500000")
    assert lag_report.independence_coverage_component == d("0.484848")
    assert lag_report.source_lag_score == d("0.700216")
    assert lag_report.hard_blocker_codes == ()
    assert lag_report.reason_codes == (
        "source_lag_watch",
        "publication_lag_watch",
        "source_after_signal_lag_watch",
        "research_signal_age_watch",
        "critical_source_count_watch",
        "independent_source_ratio_watch",
        "source_lag_score_watch",
    )


def test_stale_source_publication_lag_blocks_research_priority() -> None:
    lag_report = report(
        score_input(
            information_event_at=GENERATED_AT - timedelta(minutes=960),
            source_published_at=GENERATED_AT - timedelta(minutes=630),
            research_signal_asof_at=GENERATED_AT - timedelta(minutes=950),
            critical_source_count=d("1"),
            independent_source_ratio=d("0.200000"),
            reason_codes=(),
        ),
    )

    assert lag_report.lag_status == "block"
    assert lag_report.source_lag_score == d("0.000000")
    assert lag_report.hard_blocker_codes == (
        "publication_lag_block",
        "source_after_signal_lag_block",
        "research_signal_age_block",
        "independent_source_ratio_block",
        "source_lag_score_block",
    )
    assert lag_report.reason_codes == (
        "source_lag_block",
        "publication_lag_block",
        "source_after_signal_lag_block",
        "research_signal_age_block",
        "critical_source_count_watch",
        "independent_source_ratio_block",
        "source_lag_score_block",
    )


def test_subminute_age_calculation_ignores_ambient_decimal_context() -> None:
    subject = score_input(
        information_event_at=GENERATED_AT - timedelta(seconds=120, microseconds=500000),
        source_published_at=GENERATED_AT - timedelta(seconds=60, microseconds=250000),
        research_signal_asof_at=GENERATED_AT - timedelta(seconds=90, microseconds=750000),
    )
    expected = report(subject)

    assert expected.publication_lag_minutes == d("1.004167")
    assert expected.source_after_signal_lag_minutes == d("0.508333")
    assert expected.research_signal_age_minutes == d("1.512500")

    with localcontext() as context:
        context.prec = 2
        context.rounding = "ROUND_UP"
        actual = report(subject)

    assert actual.payload == expected.payload


def test_payload_is_json_ready_redacted_and_tamper_checked() -> None:
    module = api()
    lag_report = report()

    payload = module.candidate_decision_source_lag_score_payload(lag_report)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()

    assert payload == lag_report.payload
    assert payload["publication_lag_minutes"] == "10.000000"
    assert payload["source_lag_score"] == "1.000000"
    assert payload["lag_status"] == "pass"
    assert payload["derived_validation_digest"] == lag_report.derived_validation_digest
    assert payload["derived_validation_digest"] == payload_digest(payload)
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

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(lag_report, derived_validation_digest="0" * 64)


def test_public_payload_validator_rejects_leaks_status_aliases_and_numbers() -> None:
    module = api()
    valid_payload = module.candidate_decision_source_lag_score_payload(report())
    assert module.validate_candidate_decision_source_lag_score_public_payload(valid_payload) is None

    unsafe_payloads = (
        ({"candidate_id": "abc"}, "raw candidate"),
        ({"raw_candidate_id": "abc"}, "raw candidate"),
        ({"market_id": "abc"}, "market"),
        ({"market_slug": "will-x-happen"}, "market"),
        ({"question": "Will X happen?"}, "market"),
        ({"source_ref": "source-ref:abc123"}, "source"),
        ({"source_url": "https://example.test/source"}, "source"),
        ({"source_text": "raw source text"}, "source"),
        ({"safe_key": "https://example.test/source"}, "source"),
        ({"safe_key": "source_ref:abc123"}, "source"),
        ({"safe_key": "postgres://user@host/db"}, "source"),
        ({"safe_key": "orders table"}, "unsafe"),
        ({"safe_key": "api-token"}, "unsafe"),
        ({"safe_key": "wallet order trade"}, "unsafe"),
        ({"safe_key": "buy sell recommendation"}, "unsafe"),
        ({"safe_key": "position_size"}, "unsafe"),
        ({"lag_status": "blocked"}, "public status"),
        ({"lag_status": "ready"}, "public status"),
        ({"safe_key": "matched"}, "public status"),
        ({"critical_source_count": 1}, "decimal strings"),
        ({"critical_source_count": 1.0}, "decimal strings"),
        (["not", "object"], "public payload must be a JSON object"),
    )
    for payload, match in unsafe_payloads:
        with pytest.raises(ValueError, match=match):
            module.validate_candidate_decision_source_lag_score_public_payload(payload)


def test_dataclasses_are_frozen_final_decimal_only_and_flagged() -> None:
    module = api()
    cfg = config()
    subject = score_input()
    lag_report = report(subject, cfg)

    assert is_dataclass(cfg)
    assert is_dataclass(subject)
    assert is_dataclass(lag_report)
    assert module.CandidateDecisionSourceLagScoreConfig.__dataclass_params__.frozen
    assert module.CandidateDecisionSourceLagScoreInput.__dataclass_params__.frozen
    assert module.CandidateDecisionSourceLagScoreReport.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.critical_source_count = d("9")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        lag_report.lag_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(module.CandidateDecisionSourceLagScoreInput):
            pass

    for instance in (cfg, subject, lag_report):
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

    with pytest.raises(ValueError, match="critical_source_count must be a Decimal"):
        score_input(critical_source_count=4)
    with pytest.raises(ValueError, match="independent_source_ratio must be a Decimal"):
        score_input(independent_source_ratio=0.75)
    with pytest.raises(ValueError, match="independent_source_ratio must be a Decimal"):
        score_input(independent_source_ratio=DecimalSubclass("0.750000"))
    with pytest.raises(ValueError, match="max_pass_publication_lag_minutes must be a Decimal"):
        config(max_pass_publication_lag_minutes=DecimalSubclass("30.000000"))
    with pytest.raises(ValueError, match="critical_source_count must be integral"):
        score_input(critical_source_count=d("2.500000"))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        score_input(generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="source_published_at must not be before information_event_at"):
        score_input(
            information_event_at=GENERATED_AT - timedelta(minutes=60),
            source_published_at=GENERATED_AT - timedelta(minutes=120),
        )
    with pytest.raises(ValueError, match="source_published_at must not be after generated_at"):
        score_input(source_published_at=GENERATED_AT + timedelta(minutes=1))
    with pytest.raises(ValueError, match="research_signal_asof_at must not be after generated_at"):
        score_input(research_signal_asof_at=GENERATED_AT + timedelta(minutes=1))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        score_input(reason_codes=["local_source_lag_facts_present"])
    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(lag_report, readonly=False)
    with pytest.raises(ValueError, match="Input"):
        report(object())
    with pytest.raises(ValueError, match="Config"):
        report(score_input(), object())
    with pytest.raises(ValueError, match="supported version"):
        config(config_version="candidate-decision-source-lag-score-next")

    rebuilt_input = module.CandidateDecisionSourceLagScoreInput(**public_field_values(subject))
    assert rebuilt_input == subject
    rebuilt_report = module.CandidateDecisionSourceLagScoreReport(
        **public_field_values(lag_report),
    )
    assert rebuilt_report == lag_report


def test_report_consistency_rejects_mutated_fields_and_status_vocabulary() -> None:
    module = api()
    lag_report = report()

    with pytest.raises(ValueError, match="source_lag_score"):
        replace(lag_report, source_lag_score=d("0.500000"), derived_validation_digest="")
    with pytest.raises(ValueError, match="lag_status"):
        replace(lag_report, lag_status="watch", derived_validation_digest="")
    with pytest.raises(ValueError, match="hard_blocker_codes"):
        replace(
            lag_report,
            hard_blocker_codes=("source_lag_score_block",),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="lag_status"):
        module.CandidateDecisionSourceLagScoreReport(
            **{
                **public_field_values(lag_report),
                "lag_status": "blocked",
                "derived_validation_digest": "",
            },
        )

    assert module.SOURCE_LAG_STATUSES == ("pass", "watch", "block")
    for public_status in module.SOURCE_LAG_STATUSES:
        assert public_status in {"pass", "watch", "block"}
    assert "ready" not in module.SOURCE_LAG_STATUSES
    assert "blocked" not in module.SOURCE_LAG_STATUSES
    assert "matched" not in module.SOURCE_LAG_STATUSES
    assert "supported" not in module.SOURCE_LAG_STATUSES


def test_deterministic_payload_and_report_digest_consistency() -> None:
    first = report()
    second = report(
        score_input(
            reason_codes=("local_source_lag_facts_present",),
        ),
    )

    assert first == second
    assert first.payload == second.payload
    assert first.derived_validation_digest == payload_digest(first.payload)
    assert second.derived_validation_digest == payload_digest(second.payload)


def test_module_has_no_network_persistence_or_runtime_mutation_surface() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_CANDIDATE_DECISION_SOURCE_LAG_SCORE_CONFIG_VERSION",
        "SOURCE_LAG_STATUSES",
        "CandidateDecisionSourceLagScoreConfig",
        "CandidateDecisionSourceLagScoreInput",
        "CandidateDecisionSourceLagScoreReport",
        "build_candidate_decision_source_lag_score_report",
        "candidate_decision_source_lag_score_payload",
        "validate_candidate_decision_source_lag_score_public_payload",
        "reject_candidate_decision_source_lag_score_unsafe_payload",
    )

    source = inspect.getsource(module)
    tree = ast.parse(source)
    forbidden_import_roots = {
        "boto3",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    forbidden_call_names = {
        "commit",
        "connect",
        "execute",
        "executemany",
        "getenv",
        "open",
        "request",
        "submit",
        "urlopen",
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
