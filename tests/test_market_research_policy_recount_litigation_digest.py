from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.market_research_policy_recount_litigation_digest import (
    DEFAULT_MARKET_RESEARCH_POLICY_RECOUNT_LITIGATION_DIGEST_CONFIG_VERSION,
    MarketResearchPolicyRecountLitigationDigestConfig,
    MarketResearchPolicyRecountLitigationDigestInputRow,
    MarketResearchPolicyRecountLitigationDigestReasonCodeCount,
    MarketResearchPolicyRecountLitigationDigestReport,
    MarketResearchPolicyRecountLitigationDigestRow,
    build_market_research_policy_recount_litigation_digest,
    market_research_policy_recount_litigation_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_policy_recount_litigation_digest.py",
)


def d(value: str) -> Decimal:
    return Decimal(value)


def input_row(
    research_key: str,
    *,
    condition_id: str | None = None,
    jurisdiction: str = "pa",
    public_evidence_reference: str = "public-pa-recount-bulletin",
    observed_at: datetime = datetime(2026, 7, 4, 10, 0, tzinfo=UTC),
    source_count: Decimal = d("3"),
    recount_margin_ratio: Decimal = d("0.002000"),
    litigation_event_count: Decimal = d("0"),
    unresolved_filing_count: Decimal = d("0"),
    certified_result: bool = True,
    official_update: bool = True,
) -> MarketResearchPolicyRecountLitigationDigestInputRow:
    return MarketResearchPolicyRecountLitigationDigestInputRow(
        research_key=research_key,
        condition_id=condition_id or f"condition-{research_key}",
        jurisdiction=jurisdiction,
        public_evidence_reference=public_evidence_reference,
        observed_at=observed_at,
        source_count=source_count,
        recount_margin_ratio=recount_margin_ratio,
        litigation_event_count=litigation_event_count,
        unresolved_filing_count=unresolved_filing_count,
        certified_result=certified_result,
        official_update=official_update,
    )


def build_report(
    *rows: MarketResearchPolicyRecountLitigationDigestInputRow,
    config: MarketResearchPolicyRecountLitigationDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchPolicyRecountLitigationDigestReport:
    return build_market_research_policy_recount_litigation_digest(
        rows,
        config=config or MarketResearchPolicyRecountLitigationDigestConfig(),
        generated_at=generated_at,
    )


def assert_no_floats(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"found float in payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_floats(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_floats(item)


def test_policy_recount_litigation_digest_reduces_rows_with_utc_and_stable_reasons() -> None:
    report = build_report(
        input_row(
            "ready-pa",
            jurisdiction="pa",
            observed_at=datetime(2026, 7, 4, 7, 30, tzinfo=timezone(timedelta(hours=-4))),
        ),
        input_row(
            "watch-az",
            jurisdiction="az",
            observed_at=datetime(2026, 7, 4, 8, 0, tzinfo=UTC),
            recount_margin_ratio=d("0.000700"),
            litigation_event_count=d("2"),
        ),
        input_row(
            "blocked-nv",
            jurisdiction="nv",
            public_evidence_reference="https://example.test/election?secret=abc123",
            observed_at=datetime(2026, 7, 4, 4, 0, tzinfo=UTC),
            source_count=d("1"),
            recount_margin_ratio=d("0.000300"),
            litigation_event_count=d("1"),
            unresolved_filing_count=d("2"),
            certified_result=False,
            official_update=False,
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        DEFAULT_MARKET_RESEARCH_POLICY_RECOUNT_LITIGATION_DIGEST_CONFIG_VERSION
    )
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_policy_recount_litigation_digest"
    )
    assert report.row_count == d("3.000000")
    assert report.ready_row_count == d("1.000000")
    assert report.watch_row_count == d("1.000000")
    assert report.blocked_row_count == d("1.000000")
    assert report.recount_watch_count == d("2.000000")
    assert report.litigation_watch_count == d("2.000000")
    assert report.unresolved_filing_count == d("1.000000")
    assert report.uncertified_result_count == d("1.000000")
    assert report.thin_source_count == d("1.000000")
    assert report.stale_evidence_count == d("1.000000")
    assert report.average_recount_margin_ratio == d("0.001000")
    assert report.max_evidence_age_seconds == d("28800.000000")
    assert report.reason_codes == (
        "market_research_policy_recount_litigation_digest_unresolved_filings",
        "market_research_policy_recount_litigation_digest_uncertified_result",
        "market_research_policy_recount_litigation_digest_recount_margin",
        "market_research_policy_recount_litigation_digest_litigation_activity",
        "market_research_policy_recount_litigation_digest_stale_evidence",
        "market_research_policy_recount_litigation_digest_thin_sources",
    )

    assert tuple((row.digest_status, row.research_key) for row in report.rows) == (
        ("blocked", "blocked-nv"),
        ("watch", "watch-az"),
        ("ready", "ready-pa"),
    )
    blocked = report.rows[0]
    assert blocked.observed_at == datetime(2026, 7, 4, 4, 0, tzinfo=UTC)
    assert blocked.evidence_age_seconds == d("28800.000000")
    assert blocked.redacted_public_evidence_reference.startswith("sha256:")
    assert "secret" not in repr(blocked).lower()
    assert blocked.reason_codes == (
        "market_research_policy_recount_litigation_digest_unresolved_filings",
        "market_research_policy_recount_litigation_digest_uncertified_result",
        "market_research_policy_recount_litigation_digest_recount_margin",
        "market_research_policy_recount_litigation_digest_litigation_activity",
        "market_research_policy_recount_litigation_digest_stale_evidence",
        "market_research_policy_recount_litigation_digest_thin_sources",
    )
    assert all(item.paper_only and item.report_only and item.readonly for item in report.rows)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_policy_recount_litigation_digest_empty_inputs_are_report_only_noop() -> None:
    report = build_report()

    assert report.digest_status == "ready"
    assert report.recommended_next_step == (
        "allow_report_only_market_research_policy_recount_litigation_digest"
    )
    assert report.reason_codes == (
        "market_research_policy_recount_litigation_digest_no_inputs",
    )
    assert report.row_count == d("0.000000")
    assert report.rows == ()
    assert report.reason_code_counts == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_policy_recount_litigation_digest_ready_watch_and_blocked_thresholds() -> None:
    watch = build_report(
        input_row(
            "watch-margin",
            recount_margin_ratio=d("0.000900"),
            litigation_event_count=d("1"),
        ),
    )
    blocked = build_report(
        input_row(
            "blocked-filings",
            unresolved_filing_count=d("1"),
            certified_result=False,
        ),
    )
    ready = build_report(input_row("ready"))

    assert watch.digest_status == "watch"
    assert watch.reason_codes == (
        "market_research_policy_recount_litigation_digest_recount_margin",
        "market_research_policy_recount_litigation_digest_litigation_activity",
    )
    assert blocked.digest_status == "blocked"
    assert blocked.reason_codes == (
        "market_research_policy_recount_litigation_digest_unresolved_filings",
        "market_research_policy_recount_litigation_digest_uncertified_result",
    )
    assert ready.digest_status == "ready"
    assert ready.reason_codes == (
        "market_research_policy_recount_litigation_digest_ready",
    )


def test_policy_recount_litigation_digest_payload_uses_decimal_strings_and_redacts() -> None:
    report = build_report(
        input_row(
            "payload",
            public_evidence_reference="https://example.test/recount?api_key=abc",
            source_count=d("1"),
            unresolved_filing_count=d("1"),
            official_update=False,
        ),
    )

    payload = market_research_policy_recount_litigation_digest_payload(report)

    assert json.loads(json.dumps(payload))["digest_status"] == "blocked"
    assert payload["row_count"] == "1.000000"
    assert payload["rows"][0]["source_count"] == "1.000000"
    assert payload["rows"][0]["redacted_public_evidence_reference"].startswith("sha256:")
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_floats(payload)
    payload_text = repr(payload).lower()
    for forbidden in (
        "api_key",
        "secret",
        "wallet",
        "private_key",
        "market_slug",
        "question",
        "advice",
    ):
        assert forbidden not in payload_text


def test_policy_recount_litigation_digest_frozen_exact_types_and_validation() -> None:
    report = build_report(input_row("frozen"))

    for value in (
        MarketResearchPolicyRecountLitigationDigestConfig(),
        input_row("row"),
        report.rows[0],
        report,
        MarketResearchPolicyRecountLitigationDigestReasonCodeCount(
            reason_code="market_research_policy_recount_litigation_digest_ready",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    ):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        report.digest_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].digest_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="rows must be a tuple"):
        build_market_research_policy_recount_litigation_digest(
            [input_row("list")],
            config=MarketResearchPolicyRecountLitigationDigestConfig(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_market_research_policy_recount_litigation_digest(
            (),
            config=MarketResearchPolicyRecountLitigationDigestConfig(),
            generated_at=datetime(2026, 7, 4, 12, 0),
        )
    with pytest.raises(ValueError, match="source_count must be exactly Decimal"):
        input_row("bad-decimal", source_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="certified_result must be a bool"):
        input_row("bad-bool", certified_result=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only/report_only/readonly must be True"):
        replace(input_row("bad-flag"), readonly=False)
    with pytest.raises(ValueError, match="report must be exactly"):
        market_research_policy_recount_litigation_digest_payload(object())  # type: ignore[arg-type]

    for item in (report, report.rows[0], report.reason_code_counts[0]):
        for field in fields(item):
            if field.name.endswith("_count") or field.name.endswith("_ratio"):
                assert type(getattr(item, field.name)) is Decimal


def test_policy_recount_litigation_digest_rejects_duplicates_and_manual_drift() -> None:
    with pytest.raises(ValueError, match="research_key values must be unique"):
        build_report(input_row("duplicate"), input_row("duplicate"))

    report = build_report(input_row("manual"))
    with pytest.raises(ValueError, match="row_count must match rows"):
        replace(report, row_count=d("2.000000"))
    with pytest.raises(ValueError, match="reason_codes must match reason_code_counts"):
        replace(
            report,
            reason_codes=(
                "market_research_policy_recount_litigation_digest_thin_sources",
            ),
        )
    with pytest.raises(ValueError, match="digest_status must match rows"):
        replace(
            report,
            digest_status="blocked",
            recommended_next_step=(
                "block_report_only_market_research_policy_recount_litigation_digest"
            ),
        )
    with pytest.raises(ValueError, match="digest_status must match reason_codes"):
        replace(report.rows[0], digest_status="blocked")


def test_policy_recount_litigation_digest_static_source_is_pure_report_only() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live_trading",
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "exchange",
        "mutation",
        "private_key",
        "api_key",
        "secret",
        "market_slug",
        "question",
        "advice",
        "bet",
        "stake",
        "client",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
