from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import FrozenInstanceError, dataclass, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest


GENERATED_AT_EST = datetime(
    2026,
    7,
    5,
    9,
    15,
    tzinfo=timezone(timedelta(hours=-4)),
)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_team_research_memory_reinforcement_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def signal(
    team_id: str,
    lesson_id: str,
    domain_id: str,
    *,
    recent_outcome_error: str = "0.000000",
    source_failure_count: str = "0",
    days_since_playbook_review: str = "0",
    domain_drift_score: str = "0.000000",
    review_backlog_count: str = "0",
    source_row_count: str = "1",
    source_missing: bool = False,
):
    module = api()
    return module.StrategyTeamResearchMemoryReinforcementSignal(
        team_id=team_id,
        lesson_id=lesson_id,
        domain_id=domain_id,
        recent_outcome_error=d(recent_outcome_error),
        source_failure_count=d(source_failure_count),
        days_since_playbook_review=d(days_since_playbook_review),
        domain_drift_score=d(domain_drift_score),
        review_backlog_count=d(review_backlog_count),
        source_row_count=d(source_row_count),
        source_missing=source_missing,
    )


def report(*signals):
    module = api()
    return module.build_strategy_team_research_memory_reinforcement_report(
        signals,
        config=module.StrategyTeamResearchMemoryReinforcementConfig(),
        generated_at=GENERATED_AT_EST,
    )


def test_reduces_team_memory_signals_to_deterministic_reinforcement_rows() -> None:
    reinforcement_report = report(
        signal(
            "alpha-team",
            "calibration-loop",
            "politics",
            recent_outcome_error="0.180000",
            source_failure_count="4",
            days_since_playbook_review="20",
            domain_drift_score="0.250000",
            review_backlog_count="7",
        ),
        signal(
            "beta-team",
            "fixture-source-check",
            "sports",
            recent_outcome_error="0.030000",
            source_failure_count="0",
            days_since_playbook_review="45",
            domain_drift_score="0.050000",
            review_backlog_count="1",
        ),
        signal(
            "gamma-team",
            "macro-review",
            "macro",
            recent_outcome_error="0.080000",
            source_failure_count="1",
            days_since_playbook_review="10",
            domain_drift_score="0.100000",
            review_backlog_count="2",
        ),
        signal(
            "delta-team",
            "missing-packet",
            "crypto",
            recent_outcome_error="0.500000",
            source_failure_count="9",
            days_since_playbook_review="90",
            domain_drift_score="0.900000",
            review_backlog_count="10",
            source_row_count="0",
            source_missing=True,
        ),
    )

    assert is_dataclass(reinforcement_report)
    assert reinforcement_report.generated_at == datetime(2026, 7, 5, 13, 15, tzinfo=UTC)
    assert (
        reinforcement_report.config_version
        == "strategy-team-research-memory-reinforcement-v10"
    )
    assert reinforcement_report.source_signal_count == d("4")
    assert reinforcement_report.reinforcement_row_count == d("4")
    assert reinforcement_report.pass_row_count == d("1")
    assert reinforcement_report.watch_row_count == d("1")
    assert reinforcement_report.reinforce_row_count == d("2")
    assert reinforcement_report.source_missing_count == d("1")
    assert reinforcement_report.report_status == "reinforce"
    assert reinforcement_report.reason_codes == (
        "strategy_team_research_memory_reinforcement_reinforce",
        "strategy_team_research_memory_reinforcement_source_missing",
    )
    assert reinforcement_report.paper_only is True
    assert reinforcement_report.report_only is True
    assert reinforcement_report.readonly is True

    urgent = reinforcement_report.reinforcement_rows[0]
    assert urgent.redacted_team_ref == "<redacted-team-001>"
    assert urgent.redacted_lesson_ref == "<redacted-lesson-001>"
    assert urgent.redacted_domain_ref == "<redacted-domain-003>"
    assert urgent.memory_reinforcement_score == d("1.170000")
    assert urgent.reinforcement_status == "reinforce"
    assert urgent.priority_rank == d("1")
    assert urgent.reason_codes == (
        "outcome_error_reinforce",
        "repeated_source_failures",
        "domain_drift_reinforce",
        "review_backlog_reinforce",
    )

    stale = reinforcement_report.reinforcement_rows[1]
    assert stale.memory_reinforcement_score == d("0.430000")
    assert stale.reinforcement_status == "reinforce"
    assert stale.priority_rank == d("2")
    assert stale.reason_codes == ("playbook_stale",)

    missing = reinforcement_report.reinforcement_rows[2]
    assert missing.reinforcement_status == "watch"
    assert missing.reason_codes == (
        "strategy_team_research_memory_reinforcement_source_missing",
    )

    clear = reinforcement_report.reinforcement_rows[3]
    assert clear.reinforcement_status == "pass"
    assert clear.reason_codes == ("team_memory_reinforcement_clear",)

    report_text = repr(reinforcement_report)
    for sensitive_token in (
        "alpha-team",
        "calibration-loop",
        "fixture-source-check",
        "missing-packet",
    ):
        assert sensitive_token not in report_text


def test_empty_report_is_readonly_pass_with_decimal_zero_counts() -> None:
    reinforcement_report = report()

    assert reinforcement_report.source_signal_count == d("0")
    assert reinforcement_report.reinforcement_row_count == d("0")
    assert reinforcement_report.pass_row_count == d("0")
    assert reinforcement_report.watch_row_count == d("0")
    assert reinforcement_report.reinforce_row_count == d("0")
    assert reinforcement_report.source_missing_count == d("0")
    assert reinforcement_report.report_status == "pass"
    assert reinforcement_report.reason_codes == (
        "strategy_team_research_memory_reinforcement_clear",
    )
    assert reinforcement_report.reinforcement_rows == ()
    assert reinforcement_report.paper_only is True
    assert reinforcement_report.report_only is True
    assert reinforcement_report.readonly is True


def test_payload_is_json_ready_decimal_stringed_and_public_output_is_redacted() -> None:
    module = api()
    reinforcement_report = report(
        signal(
            "alpha-team",
            "private-playbook",
            "politics",
            recent_outcome_error="0.200000",
            source_failure_count="3",
        ),
    )

    payload = module.strategy_team_research_memory_reinforcement_payload(
        reinforcement_report,
    )
    payload_text = repr(payload).lower()

    assert "alpha-team" not in payload_text
    assert "private-playbook" not in payload_text
    assert "wallet" not in payload_text
    assert "order" not in payload_text
    assert payload["source_signal_count"] == "1"
    assert payload["reinforcement_rows"][0]["redacted_team_ref"] == "<redacted-team-001>"
    assert payload["reinforcement_rows"][0]["memory_reinforcement_score"] == "0.506667"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True


def test_payload_accepts_readonly_dicts_and_rejects_flag_or_numeric_drift() -> None:
    module = api()

    payload = module.strategy_team_research_memory_reinforcement_payload(
        {
            "generated_at": GENERATED_AT_EST,
            "source_signal_count": d("1"),
            "reinforcement_rows": (
                {
                    "memory_reinforcement_score": d("0.750000"),
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                },
            ),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )

    assert payload["generated_at"] == "2026-07-05T13:15:00+00:00"
    assert payload["source_signal_count"] == "1"
    assert payload["reinforcement_rows"][0]["memory_reinforcement_score"] == "0.750000"

    with pytest.raises(ValueError, match="paper_only"):
        module.strategy_team_research_memory_reinforcement_payload(
            {"paper_only": False, "report_only": True, "readonly": True},
        )

    with pytest.raises(ValueError, match="Decimal"):
        module.strategy_team_research_memory_reinforcement_payload(
            {
                "source_signal_count": 1,
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_report_payload_exposes_and_revalidates_tamper_evident_digests() -> None:
    module = api()
    reinforcement_report = report(
        signal(
            "alpha-team",
            "calibration-loop",
            "politics",
            recent_outcome_error="0.180000",
            source_failure_count="4",
            domain_drift_score="0.250000",
        ),
    )
    row = reinforcement_report.reinforcement_rows[0]

    assert row.validation_digest.startswith("tmrmr-v10:")
    assert reinforcement_report.validation_digest.startswith("tmrmr-v10:")
    payload = module.strategy_team_research_memory_reinforcement_payload(
        reinforcement_report,
    )
    assert payload["validation_digest"] == reinforcement_report.validation_digest
    assert payload["reinforcement_rows"][0]["validation_digest"] == row.validation_digest

    object.__setattr__(row, "memory_reinforcement_score", d("0.010000"))
    with pytest.raises(ValueError, match="validation_digest|tamper"):
        module.strategy_team_research_memory_reinforcement_payload(
            reinforcement_report,
        )

    count_tampered_report = report(
        signal("beta-team", "fixture-source-check", "sports"),
    )
    object.__setattr__(count_tampered_report, "pass_row_count", d("0"))
    with pytest.raises(ValueError, match="validation_digest|pass_row_count"):
        module.strategy_team_research_memory_reinforcement_payload(
            count_tampered_report,
        )


def test_payload_rejects_nested_non_plain_payload_objects() -> None:
    module = api()

    class PayloadDict(dict):
        pass

    @dataclass(frozen=True)
    class ForeignPayload:
        note: str
        paper_only: bool = True
        report_only: bool = True
        readonly: bool = True

    for unsafe_payload in (
        {
            "nested": PayloadDict({"note": "safe"}),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "nested": ForeignPayload("safe"),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ):
        with pytest.raises(ValueError, match="unsafe payload object|plain"):
            module.strategy_team_research_memory_reinforcement_payload(
                unsafe_payload,
            )


def test_public_dataclass_subclasses_are_rejected() -> None:
    module = api()

    @dataclass(frozen=True)
    class DerivedConfig(module.StrategyTeamResearchMemoryReinforcementConfig):
        pass

    @dataclass(frozen=True)
    class DerivedSignal(module.StrategyTeamResearchMemoryReinforcementSignal):
        pass

    with pytest.raises(ValueError, match="config"):
        DerivedConfig()

    with pytest.raises(ValueError, match="signal"):
        DerivedSignal(
            team_id="macro",
            lesson_id="rates",
            domain_id="macro",
            recent_outcome_error=d("0.000000"),
            source_failure_count=d("0"),
            days_since_playbook_review=d("0"),
            domain_drift_score=d("0.000000"),
            review_backlog_count=d("0"),
        )


def test_payload_and_reason_codes_reject_unsafe_or_sensitive_public_text() -> None:
    module = api()

    for payload in (
        {"wallet_address": "redacted", "paper_only": True, "report_only": True, "readonly": True},
        {"reason_codes": ("private_key_leak",), "paper_only": True, "report_only": True, "readonly": True},
        {"note": "send a live trading order", "paper_only": True, "report_only": True, "readonly": True},
    ):
        with pytest.raises(ValueError, match="unsafe|sensitive"):
            module.strategy_team_research_memory_reinforcement_payload(payload)

    row = report(signal("macro", "rates", "macro")).reinforcement_rows[0]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(row, reason_codes=("wallet_secret",))

    with pytest.raises(ValueError, match="redacted_team_ref must be redacted"):
        replace(row, redacted_team_ref="<redacted-team-secret>")


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    row = report(signal("macro", "rates", "macro")).reinforcement_rows[0]

    assert is_dataclass(row)
    with pytest.raises(FrozenInstanceError):
        row.review_backlog_count = d("2")  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="recent_outcome_error must be a Decimal"):
        module.StrategyTeamResearchMemoryReinforcementSignal(
            team_id="macro",
            lesson_id="rates",
            domain_id="macro",
            recent_outcome_error=1,
            source_failure_count=d("0"),
            days_since_playbook_review=d("0"),
            domain_drift_score=d("0.000000"),
            review_backlog_count=d("0"),
        )

    class DerivedDecimal(Decimal):
        pass

    with pytest.raises(ValueError, match="high_outcome_error_threshold"):
        module.StrategyTeamResearchMemoryReinforcementConfig(
            high_outcome_error_threshold=DerivedDecimal("0.150000"),
        )

    with pytest.raises(ValueError, match="duplicate team lesson pairs"):
        report(signal("macro", "rates", "macro"), signal("macro", "rates", "macro"))

    with pytest.raises(ValueError, match="readonly must be True"):
        module.StrategyTeamResearchMemoryReinforcementConfig(readonly=False)


def test_generated_at_is_normalized_to_utc_and_rejects_naive_datetime() -> None:
    module = api()

    class MissingOffsetTz(tzinfo):
        def utcoffset(self, dt):  # type: ignore[no-untyped-def]
            return None

        def dst(self, dt):  # type: ignore[no-untyped-def]
            return None

    reinforcement_report = module.build_strategy_team_research_memory_reinforcement_report(
        (),
        config=module.StrategyTeamResearchMemoryReinforcementConfig(),
        generated_at=datetime(2026, 7, 5, 9, 0, tzinfo=timezone.utc),
    )

    assert reinforcement_report.generated_at == datetime(2026, 7, 5, 9, 0, tzinfo=UTC)

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_strategy_team_research_memory_reinforcement_report(
            (),
            config=module.StrategyTeamResearchMemoryReinforcementConfig(),
            generated_at=datetime(2026, 7, 5, 9, 0),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_strategy_team_research_memory_reinforcement_report(
            (),
            config=module.StrategyTeamResearchMemoryReinforcementConfig(),
            generated_at=datetime(2026, 7, 5, 9, 0, tzinfo=MissingOffsetTz()),
        )


def test_reinforcement_order_and_payload_are_input_order_deterministic() -> None:
    first = report(
        signal(
            "z-team",
            "z-lesson",
            "z-domain",
            recent_outcome_error="0.160000",
        ),
        signal("a-team", "a-lesson", "a-domain", review_backlog_count="1"),
    )
    second = report(
        signal("a-team", "a-lesson", "a-domain", review_backlog_count="1"),
        signal(
            "z-team",
            "z-lesson",
            "z-domain",
            recent_outcome_error="0.160000",
        ),
    )

    assert first.reinforcement_rows == second.reinforcement_rows
    assert api().strategy_team_research_memory_reinforcement_payload(
        first,
    ) == api().strategy_team_research_memory_reinforcement_payload(second)


def test_module_scope_is_pure_in_memory_report_reducer_with_local_exports_only() -> None:
    module = api()
    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_STRATEGY_TEAM_RESEARCH_MEMORY_REINFORCEMENT_CONFIG_VERSION",
        "REINFORCEMENT_STATUSES",
        "StrategyTeamResearchMemoryReinforcementConfig",
        "StrategyTeamResearchMemoryReinforcementSignal",
        "StrategyTeamResearchMemoryReinforcementRow",
        "StrategyTeamResearchMemoryReinforcementReport",
        "build_strategy_team_research_memory_reinforcement_report",
        "strategy_team_research_memory_reinforcement_payload",
    )
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "typing",
        "polymarket_alpha_lab",
    }
    forbidden_source_terms = (
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "postgres",
        "sqlite",
        "auth",
        "private_key",
        "api_key",
        "secret",
        "wallet",
        "account",
        "cancel",
        "replace",
        "order",
        "broker",
        "signing",
        "trade",
        "trading",
        "client",
        "execute",
        "connect",
        "subprocess",
        "open(",
        "pathlib",
    )
    assert all(term not in source.lower() for term in forbidden_source_terms)

    forbidden_call_names = {
        "__import__",
        "connect",
        "execute",
        "float",
        "open",
        "request",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names
