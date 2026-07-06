from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_candidate_resolution_lag_penalty_score_v2.py"
)
GENERATED_AT = datetime(2026, 7, 6, 14, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_candidate_resolution_lag_penalty_score_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate(candidate_id: str = "candidate_alpha", **overrides: object):
    module = api()
    values: dict[str, object] = {
        "candidate_id": candidate_id,
        "market_id": f"market_{candidate_id}",
        "observed_at": GENERATED_AT,
        "expected_resolution_lag_days": d("1.000000"),
        "unresolved_outcome_age_days": d("1.000000"),
        "delayed_settlement_signal_count": d("0"),
        "official_evidence_signal_count": d("0"),
        "reason_codes": ("initial_resolution_review",),
    }
    values.update(overrides)
    return module.StrategyCandidateResolutionLagPenaltyScoreV2Input(**values)


def report(*items: object, **overrides: object):
    module = api()
    generated_at = overrides.pop("generated_at", GENERATED_AT)
    config = overrides.pop("config", None)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    return module.build_strategy_candidate_resolution_lag_penalty_score_v2(
        list(items),
        config=config,
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_resolution_lag_penalty_scoring_and_rollup() -> None:
    penalty_report = report(
        candidate("candidate_pass"),
        candidate(
            "candidate_watch",
            expected_resolution_lag_days=d("3.000000"),
            unresolved_outcome_age_days=d("2.000000"),
        ),
        candidate(
            "candidate_blocked",
            expected_resolution_lag_days=d("6.000000"),
            unresolved_outcome_age_days=d("5.000000"),
        ),
    )

    assert is_dataclass(penalty_report)
    assert penalty_report.candidate_count == d("3")
    assert penalty_report.pass_count == d("1")
    assert penalty_report.watch_count == d("1")
    assert penalty_report.blocked_count == d("1")
    assert penalty_report.max_resolution_lag_penalty_score == d("0.857143")
    assert penalty_report.average_resolution_lag_penalty_score == d("0.476190")
    assert penalty_report.report_status == "blocked"
    assert penalty_report.reason_codes == (
        "resolution_lag_penalty_report_blocked",
        "resolution_lag_penalty_blocked",
        "resolution_lag_penalty_watch",
        "resolution_lag_penalty_pass",
    )

    blocked, watch, passed = penalty_report.rows
    assert blocked.candidate_id == "candidate_blocked"
    assert blocked.base_resolution_lag_penalty_score == d("0.857143")
    assert blocked.resolution_lag_penalty_score == d("0.857143")
    assert blocked.penalty_status == "blocked"
    assert watch.candidate_id == "candidate_watch"
    assert watch.resolution_lag_penalty_score == d("0.428571")
    assert watch.penalty_status == "watch"
    assert passed.candidate_id == "candidate_pass"
    assert passed.resolution_lag_penalty_score == d("0.142857")
    assert passed.penalty_status == "pass"


def test_delayed_settlement_penalties_raise_score_and_reason_codes() -> None:
    penalty_report = report(
        candidate(
            "candidate_delay",
            expected_resolution_lag_days=d("2.000000"),
            unresolved_outcome_age_days=d("2.000000"),
            delayed_settlement_signal_count=d("2"),
        ),
    )

    row = penalty_report.rows[0]
    assert row.base_resolution_lag_penalty_score == d("0.285714")
    assert row.delayed_settlement_penalty_score == d("0.300000")
    assert row.resolution_lag_penalty_score == d("0.585714")
    assert row.penalty_status == "watch"
    assert row.reason_codes == (
        "initial_resolution_review",
        "delayed_settlement_penalty",
        "resolution_lag_penalty_watch",
    )
    assert penalty_report.delayed_settlement_candidate_count == d("1")


def test_official_evidence_boosts_reduce_resolution_lag_penalty() -> None:
    without_boost = report(
        candidate(
            "candidate_no_boost",
            expected_resolution_lag_days=d("4.000000"),
            unresolved_outcome_age_days=d("4.000000"),
        ),
    ).rows[0]
    with_boost = report(
        candidate(
            "candidate_with_boost",
            expected_resolution_lag_days=d("4.000000"),
            unresolved_outcome_age_days=d("4.000000"),
            official_evidence_signal_count=d("2"),
        ),
    )
    row = with_boost.rows[0]

    assert without_boost.resolution_lag_penalty_score == d("0.571429")
    assert row.official_evidence_boost_score == d("0.200000")
    assert row.resolution_lag_penalty_score == d("0.371429")
    assert row.penalty_status == "watch"
    assert "official_evidence_boost" in row.reason_codes
    assert with_boost.official_evidence_boosted_candidate_count == d("1")


def test_payload_serializes_decimals_as_strings_and_revalidates_flags() -> None:
    module = api()
    penalty_report = report(
        candidate(
            "candidate_delay",
            expected_resolution_lag_days=d("2.000000"),
            unresolved_outcome_age_days=d("2.000000"),
            delayed_settlement_signal_count=d("1"),
            official_evidence_signal_count=d("1"),
        ),
    )

    payload = module.strategy_candidate_resolution_lag_penalty_score_v2_payload(
        penalty_report,
    )

    assert payload["generated_at"] == "2026-07-06T14:00:00+00:00"
    assert payload["candidate_count"] == "1"
    assert payload["rows"][0]["resolution_lag_penalty_score"] == "0.335714"
    assert payload["rows"][0]["delayed_settlement_penalty_score"] == "0.150000"
    assert payload["rows"][0]["official_evidence_boost_score"] == "0.100000"
    assert payload["derived_validation_digest"] == penalty_report.derived_validation_digest
    assert payload["rows"][0]["derived_validation_digest"].startswith("scrlps-v2:")
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)

    readonly_payload = module.strategy_candidate_resolution_lag_penalty_score_v2_payload(
        {
            "candidate_count": d("1"),
            "rows": (
                {
                    "resolution_lag_penalty_score": d("0.250000"),
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
    assert readonly_payload["candidate_count"] == "1"
    assert readonly_payload["rows"][0]["resolution_lag_penalty_score"] == "0.250000"

    with pytest.raises(ValueError, match="readonly"):
        module.strategy_candidate_resolution_lag_penalty_score_v2_payload(
            {"paper_only": True, "report_only": True, "readonly": False},
        )
    with pytest.raises(ValueError, match="float"):
        module.strategy_candidate_resolution_lag_penalty_score_v2_payload(
            {"score": 0.1, "paper_only": True, "report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="Decimal"):
        module.strategy_candidate_resolution_lag_penalty_score_v2_payload(
            {"score": 1, "paper_only": True, "report_only": True, "readonly": True},
        )


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.StrategyCandidateResolutionLagPenaltyScoreV2Config()
    sample = candidate()
    penalty_report = report(sample)
    row = penalty_report.rows[0]

    public_decimal_fields = {
        "watch_resolution_lag_penalty_score",
        "blocked_resolution_lag_penalty_score",
        "delayed_settlement_penalty_per_signal",
        "max_delayed_settlement_penalty_score",
        "official_evidence_boost_per_signal",
        "max_official_evidence_boost_score",
        "expected_resolution_lag_days",
        "unresolved_outcome_age_days",
        "delayed_settlement_signal_count",
        "official_evidence_signal_count",
        "base_resolution_lag_penalty_score",
        "delayed_settlement_penalty_score",
        "official_evidence_boost_score",
        "resolution_lag_penalty_score",
        "candidate_count",
        "pass_count",
        "watch_count",
        "blocked_count",
        "max_resolution_lag_penalty_score",
        "average_resolution_lag_penalty_score",
        "delayed_settlement_candidate_count",
        "official_evidence_boosted_candidate_count",
    }
    for item in (config, sample, row, penalty_report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.readonly = False  # type: ignore[misc]
        for field in fields(item):
            if field.name in public_decimal_fields:
                assert type(getattr(item, field.name)) is Decimal

    with pytest.raises(ValueError, match="paper_only"):
        module.StrategyCandidateResolutionLagPenaltyScoreV2Config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        candidate(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        candidate(readonly=False)
    with pytest.raises(ValueError, match="expected_resolution_lag_days must be a Decimal"):
        candidate(expected_resolution_lag_days=1)
    with pytest.raises(ValueError, match="must use six decimal places or fewer"):
        candidate(expected_resolution_lag_days=d("1.0000001"))
    with pytest.raises(ValueError, match="must be a Decimal"):
        module.StrategyCandidateResolutionLagPenaltyScoreV2Config(
            watch_resolution_lag_penalty_score=DecimalSubclass("0.300000"),
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        candidate(observed_at=datetime(2026, 7, 6, 14, 0))


def test_derived_validation_digest_rejects_tampering() -> None:
    module = api()
    penalty_report = report(
        candidate(
            "candidate_delay",
            expected_resolution_lag_days=d("2.000000"),
            unresolved_outcome_age_days=d("2.000000"),
            delayed_settlement_signal_count=d("1"),
        ),
    )
    row = penalty_report.rows[0]

    assert row.derived_validation_digest.startswith("scrlps-v2:")
    assert penalty_report.derived_validation_digest.startswith("scrlps-v2:")

    object.__setattr__(row, "resolution_lag_penalty_score", d("0.010000"))
    with pytest.raises(ValueError, match="derived_validation_digest|tamper"):
        module.strategy_candidate_resolution_lag_penalty_score_v2_payload(penalty_report)

    clean_report = report(candidate("candidate_clean"))
    object.__setattr__(clean_report, "candidate_count", d("2"))
    with pytest.raises(ValueError, match="candidate_count|derived_validation_digest|tamper"):
        module.strategy_candidate_resolution_lag_penalty_score_v2_payload(clean_report)


def test_unsafe_public_keys_and_values_are_rejected() -> None:
    module = api()
    unsafe_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )

    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe public"):
            module.strategy_candidate_resolution_lag_penalty_score_v2_payload(
                {
                    f"{term}_field": "redacted",
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                },
            )
        with pytest.raises(ValueError, match="unsafe public"):
            module.strategy_candidate_resolution_lag_penalty_score_v2_payload(
                {
                    "note": f"contains {term} surface",
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                },
            )

    with pytest.raises(ValueError, match="unsafe public"):
        candidate(candidate_id="candidate_wallet")
    with pytest.raises(ValueError, match="reason_codes"):
        candidate(reason_codes=("trade_term",))

    class PayloadDict(dict):
        pass

    with pytest.raises(ValueError, match="unsafe payload object|plain"):
        module.strategy_candidate_resolution_lag_penalty_score_v2_payload(
            {
                "nested": PayloadDict({"note": "safe"}),
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_module_scope_has_no_unsafe_surfaces() -> None:
    module = api()
    source_text = inspect.getsource(module)
    tree = ast.parse(source_text)

    assert module.__all__ == (
        "DEFAULT_STRATEGY_CANDIDATE_RESOLUTION_LAG_PENALTY_SCORE_V2_CONFIG_VERSION",
        "ROW_STATUSES",
        "REPORT_STATUSES",
        "StrategyCandidateResolutionLagPenaltyScoreV2Config",
        "StrategyCandidateResolutionLagPenaltyScoreV2Input",
        "StrategyCandidateResolutionLagPenaltyScoreV2Row",
        "StrategyCandidateResolutionLagPenaltyScoreV2Report",
        "build_strategy_candidate_resolution_lag_penalty_score_v2",
        "strategy_candidate_resolution_lag_penalty_score_v2_payload",
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
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
        "trading",
        "broker",
        "client",
        "execute",
        "connect",
        "subprocess",
        "open(",
        "pathlib",
        "write_text",
        "write_bytes",
    )
    assert all(term not in source_text.lower() for term in forbidden_source_terms)

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
