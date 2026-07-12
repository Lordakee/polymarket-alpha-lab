from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.operator_daily_screening_digest_readiness_report as api
from polymarket_alpha_lab.operator_daily_screening_digest_readiness_report import (
    OperatorDailyScreeningDigestReadinessInput,
    OperatorDailyScreeningDigestReadinessReport,
    build_operator_daily_screening_digest_readiness_report,
    operator_daily_screening_digest_readiness_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/operator_daily_screening_digest_readiness_report.py",
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def screening_input(
    *,
    screened_market_count: Decimal = d("12.000000"),
    candidate_count: Decimal = d("4.000000"),
    blocked_count: Decimal = ZERO,
    watch_count: Decimal = ZERO,
    ready_packet_count: Decimal = ONE,
    digest_generated: bool = True,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> OperatorDailyScreeningDigestReadinessInput:
    return OperatorDailyScreeningDigestReadinessInput(
        screened_market_count=screened_market_count,
        candidate_count=candidate_count,
        blocked_count=blocked_count,
        watch_count=watch_count,
        ready_packet_count=ready_packet_count,
        digest_generated=digest_generated,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    readiness_input: OperatorDailyScreeningDigestReadinessInput,
) -> OperatorDailyScreeningDigestReadinessReport:
    return build_operator_daily_screening_digest_readiness_report(readiness_input)


def assert_no_float_or_int_values(value: Any) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def test_ready_digest_report_exposes_public_payload_and_digest() -> None:
    readiness = report(screening_input())

    assert is_dataclass(readiness)
    assert readiness.digest_status == "ready"
    assert readiness.reason_codes == ("operator_daily_screening_digest_ready",)
    assert readiness.manual_next_step == "review_daily_screening_digest"
    assert readiness.screened_market_count == d("12.000000")
    assert readiness.candidate_count == d("4.000000")
    assert readiness.blocked_count == ZERO
    assert readiness.watch_count == ZERO
    assert readiness.ready_packet_count == ONE
    assert readiness.digest_generated is True
    assert readiness.paper_only is True
    assert readiness.report_only is True
    assert readiness.readonly is True

    payload = readiness.public_payload
    assert payload == operator_daily_screening_digest_readiness_payload(readiness)
    assert payload == {
        "digest_status": "ready",
        "reason_codes": ["operator_daily_screening_digest_ready"],
        "manual_next_step": "review_daily_screening_digest",
        "screened_market_count": "12.000000",
        "candidate_count": "4.000000",
        "blocked_count": "0.000000",
        "watch_count": "0.000000",
        "ready_packet_count": "1.000000",
        "digest_generated": True,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "payload_digest": readiness.payload_digest,
    }
    assert len(readiness.payload_digest) == 64
    int(readiness.payload_digest, 16)
    assert_no_float_or_int_values(payload)


def test_pending_digest_when_no_ready_packet_or_digest_generated() -> None:
    readiness = report(
        screening_input(
            screened_market_count=d("8.000000"),
            candidate_count=d("3.000000"),
            watch_count=d("2.000000"),
            ready_packet_count=ZERO,
            digest_generated=False,
        ),
    )

    assert readiness.digest_status == "pending"
    assert readiness.reason_codes == (
        "operator_daily_screening_digest_ready_packet_missing",
        "operator_daily_screening_digest_not_generated",
        "operator_daily_screening_digest_watch_items_present",
    )
    assert readiness.manual_next_step == "prepare_ready_packet_then_generate_digest"
    assert readiness.public_payload["payload_digest"] == readiness.payload_digest
    assert_no_float_or_int_values(readiness.public_payload)


def test_blocked_digest_when_no_screening_or_all_candidates_blocked() -> None:
    readiness = report(
        screening_input(
            screened_market_count=d("2.000000"),
            candidate_count=d("2.000000"),
            blocked_count=d("2.000000"),
            ready_packet_count=ZERO,
            digest_generated=False,
        ),
    )

    assert readiness.digest_status == "blocked"
    assert readiness.reason_codes == (
        "operator_daily_screening_digest_all_candidates_blocked",
        "operator_daily_screening_digest_ready_packet_missing",
        "operator_daily_screening_digest_not_generated",
    )
    assert readiness.manual_next_step == "complete_daily_screening_before_digest_review"


def test_counts_are_decimal_only_integral_and_consistent() -> None:
    with pytest.raises(ValueError, match="screened_market_count must be a Decimal"):
        screening_input(screened_market_count=12)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="candidate_count must be nonnegative"):
        screening_input(candidate_count=d("-1.000000"))

    with pytest.raises(ValueError, match="watch_count must be an integer"):
        screening_input(watch_count=d("1.500000"))

    with pytest.raises(ValueError, match="candidate_count cannot exceed screened_market_count"):
        screening_input(screened_market_count=ONE, candidate_count=d("2.000000"))

    with pytest.raises(ValueError, match="blocked_count plus watch_count cannot exceed candidate_count"):
        screening_input(
            candidate_count=d("3.000000"),
            blocked_count=d("2.000000"),
            watch_count=d("2.000000"),
        )

    with pytest.raises(ValueError, match="ready_packet_count cannot exceed candidate_count"):
        screening_input(candidate_count=ONE, ready_packet_count=d("2.000000"))

    with pytest.raises(ValueError, match="digest_generated must be a bool"):
        screening_input(digest_generated=ONE)  # type: ignore[arg-type]


def test_dataclasses_are_frozen_final_and_enforce_readonly_flags() -> None:
    readiness = report(screening_input())

    with pytest.raises(FrozenInstanceError):
        readiness.digest_status = "pending"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(OperatorDailyScreeningDigestReadinessInput):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        screening_input(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        screening_input(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(readiness, readonly=False)


def test_public_api_has_no_execution_or_sensitive_surfaces() -> None:
    forbidden_fragments = (
        "live",
        "auth",
        "wallet",
        "order",
        "key",
        "sign",
        "execute",
        "trade",
        "database",
        "network",
        "request",
        "http",
        "broker",
    )

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)

    for cls in (
        OperatorDailyScreeningDigestReadinessInput,
        OperatorDailyScreeningDigestReadinessReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in forbidden_fragments)

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
        "subprocess",
        "open",
    ):
        assert not hasattr(api, forbidden_name)

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered_source = source.lower()
    assert "自动下单" not in source
    assert "执行路径" not in source
    assert "签名" not in source
    assert "private_key" not in lowered_source
    assert "api_key" not in lowered_source

    tree = ast.parse(source)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    assert imported_roots.isdisjoint(
        {
            "requests",
            "httpx",
            "urllib",
            "socket",
            "sqlite3",
            "sqlalchemy",
            "psycopg",
            "web3",
            "ccxt",
            "subprocess",
            "pathlib",
        },
    )
