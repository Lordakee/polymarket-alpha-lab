import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=timezone.utc)


class DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_source_family_coverage_gap_v2",
    )


def observed_at(hours_old: int) -> datetime:
    return GENERATED_AT - timedelta(hours=hours_old)


def evidence(
    source_id: str,
    family: str,
    family_kind: str,
    *,
    hours_old: int = 1,
    independence_key: str | None = None,
):
    module = api()
    return module.ResearchPacketSourceFamilyCoverageEvidenceV2(
        source_id=source_id,
        source_family=family,
        source_family_kind=family_kind,
        observed_at=observed_at(hours_old),
        independence_key=independence_key or source_id,
    )


def subject(
    packet_id: str,
    category: str,
    archetype: str,
    *,
    required_official_source_families: tuple[str, ...] = ("official-release",),
    required_primary_source_families: tuple[str, ...] = ("primary-data",),
    required_secondary_source_families: tuple[str, ...] = ("secondary-context",),
    required_contradiction_source_families: tuple[str, ...] = ("contradiction-check",),
    observed_source_families: tuple[object, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchPacketSourceFamilyCoverageSubjectV2(
        packet_id=packet_id,
        category=category,
        archetype=archetype,
        required_official_source_families=required_official_source_families,
        required_primary_source_families=required_primary_source_families,
        required_secondary_source_families=required_secondary_source_families,
        required_contradiction_source_families=required_contradiction_source_families,
        observed_source_families=observed_source_families,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*subjects: object, generated_at: datetime = GENERATED_AT, **overrides: object):
    module = api()
    config = module.ResearchPacketSourceFamilyCoverageGapV2Config(**overrides)
    return module.build_research_packet_source_family_coverage_gap_v2_report(
        subjects,
        generated_at=generated_at,
        config=config,
    )


def contains_float(value: object) -> bool:
    if type(value) is float:
        return True
    if isinstance(value, dict):
        return any(contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_float(item) for item in value)
    return False


def test_scores_source_family_coverage_gaps_by_category_and_archetype() -> None:
    complete = subject(
        "packet-complete",
        "macro",
        "rate-decision",
        observed_source_families=(
            evidence("fed", "official-release", "official", independence_key="fed"),
            evidence("bls", "primary-data", "primary", independence_key="bls"),
            evidence(
                "wire",
                "secondary-context",
                "secondary",
                independence_key="wire",
            ),
            evidence(
                "odds",
                "contradiction-check",
                "contradiction",
                independence_key="odds",
            ),
        ),
    )
    gapped = subject(
        "packet-gapped",
        "sports",
        "injury-report",
        observed_source_families=(
            evidence(
                "league-old",
                "official-release",
                "official",
                hours_old=36,
                independence_key="league",
            ),
            evidence(
                "beat",
                "secondary-context",
                "secondary",
                independence_key="league",
            ),
        ),
    )

    result = report(gapped, complete)

    assert is_dataclass(result)
    assert result.status == "blocked"
    assert result.row_count == d("2.000000")
    assert result.covered_row_count == d("1.000000")
    assert result.blocked_row_count == d("1.000000")
    assert result.max_coverage_gap_score == d("0.569445")
    assert result.reason_codes == ("blocked_source_family_coverage_gap_detected",)
    assert [row.packet_id for row in result.rows] == [
        "packet-complete",
        "packet-gapped",
    ]

    covered_row, blocked_row = result.rows
    assert covered_row.category == "macro"
    assert covered_row.archetype == "rate-decision"
    assert covered_row.coverage_status == "covered"
    assert covered_row.coverage_gap_score == d("0.000000")
    assert covered_row.reason_codes == ("source_family_coverage_complete",)

    assert blocked_row.category == "sports"
    assert blocked_row.archetype == "injury-report"
    assert blocked_row.coverage_status == "blocked"
    assert blocked_row.official_family_gap_score == d("0.000000")
    assert blocked_row.primary_family_gap_score == d("1.000000")
    assert blocked_row.secondary_family_gap_score == d("0.000000")
    assert blocked_row.contradiction_family_gap_score == d("1.000000")
    assert blocked_row.freshness_gap_score == d("0.750000")
    assert blocked_row.independence_gap_score == d("0.666667")
    assert blocked_row.coverage_gap_score == d("0.569445")
    assert blocked_row.required_family_count == d("4.000000")
    assert blocked_row.observed_required_family_count == d("2.000000")
    assert blocked_row.fresh_required_family_count == d("1.000000")
    assert blocked_row.independent_source_count == d("1.000000")
    assert blocked_row.missing_primary_source_families == ("primary-data",)
    assert blocked_row.missing_contradiction_source_families == (
        "contradiction-check",
    )
    assert blocked_row.stale_required_source_families == ("official-release",)
    assert blocked_row.reason_codes == (
        "missing_primary_source_family",
        "missing_contradiction_source_family",
        "stale_required_source_family",
        "independent_source_count_below_floor",
        "source_family_coverage_blocked",
    )


def test_report_digest_payload_and_reason_order_are_deterministic() -> None:
    alpha = subject(
        "packet-alpha",
        "crypto",
        "bridge-liveness",
        observed_source_families=(
            evidence("status", "official-release", "official"),
            evidence("explorer", "primary-data", "primary"),
            evidence("forum", "secondary-context", "secondary"),
            evidence("watcher", "contradiction-check", "contradiction"),
        ),
    )
    beta = subject(
        "packet-beta",
        "crypto",
        "validator-exit",
        observed_source_families=(
            evidence("status-old", "official-release", "official", hours_old=48),
        ),
    )

    first = report(beta, alpha)
    second = report(alpha, beta)

    assert first.rows == second.rows
    assert first.derived_validation_digest == second.derived_validation_digest
    assert len(first.derived_validation_digest) == 64

    payload = api().research_packet_source_family_coverage_gap_v2_payload(first)
    assert payload == first.payload
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["max_coverage_gap_score"] == "0.777778"
    assert payload["rows"][1]["coverage_gap_score"] == "0.777778"
    assert payload["rows"][1]["missing_primary_source_families"] == [
        "primary-data",
    ]
    assert not contains_float(payload)
    json.dumps(payload, sort_keys=True)


def test_frozen_decimal_only_and_exact_hard_flags() -> None:
    module = api()
    item = evidence("fed", "official-release", "official")
    ready_report = report(
        subject(
            "packet-complete",
            "macro",
            "rate-decision",
            observed_source_families=(
                item,
                evidence("bls", "primary-data", "primary"),
                evidence("wire", "secondary-context", "secondary"),
                evidence("watch", "contradiction-check", "contradiction"),
            ),
        ),
    )

    for value in (item, ready_report.rows[0], ready_report):
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.readonly = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="max_freshness_age_hours"):
        module.ResearchPacketSourceFamilyCoverageGapV2Config(
            max_freshness_age_hours=24,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="watch_gap_score"):
        module.ResearchPacketSourceFamilyCoverageGapV2Config(
            watch_gap_score=0.25,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="blocked_gap_score"):
        module.ResearchPacketSourceFamilyCoverageGapV2Config(
            blocked_gap_score=DecimalSubclass("0.500000"),
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(ready_report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(ready_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="paper_only"):
        subject("packet-bad", "macro", "rate-decision", paper_only=False)  # type: ignore[call-arg]


def test_validates_public_surface_without_mutable_or_unsafe_inputs() -> None:
    module = api()

    with pytest.raises(ValueError, match="source_family_kind"):
        evidence("fed", "official-release", "tertiary")
    with pytest.raises(ValueError, match="source_id"):
        evidence(" wallet ", "official-release", "official")
    with pytest.raises(ValueError, match="unsafe"):
        evidence("private-key", "official-release", "official")
    with pytest.raises(ValueError, match="observed_at"):
        module.ResearchPacketSourceFamilyCoverageEvidenceV2(
            source_id="fed",
            source_family="official-release",
            source_family_kind="official",
            observed_at="2026-07-07T12:00:00Z",  # type: ignore[arg-type]
            independence_key="fed",
        )
    with pytest.raises(ValueError, match="observed_source_families"):
        subject(
            "packet-bad",
            "macro",
            "rate-decision",
            observed_source_families=[evidence("fed", "official-release", "official")],  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(
            subject(
                "packet-future",
                "macro",
                "rate-decision",
                observed_source_families=(
                    evidence("fed", "official-release", "official", hours_old=-1),
                ),
            ),
        )


def test_static_module_surface_is_readonly_report_only_paper_only() -> None:
    module = api()
    source = inspect.getsource(module).lower()

    assert "paper_only: bool = true" in source
    assert "report_only: bool = true" in source
    assert "readonly: bool = true" in source

    forbidden_terms = (
        "requests",
        "httpx",
        "socket",
        "web3",
        "private_key",
        "secret",
        "place_order",
        "create_order",
        "trade",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "insert(",
        "update(",
        "delete(",
    )
    for term in forbidden_terms:
        assert term not in source
