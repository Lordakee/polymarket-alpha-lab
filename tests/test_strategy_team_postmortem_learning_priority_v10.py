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
    6,
    10,
    45,
    tzinfo=timezone(timedelta(hours=-4)),
)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_team_postmortem_learning_priority_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def signal(
    team_id: str,
    market_id: str,
    postmortem_id: str,
    *,
    forecast_miss: str = "0.000000",
    notional_proxy: str = "0.00",
    source_failure_rate: str = "0.000000",
    resolution_ambiguity_score: str = "0.000000",
    lesson_reuse_potential: str = "0.000000",
    source_row_count: str = "1",
    source_missing: bool = False,
):
    module = api()
    return module.StrategyTeamPostmortemLearningPrioritySignal(
        team_id=team_id,
        market_id=market_id,
        postmortem_id=postmortem_id,
        forecast_miss=d(forecast_miss),
        notional_proxy=d(notional_proxy),
        source_failure_rate=d(source_failure_rate),
        resolution_ambiguity_score=d(resolution_ambiguity_score),
        lesson_reuse_potential=d(lesson_reuse_potential),
        source_row_count=d(source_row_count),
        source_missing=source_missing,
    )


def report(*signals):
    module = api()
    return module.build_strategy_team_postmortem_learning_priority_report(
        signals,
        config=module.StrategyTeamPostmortemLearningPriorityConfig(),
        generated_at=GENERATED_AT_EST,
    )


def test_reduces_completed_postmortems_to_deterministic_priority_rows() -> None:
    priority_report = report(
        signal(
            "alpha-team",
            "election-late-swing",
            "pm-001",
            forecast_miss="0.320000",
            notional_proxy="3000.00",
            source_failure_rate="0.600000",
            resolution_ambiguity_score="0.500000",
            lesson_reuse_potential="0.900000",
        ),
        signal(
            "beta-team",
            "sports-settlement",
            "pm-002",
            forecast_miss="0.040000",
            notional_proxy="250.00",
            source_failure_rate="0.000000",
            resolution_ambiguity_score="0.050000",
            lesson_reuse_potential="0.950000",
        ),
        signal(
            "gamma-team",
            "macro-clear",
            "pm-003",
            forecast_miss="0.020000",
            notional_proxy="100.00",
            source_failure_rate="0.010000",
            resolution_ambiguity_score="0.040000",
            lesson_reuse_potential="0.200000",
        ),
        signal(
            "delta-team",
            "crypto-missing",
            "pm-004",
            forecast_miss="0.900000",
            notional_proxy="9000.00",
            source_failure_rate="0.900000",
            resolution_ambiguity_score="0.900000",
            lesson_reuse_potential="0.900000",
            source_row_count="0",
            source_missing=True,
        ),
    )

    assert is_dataclass(priority_report)
    assert priority_report.generated_at == datetime(2026, 7, 6, 14, 45, tzinfo=UTC)
    assert (
        priority_report.config_version
        == "strategy-team-postmortem-learning-priority-v10"
    )
    assert priority_report.source_signal_count == d("4")
    assert priority_report.priority_row_count == d("4")
    assert priority_report.pass_row_count == d("1")
    assert priority_report.watch_row_count == d("1")
    assert priority_report.prioritize_row_count == d("2")
    assert priority_report.source_missing_count == d("1")
    assert priority_report.report_status == "prioritize"
    assert priority_report.reason_codes == (
        "strategy_team_postmortem_learning_priority_prioritize",
        "strategy_team_postmortem_learning_priority_source_missing",
    )
    assert priority_report.paper_only is True
    assert priority_report.report_only is True
    assert priority_report.readonly is True

    urgent = priority_report.priority_rows[0]
    assert urgent.redacted_team_ref == "<redacted-team-001>"
    assert urgent.redacted_market_ref == "<redacted-market-002>"
    assert urgent.redacted_postmortem_ref == "<redacted-postmortem-001>"
    assert urgent.learning_priority_score == d("3.070000")
    assert urgent.learning_priority_status == "prioritize"
    assert urgent.priority_rank == d("1")
    assert urgent.reason_codes == (
        "forecast_miss_high",
        "stake_notional_proxy_high",
        "source_failure_rate_high",
        "resolution_ambiguity_high",
        "lesson_reuse_potential_high",
    )

    reusable = priority_report.priority_rows[1]
    assert reusable.learning_priority_score == d("1.040000")
    assert reusable.learning_priority_status == "prioritize"
    assert reusable.priority_rank == d("2")
    assert reusable.reason_codes == ("lesson_reuse_potential_high",)

    missing = priority_report.priority_rows[2]
    assert missing.learning_priority_status == "watch"
    assert missing.reason_codes == (
        "strategy_team_postmortem_learning_priority_source_missing",
    )

    clear = priority_report.priority_rows[3]
    assert clear.learning_priority_status == "pass"
    assert clear.reason_codes == ("postmortem_learning_priority_clear",)

    report_text = repr(priority_report)
    for sensitive_token in (
        "alpha-team",
        "election-late-swing",
        "sports-settlement",
        "crypto-missing",
        "pm-001",
    ):
        assert sensitive_token not in report_text


def test_empty_report_is_readonly_pass_with_decimal_zero_counts() -> None:
    priority_report = report()

    assert priority_report.source_signal_count == d("0")
    assert priority_report.priority_row_count == d("0")
    assert priority_report.pass_row_count == d("0")
    assert priority_report.watch_row_count == d("0")
    assert priority_report.prioritize_row_count == d("0")
    assert priority_report.source_missing_count == d("0")
    assert priority_report.report_status == "pass"
    assert priority_report.reason_codes == (
        "strategy_team_postmortem_learning_priority_clear",
    )
    assert priority_report.priority_rows == ()
    assert priority_report.paper_only is True
    assert priority_report.report_only is True
    assert priority_report.readonly is True


def test_payload_is_json_ready_decimal_stringed_and_public_output_is_redacted() -> None:
    module = api()
    priority_report = report(
        signal(
            "alpha-team",
            "private-market",
            "pm-private",
            forecast_miss="0.200000",
            notional_proxy="2000.00",
            source_failure_rate="0.250000",
            resolution_ambiguity_score="0.300000",
            lesson_reuse_potential="0.800000",
        ),
    )

    payload = module.strategy_team_postmortem_learning_priority_payload(
        priority_report,
    )
    payload_text = repr(payload).lower()

    assert "alpha-team" not in payload_text
    assert "private-market" not in payload_text
    assert "pm-private" not in payload_text
    assert "wallet" not in payload_text
    assert "order" not in payload_text
    assert payload["source_signal_count"] == "1"
    assert payload["priority_rows"][0]["redacted_team_ref"] == "<redacted-team-001>"
    assert payload["priority_rows"][0]["learning_priority_score"] == "2.050000"
    assert payload["validation_digest"] == priority_report.validation_digest
    assert (
        payload["priority_rows"][0]["validation_digest"]
        == priority_report.priority_rows[0].validation_digest
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True


def test_payload_accepts_readonly_dicts_and_rejects_flag_or_numeric_drift() -> None:
    module = api()

    payload = module.strategy_team_postmortem_learning_priority_payload(
        {
            "generated_at": GENERATED_AT_EST,
            "source_signal_count": d("1"),
            "priority_rows": (
                {
                    "learning_priority_score": d("0.750000"),
                    "notional_proxy": d("1500.00"),
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

    assert payload["generated_at"] == "2026-07-06T14:45:00+00:00"
    assert payload["source_signal_count"] == "1"
    assert payload["priority_rows"][0]["learning_priority_score"] == "0.750000"
    assert payload["priority_rows"][0]["notional_proxy"] == "1500.00"

    with pytest.raises(ValueError, match="paper_only"):
        module.strategy_team_postmortem_learning_priority_payload(
            {"paper_only": False, "report_only": True, "readonly": True},
        )

    with pytest.raises(ValueError, match="Decimal"):
        module.strategy_team_postmortem_learning_priority_payload(
            {
                "source_signal_count": 1,
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_payload_and_reason_codes_reject_unsafe_or_sensitive_public_text() -> None:
    module = api()

    for payload in (
        {
            "wallet_address": "redacted",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "reason_codes": ("private_key_leak",),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "note": "send a live trading order",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ):
        with pytest.raises(ValueError, match="unsafe|sensitive"):
            module.strategy_team_postmortem_learning_priority_payload(payload)

    row = report(signal("macro", "rates", "pm-rates")).priority_rows[0]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(row, reason_codes=("wallet_secret",))

    with pytest.raises(ValueError, match="redacted_market_ref must be redacted"):
        replace(row, redacted_market_ref="<redacted-market-secret>")


def test_report_payload_revalidates_tamper_evident_digests() -> None:
    module = api()
    priority_report = report(
        signal(
            "alpha-team",
            "late-break",
            "pm-late-break",
            forecast_miss="0.200000",
            notional_proxy="3000.00",
            source_failure_rate="0.250000",
            resolution_ambiguity_score="0.300000",
            lesson_reuse_potential="0.800000",
        ),
    )
    row = priority_report.priority_rows[0]

    assert row.validation_digest.startswith("stplp-v10:")
    assert priority_report.validation_digest.startswith("stplp-v10:")

    with pytest.raises(ValueError, match="validation_digest|tamper"):
        replace(row, learning_priority_score=d("0.010000"))

    object.__setattr__(row, "learning_priority_score", d("0.010000"))
    with pytest.raises(ValueError, match="validation_digest|tamper"):
        module.strategy_team_postmortem_learning_priority_payload(priority_report)

    count_tampered_report = report(signal("beta-team", "clear-market", "pm-clear"))
    object.__setattr__(count_tampered_report, "pass_row_count", d("0"))
    with pytest.raises(ValueError, match="validation_digest|pass_row_count"):
        module.strategy_team_postmortem_learning_priority_payload(count_tampered_report)


def test_payload_rejects_nested_non_plain_objects_and_flag_drift() -> None:
    module = api()

    class PayloadDict(dict):
        pass

    @dataclass(frozen=True)
    class ForeignPayload:
        note: str
        paper_only: bool = True
        report_only: bool = True
        readonly: bool = True

    for payload in (
        {
            "priority_rows": (PayloadDict({"readonly": True}),),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "priority_rows": (
                ForeignPayload(note="redacted"),
            ),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "priority_rows": (
                {"paper_only": True, "report_only": True, "readonly": False},
            ),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ):
        with pytest.raises(ValueError, match="payload|readonly|dataclass"):
            module.strategy_team_postmortem_learning_priority_payload(payload)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    row = report(signal("macro", "rates", "pm-rates")).priority_rows[0]

    assert is_dataclass(row)
    with pytest.raises(FrozenInstanceError):
        row.forecast_miss = d("0.500000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="forecast_miss must be a Decimal"):
        module.StrategyTeamPostmortemLearningPrioritySignal(
            team_id="macro",
            market_id="rates",
            postmortem_id="pm-rates",
            forecast_miss=1,
            notional_proxy=d("0.00"),
            source_failure_rate=d("0.000000"),
            resolution_ambiguity_score=d("0.000000"),
            lesson_reuse_potential=d("0.000000"),
        )

    class DerivedDecimal(Decimal):
        pass

    with pytest.raises(ValueError, match="forecast_miss_threshold"):
        module.StrategyTeamPostmortemLearningPriorityConfig(
            forecast_miss_threshold=DerivedDecimal("0.150000"),
        )

    with pytest.raises(ValueError, match="duplicate team postmortem pairs"):
        report(signal("macro", "rates", "pm-rates"), signal("macro", "rates", "pm-rates"))

    with pytest.raises(ValueError, match="readonly must be True"):
        module.StrategyTeamPostmortemLearningPriorityConfig(readonly=False)


def test_generated_at_is_normalized_to_utc_and_rejects_naive_datetime() -> None:
    module = api()

    class MissingOffsetTz(tzinfo):
        def utcoffset(self, dt):  # type: ignore[no-untyped-def]
            return None

        def dst(self, dt):  # type: ignore[no-untyped-def]
            return None

    priority_report = module.build_strategy_team_postmortem_learning_priority_report(
        (),
        config=module.StrategyTeamPostmortemLearningPriorityConfig(),
        generated_at=datetime(2026, 7, 6, 9, 0, tzinfo=timezone.utc),
    )

    assert priority_report.generated_at == datetime(2026, 7, 6, 9, 0, tzinfo=UTC)

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_strategy_team_postmortem_learning_priority_report(
            (),
            config=module.StrategyTeamPostmortemLearningPriorityConfig(),
            generated_at=datetime(2026, 7, 6, 9, 0),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_strategy_team_postmortem_learning_priority_report(
            (),
            config=module.StrategyTeamPostmortemLearningPriorityConfig(),
            generated_at=datetime(2026, 7, 6, 9, 0, tzinfo=MissingOffsetTz()),
        )


def test_priority_sort_and_payload_are_input_sequence_deterministic() -> None:
    first = report(
        signal(
            "z-team",
            "z-market",
            "z-postmortem",
            forecast_miss="0.160000",
        ),
        signal("a-team", "a-market", "a-postmortem", lesson_reuse_potential="0.100000"),
    )
    second = report(
        signal("a-team", "a-market", "a-postmortem", lesson_reuse_potential="0.100000"),
        signal(
            "z-team",
            "z-market",
            "z-postmortem",
            forecast_miss="0.160000",
        ),
    )

    assert first.priority_rows == second.priority_rows
    assert api().strategy_team_postmortem_learning_priority_payload(
        first,
    ) == api().strategy_team_postmortem_learning_priority_payload(second)


def test_module_scope_is_pure_in_memory_report_reducer_with_local_exports_only() -> None:
    module = api()
    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_STRATEGY_TEAM_POSTMORTEM_LEARNING_PRIORITY_CONFIG_VERSION",
        "LEARNING_PRIORITY_STATUSES",
        "StrategyTeamPostmortemLearningPriorityConfig",
        "StrategyTeamPostmortemLearningPrioritySignal",
        "StrategyTeamPostmortemLearningPriorityRow",
        "StrategyTeamPostmortemLearningPriorityReport",
        "build_strategy_team_postmortem_learning_priority_report",
        "strategy_team_postmortem_learning_priority_payload",
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
        "fastapi",
        "live",
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
