from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_market_source_memory_cost_guard_report import (
    ResearchMarketSourceMemoryCostGuardConfig,
    ResearchMarketSourceMemoryCostGuardInputRow,
    ResearchMarketSourceMemoryCostGuardReasonCodeCount,
    ResearchMarketSourceMemoryCostGuardReport,
    ResearchMarketSourceMemoryCostGuardReportRow,
    build_research_market_source_memory_cost_guard_report,
    research_market_source_memory_cost_guard_public_payload,
    validate_research_market_source_memory_cost_guard_payload_digest,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
HEX_A = "a" * 64
HEX_B = "b" * 64
HEX_C = "c" * 64


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> ResearchMarketSourceMemoryCostGuardConfig:
    values = {
        "config_version": "memory-cost-guard-v0",
        "item_pass_memory_mb": d("64.000000"),
        "item_block_memory_mb": d("128.000000"),
        "item_pass_cost_usd": d("0.050000"),
        "item_block_cost_usd": d("0.100000"),
        "total_pass_memory_mb": d("160.000000"),
        "total_block_memory_mb": d("240.000000"),
        "total_pass_cost_usd": d("0.120000"),
        "total_block_cost_usd": d("0.200000"),
    }
    values.update(overrides)
    return ResearchMarketSourceMemoryCostGuardConfig(**values)


def item(
    digest: str,
    *,
    observed_at: datetime | None = None,
    memory_mb: Decimal = d("24.000000"),
    cost_usd: Decimal = d("0.010000"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchMarketSourceMemoryCostGuardInputRow:
    return ResearchMarketSourceMemoryCostGuardInputRow(
        item_digest=digest,
        observed_at=(
            observed_at
            if observed_at is not None
            else GENERATED_AT - timedelta(minutes=5)
        ),
        memory_mb=memory_mb,
        cost_usd=cost_usd,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[ResearchMarketSourceMemoryCostGuardInputRow, ...],
    *,
    config: ResearchMarketSourceMemoryCostGuardConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketSourceMemoryCostGuardReport:
    return build_research_market_source_memory_cost_guard_report(
        rows,
        config=config or cfg(),
        generated_at=generated_at,
    )


def test_empty_input_returns_report_only_block_payload_with_valid_digest() -> None:
    guard_report = report(())
    payload = research_market_source_memory_cost_guard_public_payload(guard_report)

    assert type(guard_report) is ResearchMarketSourceMemoryCostGuardReport
    assert guard_report.generated_at == GENERATED_AT
    assert guard_report.status == "block"
    assert guard_report.item_count == d("0")
    assert guard_report.pass_count == d("0")
    assert guard_report.watch_count == d("0")
    assert guard_report.block_count == d("0")
    assert guard_report.total_memory_mb == d("0.000000")
    assert guard_report.total_cost_usd == d("0.000000")
    assert guard_report.reason_codes == ("no_items",)
    assert guard_report.reason_code_counts == (
        ResearchMarketSourceMemoryCostGuardReasonCodeCount(
            reason_code="no_items",
            count=d("1"),
        ),
    )
    assert guard_report.rows == ()
    assert guard_report.paper_only is True
    assert guard_report.report_only is True
    assert guard_report.readonly is True
    assert payload["validation_digest"] == guard_report.validation_digest
    assert validate_research_market_source_memory_cost_guard_payload_digest(payload)


def test_rows_statuses_totals_and_reason_counts_are_deterministic() -> None:
    guard_report = report(
        (
            item(HEX_C, memory_mb=d("140.000000"), cost_usd=d("0.040000")),
            item(HEX_A, memory_mb=d("32.000000"), cost_usd=d("0.020000")),
            item(HEX_B, memory_mb=d("72.000000"), cost_usd=d("0.080000")),
        ),
    )

    assert guard_report.status == "block"
    assert guard_report.item_count == d("3")
    assert guard_report.pass_count == d("0")
    assert guard_report.watch_count == d("0")
    assert guard_report.block_count == d("3")
    assert guard_report.total_memory_mb == d("244.000000")
    assert guard_report.total_cost_usd == d("0.140000")
    assert guard_report.peak_memory_mb == d("140.000000")
    assert guard_report.peak_cost_usd == d("0.080000")
    assert guard_report.average_memory_mb == d("81.333333")
    assert guard_report.average_cost_usd == d("0.046667")
    assert tuple(row.item_digest for row in guard_report.rows) == (HEX_A, HEX_B, HEX_C)
    assert tuple(row.status for row in guard_report.rows) == ("block", "block", "block")
    assert guard_report.rows[0].reason_codes == (
        "total_cost_watch",
        "total_memory_block",
        "usage_guard_block",
    )
    assert guard_report.rows[1].reason_codes == (
        "item_cost_watch",
        "item_memory_watch",
        "total_cost_watch",
        "total_memory_block",
        "usage_guard_block",
    )
    assert guard_report.rows[2].reason_codes == (
        "item_memory_block",
        "total_cost_watch",
        "total_memory_block",
        "usage_guard_block",
    )
    assert guard_report.reason_codes == (
        "item_cost_watch",
        "item_memory_block",
        "item_memory_watch",
        "total_cost_watch",
        "total_memory_block",
        "usage_guard_block",
    )
    assert tuple(
        (count.reason_code, count.count)
        for count in guard_report.reason_code_counts
    ) == (
        ("item_cost_watch", d("1")),
        ("item_memory_block", d("1")),
        ("item_memory_watch", d("1")),
        ("total_cost_watch", d("3")),
        ("total_memory_block", d("3")),
        ("usage_guard_block", d("3")),
    )


def test_public_payload_is_decimal_string_only_redacted_and_sha256_validated() -> None:
    guard_report = report(
        (
            item(
                HEX_B,
                memory_mb=d("72.000000"),
                cost_usd=d("0.080000"),
                reason_codes=("manual_review",),
            ),
            item(HEX_A, memory_mb=d("32.000000"), cost_usd=d("0.020000")),
        ),
    )
    payload = research_market_source_memory_cost_guard_public_payload(guard_report)
    payload_without_digest = dict(payload)
    validation_digest = payload_without_digest.pop("validation_digest")
    encoded_body = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    encoded_payload = json.dumps(payload, ensure_ascii=True, sort_keys=True)

    assert validation_digest == hashlib.sha256(
        encoded_body.encode("utf-8"),
    ).hexdigest()
    assert validate_research_market_source_memory_cost_guard_payload_digest(payload)
    assert payload["rows"][0]["memory_mb"] == "72.000000"
    assert payload["rows"][0]["cost_usd"] == "0.080000"
    assert not any(type(value) in (int, float) for value in _walk(payload))
    for unsafe in (
        "raw-candidate",
        "https://example.test/private",
        "postgres://hidden",
        "secret-token",
        "private table",
    ):
        assert unsafe not in encoded_payload
    for unsafe_key in ("candidate", "source_url", "text", "dsn", "table", "token"):
        assert unsafe_key not in encoded_payload

    tampered = dict(payload)
    tampered["total_cost_usd"] = "0.999999"
    assert not validate_research_market_source_memory_cost_guard_payload_digest(tampered)


def test_validation_rejects_non_decimal_values_raw_public_strings_times_and_flags() -> None:
    with pytest.raises(ValueError, match="item_pass_memory_mb"):
        cfg(item_pass_memory_mb=64)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="item_pass_cost_usd"):
        cfg(item_pass_cost_usd=0.05)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="item_block_memory_mb"):
        cfg(item_block_memory_mb=DecimalSubclass("128.000000"))
    with pytest.raises(ValueError, match="item_memory_mb"):
        cfg(item_pass_memory_mb=d("128.000000"), item_block_memory_mb=d("64.000000"))
    with pytest.raises(ValueError, match="config_version"):
        cfg(config_version="market-source-v0")
    with pytest.raises(ValueError, match="item_digest"):
        item(HEX_A.upper())
    with pytest.raises(ValueError, match="item_digest"):
        item("not-a-digest")
    with pytest.raises(ValueError, match="observed_at"):
        item(HEX_A, observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        item(HEX_A, observed_at=DatetimeSubclass(2026, 7, 9, 11, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        report((item(HEX_A),), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        report((item(HEX_A, observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="reason_codes"):
        item(HEX_A, reason_codes=("secret-token",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(item(HEX_A), paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(cfg(), readonly=False)


@pytest.mark.parametrize(
    "unsafe_reason_code",
    (
        "question",
        "slug",
        "wallet",
        "order",
        "trade",
        "execution",
        "sizing",
        "recommendation",
        "auth",
    ),
)
def test_public_reason_codes_reject_private_execution_surfaces(
    unsafe_reason_code: str,
) -> None:
    with pytest.raises(ValueError, match="reason_codes"):
        item(HEX_A, reason_codes=(unsafe_reason_code,))


@pytest.mark.parametrize(
    ("unsafe_key", "unsafe_value"),
    (
        ("wallet_surface", "paper"),
        ("order_surface", "paper"),
        ("trade_surface", "paper"),
        ("question", "paper"),
        ("slug", "paper"),
        ("public_note", "execution"),
        ("public_note", "sizing"),
        ("public_note", "recommendation"),
        ("public_note", "auth"),
    ),
)
def test_digest_valid_payload_validation_rejects_private_surfaces(
    unsafe_key: str,
    unsafe_value: str,
) -> None:
    guard_report = report((item(HEX_A),))
    payload = research_market_source_memory_cost_guard_public_payload(guard_report)
    payload_without_digest = dict(payload)
    payload_without_digest.pop("validation_digest")
    payload_without_digest[unsafe_key] = unsafe_value

    encoded_body = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    payload_without_digest["validation_digest"] = hashlib.sha256(
        encoded_body.encode("utf-8"),
    ).hexdigest()

    assert not validate_research_market_source_memory_cost_guard_payload_digest(
        payload_without_digest,
    )


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    guard_report = report((item(HEX_A),))
    reason_count = guard_report.reason_code_counts[0]

    with pytest.raises(FrozenInstanceError):
        guard_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        guard_report.rows[0].memory_mb = d("1.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        reason_count.count = d("2.000000")  # type: ignore[misc]
    assert reason_count.paper_only is True
    assert reason_count.report_only is True
    assert reason_count.readonly is True
    with pytest.raises(TypeError):
        class BadRow(ResearchMarketSourceMemoryCostGuardReportRow):
            pass
    with pytest.raises(ValueError, match="status"):
        replace(guard_report.rows[0], status="ready")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(guard_report.rows[0], status="pass", reason_codes=("usage_guard_block",))
    with pytest.raises(ValueError, match="status"):
        replace(guard_report, status="block")
    with pytest.raises(ValueError, match="validation_digest"):
        replace(guard_report, validation_digest="0" * 64)
    with pytest.raises(ValueError, match="paper_only"):
        replace(reason_count, paper_only=False)


def test_owned_module_has_no_live_or_private_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_source_memory_cost_guard_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "open(",
        "connect(",
        "wallet",
        "auth",
        "live trading",
        "sizing",
        "recommendation",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        values.extend(value.keys())
        for item_value in value.values():
            values.extend(_walk(item_value))
    elif isinstance(value, list):
        for item_value in value:
            values.extend(_walk(item_value))
    else:
        values.append(value)
    return tuple(values)
