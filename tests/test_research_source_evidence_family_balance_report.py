from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_source_evidence_family_balance_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "fresh_age_seconds": d("3600.000000"),
        "stale_age_seconds": d("86400.000000"),
        "coverage_balance_watch_threshold": d("0.750000"),
        "coverage_balance_block_threshold": d("0.500000"),
        "freshness_watch_threshold": d("0.750000"),
        "freshness_block_threshold": d("0.500000"),
        "contradiction_watch_threshold": d("0.200000"),
        "contradiction_block_threshold": d("0.400000"),
        "stale_family_watch_ratio": d("0.250000"),
        "stale_family_block_ratio": d("0.500000"),
        "missing_family_block_count": d("2.000000"),
    }
    values.update(overrides)
    return module.ResearchSourceEvidenceFamilyBalanceConfig(**values)


def observation(
    evidence_family: str,
    *,
    observed_at: datetime | None = None,
    evidence_count: Decimal = d("1.000000"),
    contradiction_count: Decimal = d("0.000000"),
) -> Any:
    module = api()
    return module.ResearchSourceEvidenceFamilyBalanceObservation(
        evidence_family=evidence_family,
        observed_at=(
            observed_at if observed_at is not None else GENERATED_AT - timedelta(minutes=30)
        ),
        evidence_count=evidence_count,
        contradiction_count=contradiction_count,
    )


def report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_evidence_family_balance_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_empty_input_blocks_with_hard_flags_digest_and_public_status() -> None:
    module = api()
    balance_report = report()

    assert type(balance_report) is module.ResearchSourceEvidenceFamilyBalanceReport
    assert is_dataclass(balance_report)
    assert module.STATUSES == ("pass", "watch", "block")
    assert balance_report.generated_at == GENERATED_AT
    assert balance_report.status == "block"
    assert balance_report.required_family_count == d("4.000000")
    assert balance_report.covered_family_count == d("0.000000")
    assert balance_report.missing_family_count == d("4.000000")
    assert balance_report.evidence_count == d("0.000000")
    assert balance_report.coverage_balance_score == d("0.000000")
    assert balance_report.average_freshness_score == d("0.000000")
    assert balance_report.contradiction_pressure_score == d("0.000000")
    assert balance_report.family_rows == ()
    assert balance_report.reason_codes == (
        "evidence_family_balance_no_evidence",
    )
    assert len(balance_report.derived_validation_digest) == 64
    int(balance_report.derived_validation_digest, 16)
    assert balance_report.paper_only is True
    assert balance_report.report_only is True
    assert balance_report.readonly is True


def test_aggregates_sanitized_official_primary_news_data_family_balance() -> None:
    balance_report = report(
        observation("news", evidence_count=d("3.000000")),
        observation("official", evidence_count=d("3.000000")),
        observation("data", evidence_count=d("3.000000")),
        observation("primary", evidence_count=d("3.000000")),
    )

    assert balance_report.status == "pass"
    assert balance_report.required_family_count == d("4.000000")
    assert balance_report.covered_family_count == d("4.000000")
    assert balance_report.missing_family_count == d("0.000000")
    assert balance_report.evidence_count == d("12.000000")
    assert balance_report.contradiction_count == d("0.000000")
    assert balance_report.coverage_balance_score == d("1.000000")
    assert balance_report.average_freshness_score == d("1.000000")
    assert balance_report.contradiction_pressure_score == d("0.000000")
    assert balance_report.stale_family_ratio == d("0.000000")
    assert balance_report.reason_codes == (
        "evidence_family_balance_pass",
    )

    assert tuple(row.evidence_family for row in balance_report.family_rows) == (
        "official",
        "primary",
        "news",
        "data",
    )
    official = balance_report.family_rows[0]
    assert official.evidence_family == "official"
    assert official.evidence_count == d("3.000000")
    assert official.family_share == d("0.250000")
    assert official.latest_age_seconds == d("1800.000000")
    assert official.freshness_score == d("1.000000")
    assert official.contradiction_pressure_score == d("0.000000")
    assert official.status == "pass"
    assert official.reason_codes == ("evidence_family_balance_pass",)


def test_watch_and_block_statuses_are_threshold_driven() -> None:
    missing_family_report = report(
        observation("official", evidence_count=d("2.000000")),
        observation("primary", evidence_count=d("2.000000")),
        observation("news", evidence_count=d("2.000000")),
    )
    contradiction_report = report(
        observation(
            "official",
            evidence_count=d("2.000000"),
            contradiction_count=d("2.000000"),
        ),
        observation(
            "primary",
            evidence_count=d("2.000000"),
            contradiction_count=d("1.000000"),
        ),
        observation("news", evidence_count=d("2.000000")),
        observation(
            "data",
            evidence_count=d("2.000000"),
            contradiction_count=d("1.000000"),
        ),
    )

    assert missing_family_report.status == "watch"
    assert missing_family_report.covered_family_count == d("3.000000")
    assert missing_family_report.missing_family_count == d("1.000000")
    assert missing_family_report.coverage_balance_score == d("0.666667")
    assert missing_family_report.average_freshness_score == d("0.750000")
    assert missing_family_report.stale_family_ratio == d("0.250000")
    assert missing_family_report.reason_codes == (
        "evidence_family_balance_missing_family_watch",
        "evidence_family_balance_coverage_balance_watch",
        "evidence_family_balance_stale_family_watch",
    )

    assert contradiction_report.status == "block"
    assert contradiction_report.coverage_balance_score == d("1.000000")
    assert contradiction_report.contradiction_count == d("4.000000")
    assert contradiction_report.contradiction_pressure_score == d("0.500000")
    assert contradiction_report.reason_codes == (
        "evidence_family_balance_contradiction_pressure_block",
    )


def test_public_payload_is_deterministic_decimal_only_and_digest_validated() -> None:
    module = api()
    rows = (
        observation("news", evidence_count=d("3.000000")),
        observation("official", evidence_count=d("3.000000")),
        observation("data", evidence_count=d("3.000000")),
        observation("primary", evidence_count=d("3.000000")),
    )

    payload = module.research_source_evidence_family_balance_report_payload(
        report(*rows),
    )
    reversed_payload = module.research_source_evidence_family_balance_report_payload(
        report(*reversed(rows)),
    )

    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert module.validate_research_source_evidence_family_balance_report_payload(
        payload,
    )
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["family_rows"][0]["evidence_count"] == "3.000000"
    assert not any(type(value) in (float, int) for value in walk_payload_values(payload))

    rendered = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "https://",
        "http://",
        "url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "auth",
        "recommendation",
        "sizing",
    ):
        assert forbidden not in rendered

    tampered = dict(payload)
    tampered["status"] = "pass" if payload["status"] != "pass" else "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_source_evidence_family_balance_report_payload(tampered)

    bad_status = dict(payload)
    bad_status["status"] = "hold"
    bad_status["derived_validation_digest"] = canonical_digest(bad_status)
    with pytest.raises(ValueError, match="status"):
        module.validate_research_source_evidence_family_balance_report_payload(bad_status)

    bad_row_status = dict(payload)
    bad_rows = [dict(row) for row in payload["family_rows"]]
    bad_rows[0]["status"] = "hold"
    bad_row_status["family_rows"] = bad_rows
    bad_row_status["derived_validation_digest"] = canonical_digest(bad_row_status)
    with pytest.raises(ValueError, match="status"):
        module.validate_research_source_evidence_family_balance_report_payload(
            bad_row_status,
        )

    downgraded_row_flag = dict(payload)
    downgraded_rows = [dict(row) for row in payload["family_rows"]]
    downgraded_rows[0]["paper_only"] = False
    downgraded_row_flag["family_rows"] = downgraded_rows
    downgraded_row_flag["derived_validation_digest"] = canonical_digest(
        downgraded_row_flag,
    )
    with pytest.raises(ValueError, match="paper_only"):
        module.validate_research_source_evidence_family_balance_report_payload(
            downgraded_row_flag,
        )

    unsafe = dict(payload)
    unsafe["market_id"] = "raw-market-1"
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_source_evidence_family_balance_report_payload(unsafe)


def test_validation_rejects_bad_types_future_times_and_flag_downgrades() -> None:
    module = api()
    with pytest.raises(ValueError, match="fresh_age_seconds must be a Decimal"):
        config(fresh_age_seconds=3600)
    with pytest.raises(ValueError, match="coverage_balance_watch_threshold must be a Decimal"):
        config(coverage_balance_watch_threshold=_DecimalSubclass("0.750000"))
    with pytest.raises(ValueError, match="evidence_family"):
        observation("blog")
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation("official", observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at must not be in the future"):
        report(observation("official", observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="evidence_count must be a Decimal"):
        observation("official", evidence_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="contradiction_count must not exceed evidence_count"):
        observation(
            "official",
            evidence_count=d("1.000000"),
            contradiction_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation("official"), paper_only=False)
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_source_evidence_family_balance_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    balance_report = report(observation("official"))

    with pytest.raises(FrozenInstanceError):
        balance_report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        balance_report.family_rows[0].status = "block"
    with pytest.raises(ValueError, match="evidence_count"):
        replace(balance_report, evidence_count=d("99.000000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(balance_report, derived_validation_digest="0" * 64)


def test_module_scope_is_pure_report_only_without_execution_surfaces() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_EVIDENCE_FAMILY_BALANCE_CONFIG_VERSION",
        "STATUSES",
        "EVIDENCE_FAMILIES",
        "ResearchSourceEvidenceFamilyBalanceConfig",
        "ResearchSourceEvidenceFamilyBalanceObservation",
        "ResearchSourceEvidenceFamilyBalanceFamilyRow",
        "ResearchSourceEvidenceFamilyBalanceReport",
        "build_research_source_evidence_family_balance_report",
        "research_source_evidence_family_balance_report_payload",
        "validate_research_source_evidence_family_balance_report_payload",
    )

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "wallet",
        "private_key",
        "credential",
        "recommendation",
        "sizing",
        "trading",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
            }

    assert imported_modules <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }


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
