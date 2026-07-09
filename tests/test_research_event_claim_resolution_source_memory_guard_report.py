from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_event_claim_resolution_source_memory_guard_report"
)
REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_claim_resolution_source_memory_guard_report.py"
)
CONFIG_VERSION = "research-event-claim-resolution-memory-guard-report-test"
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")

RAW_PRIVATE_VALUES = (
    "candidate-alpha-raw-id",
    "market-fed-cut-by-september",
    "will the fed cut rates by september?",
    "https://example.test/resolution-note?token=secret-alpha",
    "raw source text says the event resolved yes",
    "postgres://user:pass@example.test:5432/claims",
    "resolution_claims_private_table",
    "wallet-alpha order-alpha trade-alpha",
)


class DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": CONFIG_VERSION,
        "watch_guard_pressure_score": d("0.250000"),
        "block_guard_pressure_score": d("0.750000"),
        "minimum_evidence_record_count": d("2"),
        "conflict_weight": d("0.400000"),
        "stale_weight": d("0.200000"),
        "unverified_weight": d("0.200000"),
        "memory_gap_weight": d("0.200000"),
    }
    values.update(overrides)
    return module.ResearchEventClaimResolutionSourceMemoryGuardReportConfig(**values)


def claim(
    private_claim_ref: str = RAW_PRIVATE_VALUES[0],
    private_event_ref: str = RAW_PRIVATE_VALUES[1],
    *,
    observed_age_seconds: int = 3600,
    resolution_lag_seconds: int = 1800,
    memory_lag_seconds: int = 120,
    **overrides: object,
) -> Any:
    module = api()
    claim_observed_at = GENERATED_AT - timedelta(seconds=observed_age_seconds)
    resolution_observed_at = claim_observed_at + timedelta(seconds=resolution_lag_seconds)
    values: dict[str, object] = {
        "private_claim_ref": private_claim_ref,
        "private_event_ref": private_event_ref,
        "private_rule_ref": RAW_PRIVATE_VALUES[2],
        "private_evidence_locator": RAW_PRIVATE_VALUES[3],
        "private_evidence_excerpt": RAW_PRIVATE_VALUES[4],
        "private_store_locator": RAW_PRIVATE_VALUES[5],
        "private_set_name": RAW_PRIVATE_VALUES[6],
        "private_secret_marker": RAW_PRIVATE_VALUES[7],
        "claim_observed_at": claim_observed_at,
        "resolution_observed_at": resolution_observed_at,
        "memory_recorded_at": resolution_observed_at + timedelta(seconds=memory_lag_seconds),
        "evidence_record_count": d("4"),
        "confirmed_record_count": d("4"),
        "conflicting_record_count": d("0"),
        "stale_record_count": d("0"),
        "unverified_record_count": d("0"),
        "reason_codes": ("resolution_memory_reviewed",),
    }
    values.update(overrides)
    return module.ResearchEventClaimResolutionSourceMemoryGuardInput(**values)


def report(
    *items: Any,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_event_claim_resolution_source_memory_guard_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_public_numeric_scalars_are_strings(value: object) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected numeric scalar {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_scalars_are_strings(item)
    elif isinstance(value, list):
        for item in value:
            assert_public_numeric_scalars_are_strings(item)


def assert_no_raw_private_terms(value: object) -> None:
    blocked_terms = (
        "candidate",
        "market",
        "question",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live trading",
        "sizing",
        "recommendation",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            assert [term for term in blocked_terms if term in lowered] == []
            assert_no_raw_private_terms(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_raw_private_terms(item)
    elif isinstance(value, str):
        lowered = value.lower()
        assert [term for term in blocked_terms if term in lowered] == []


def assert_numeric_dataclass_fields_are_decimal(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if type(item) is bool or item is None:
            continue
        assert type(item) is not float
        assert type(item) is not int
        if isinstance(item, tuple):
            for nested in item:
                if is_dataclass(nested):
                    assert_numeric_dataclass_fields_are_decimal(nested)


def test_report_rolls_up_pass_watch_block_and_omits_raw_resolution_inputs() -> None:
    module = api()

    result = report(
        claim(
            "candidate-pass",
            "market-pass",
            evidence_record_count=d("4"),
            confirmed_record_count=d("4"),
            conflicting_record_count=d("0"),
            stale_record_count=d("0"),
            unverified_record_count=d("0"),
        ),
        claim(
            "candidate-watch",
            "market-watch",
            evidence_record_count=d("4"),
            confirmed_record_count=d("2"),
            conflicting_record_count=d("2"),
            stale_record_count=d("1"),
            unverified_record_count=d("1"),
        ),
        claim(
            "candidate-block",
            "market-block",
            evidence_record_count=d("1"),
            confirmed_record_count=d("0"),
            conflicting_record_count=d("1"),
            stale_record_count=d("1"),
            unverified_record_count=d("1"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == CONFIG_VERSION
    assert result.claim_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.conflict_claim_count == d("2")
    assert result.stale_claim_count == d("2")
    assert result.unverified_claim_count == d("2")
    assert result.memory_gap_claim_count == d("1")
    assert result.max_guard_pressure_score == d("0.900000")
    assert result.average_guard_pressure_score == d("0.400000")
    assert result.status == "block"
    assert result.reason_codes == (
        "resolution_memory_guard_report_block",
        "resolution_memory_guard_block",
        "resolution_memory_guard_watch",
        "resolution_memory_guard_pass",
        "evidence_conflict_present",
        "stale_memory_present",
        "unverified_memory_present",
        "memory_gap_present",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert module.STATUSES == ("pass", "watch", "block")
    assert_numeric_dataclass_fields_are_decimal(result)

    blocked, watched, passed = result.rows
    assert blocked.row_ref.startswith("recsmg-v0:")
    assert blocked.status == "block"
    assert blocked.confirmation_ratio == ZERO
    assert blocked.conflict_ratio == d("1.000000")
    assert blocked.stale_ratio == d("1.000000")
    assert blocked.unverified_ratio == d("1.000000")
    assert blocked.memory_gap_ratio == d("0.500000")
    assert blocked.guard_pressure_score == d("0.900000")

    assert watched.status == "watch"
    assert watched.confirmation_ratio == d("0.500000")
    assert watched.guard_pressure_score == d("0.300000")
    assert passed.status == "pass"
    assert passed.confirmation_ratio == d("1.000000")
    assert passed.guard_pressure_score == ZERO

    payload = module.research_event_claim_resolution_source_memory_guard_report_payload(
        result,
    )
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)
    assert_no_raw_private_terms(payload)
    for raw_value in RAW_PRIVATE_VALUES:
        assert raw_value not in encoded


def test_payload_is_stable_decimal_string_only_and_digest_checked() -> None:
    module = api()
    result = report(
        claim(
            "candidate-watch",
            "market-watch",
            evidence_record_count=d("4"),
            confirmed_record_count=d("2"),
            conflicting_record_count=d("2"),
            stale_record_count=d("1"),
            unverified_record_count=d("1"),
        ),
    )

    payload = module.research_event_claim_resolution_source_memory_guard_report_payload(
        result,
    )
    repeated_payload = (
        module.research_event_claim_resolution_source_memory_guard_report_payload(
            result,
        )
    )

    assert payload == repeated_payload
    assert json.dumps(payload, sort_keys=True, allow_nan=False) == json.dumps(
        repeated_payload,
        sort_keys=True,
        allow_nan=False,
    )
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["claim_count"] == "1"
    assert payload["rows"][0]["guard_pressure_score"] == "0.300000"
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["rows"][0]["derived_validation_digest"] == (
        result.rows[0].derived_validation_digest
    )
    assert payload["derived_validation_digest"].startswith("recsmg-v0:")
    assert payload["rows"][0]["derived_validation_digest"].startswith("recsmg-v0:")
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_public_numeric_scalars_are_strings(payload)
    assert_no_raw_private_terms(payload)
    assert (
        module.research_event_claim_resolution_source_memory_guard_report_payload(
            payload,
        )
        == payload
    )

    object.__setattr__(result.rows[0], "guard_pressure_score", d("0.010000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_event_claim_resolution_source_memory_guard_report_payload(
            result,
        )


def test_empty_report_is_block_readonly_and_decimal_zeroed() -> None:
    result = report()

    assert result.claim_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.max_guard_pressure_score == ZERO
    assert result.average_guard_pressure_score == ZERO
    assert result.status == "block"
    assert result.reason_codes == ("resolution_memory_guard_report_empty",)
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_public_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    cfg = config()
    sample = claim()
    result = report(sample)
    row = result.rows[0]

    for item in (cfg, sample, row, result):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.readonly = False  # type: ignore[misc]
        assert_numeric_dataclass_fields_are_decimal(item)

    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        claim(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        claim(readonly=False)
    with pytest.raises(ValueError, match="evidence_record_count must be a Decimal"):
        claim(evidence_record_count=1)
    with pytest.raises(ValueError, match="watch_guard_pressure_score must be a Decimal"):
        config(watch_guard_pressure_score=DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="six decimal places"):
        claim(stale_record_count=d("1.0000001"))
    with pytest.raises(ValueError, match="status"):
        replace(row, status="blocked")
    sorted_result = report(
        claim("candidate-alpha", "market-alpha"),
        claim(
            "candidate-zeta",
            "market-zeta",
            evidence_record_count=d("4"),
            confirmed_record_count=d("2"),
            conflicting_record_count=d("2"),
            stale_record_count=d("1"),
            unverified_record_count=d("1"),
        ),
    )
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(sorted_result, rows=tuple(reversed(sorted_result.rows)))


def test_datetime_count_shape_and_duplicate_inputs_are_rejected() -> None:
    module = api()

    with pytest.raises(ValueError, match="claim_observed_at must be timezone-aware"):
        claim(claim_observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_event_claim_resolution_source_memory_guard_report(
            (claim(),),
            config=config(),
            generated_at=datetime(2026, 7, 9, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="resolution_observed_at must not be before"):
        claim(resolution_observed_at=GENERATED_AT - timedelta(days=2))
    with pytest.raises(ValueError, match="memory_recorded_at must not be before"):
        claim(memory_recorded_at=GENERATED_AT - timedelta(days=2))
    with pytest.raises(ValueError, match="confirmed_record_count must not exceed"):
        claim(confirmed_record_count=d("5"))
    with pytest.raises(ValueError, match="claims must not contain duplicate"):
        report(claim("same-private-claim", "same-private-event"), claim("same-private-claim", "same-private-event"))


def test_payload_rejects_unsafe_public_leakage_and_no_runtime_surfaces() -> None:
    module = api()
    unsafe_public_terms = (
        "".join(parts)
        for parts in (
            ("can", "didate_id"),
            ("mar", "ket_slug"),
            ("mar", "ket_question"),
            ("sou", "rce_url"),
            ("raw_", "text"),
            ("d", "sn"),
            ("ta", "ble"),
            ("to", "ken"),
            ("wa", "llet"),
            ("or", "der"),
            ("tra", "de"),
            ("live", "_trading"),
            ("si", "zing"),
            ("recommen", "dation"),
        )
    )

    for term in unsafe_public_terms:
        with pytest.raises(ValueError, match="unsafe public"):
            module.research_event_claim_resolution_source_memory_guard_report_payload(
                {
                    term: "redacted",
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                },
            )
        with pytest.raises(ValueError, match="unsafe public"):
            module.research_event_claim_resolution_source_memory_guard_report_payload(
                {
                    "note": f"{term} leak",
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                },
            )

    parsed = ast.parse(MODULE_PATH.read_text())
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(parsed)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert imported_roots.isdisjoint(
        {
            "requests",
            "urllib",
            "httpx",
            "aiohttp",
            "socket",
            "sqlite3",
            "psycopg",
            "sqlalchemy",
            "web3",
            "eth_account",
            "clob",
        },
    )
