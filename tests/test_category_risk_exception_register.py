from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 2, 8, 15, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.category_risk_exception_register",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def risk_row(
    team_id: str,
    category_id: str,
    *,
    exception_count: str = "0",
    risk_status: str = "pass",
    severity_score: str = "0",
    review_queue_count: str = "0",
    source_row_count: str = "1",
    reason_codes: tuple[str, ...] = ("risk_exception_pass",),
):
    register = api()
    return register.CategoryRiskExceptionRegisterInput(
        team_id=team_id,
        category_id=category_id,
        exception_count=d(exception_count),
        risk_status=risk_status,
        severity_score=d(severity_score),
        review_queue_count=d(review_queue_count),
        source_row_count=d(source_row_count),
        reason_codes=reason_codes,
    )


def report(*rows):
    register = api()
    return register.build_category_risk_exception_register_report(
        rows,
        config=register.CategoryRiskExceptionRegisterConfig(),
        generated_at=GENERATED_AT,
    )


def test_register_summarizes_category_exception_counts_severity_and_review_queue() -> None:
    register_report = report(
        risk_row(
            "politics",
            "politics",
            exception_count="2",
            risk_status="watch",
            severity_score="0.300000",
            review_queue_count="1",
            source_row_count="3",
            reason_codes=("risk_exception_watch",),
        ),
        risk_row(
            "crypto_btc",
            "crypto",
            exception_count="3",
            risk_status="blocked",
            severity_score="0.900000",
            review_queue_count="2",
            source_row_count="2",
            reason_codes=("risk_exception_blocked",),
        ),
        risk_row(
            "crypto_eth",
            "crypto",
            exception_count="1",
            risk_status="watch",
            severity_score="0.100000",
            review_queue_count="0",
            source_row_count="2",
            reason_codes=("risk_exception_watch",),
        ),
        risk_row(
            "macro_rates",
            "macro",
            exception_count="0",
            risk_status="pass",
            severity_score="0.000000",
            review_queue_count="0",
            reason_codes=("risk_exception_pass",),
        ),
    )

    assert is_dataclass(register_report)
    assert register_report.generated_at == GENERATED_AT
    assert register_report.source_row_count == d("8")
    assert register_report.category_count == d("3")
    assert register_report.exception_count == d("6")
    assert register_report.review_queue_count == d("3")
    assert register_report.low_severity_count == d("1")
    assert register_report.medium_severity_count == d("1")
    assert register_report.high_severity_count == d("0")
    assert register_report.critical_severity_count == d("1")
    assert register_report.status == "blocked"
    assert register_report.reason_codes == (
        "risk_exceptions_blocked",
        "risk_review_queue_present",
    )
    assert register_report.paper_only is True
    assert register_report.report_only is True
    assert register_report.readonly is True

    assert tuple(row.category_id for row in register_report.category_rows) == (
        "crypto",
        "politics",
        "macro",
    )
    crypto = register_report.category_rows[0]
    assert crypto.team_count == d("2")
    assert crypto.source_row_count == d("4")
    assert crypto.exception_count == d("4")
    assert crypto.review_queue_count == d("2")
    assert crypto.severity_bucket == "critical"
    assert crypto.risk_status == "blocked"
    assert crypto.reason_codes == (
        "category_risk_blocked",
        "category_review_queue_present",
    )

    politics = register_report.category_rows[1]
    assert politics.severity_bucket == "medium"
    assert politics.risk_status == "watch"
    assert politics.exception_count == d("2")

    macro = register_report.category_rows[2]
    assert macro.severity_bucket == "low"
    assert macro.risk_status == "pass"
    assert macro.reason_codes == ("category_risk_pass",)


def test_empty_register_report_is_readonly_and_has_zero_decimal_counts() -> None:
    register_report = report()

    assert register_report.category_count == d("0")
    assert register_report.exception_count == d("0")
    assert register_report.review_queue_count == d("0")
    assert register_report.low_severity_count == d("0")
    assert register_report.medium_severity_count == d("0")
    assert register_report.high_severity_count == d("0")
    assert register_report.critical_severity_count == d("0")
    assert register_report.status == "pass"
    assert register_report.reason_codes == ("risk_exception_register_clear",)
    assert register_report.category_rows == ()


def test_register_rejects_float_numeric_inputs_and_mutation() -> None:
    register = api()

    with pytest.raises(ValueError, match="exception_count must be a Decimal"):
        register.CategoryRiskExceptionRegisterInput(
            team_id="politics",
            category_id="politics",
            exception_count=1.0,
            risk_status="watch",
            severity_score=d("0.500000"),
            review_queue_count=d("0"),
            source_row_count=d("1"),
            reason_codes=("risk_exception_watch",),
        )

    row = risk_row("politics", "politics")
    with pytest.raises(FrozenInstanceError):
        row.exception_count = d("9")  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="paper_only must be True"):
        register.CategoryRiskExceptionRegisterConfig(paper_only=False)


def test_register_validates_category_team_pair_and_status_counts() -> None:
    register = api()

    with pytest.raises(ValueError, match="team_id must match category_id"):
        risk_row("crypto_btc", "politics")

    with pytest.raises(ValueError, match="review_queue_count requires exceptions"):
        risk_row(
            "politics",
            "politics",
            exception_count="0",
            review_queue_count="1",
        )

    with pytest.raises(ValueError, match="blocked rows require exceptions"):
        risk_row(
            "politics",
            "politics",
            risk_status="blocked",
            exception_count="0",
            reason_codes=("risk_exception_blocked",),
        )

    with pytest.raises(ValueError, match="pass rows must use zero severity"):
        risk_row("politics", "politics", risk_status="pass", severity_score="0.1")

    with pytest.raises(ValueError, match="inputs must not contain duplicate"):
        report(
            risk_row("politics", "politics"),
            risk_row("politics", "politics"),
        )


def test_payload_is_redacted_json_ready_and_omits_market_surfaces() -> None:
    payload = api().category_risk_exception_register_payload(
        report(
            risk_row(
                "politics",
                "politics",
                exception_count="1",
                risk_status="watch",
                severity_score="0.400000",
                review_queue_count="1",
                reason_codes=("risk_exception_watch",),
            ),
        ),
    )

    payload_text = repr(payload).lower()
    assert "market_slug" not in payload_text
    assert "question" not in payload_text
    assert "payload" not in payload_text
    assert "recommend" not in payload_text
    assert "wallet" not in payload_text
    assert "order" not in payload_text
    assert payload["exception_count"] == "1"
    assert payload["category_rows"][0]["category_id"] == "politics"
    assert payload["category_rows"][0]["severity_bucket"] == "medium"


def test_validation_digest_is_deterministic_payload_bound_and_tamper_evident() -> None:
    register = api()
    rows = (
        risk_row(
            "crypto_btc",
            "crypto",
            exception_count="3",
            risk_status="blocked",
            severity_score="0.900000",
            review_queue_count="2",
            source_row_count="2",
            reason_codes=("risk_exception_blocked",),
        ),
        risk_row(
            "politics",
            "politics",
            exception_count="2",
            risk_status="watch",
            severity_score="0.300000",
            review_queue_count="1",
            source_row_count="3",
            reason_codes=("risk_exception_watch",),
        ),
    )

    first = report(*rows)
    second = report(*reversed(rows))

    assert len(first.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in first.derived_validation_digest)
    assert first.derived_validation_digest == second.derived_validation_digest
    assert (
        register.category_risk_exception_register_payload(first)[
            "derived_validation_digest"
        ]
        == first.derived_validation_digest
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)

    object.__setattr__(second, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        register.category_risk_exception_register_payload(second)


def test_module_scope_has_no_live_auth_wallet_store_fast_or_sensitive_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/category_risk_exception_register.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "market_slug",
        "question",
        "payload_json",
        "investment_recommendation",
        "durable",
        "open(",
        "fast",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
