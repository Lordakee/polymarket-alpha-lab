from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_team_memory_retrieval_policy.py",
)
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_memory_retrieval_policy",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def memory(**overrides: object):
    module = api()
    values = {
        "team_id": "team_alpha",
        "domain": "macro_rates",
        "event_type": "central_bank_release",
        "retrieval_reference": "raw-candidate-alpha-market_slug-question",
        "evidence_similarity_score": d("0.900000"),
        "historical_error_rate": d("0.050000"),
        "historical_error_pattern_count": d("0.000000"),
        "analog_event_count": d("5.000000"),
        "memory_age_days": d("5.000000"),
    }
    values.update(overrides)
    return module.ResearchTeamMemoryRetrievalPolicyMemory(**values)


def build_report(*items: object, **overrides: object):
    module = api()
    values = {
        "memories": items,
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return module.build_research_team_memory_retrieval_policy_report(**values)


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        return tuple(child for item in value.values() for child in walk_values(item))
    if isinstance(value, list):
        return tuple(child for item in value for child in walk_values(item))
    return (value,)


def test_retrieval_policy_builds_pass_watch_and_block_report_only_plan() -> None:
    module = api()
    report = build_report(
        memory(
            team_id="team_pass",
            domain="macro_rates",
            event_type="central_bank_release",
            retrieval_reference="raw-pass-id",
            evidence_similarity_score=d("0.900000"),
            historical_error_rate=d("0.050000"),
            historical_error_pattern_count=d("0.000000"),
            analog_event_count=d("5.000000"),
            memory_age_days=d("5.000000"),
        ),
        memory(
            team_id="team_watch",
            domain="policy_ai",
            event_type="rulemaking_window",
            retrieval_reference="https://unsafe.example/source?token=secret",
            evidence_similarity_score=d("0.620000"),
            historical_error_rate=d("0.120000"),
            historical_error_pattern_count=d("1.000000"),
            analog_event_count=d("2.000000"),
            memory_age_days=d("20.000000"),
        ),
        memory(
            team_id="team_block",
            domain="sports_soccer",
            event_type="lineup_news",
            retrieval_reference="wallet://auth/raw-market-question",
            evidence_similarity_score=d("0.200000"),
            historical_error_rate=d("0.500000"),
            historical_error_pattern_count=d("4.000000"),
            analog_event_count=d("0.000000"),
            memory_age_days=d("120.000000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone.utc),
    )

    assert type(report) is module.ResearchTeamMemoryRetrievalPolicyReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.plan_status == "block"
    assert report.memory_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_retrieval_score == d("0.554018")
    assert report.highest_error_risk_score == d("1.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.plan_status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.retrieval_rank for row in report.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )

    blocked = report.rows[0]
    assert blocked.team_id == "team_block"
    assert blocked.memory_digest != "wallet://auth/raw-market-question"
    assert blocked.retrieval_score == d("0.090000")
    assert blocked.error_risk_score == d("1.000000")
    assert blocked.plan_focus == "domain_event_error_pattern_review"
    assert blocked.reason_codes == (
        "memory_retrieval_policy_block",
        "evidence_similarity_weak",
        "historical_error_pattern_severe",
        "analog_event_depth_missing",
        "memory_age_expired",
    )

    watched = report.rows[1]
    assert watched.plan_status == "watch"
    assert watched.retrieval_score == d("0.635111")
    assert watched.error_risk_score == d("0.286667")
    assert watched.reason_codes == (
        "memory_retrieval_policy_watch",
        "evidence_similarity_watch",
        "historical_error_pattern_elevated",
        "analog_event_depth_thin",
        "memory_age_fresh",
    )

    passed = report.rows[2]
    assert passed.plan_status == "pass"
    assert passed.retrieval_score == d("0.936944")
    assert passed.error_risk_score == d("0.050000")
    assert passed.reason_codes == (
        "memory_retrieval_policy_pass",
        "evidence_similarity_strong",
        "historical_error_pattern_clear",
        "analog_event_depth_sufficient",
        "memory_age_fresh",
    )


def test_payload_is_json_ready_deterministic_and_does_not_leak_raw_identifiers() -> None:
    first = memory(
        team_id="team_pass",
        retrieval_reference="raw-candidate-001-market_id-market_slug-question",
    )
    second = memory(
        team_id="team_watch",
        domain="policy_ai",
        event_type="rulemaking_window",
        retrieval_reference="https://source.example/text?token=secret&dsn=postgres",
        evidence_similarity_score=d("0.620000"),
        historical_error_rate=d("0.120000"),
        historical_error_pattern_count=d("1.000000"),
        analog_event_count=d("2.000000"),
        memory_age_days=d("20.000000"),
    )

    left = build_report(first, second)
    right = build_report(second, first)
    payload = api().research_team_memory_retrieval_policy_payload(left)

    assert left.payload == right.payload
    assert left.validation_digest == right.validation_digest
    assert payload == left.payload
    json.dumps(payload, sort_keys=True)
    assert payload["memory_count"] == "2.000000"
    assert payload["average_retrieval_score"] == "0.786028"
    assert payload["rows"][0]["memory_digest"] != (
        "raw-candidate-001-market_id-market_slug-question"
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(type(value) in (Decimal, float, int) for value in walk_values(payload))

    public = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "raw-candidate-001",
        "market_id",
        "market_slug",
        "question",
        "source.example",
        "source_ref",
        "source_url",
        "source_text",
        "token",
        "secret",
        "dsn",
        "postgres",
        "table",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    ):
        assert forbidden not in public


def test_empty_report_is_blocked_report_only_and_digest_backed() -> None:
    report = build_report()

    assert report.plan_status == "block"
    assert report.memory_count == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("no_memory_retrieval_rows_supplied",)
    assert report.payload["validation_digest"] == report.validation_digest
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    cfg = module.ResearchTeamMemoryRetrievalPolicyConfig()
    item = memory()
    report = build_report(item)
    row = report.rows[0]

    for value in (cfg, item, row, report):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.readonly = False  # type: ignore[misc]
        for field in fields(value):
            field_value = getattr(value, field.name)
            if field.name.endswith("_score") or field.name.endswith("_count"):
                assert type(field_value) is Decimal
            if field.name in {"retrieval_rank", "analog_event_count", "memory_age_days"}:
                assert type(field_value) is Decimal


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        ("team_id", _StringSubclass("team_alpha"), "team_id must be a string"),
        ("domain", "market_slug", "domain has unsafe public value"),
        ("event_type", "question_text", "event_type has unsafe public value"),
        ("retrieval_reference", _StringSubclass("raw-alpha"), "retrieval_reference"),
        (
            "evidence_similarity_score",
            _DecimalSubclass("0.900000"),
            "evidence_similarity_score must be exactly Decimal",
        ),
        (
            "historical_error_rate",
            d("1.000001"),
            "historical_error_rate must be between zero and one",
        ),
        (
            "historical_error_pattern_count",
            d("-1.000000"),
            "historical_error_pattern_count must be nonnegative",
        ),
        (
            "analog_event_count",
            d("1.0000004"),
            "analog_event_count must use six decimal places or fewer",
        ),
        ("memory_age_days", Decimal("NaN"), "memory_age_days must be finite"),
    ),
)
def test_strict_type_and_value_validation_rejects_bad_inputs(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        memory(**{field_name: bad_value})


def test_build_and_payload_reject_bad_types_flags_and_leaky_public_payloads() -> None:
    module = api()

    with pytest.raises(ValueError, match="memories must be a sequence"):
        module.build_research_team_memory_retrieval_policy_report(
            memories=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="memories must contain"):
        build_report(object())
    with pytest.raises(ValueError, match="duplicate memory retrieval key"):
        build_report(memory(), memory())
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        build_report(generated_at=_DatetimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="paper_only must be True"):
        memory(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(memory(), report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        module.ResearchTeamMemoryRetrievalPolicyConfig(readonly=False)
    with pytest.raises(ValueError, match="weights must sum to 1.000000"):
        module.ResearchTeamMemoryRetrievalPolicyConfig(
            evidence_similarity_weight=d("0.460000"),
        )

    report = build_report(memory())
    with pytest.raises(ValueError, match="validation_digest"):
        replace(report, validation_digest="0" * 64)
    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_team_memory_retrieval_policy_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "market_id": "redacted",
            },
        )
    with pytest.raises(ValueError, match="unsafe public value"):
        module.research_team_memory_retrieval_policy_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "plan": "buy now",
            },
        )
    with pytest.raises(ValueError, match="float"):
        module.research_team_memory_retrieval_policy_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "score": 0.1,
            },
        )


def test_manual_rows_must_remain_consistent_and_public_status_limited() -> None:
    module = api()
    row = build_report(memory()).rows[0]

    with pytest.raises(ValueError, match="plan_status"):
        replace(row, plan_status="ready")
    with pytest.raises(ValueError, match="pass rows must include"):
        replace(
            row,
            reason_codes=tuple(
                reason
                for reason in row.reason_codes
                if reason != "memory_retrieval_policy_pass"
            ),
        )
    with pytest.raises(ValueError, match="memory_digest"):
        replace(row, memory_digest="raw-candidate-alpha")
    with pytest.raises(ValueError, match="retrieval_score"):
        replace(row, retrieval_score=d("-0.000001"))


def test_static_module_surface_has_no_live_io_or_trading_entrypoints() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_modules = (
        "aiohttp",
        "http",
        "httpx",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "supabase",
        "urllib",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "order",
        "place_order",
        "rollback",
        "sell",
        "send",
        "trade",
        "write",
    }

    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    assert not float_constants
    assert not any(
        imported == forbidden or imported.startswith(f"{forbidden}.")
        for imported in imports
        for forbidden in forbidden_modules
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
