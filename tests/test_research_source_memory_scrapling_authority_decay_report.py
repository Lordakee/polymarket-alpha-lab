from __future__ import annotations

import ast
import hashlib
import importlib
import json
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_source_memory_scrapling_authority_decay_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_memory_scrapling_authority_decay_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "stale_after_seconds": d("3600.000000"),
        "blocked_after_seconds": d("7200.000000"),
        "watch_decay_score": d("0.400000"),
        "block_decay_score": d("0.700000"),
    }
    values.update(overrides)
    return module.ResearchSourceMemoryScraplingAuthorityDecayConfig(**values)


def signal(
    entry_key: str,
    *,
    group_key: str = "event_alpha",
    captured_seconds_ago: Decimal = d("900.000000"),
    confirmed_seconds_ago: Decimal | None = d("600.000000"),
    captured_at: datetime | None = None,
    last_confirmed_at: datetime | None = None,
    authority_score: Decimal = d("0.950000"),
    memory_confidence_score: Decimal = d("0.900000"),
    scrapling_quality_score: Decimal = d("0.950000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    if captured_at is None:
        captured_at = GENERATED_AT - _timedelta_from_decimal_seconds(
            captured_seconds_ago,
        )
    if last_confirmed_at is None and confirmed_seconds_ago is not None:
        last_confirmed_at = GENERATED_AT - _timedelta_from_decimal_seconds(
            confirmed_seconds_ago,
        )
    return module.ResearchSourceMemoryScraplingAuthorityDecaySignal(
        entry_key=entry_key,
        group_key=group_key,
        captured_at=captured_at,
        last_confirmed_at=last_confirmed_at,
        authority_score=authority_score,
        memory_confidence_score=memory_confidence_score,
        scrapling_quality_score=scrapling_quality_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_memory_scrapling_authority_decay_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def test_empty_report_is_frozen_report_only_decimal_and_digest_safe() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchSourceMemoryScraplingAuthorityDecayReport
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen is True
    assert report.generated_at == GENERATED_AT
    assert report.status == "pass"
    assert report.entry_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.stale_count == d("0.000000")
    assert report.missing_confirmation_count == d("0.000000")
    assert report.average_authority_decay_score == d("0.000000")
    assert report.max_authority_decay_score == d("0.000000")
    assert report.reason_codes == ("memory_scrapling_authority_decay_empty",)
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    payload = module.research_source_memory_scrapling_authority_decay_report_payload(
        report,
    )
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["entry_count"] == "0.000000"
    assert payload["status"] == "pass"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    module.validate_research_source_memory_scrapling_authority_decay_public_payload(
        payload,
    )
    json.dumps(payload, sort_keys=True)
    _assert_no_public_float_or_int(payload)


def test_status_rollups_rows_and_public_payload_are_deterministic() -> None:
    module = api()
    pass_item = signal("entry_pass")
    watch_item = signal(
        "entry_watch",
        captured_seconds_ago=d("5400.000000"),
        confirmed_seconds_ago=d("3000.000000"),
        authority_score=d("0.800000"),
        memory_confidence_score=d("0.750000"),
        scrapling_quality_score=d("0.700000"),
    )
    block_item = signal(
        "entry_block",
        captured_seconds_ago=d("9000.000000"),
        confirmed_seconds_ago=None,
        authority_score=d("0.700000"),
        memory_confidence_score=d("0.700000"),
        scrapling_quality_score=d("0.700000"),
    )

    report_a = build_report(watch_item, pass_item, block_item)
    report_b = build_report(block_item, watch_item, pass_item)

    assert report_a == report_b
    assert report_a.status == "block"
    assert report_a.reason_codes == (
        "memory_scrapling_capture_stale",
        "memory_scrapling_capture_block_stale",
        "memory_scrapling_confirmation_missing",
    )
    assert report_a.entry_count == d("3.000000")
    assert report_a.pass_count == d("1.000000")
    assert report_a.watch_count == d("1.000000")
    assert report_a.block_count == d("1.000000")
    assert report_a.stale_count == d("2.000000")
    assert report_a.missing_confirmation_count == d("1.000000")

    assert tuple(row.entry_key for row in report_a.rows) == (
        "entry_block",
        "entry_watch",
        "entry_pass",
    )
    assert tuple(row.status for row in report_a.rows) == ("block", "watch", "pass")
    assert tuple(row.capture_age_seconds for row in report_a.rows) == (
        d("9000.000000"),
        d("5400.000000"),
        d("900.000000"),
    )
    assert tuple(row.confirmation_age_seconds for row in report_a.rows) == (
        d("0.000000"),
        d("3000.000000"),
        d("600.000000"),
    )

    payload = module.research_source_memory_scrapling_authority_decay_report_payload(
        report_a,
    )
    without_digest = dict(payload)
    without_digest.pop("derived_validation_digest")
    expected_digest = hashlib.sha256(
        json.dumps(without_digest, sort_keys=True, separators=(",", ":")).encode(),
    ).hexdigest()
    assert payload["derived_validation_digest"] == expected_digest
    assert payload == module.research_source_memory_scrapling_authority_decay_report_payload(
        report_b,
    )
    _assert_public_payload_has_no_raw_leaks(payload)


def test_dataclasses_are_frozen_exact_decimal_only_and_flags_are_hard() -> None:
    module = api()
    report = build_report(signal("entry_pass"), signal("entry_watch"))

    for cls in (
        module.ResearchSourceMemoryScraplingAuthorityDecayConfig,
        module.ResearchSourceMemoryScraplingAuthorityDecaySignal,
        module.ResearchSourceMemoryScraplingAuthorityDecayRow,
        module.ResearchSourceMemoryScraplingAuthorityDecayReport,
    ):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True

    _assert_decimal_public_fields(report)
    for row in report.rows:
        _assert_decimal_public_fields(row)

    with pytest.raises(ValueError, match="stale_after_seconds"):
        config(stale_after_seconds=3600)
    with pytest.raises(ValueError, match="blocked_after_seconds"):
        config(blocked_after_seconds=_DecimalSubclass("7200.000000"))
    with pytest.raises(ValueError, match="authority_score"):
        signal("entry_bad_authority", authority_score=d("1.100000"))
    with pytest.raises(ValueError, match="memory_confidence_score"):
        signal("entry_bad_memory", memory_confidence_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        signal("entry_flag_case", paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_status_vocabulary_datetime_validation_and_unsafe_input_rejection() -> None:
    module = api()
    offset = timezone(timedelta(hours=-4))
    normalized = signal(
        "entry_offset",
        captured_at=datetime(2026, 7, 9, 7, 0, tzinfo=offset),
        last_confirmed_at=datetime(2026, 7, 9, 7, 30, tzinfo=offset),
    )

    assert normalized.captured_at == datetime(2026, 7, 9, 11, 0, tzinfo=UTC)
    assert normalized.last_confirmed_at == datetime(2026, 7, 9, 11, 30, tzinfo=UTC)
    assert build_report(normalized).rows[0].capture_age_seconds == d("3600.000000")

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_source_memory_scrapling_authority_decay_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 9, 12, 0),
        )
    with pytest.raises(ValueError, match="captured_at must be timezone-aware"):
        signal("entry_naive", captured_at=datetime(2026, 7, 9, 11, 0))
    with pytest.raises(ValueError, match="future"):
        build_report(
            signal(
                "entry_future",
                captured_at=GENERATED_AT + timedelta(seconds=1),
                last_confirmed_at=GENERATED_AT,
            ),
        )
    with pytest.raises(ValueError, match="status"):
        replace(build_report(), status="ready")
    with pytest.raises(ValueError, match="entry_key"):
        signal("candidate-election-alpha")
    with pytest.raises(ValueError, match="group_key"):
        signal("entry_safe", group_key="market-politics")
    with pytest.raises(ValueError, match="entry_key"):
        signal("https://example.invalid/path?token=secret")


def test_public_payload_validation_catches_tampering_and_raw_leak_shapes() -> None:
    module = api()
    report = build_report(signal("entry_pass"))
    payload = module.research_source_memory_scrapling_authority_decay_report_payload(
        report,
    )

    tampered_digest = dict(payload)
    tampered_digest["pass_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_source_memory_scrapling_authority_decay_public_payload(
            tampered_digest,
        )

    numeric_payload = dict(payload)
    numeric_payload["pass_count"] = 1
    with pytest.raises(ValueError, match="Decimal-derived strings"):
        module.validate_research_source_memory_scrapling_authority_decay_public_payload(
            numeric_payload,
        )

    invalid_status_payload = dict(payload)
    invalid_status_payload["status"] = "ready"
    invalid_status_without_digest = dict(invalid_status_payload)
    invalid_status_without_digest.pop("derived_validation_digest")
    invalid_status_payload["derived_validation_digest"] = hashlib.sha256(
        json.dumps(
            invalid_status_without_digest,
            sort_keys=True,
            separators=(",", ":"),
        ).encode(),
    ).hexdigest()
    with pytest.raises(ValueError, match="status"):
        module.validate_research_source_memory_scrapling_authority_decay_public_payload(
            invalid_status_payload,
        )

    raw_payload = dict(payload)
    raw_payload["rows"] = [
        {
            "entry_key": "candidate-alpha",
            "raw_url": "https://example.invalid?token=secret",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    with pytest.raises(ValueError, match="unsafe public"):
        module.validate_research_source_memory_scrapling_authority_decay_public_payload(
            raw_payload,
        )


def test_module_is_report_only_without_forbidden_runtime_surfaces() -> None:
    source = MODULE_PATH.read_text()
    tree = ast.parse(source)

    forbidden_import_roots = {
        "requests",
        "socket",
        "httpx",
        "urllib",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "web3",
    }
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".")[0])
    assert imported_roots.isdisjoint(forbidden_import_roots)

    lowered = source.lower()
    forbidden_runtime_words = (
        "db",
        "network",
        "wallet",
        "auth",
        "order",
        "live",
        "trading",
        "sizing",
        "recommendation",
    )
    for word in forbidden_runtime_words:
        if word == "auth":
            pattern = r"(?<!authority_)\bauth\b"
        else:
            pattern = rf"\b{re.escape(word)}\b"
        assert re.search(pattern, lowered) is None


def _assert_decimal_public_fields(value: Any) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if isinstance(item, Decimal):
            assert type(item) is Decimal


def _timedelta_from_decimal_seconds(value: Decimal) -> timedelta:
    return timedelta(microseconds=int(value * d("1000000")))


def _assert_no_public_float_or_int(value: Any) -> None:
    if isinstance(value, bool):
        return
    assert not isinstance(value, (float, int))
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_public_float_or_int(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_public_float_or_int(item)


def _assert_public_payload_has_no_raw_leaks(payload: dict[str, Any]) -> None:
    encoded = json.dumps(payload, sort_keys=True).lower()
    forbidden_fragments = (
        "candidate",
        "market",
        "raw_url",
        "raw_text",
        "dsn",
        "table",
        "token",
        "https://",
        "http://",
    )
    for fragment in forbidden_fragments:
        assert fragment not in encoded
    _assert_no_public_float_or_int(payload)
