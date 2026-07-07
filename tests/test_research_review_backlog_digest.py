from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_PATH = Path("src/polymarket_alpha_lab/research_review_backlog_digest.py")
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module("polymarket_alpha_lab.research_review_backlog_digest")


def d(value: str) -> Decimal:
    return Decimal(value)


def item(**overrides: object):
    module = api()
    values = {
        "candidate_id": "cand-private-001",
        "market_id": "mkt-private-001",
        "market_slug": "private-election-slug",
        "market_question": "Will the private event resolve?",
        "source_ref": "private-source-row",
        "source_url": "https://example.invalid/private-source",
        "source_text": "raw private source excerpt",
        "team_id": "macro_review",
        "domain": "macro.rates",
        "queue_depth": d("3.000000"),
        "queue_capacity": d("10.000000"),
        "reminder_priority": d("0.100000"),
        "team_available_capacity": d("8.000000"),
        "team_committed_reviews": d("2.000000"),
        "domain_backlog_count": d("2.000000"),
        "total_backlog_count": d("10.000000"),
    }
    values.update(overrides)
    return module.ResearchReviewBacklogDigestItem(**values)


def report(*items: object, cfg: object | None = None):
    module = api()
    return module.build_research_review_backlog_digest(
        items,
        generated_at=GENERATED_AT,
        config=cfg if cfg is not None else module.ResearchReviewBacklogDigestConfig(),
    )


def assert_decimal_only(value: Any) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"numeric value must be Decimal, got {value!r}")
    if type(value) is Decimal:
        return
    if isinstance(value, datetime):
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_decimal_only(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for nested in value.values():
            assert_decimal_only(nested)
        return
    if isinstance(value, (list, tuple)):
        for nested in value:
            assert_decimal_only(nested)


def test_builds_pass_watch_block_digest_with_redacted_summary() -> None:
    digest = report(
        item(
            candidate_id="cand-pass-secret",
            market_id="mkt-pass-secret",
            team_id="macro_review",
            domain="macro.rates",
            queue_depth=d("1.000000"),
            queue_capacity=d("10.000000"),
            reminder_priority=d("0.000000"),
            team_available_capacity=d("10.000000"),
            team_committed_reviews=d("1.000000"),
            domain_backlog_count=d("1.000000"),
            total_backlog_count=d("10.000000"),
        ),
        item(
            candidate_id="cand-watch-secret",
            market_id="mkt-watch-secret",
            team_id="crypto_review",
            domain="crypto.btc",
            queue_depth=d("7.000000"),
            queue_capacity=d("10.000000"),
            reminder_priority=d("0.600000"),
            team_available_capacity=d("5.000000"),
            team_committed_reviews=d("4.000000"),
            domain_backlog_count=d("6.000000"),
            total_backlog_count=d("10.000000"),
        ),
        item(
            candidate_id="cand-block-secret",
            market_id="mkt-block-secret",
            team_id="sports_review",
            domain="sports.basketball",
            queue_depth=d("10.000000"),
            queue_capacity=d("10.000000"),
            reminder_priority=d("0.950000"),
            team_available_capacity=d("4.000000"),
            team_committed_reviews=d("5.000000"),
            domain_backlog_count=d("9.000000"),
            total_backlog_count=d("10.000000"),
        ),
    )

    assert is_dataclass(digest)
    assert digest.report_status == "block"
    assert digest.item_count == d("3.000000")
    assert digest.pass_count == d("1.000000")
    assert digest.watch_count == d("1.000000")
    assert digest.block_count == d("1.000000")
    assert tuple(row.status for row in digest.rows) == ("block", "watch", "pass")
    assert tuple(row.redacted_candidate_ref for row in digest.rows) == (
        "<redacted-candidate-001>",
        "<redacted-candidate-002>",
        "<redacted-candidate-003>",
    )
    assert digest.rows[0].digest_summary == (
        "block review backlog: queue saturated; reminder critical; "
        "capacity overdrawn; domain concentrated"
    )
    assert digest.rows[1].digest_summary == (
        "watch review backlog: queue elevated; reminder elevated; "
        "capacity tightening; domain clustered"
    )
    assert digest.rows[2].digest_summary == (
        "pass review backlog: queue manageable; reminder low; "
        "capacity available; domain dispersed"
    )
    assert digest.rows[0].reason_codes == (
        "review_backlog_block",
        "queue_pressure_block",
        "reminder_priority_block",
        "team_capacity_block",
        "domain_concentration_watch",
    )

    payload = api().research_review_backlog_digest_payload(digest)
    payload_text = repr(payload).lower()
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["redacted_candidate_ref"] == "<redacted-candidate-001>"
    assert payload["rows"][0]["digest_summary"].startswith("block review backlog")
    for forbidden in (
        "cand-pass-secret",
        "cand-watch-secret",
        "cand-block-secret",
        "mkt-pass-secret",
        "private-election-slug",
        "will the private event resolve",
        "private-source",
        "source_url",
        "source_text",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
        "dsn",
        "table",
    ):
        assert forbidden not in payload_text
    assert_decimal_only(digest)


def test_report_can_be_all_pass_all_watch_or_all_block() -> None:
    assert report(item()).report_status == "pass"
    assert report(
        item(
            candidate_id="watch-only",
            queue_depth=d("8.000000"),
            queue_capacity=d("10.000000"),
            reminder_priority=d("0.300000"),
            team_available_capacity=d("10.000000"),
            team_committed_reviews=d("7.000000"),
            domain_backlog_count=d("5.000000"),
            total_backlog_count=d("10.000000"),
        ),
    ).report_status == "watch"
    assert report(
        item(
            candidate_id="block-only",
            queue_depth=d("10.000000"),
            queue_capacity=d("10.000000"),
            reminder_priority=d("0.900000"),
            team_available_capacity=d("1.000000"),
            team_committed_reviews=d("2.000000"),
            domain_backlog_count=d("10.000000"),
            total_backlog_count=d("10.000000"),
        ),
    ).report_status == "block"


def test_rejects_wrong_types_subclasses_and_inconsistent_counts() -> None:
    module = api()
    with pytest.raises(ValueError, match="queue_depth must be exactly Decimal"):
        item(queue_depth=1)
    with pytest.raises(ValueError, match="reminder_priority must be exactly Decimal"):
        item(reminder_priority=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="candidate_id must be a non-empty string"):
        item(candidate_id="")
    with pytest.raises(ValueError, match="config"):
        module.build_research_review_backlog_digest((), generated_at=GENERATED_AT, config=object())
    with pytest.raises(ValueError, match="items must contain"):
        module.build_research_review_backlog_digest((object(),), generated_at=GENERATED_AT)
    with pytest.raises(ValueError, match="queue_capacity must be positive"):
        item(queue_capacity=d("0.000000"))
    with pytest.raises(ValueError, match="domain_backlog_count must not exceed"):
        item(domain_backlog_count=d("11.000000"), total_backlog_count=d("10.000000"))


def test_payload_rejects_public_leaks_and_hard_flag_drift() -> None:
    module = api()
    safe_payload = module.research_review_backlog_digest_payload(report(item()))
    safe_payload["rows"][0]["market_id"] = "mkt-secret"
    with pytest.raises(ValueError, match="unsafe|sensitive|market_id"):
        module.research_review_backlog_digest_payload(safe_payload)

    safe_payload = module.research_review_backlog_digest_payload(report(item()))
    safe_payload["rows"][0]["digest_summary"] = "place a buy recommendation"
    with pytest.raises(ValueError, match="unsafe|sensitive"):
        module.research_review_backlog_digest_payload(safe_payload)

    safe_payload = module.research_review_backlog_digest_payload(report(item()))
    safe_payload["paper_only"] = False
    with pytest.raises(ValueError, match="paper_only"):
        module.research_review_backlog_digest_payload(safe_payload)

    with pytest.raises(ValueError, match="readonly"):
        replace(report(item()), readonly=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(item(), report_only=False)


def test_dataclasses_are_frozen_and_payload_digest_is_tamper_evident() -> None:
    module = api()
    digest = report(item())
    with pytest.raises(FrozenInstanceError):
        digest.rows[0].status = "block"  # type: ignore[misc]

    payload = module.research_review_backlog_digest_payload(digest)
    payload["rows"][0]["status"] = "block"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_review_backlog_digest_payload(payload)


def test_output_is_deterministic_across_input_order() -> None:
    first = item(candidate_id="z-private", team_id="zeta", domain="macro.rates")
    second = item(
        candidate_id="a-private",
        team_id="alpha",
        domain="crypto.btc",
        queue_depth=d("8.000000"),
        queue_capacity=d("10.000000"),
        reminder_priority=d("0.600000"),
        team_available_capacity=d("5.000000"),
        team_committed_reviews=d("4.000000"),
        domain_backlog_count=d("6.000000"),
        total_backlog_count=d("10.000000"),
    )

    left = report(first, second)
    right = report(second, first)
    assert left.rows == right.rows
    assert api().research_review_backlog_digest_payload(left) == api().research_review_backlog_digest_payload(right)


def test_module_is_pure_report_only_strategy_reducer() -> None:
    module = api()
    source = MODULE_PATH.read_text()
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_REVIEW_BACKLOG_DIGEST_CONFIG_VERSION",
        "RESEARCH_REVIEW_BACKLOG_DIGEST_STATUSES",
        "ResearchReviewBacklogDigestConfig",
        "ResearchReviewBacklogDigestItem",
        "ResearchReviewBacklogDigestRow",
        "ResearchReviewBacklogDigestReport",
        "build_research_review_backlog_digest",
        "research_review_backlog_digest_payload",
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
        "json",
        "re",
        "typing",
    }

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
