from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_signal_review_latency_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 16, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_signal_review_latency_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            "research-team-signal-review-latency-report-v0"
        ),
        "pass_latency_score_threshold": d("0.350000"),
        "block_latency_score_threshold": d("0.750000"),
        "watch_signal_age_seconds": d("3600.000000"),
        "block_signal_age_seconds": d("7200.000000"),
        "watch_min_reviewer_availability_ratio": d("0.600000"),
        "block_min_reviewer_availability_ratio": d("0.300000"),
        "watch_unresolved_dissent_ratio": d("0.200000"),
        "block_unresolved_dissent_ratio": d("0.500000"),
        "watch_memory_writeback_lag_seconds": d("3600.000000"),
        "block_memory_writeback_lag_seconds": d("7200.000000"),
        "watch_queue_pressure_ratio": d("0.750000"),
        "block_queue_pressure_ratio": d("1.250000"),
        "watch_manual_escalation_urgency": d("0.300000"),
        "block_manual_escalation_urgency": d("0.800000"),
    }
    values.update(overrides)
    return module.ResearchTeamSignalReviewLatencyConfig(**values)


def observation(**overrides: object):
    module = api()
    values = {
        "team_key": "macro_research",
        "review_lane_key": "rates_policy",
        "pending_signal_count": d("4.000000"),
        "required_reviewer_count": d("4.000000"),
        "available_reviewer_count": d("4.000000"),
        "mean_signal_age_seconds": d("900.000000"),
        "unresolved_dissent_count": d("0.000000"),
        "memory_writeback_lag_seconds": d("300.000000"),
        "pending_review_queue_count": d("4.000000"),
        "review_queue_capacity_count": d("10.000000"),
        "manual_escalation_urgency": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchTeamSignalReviewLatencyInput(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_signal_review_latency_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def walk_payload(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(walk_payload(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(walk_payload(item))
        return tuple(nested)
    return (value,)


def payload_with_digest(payload: dict[Any, Any]) -> dict[Any, Any]:
    values = dict(payload)
    values.pop("public_digest", None)
    encoded = json.dumps(values, sort_keys=True, separators=(",", ":")).encode("utf-8")
    values["public_digest"] = sha256(encoded).hexdigest()
    return values


def assert_no_unsafe_public_surface(value: object) -> None:
    forbidden = (
        "raw",
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "url",
        "dsn",
        "table",
        "private",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "buy",
        "sell",
        "recommendation",
        "sizing",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lower_key = key.lower()
            assert not any(fragment in lower_key for fragment in forbidden), lower_key
            assert_no_unsafe_public_surface(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_unsafe_public_surface(item)
        return
    if isinstance(value, str):
        lower_value = value.lower()
        assert not any(fragment in lower_value for fragment in forbidden), lower_value


def assert_decimal_fields_are_plain(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if isinstance(item, Decimal):
            assert type(item) is Decimal, field.name


def test_public_api_declares_report_only_latency_contract() -> None:
    module = api()

    assert module.DEFAULT_RESEARCH_TEAM_SIGNAL_REVIEW_LATENCY_REPORT_CONFIG_VERSION == (
        "research-team-signal-review-latency-report-v0"
    )
    assert module.STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_SIGNAL_REVIEW_LATENCY_REPORT_CONFIG_VERSION",
        "STATUSES",
        "ResearchTeamSignalReviewLatencyConfig",
        "ResearchTeamSignalReviewLatencyInput",
        "ResearchTeamSignalReviewLatencyReasonCodeCount",
        "ResearchTeamSignalReviewLatencyReport",
        "ResearchTeamSignalReviewLatencyRow",
        "build_research_team_signal_review_latency_report",
        "research_team_signal_review_latency_report_payload",
    )

    defaults = {
        field.name: field.default
        for field in fields(module.ResearchTeamSignalReviewLatencyConfig)
    }
    assert defaults["paper_only"] is True
    assert defaults["report_only"] is True
    assert defaults["readonly"] is True


def test_summarizes_team_signal_review_latency_with_public_safe_aggregates() -> None:
    report = build_report(
        observation(),
        observation(
            team_key="sports_research",
            review_lane_key="injury_updates",
            pending_signal_count=d("8.000000"),
            required_reviewer_count=d("4.000000"),
            available_reviewer_count=d("2.000000"),
            mean_signal_age_seconds=d("4500.000000"),
            unresolved_dissent_count=d("2.000000"),
            memory_writeback_lag_seconds=d("5000.000000"),
            pending_review_queue_count=d("9.000000"),
            review_queue_capacity_count=d("10.000000"),
            manual_escalation_urgency=d("0.450000"),
        ),
        observation(
            team_key="crypto_research",
            review_lane_key="stablecoin_policy",
            pending_signal_count=d("10.000000"),
            required_reviewer_count=d("5.000000"),
            available_reviewer_count=d("1.000000"),
            mean_signal_age_seconds=d("9000.000000"),
            unresolved_dissent_count=d("6.000000"),
            memory_writeback_lag_seconds=d("9000.000000"),
            pending_review_queue_count=d("15.000000"),
            review_queue_capacity_count=d("10.000000"),
            manual_escalation_urgency=d("0.900000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
    )

    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "research-team-signal-review-latency-report-v0"
    )
    assert report.status == "block"
    assert report.review_group_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.total_pending_signals == d("22.000000")
    assert report.total_pending_review_queue == d("28.000000")
    assert report.average_signal_age_seconds == d("4800.000000")
    assert report.average_reviewer_availability_ratio == d("0.566667")
    assert report.average_unresolved_dissent_ratio == d("0.283333")
    assert report.average_memory_writeback_lag_seconds == d("4766.666667")
    assert report.average_queue_pressure_ratio == d("0.933333")
    assert report.max_manual_escalation_urgency == d("0.900000")
    assert report.max_latency_score == d("1.000000")
    assert report.reason_codes == (
        "signal_review_latency_report_block_rows",
        "signal_review_latency_report_watch_rows",
    )
    assert len(report.public_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.team_key, row.review_lane_key) for row in report.rows) == (
        ("crypto_research", "stablecoin_policy"),
        ("sports_research", "injury_updates"),
        ("macro_research", "rates_policy"),
    )
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.reviewer_availability_ratio for row in report.rows) == (
        d("0.200000"),
        d("0.500000"),
        d("1.000000"),
    )
    assert tuple(row.unresolved_dissent_ratio for row in report.rows) == (
        d("0.600000"),
        d("0.250000"),
        d("0.000000"),
    )
    assert tuple(row.queue_pressure_ratio for row in report.rows) == (
        d("1.500000"),
        d("0.900000"),
        d("0.400000"),
    )
    assert tuple(row.latency_score for row in report.rows) == (
        d("1.000000"),
        d("0.571084"),
        d("0.107750"),
    )
    assert report.rows[0].reason_codes == (
        "signal_age_block",
        "reviewer_availability_block",
        "unresolved_dissent_block",
        "memory_writeback_lag_block",
        "queue_pressure_block",
        "manual_escalation_block",
    )
    assert report.rows[1].reason_codes == (
        "signal_age_watch",
        "reviewer_availability_watch",
        "unresolved_dissent_watch",
        "memory_writeback_lag_watch",
        "queue_pressure_watch",
        "manual_escalation_watch",
    )
    assert report.rows[2].reason_codes == ("signal_review_latency_pass",)

    reason_counts = {item.reason_code: item for item in report.reason_code_counts}
    assert reason_counts["signal_age_block"].count == d("1.000000")
    assert reason_counts["signal_age_block"].review_group_ratio == d("0.333333")
    assert reason_counts["signal_review_latency_pass"].count == d("1.000000")
    for value in (report, *report.rows, *report.reason_code_counts):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
        assert_decimal_fields_are_plain(value)


def test_payload_and_digest_are_deterministic_json_safe_and_validated() -> None:
    inputs = (
        observation(
            team_key="sports_research",
            review_lane_key="injury_updates",
            pending_signal_count=d("8.000000"),
            required_reviewer_count=d("4.000000"),
            available_reviewer_count=d("2.000000"),
            mean_signal_age_seconds=d("4500.000000"),
            unresolved_dissent_count=d("2.000000"),
            memory_writeback_lag_seconds=d("5000.000000"),
            pending_review_queue_count=d("9.000000"),
            manual_escalation_urgency=d("0.450000"),
        ),
        observation(),
    )

    first = build_report(*inputs)
    second = build_report(*reversed(inputs), generated_at=GENERATED_AT)
    first_payload = api().research_team_signal_review_latency_report_payload(first)
    second_payload = api().research_team_signal_review_latency_report_payload(second)

    assert first == second
    assert first.public_digest == second.public_digest
    assert first_payload == second_payload
    assert json.loads(json.dumps(first_payload, sort_keys=True)) == first_payload
    assert first_payload["public_digest"] == first.public_digest
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert "8.000000" in walk_payload(first_payload)
    assert all(type(value) is not Decimal for value in walk_payload(first_payload))
    assert_no_unsafe_public_surface(first_payload)

    assert api().research_team_signal_review_latency_report_payload(first_payload) == (
        first_payload
    )

    tampered_payload = dict(first_payload)
    tampered_payload["status"] = "pass"
    with pytest.raises(ValueError, match="public_digest"):
        api().research_team_signal_review_latency_report_payload(tampered_payload)

    digest_tampered = dict(first_payload)
    digest_tampered["public_digest"] = "0" * 64
    with pytest.raises(ValueError, match="public_digest"):
        api().research_team_signal_review_latency_report_payload(digest_tampered)

    for invalid_status_payload in (
        payload_with_digest(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "status": "halt",
            },
        ),
        payload_with_digest(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "status": "pass",
                "rows": [{"status": "halt"}],
            },
        ),
    ):
        with pytest.raises(ValueError, match="status must be one of"):
            api().research_team_signal_review_latency_report_payload(
                invalid_status_payload,
            )

    nested_flag_downgrade_payload = payload_with_digest(
        {
            "paper_only": True,
            "report_only": True,
            "readonly": True,
            "status": "pass",
            "rows": [
                {
                    "status": "pass",
                    "paper_only": False,
                    "report_only": True,
                    "readonly": True,
                },
            ],
        },
    )
    with pytest.raises(ValueError, match="paper_only"):
        api().research_team_signal_review_latency_report_payload(
            nested_flag_downgrade_payload,
        )

    for unsafe_payload in (
        payload_with_digest(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "status": "pass",
                "numeric_metric": 1,
            },
        ),
        payload_with_digest(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "status": "pass",
                "numeric_metric": 0.5,
            },
        ),
    ):
        with pytest.raises(ValueError, match="JSON numeric value must use Decimal"):
            api().research_team_signal_review_latency_report_payload(unsafe_payload)

    nonfinite_decimal_payload = {
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "status": "pass",
        "numeric_metric": Decimal("NaN"),
        "public_digest": payload_with_digest(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "status": "pass",
                "numeric_metric": "NaN",
            },
        )["public_digest"],
    }
    with pytest.raises(ValueError, match="finite"):
        api().research_team_signal_review_latency_report_payload(
            nonfinite_decimal_payload,
        )

    non_string_key_payload = {
        7: "public_value",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "status": "pass",
        "public_digest": payload_with_digest(
            {
                "7": "public_value",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "status": "pass",
            },
        )["public_digest"],
    }
    with pytest.raises(ValueError, match="JSON object keys must be strings"):
        api().research_team_signal_review_latency_report_payload(non_string_key_payload)


def test_empty_input_returns_report_only_block_without_private_surface() -> None:
    report = build_report()

    assert report.status == "block"
    assert report.review_group_count == ZERO
    assert report.pass_count == ZERO
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.rows == ()
    assert report.reason_codes == ("signal_review_latency_no_inputs",)
    assert report.reason_code_counts[0].reason_code == "signal_review_latency_no_inputs"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert_no_unsafe_public_surface(
        api().research_team_signal_review_latency_report_payload(report),
    )


def test_statuses_are_exactly_pass_watch_block_and_config_thresholds_are_respected() -> None:
    module = api()

    assert module.STATUSES == ("pass", "watch", "block")
    assert build_report(observation()).status == "pass"
    assert build_report(
        observation(
            pending_signal_count=d("8.000000"),
            required_reviewer_count=d("4.000000"),
            available_reviewer_count=d("2.000000"),
            mean_signal_age_seconds=d("4500.000000"),
            unresolved_dissent_count=d("2.000000"),
            memory_writeback_lag_seconds=d("5000.000000"),
            pending_review_queue_count=d("9.000000"),
            manual_escalation_urgency=d("0.450000"),
        ),
    ).status == "watch"
    assert build_report(
        observation(
            pending_signal_count=d("10.000000"),
            required_reviewer_count=d("5.000000"),
            available_reviewer_count=d("1.000000"),
            mean_signal_age_seconds=d("9000.000000"),
            unresolved_dissent_count=d("6.000000"),
            memory_writeback_lag_seconds=d("9000.000000"),
            pending_review_queue_count=d("15.000000"),
            manual_escalation_urgency=d("0.900000"),
        ),
    ).status == "block"

    relaxed = config(
        pass_latency_score_threshold=d("0.650000"),
        block_latency_score_threshold=d("0.950000"),
        watch_signal_age_seconds=d("5000.000000"),
        block_signal_age_seconds=d("10000.000000"),
        watch_min_reviewer_availability_ratio=d("0.400000"),
        block_min_reviewer_availability_ratio=d("0.100000"),
        watch_unresolved_dissent_ratio=d("0.350000"),
        block_unresolved_dissent_ratio=d("0.800000"),
        watch_memory_writeback_lag_seconds=d("5500.000000"),
        block_memory_writeback_lag_seconds=d("10000.000000"),
        watch_queue_pressure_ratio=d("0.950000"),
        block_queue_pressure_ratio=d("1.750000"),
        watch_manual_escalation_urgency=d("0.500000"),
        block_manual_escalation_urgency=d("0.950000"),
    )
    report = build_report(
        observation(
            pending_signal_count=d("8.000000"),
            required_reviewer_count=d("4.000000"),
            available_reviewer_count=d("2.000000"),
            mean_signal_age_seconds=d("4500.000000"),
            unresolved_dissent_count=d("2.000000"),
            memory_writeback_lag_seconds=d("5000.000000"),
            pending_review_queue_count=d("9.000000"),
            manual_escalation_urgency=d("0.450000"),
        ),
        cfg=relaxed,
    )

    assert report.status == "pass"
    assert report.rows[0].status == "pass"
    assert report.rows[0].reason_codes == ("signal_review_latency_pass",)
    assert report.reason_codes == ("signal_review_latency_report_pass",)


def test_validation_rejects_non_decimal_subclasses_flags_and_private_identifiers() -> None:
    module = api()
    report = build_report(observation())

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.reason_code_counts[0].count = d("2.000000")  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclass"):
        type("BadInput", (module.ResearchTeamSignalReviewLatencyInput,), {})
    with pytest.raises(ValueError, match="Decimal"):
        observation(pending_signal_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        observation(manual_escalation_urgency=0.2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        observation(required_reviewer_count=_DecimalSubclass("4.000000"))
    with pytest.raises(ValueError, match="plain str"):
        observation(team_key=_StringSubclass("macro_research"))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(observation(), generated_at=_DatetimeSubclass(2026, 7, 8, 16, 45))
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="inputs must contain"):
        build_report("not-an-input")
    with pytest.raises(ValueError, match="duplicate team_key/review_lane_key"):
        build_report(observation(), observation())
    with pytest.raises(ValueError, match="private public payload"):
        observation(team_key="raw_candidate_42")
    with pytest.raises(ValueError, match="private public payload"):
        observation(review_lane_key="market_slug_question")
    with pytest.raises(ValueError, match="private public payload"):
        observation(team_key="table_exports")
    with pytest.raises(ValueError, match="private public payload"):
        observation(review_lane_key="execution_lane")
    for unsafe_review_lane_key in (
        "api_tokens",
        "wallets",
        "orders",
        "trades",
        "trading_surface",
    ):
        with pytest.raises(ValueError, match="private public payload"):
            observation(review_lane_key=unsafe_review_lane_key)
    with pytest.raises(ValueError, match="available_reviewer_count"):
        observation(available_reviewer_count=d("5.000000"))
    with pytest.raises(ValueError, match="pass_latency_score_threshold"):
        config(
            pass_latency_score_threshold=d("0.800000"),
            block_latency_score_threshold=d("0.700000"),
        )

    valid_row = report.rows[0]
    with pytest.raises(ValueError, match="latency_score must match"):
        replace(valid_row, latency_score=d("0.900000"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(valid_row, reason_codes=("signal_age_watch",))


def test_module_has_no_database_network_wallet_order_or_recommendation_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    banned_import_roots = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "psycopg2",
        "sqlite3",
        "sqlalchemy",
        "web3",
        "subprocess",
        "py_clob_client",
    }
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert imports.isdisjoint(banned_import_roots)

    banned_call_names = {
        "connect",
        "execute",
        "executemany",
        "commit",
        "rollback",
        "send",
        "submit",
        "get",
        "post",
        "put",
        "patch",
        "delete",
        "request",
        "insert",
        "upsert",
        "order",
        "trade",
        "buy",
        "sell",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in banned_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in banned_call_names

    lowered = source.lower()
    for term in (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table name",
        "private token",
        "wallet",
        "auth",
        "order",
        "trade",
        "live execution",
        "buy",
        "sell",
        "recommendation",
        "position sizing",
    ):
        assert term not in lowered
