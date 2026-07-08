from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_source_evidence_lineage_gap_queue_report.py",
)
FORBIDDEN_PUBLIC_FRAGMENTS = (
    "candidate_id",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "url",
    "text",
    "postgres://",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_source_evidence_lineage_gap_queue_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def observation(
    evidence_label: str = "evidence_alpha",
    *,
    source_authority_score: Decimal = d("0.950000"),
    lineage_completeness_score: Decimal = d("0.950000"),
    latest_evidence_at: datetime = GENERATED_AT - timedelta(hours=2),
    contradiction_pressure: Decimal = d("0.050000"),
    extraction_confidence: Decimal = d("0.950000"),
    missing_field_count: Decimal = d("0"),
    required_field_count: Decimal = d("4"),
    deadline_at: datetime = GENERATED_AT + timedelta(hours=96),
    **overrides: object,
) -> Any:
    values = {
        "evidence_label": evidence_label,
        "source_authority_score": source_authority_score,
        "lineage_completeness_score": lineage_completeness_score,
        "latest_evidence_at": latest_evidence_at,
        "contradiction_pressure": contradiction_pressure,
        "extraction_confidence": extraction_confidence,
        "missing_field_count": missing_field_count,
        "required_field_count": required_field_count,
        "deadline_at": deadline_at,
    }
    values.update(overrides)
    return api().ResearchSourceEvidenceLineageGapObservation(**values)


def build_report(*items: object, cfg: object | None = None) -> Any:
    module = api()
    return module.build_research_source_evidence_lineage_gap_queue_report(
        items,
        config=(
            module.ResearchSourceEvidenceLineageGapQueueConfig()
            if cfg is None
            else cfg
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def test_lineage_gap_queue_scores_ranks_and_digest_validates() -> None:
    passing = observation("evidence_pass")
    watching = observation(
        "evidence_watch",
        source_authority_score=d("0.600000"),
        lineage_completeness_score=d("0.650000"),
        latest_evidence_at=GENERATED_AT - timedelta(hours=36),
        contradiction_pressure=d("0.300000"),
        extraction_confidence=d("0.650000"),
        missing_field_count=d("1"),
        required_field_count=d("4"),
        deadline_at=GENERATED_AT + timedelta(hours=24),
    )
    blocking = observation(
        "evidence_block",
        source_authority_score=d("0.200000"),
        lineage_completeness_score=d("0.100000"),
        latest_evidence_at=GENERATED_AT - timedelta(hours=72),
        contradiction_pressure=d("0.900000"),
        extraction_confidence=d("0.200000"),
        missing_field_count=d("4"),
        required_field_count=d("4"),
        deadline_at=GENERATED_AT + timedelta(hours=6),
    )

    report = build_report(passing, watching, blocking)
    reversed_report = build_report(blocking, watching, passing)

    assert api().SOURCE_EVIDENCE_LINEAGE_GAP_QUEUE_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.queue_item_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_lineage_gap_score == d("0.430833")
    assert report.max_lineage_gap_score == d("0.855000")
    assert report.average_source_authority_gap_score == d("0.416667")
    assert report.average_lineage_completeness_gap_score == d("0.433333")
    assert report.average_freshness_gap_score == d("0.381944")
    assert report.average_contradiction_pressure == d("0.416667")
    assert report.average_extraction_confidence_gap_score == d("0.400000")
    assert report.average_missing_field_gap_score == d("0.416667")
    assert report.average_deadline_proximity_score == d("0.493056")

    assert tuple(row.evidence_label for row in report.rows) == (
        "evidence_block",
        "evidence_watch",
        "evidence_pass",
    )
    by_label = {row.evidence_label: row for row in report.rows}
    assert by_label["evidence_block"].queue_status == "block"
    assert by_label["evidence_block"].lineage_gap_score == d("0.855000")
    assert by_label["evidence_block"].reason_codes == (
        "source_authority_gap",
        "lineage_completeness_gap",
        "freshness_gap",
        "contradiction_pressure",
        "extraction_confidence_gap",
        "missing_field_gap",
        "deadline_proximity_pressure",
        "source_evidence_lineage_gap_block",
    )
    assert by_label["evidence_watch"].queue_status == "watch"
    assert by_label["evidence_watch"].lineage_gap_score == d("0.400000")
    assert by_label["evidence_pass"].queue_status == "pass"
    assert by_label["evidence_pass"].lineage_gap_score == d("0.037500")
    assert by_label["evidence_pass"].reason_codes == (
        "source_evidence_lineage_gap_pass",
    )

    payload = api().research_source_evidence_lineage_gap_queue_report_payload(report)
    reversed_payload = (
        api().research_source_evidence_lineage_gap_queue_report_payload(
            reversed_report,
        )
    )
    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert (
        api().research_source_evidence_lineage_gap_queue_report_digest(report)
        == payload["derived_validation_digest"]
    )
    assert payload["queue_item_count"] == "3.000000"
    assert payload["rows"][0]["lineage_gap_score"] == "0.855000"
    assert _float_paths(payload) == ()
    assert _unsafe_public_paths(payload) == ()
    json.dumps(payload, sort_keys=True, separators=(",", ":"))


def test_custom_config_drives_row_validation_and_status_boundaries() -> None:
    module = api()
    cfg = module.ResearchSourceEvidenceLineageGapQueueConfig(
        watch_score_threshold=d("0.500000"),
        block_score_threshold=d("0.800000"),
    )
    report = build_report(
        observation(
            "evidence_custom_watch",
            source_authority_score=d("0.200000"),
            lineage_completeness_score=d("0.200000"),
            latest_evidence_at=GENERATED_AT - timedelta(hours=48),
            contradiction_pressure=d("0.600000"),
            extraction_confidence=d("0.400000"),
            missing_field_count=d("2"),
            required_field_count=d("4"),
            deadline_at=GENERATED_AT + timedelta(hours=10),
        ),
        cfg=cfg,
    )

    assert report.rows[0].lineage_gap_score == d("0.737083")
    assert report.rows[0].queue_status == "watch"
    assert report.status == "watch"


def test_fractional_hour_windows_are_valid_report_inputs() -> None:
    report = build_report(
        observation(
            "evidence_fractional_hours",
            latest_evidence_at=GENERATED_AT - timedelta(hours=1, minutes=30),
            deadline_at=GENERATED_AT + timedelta(hours=2, minutes=15),
        ),
    )

    assert report.rows[0].evidence_age_hours == d("1.500000")
    assert report.rows[0].deadline_proximity_hours == d("2.250000")


def test_empty_queue_is_report_only_pass_with_stable_payload() -> None:
    report = build_report()

    assert report.status == "pass"
    assert report.queue_item_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.average_lineage_gap_score == d("0.000000")
    assert report.max_lineage_gap_score == d("0.000000")
    assert report.reason_codes == ("source_evidence_lineage_gap_report_pass",)
    assert report.reason_code_counts == ()
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.payload["derived_validation_digest"] == canonical_digest(report.payload)


def test_frozen_dataclasses_decimal_only_exact_types_and_flags() -> None:
    module = api()
    report = build_report(observation("evidence_exact"))

    for value in (
        module.ResearchSourceEvidenceLineageGapQueueConfig(),
        observation("evidence_observation_exact"),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    ):
        assert is_dataclass(value)
        for flag_name in ("paper_only", "report_only", "readonly"):
            assert getattr(value, flag_name) is True
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    for cls in (
        module.ResearchSourceEvidenceLineageGapQueueConfig,
        module.ResearchSourceEvidenceLineageGapObservation,
        module.ResearchSourceEvidenceLineageGapQueueRow,
        module.ResearchSourceEvidenceLineageGapQueueReasonCodeCount,
        module.ResearchSourceEvidenceLineageGapQueueReport,
    ):
        field_names = {field.name for field in fields(cls)}
        assert {"paper_only", "report_only", "readonly"} <= field_names

    with pytest.raises(TypeError):

        class BadObservation(module.ResearchSourceEvidenceLineageGapObservation):
            pass

    with pytest.raises(ValueError, match="source_authority_score"):
        observation("evidence_bad_float", source_authority_score=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="extraction_confidence"):
        observation(
            "evidence_bad_decimal_subclass",
            extraction_confidence=_DecimalSubclass("0.500000"),
        )
    with pytest.raises(ValueError, match="missing_field_count"):
        observation("evidence_bad_missing", missing_field_count=d("1.500000"))
    with pytest.raises(ValueError, match="latest_evidence_at"):
        observation(
            "evidence_bad_datetime",
            latest_evidence_at=_DateTimeSubclass(2026, 7, 8, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="paper_only"):
        module.ResearchSourceEvidenceLineageGapQueueConfig(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_validation_rejects_unsafe_public_surfaces_and_payload_tampering() -> None:
    module = api()
    report = build_report(observation("evidence_safe"))
    payload = module.research_source_evidence_lineage_gap_queue_report_payload(report)

    for bad_label in (
        "candidate_id_alpha",
        "market_id_alpha",
        "market_slug_alpha",
        "slug_alpha",
        "question_alpha",
        "url_alpha",
        "wallet_alpha",
        "order_alpha",
        "trade_alpha",
        "live_alpha",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            observation(bad_label)

    with pytest.raises(ValueError, match="latest_evidence_at"):
        build_report(
            observation(
                "evidence_future",
                latest_evidence_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="unique"):
        build_report(observation("evidence_dup"), observation("evidence_dup"))
    with pytest.raises(ValueError, match="missing_field_count"):
        observation(
            "evidence_too_many_missing",
            missing_field_count=d("5"),
            required_field_count=d("4"),
        )
    with pytest.raises(ValueError, match="block_score_threshold"):
        module.ResearchSourceEvidenceLineageGapQueueConfig(
            watch_score_threshold=d("0.700000"),
            block_score_threshold=d("0.700000"),
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    tampered_status = dict(payload)
    tampered_status["status"] = "blocked"
    tampered_status["derived_validation_digest"] = canonical_digest(tampered_status)
    with pytest.raises(ValueError, match="status"):
        module.research_source_evidence_lineage_gap_queue_report_payload(
            tampered_status,
        )

    leaked = dict(payload)
    leaked["candidate_id"] = "candidate_alpha"
    leaked["derived_validation_digest"] = canonical_digest(leaked)
    with pytest.raises(ValueError, match="unsafe"):
        module.research_source_evidence_lineage_gap_queue_report_payload(leaked)

    numeric = dict(payload)
    numeric["queue_item_count"] = 3
    numeric["derived_validation_digest"] = canonical_digest(numeric)
    with pytest.raises(ValueError, match="Decimal"):
        module.research_source_evidence_lineage_gap_queue_report_payload(numeric)


def test_module_imports_no_db_network_or_scraping_dependencies() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_roots = {
        "bs4",
        "httpx",
        "playwright",
        "psycopg",
        "requests",
        "scrapy",
        "selenium",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "urllib",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_roots
        elif isinstance(node, ast.ImportFrom):
            assert node.module is not None
            assert node.module.split(".", 1)[0] not in forbidden_roots


def _float_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if isinstance(value, float):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_float_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_float_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()


def _unsafe_public_paths(value: object, path: str = "$") -> tuple[str, ...]:
    paths: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in FORBIDDEN_PUBLIC_FRAGMENTS):
                paths.append(f"{path}.{key}")
            paths.extend(_unsafe_public_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        for index, item in enumerate(value):
            paths.extend(_unsafe_public_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    if isinstance(value, str):
        lowered_value = value.lower()
        if any(fragment in lowered_value for fragment in FORBIDDEN_PUBLIC_FRAGMENTS):
            paths.append(path)
    return tuple(paths)
