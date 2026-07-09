from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path
import re
from typing import Any

import pytest

import polymarket_alpha_lab.research_event_resolution_authority_memory_gap_report as api
from polymarket_alpha_lab.research_event_resolution_authority_memory_gap_report import (
    ResearchEventResolutionAuthorityMemoryGapConfig,
    ResearchEventResolutionAuthorityMemoryGapInput,
    ResearchEventResolutionAuthorityMemoryGapReport,
    ResearchEventResolutionAuthorityMemoryGapReportRow,
    build_research_event_resolution_authority_memory_gap_report,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchEventResolutionAuthorityMemoryGapConfig:
    values = {
        "config_version": (
            api.DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_MEMORY_GAP_REPORT_CONFIG_VERSION
        ),
        "fresh_age_seconds": d("3600.000000"),
        "stale_age_seconds": d("86400.000000"),
        "watch_gap_score": d("0.350000"),
        "block_gap_score": d("0.700000"),
        "min_authority_memory_count": d("1.000000"),
        "min_resolution_record_count": d("1.000000"),
    }
    values.update(overrides)
    return ResearchEventResolutionAuthorityMemoryGapConfig(**values)


def event_input(
    index: int,
    *,
    event_id: str | None = None,
    authority_id: str = "resolution-authority",
    private_resolution_fragments: tuple[str, ...] = (
        "candidate://raw-yes-outcome",
        "market://raw-polymarket-condition",
        "https://example.invalid/raw-source?token=secret",
        "original source text with dsn table token material",
        "postgres://user:pass@example.invalid:5432/raw",
        "raw_schema.raw_table",
        "token-secret-value",
    ),
    observed_at: datetime | None = None,
    authority_memory_count: Decimal = d("1.000000"),
    parser_memory_count: Decimal = d("1.000000"),
    resolution_record_count: Decimal = d("1.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchEventResolutionAuthorityMemoryGapInput:
    return ResearchEventResolutionAuthorityMemoryGapInput(
        event_id=event_id or f"event-{index:03d}",
        authority_id=authority_id,
        private_resolution_fragments=private_resolution_fragments,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        authority_memory_count=authority_memory_count,
        parser_memory_count=parser_memory_count,
        resolution_record_count=resolution_record_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[ResearchEventResolutionAuthorityMemoryGapInput, ...],
    *,
    cfg: ResearchEventResolutionAuthorityMemoryGapConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchEventResolutionAuthorityMemoryGapReport:
    return build_research_event_resolution_authority_memory_gap_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_public_payload_is_deterministic_digest_validated_and_redacted() -> None:
    private_fragments = (
        "candidate://condition-raw-outcome",
        "market://condition-will-resolve-raw",
        "https://example.invalid/source/path?token=top-secret",
        "raw source text mentioning dsn table and token",
        "postgres://user:pass@example.invalid:5432/raw",
        "private_schema.private_table",
        "token-super-secret",
    )
    gap_report = report(
        (
            event_input(
                1,
                private_resolution_fragments=private_fragments,
                resolution_record_count=d("2.000000"),
            ),
        ),
    )

    payload = gap_report.payload
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == gap_report.payload
    assert payload["derived_validation_digest"] == gap_report.derived_validation_digest
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    assert gap_report.status == "pass"
    assert gap_report.paper_only is True
    assert gap_report.report_only is True
    assert gap_report.readonly is True
    assert payload["rows"][0]["evidence_fingerprint"].startswith("sha256:")
    assert len(payload["rows"][0]["evidence_fingerprint"]) == len("sha256:") + 64
    assert payload["rows"][0]["memory_gap_score"] == "0.020833"
    assert not any(isinstance(value, float) for value in walk_payload_values(payload))
    assert not any(
        type(value) is int and not isinstance(value, bool)
        for value in walk_payload_values(payload)
    )
    for fragment in private_fragments:
        assert fragment not in encoded
    for raw_key in ("candidate", "market", "source", "url", "text", "dsn", "table", "token"):
        assert not any(raw_key in key_path.lower() for key_path in walk_payload_key_paths(payload))


def test_statuses_are_only_pass_watch_and_block_with_decimal_counts() -> None:
    gap_report = report(
        (
            event_input(
                3,
                event_id="event-block",
                authority_memory_count=d("0.000000"),
                parser_memory_count=d("0.000000"),
                resolution_record_count=d("0.000000"),
            ),
            event_input(
                1,
                event_id="event-pass",
                resolution_record_count=d("2.000000"),
            ),
            event_input(
                2,
                event_id="event-watch",
                parser_memory_count=d("0.000000"),
                resolution_record_count=d("0.000000"),
            ),
        ),
    )

    assert tuple(row.event_id for row in gap_report.rows) == (
        "event-block",
        "event-pass",
        "event-watch",
    )
    assert tuple(row.status for row in gap_report.rows) == ("block", "pass", "watch")
    assert {row.status for row in gap_report.rows} <= {"pass", "watch", "block"}
    assert gap_report.status == "block"
    assert gap_report.event_count == d("3.000000")
    assert gap_report.pass_count == d("1.000000")
    assert gap_report.watch_count == d("1.000000")
    assert gap_report.block_count == d("1.000000")
    assert gap_report.average_memory_gap_score == d("0.562500")
    assert tuple(row.memory_gap_score for row in gap_report.rows) == (
        d("1.000000"),
        d("0.020833"),
        d("0.666667"),
    )
    assert not any(
        isinstance(value, float) or type(value) is int
        for value in walk_public_dataclass_values(gap_report)
    )


def test_empty_input_returns_block_report_without_numeric_literals() -> None:
    gap_report = report(())
    payload = gap_report.payload

    assert gap_report.status == "block"
    assert gap_report.rows == ()
    assert gap_report.event_count == d("0.000000")
    assert gap_report.average_memory_gap_score == d("0.000000")
    assert gap_report.reason_codes == ("no_event_resolution_evidence",)
    assert payload["status"] == "block"
    assert payload["event_count"] == "0.000000"
    assert not any(isinstance(value, float) for value in walk_payload_values(payload))
    assert not any(
        type(value) is int and not isinstance(value, bool)
        for value in walk_payload_values(payload)
    )


def test_validation_rejects_non_decimals_bad_states_flags_and_digest_tampering() -> None:
    with pytest.raises(ValueError, match="watch_gap_score"):
        config(watch_gap_score=DecimalSubclass("0.350000"))
    with pytest.raises(ValueError, match="authority_memory_count"):
        event_input(1, authority_memory_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at"):
        event_input(1, observed_at=datetime(2026, 7, 9, 11, 30))
    with pytest.raises(ValueError, match="paper_only"):
        event_input(1, paper_only=False)
    with pytest.raises(ValueError, match="status"):
        replace(report((event_input(1),)).rows[0], status="blocked")

    gap_report = report((event_input(1), event_input(2)))
    with pytest.raises(FrozenInstanceError):
        gap_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(gap_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            gap_report,
            rows=(
                replace(
                    gap_report.rows[0],
                    memory_gap_score=d("0.400000"),
                    status="watch",
                    reason_codes=("event_resolution_authority_memory_watch",),
                ),
                gap_report.rows[1],
            ),
        )


def test_public_payload_rejects_slug_question_wallet_order_and_trade_terms() -> None:
    for raw_term in ("slug", "question", "wallet", "order", "trade"):
        with pytest.raises(ValueError, match="leaks raw private context"):
            report((event_input(1, event_id=f"event-{raw_term}-raw"),))


def test_public_dataclasses_and_module_have_no_disallowed_runtime_surface() -> None:
    for cls in (
        ResearchEventResolutionAuthorityMemoryGapConfig,
        ResearchEventResolutionAuthorityMemoryGapInput,
        ResearchEventResolutionAuthorityMemoryGapReportRow,
        ResearchEventResolutionAuthorityMemoryGapReport,
    ):
        for field in fields(cls):
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            assert not re.fullmatch(r"db|network|wallet|auth|order", field.name.lower())

    for public_name in api.__all__:
        assert not re.search(r"\b(db|network|wallet|auth|order)\b", public_name.lower())

    source = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_event_resolution_authority_memory_gap_report.py"
    ).read_text(encoding="utf-8")
    lowered_source = source.lower()
    for forbidden_pattern in (
        r"\bdb\b",
        r"\bnetwork\b",
        r"\bwallet\b",
        r"\bauth\b",
        r"\border\b",
        r"\blive\s+trading\b",
        r"\bsizing\b",
        r"\brecommendation\b",
        r"\brequests\b",
        r"\bhttpx\b",
        r"\burllib\b",
        r"\bsocket\b",
        r"\bsqlite3\b",
        r"\bsqlalchemy\b",
        r"\bpsycopg\b",
        r"\bweb3\b",
        r"\bccxt\b",
    ):
        assert not re.search(forbidden_pattern, lowered_source)


def walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)


def walk_payload_key_paths(value: object, prefix: str = "") -> tuple[str, ...]:
    paths: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else key
            paths.append(path)
            paths.extend(walk_payload_key_paths(item, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            paths.extend(walk_payload_key_paths(item, f"{prefix}[{index}]"))
    return tuple(paths)


def walk_public_dataclass_values(value: Any) -> tuple[object, ...]:
    values: list[object] = []
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            values.extend(walk_public_dataclass_values(getattr(value, field.name)))
    elif isinstance(value, tuple):
        for item in value:
            values.extend(walk_public_dataclass_values(item))
    else:
        values.append(value)
    return tuple(values)
