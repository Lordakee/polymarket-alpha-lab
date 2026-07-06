from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from json import dumps

import pytest

from polymarket_alpha_lab import research_packet_information_quality_score as score_module
from polymarket_alpha_lab.research_packet_information_quality_score import (
    ResearchPacketInformationQualityScoreConfig,
    ResearchPacketInformationQualityScoreReport,
    ResearchPacketInformationQualityScoreRow,
    ResearchPacketInformationQualitySourceEvidence,
    build_research_packet_information_quality_score_report,
    research_packet_information_quality_score_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def _evidence(
    packet_id: str,
    *,
    market_slug: str | None = None,
    event_title: str = "Will the committee publish its final ruling?",
    resolution_criteria: str = (
        "Resolves Yes only if the named committee publishes a final public ruling "
        "before the stated event deadline."
    ),
    source_id: str | None = None,
    source_name: str = "Official committee bulletin",
    source_family: str = "official",
    source_reference: str = "committee-bulletin-2026-07-06",
    source_published_at: datetime | None = None,
    observed_at: datetime | None = None,
    is_official_source: bool = True,
    supports_resolution_criteria: bool = True,
    supports_current_outcome: bool = True,
    contradicts_packet: bool = False,
    evidence_quote: str = "Final ruling publication criteria are stated.",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchPacketInformationQualitySourceEvidence:
    return ResearchPacketInformationQualitySourceEvidence(
        packet_id=packet_id,
        market_slug=market_slug or f"{packet_id}-market",
        event_title=event_title,
        resolution_criteria=resolution_criteria,
        source_id=source_id or f"{packet_id}-{source_family}",
        source_name=source_name,
        source_family=source_family,
        source_reference=source_reference,
        source_published_at=source_published_at
        or GENERATED_AT
        - timedelta(seconds=600),
        observed_at=observed_at or GENERATED_AT - timedelta(seconds=300),
        is_official_source=is_official_source,
        supports_resolution_criteria=supports_resolution_criteria,
        supports_current_outcome=supports_current_outcome,
        contradicts_packet=contradicts_packet,
        evidence_quote=evidence_quote,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _config() -> ResearchPacketInformationQualityScoreConfig:
    return ResearchPacketInformationQualityScoreConfig(
        fresh_source_max_age_seconds=Decimal("3600.000000"),
        usable_source_max_age_seconds=Decimal("86400.000000"),
        min_official_source_count=Decimal("1"),
        min_source_family_count=Decimal("2"),
        min_traceable_source_count=Decimal("2"),
        min_resolution_criteria_characters=Decimal("40"),
        pass_quality_score=Decimal("0.800000"),
        watch_quality_score=Decimal("0.500000"),
    )


def test_builds_decimal_only_information_quality_scores_by_packet() -> None:
    report = build_research_packet_information_quality_score_report(
        (
            _evidence(
                "clear-packet",
                source_family="official",
                source_id="clear-official",
                source_reference="official-resolution-criteria",
            ),
            _evidence(
                "clear-packet",
                source_family="news",
                source_id="clear-news",
                source_name="Newswire event summary",
                source_reference="wire-summary-2026-07-06",
                is_official_source=False,
            ),
            _evidence(
                "weak-packet",
                event_title="Will an outcome be announced?",
                resolution_criteria="TBD",
                source_family="social",
                source_id="weak-social",
                source_name="Public commentary",
                source_reference="public-commentary-2026-07-04",
                source_published_at=GENERATED_AT - timedelta(seconds=172800),
                observed_at=GENERATED_AT - timedelta(seconds=172700),
                is_official_source=False,
                supports_resolution_criteria=False,
                supports_current_outcome=False,
                contradicts_packet=True,
                evidence_quote="",
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.status == "blocked"
    assert report.packet_count == Decimal("2")
    assert report.pass_count == Decimal("1")
    assert report.blocked_count == Decimal("1")
    assert report.watch_count == Decimal("0")
    assert report.average_information_quality_score == Decimal("0.541666")
    assert report.average_source_recency_score == Decimal("0.500000")
    assert report.average_official_source_coverage_score == Decimal("0.500000")
    assert report.average_source_diversity_score == Decimal("0.750000")
    assert report.average_contradiction_risk_score == Decimal("0.500000")
    assert report.average_resolution_criteria_clarity_score == Decimal("0.500000")
    assert report.average_evidence_traceability_score == Decimal("0.500000")
    assert report.reason_codes == (
        "contradiction_risk_elevated",
        "evidence_traceability_weak",
        "official_source_coverage_thin",
        "resolution_criteria_unclear",
        "source_diversity_thin",
        "source_recency_stale",
    )
    assert tuple(row.packet_id for row in report.rows) == (
        "weak-packet",
        "clear-packet",
    )

    weak_row, clear_row = report.rows
    assert weak_row.status == "blocked"
    assert weak_row.source_recency_score == Decimal("0.000000")
    assert weak_row.official_source_coverage_score == Decimal("0.000000")
    assert weak_row.source_diversity_score == Decimal("0.500000")
    assert weak_row.contradiction_risk_score == Decimal("0.000000")
    assert weak_row.resolution_criteria_clarity_score == Decimal("0.000000")
    assert weak_row.evidence_traceability_score == Decimal("0.000000")
    assert weak_row.information_quality_score == Decimal("0.083333")
    assert weak_row.reason_codes == (
        "contradiction_risk_elevated",
        "evidence_traceability_weak",
        "official_source_coverage_thin",
        "resolution_criteria_unclear",
        "source_diversity_thin",
        "source_recency_stale",
    )

    assert clear_row.status == "pass"
    assert clear_row.information_quality_score == Decimal("1.000000")
    assert clear_row.reason_codes == ("research_packet_information_quality_clear",)
    assert clear_row.latest_source_published_at == GENERATED_AT - timedelta(seconds=600)
    assert clear_row.newest_source_age_seconds == Decimal("600.000000")
    assert clear_row.source_count == Decimal("2")
    assert clear_row.official_source_count == Decimal("1")
    assert clear_row.source_family_count == Decimal("2")
    assert clear_row.traceable_source_count == Decimal("2")
    assert clear_row.criteria_support_source_count == Decimal("2")
    assert clear_row.contradiction_source_count == Decimal("0")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_empty_report_is_blocked_report_only_readonly_and_decimal_zeroed() -> None:
    report = build_research_packet_information_quality_score_report(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.status == "blocked"
    assert report.packet_count == Decimal("0")
    assert report.average_information_quality_score == Decimal("0.000000")
    assert report.reason_codes == ("no_source_evidence",)
    assert report.reason_code_counts == ()
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_serializes_decimal_values_as_strings_and_rejects_floats() -> None:
    report = build_research_packet_information_quality_score_report(
        (
            _evidence("payload-packet", source_family="official", source_id="payload-official"),
            _evidence(
                "payload-packet",
                source_family="analysis",
                source_id="payload-analysis",
                source_name="Analyst packet review",
                source_reference="analyst-review-2026-07-06",
                is_official_source=False,
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    payload = research_packet_information_quality_score_payload(report)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["packet_count"] == "1"
    assert payload["average_information_quality_score"] == "1.000000"
    assert payload["rows"][0]["newest_source_age_seconds"] == "600.000000"
    assert payload["rows"][0]["information_quality_score"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _float_paths(payload) == ()
    dumps(payload, sort_keys=True)

    with pytest.raises(ValueError, match="public numeric values must be Decimal strings"):
        research_packet_information_quality_score_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "packet_count": 1,
            },
        )

    with pytest.raises(ValueError, match="public numeric values must be Decimal strings"):
        research_packet_information_quality_score_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "average_information_quality_score": 1.0,
            },
        )


def test_report_exposes_deterministic_validation_digest_and_rejects_tampering() -> None:
    report = build_research_packet_information_quality_score_report(
        (_evidence("digest-packet"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    repeated = build_research_packet_information_quality_score_report(
        (_evidence("digest-packet"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    changed = build_research_packet_information_quality_score_report(
        (_evidence("digest-packet", source_published_at=GENERATED_AT - timedelta(seconds=7200)),),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)
    assert report.derived_validation_digest == repeated.derived_validation_digest
    assert report.derived_validation_digest != changed.derived_validation_digest

    payload = research_packet_information_quality_score_payload(report)
    assert payload["derived_validation_digest"] == report.derived_validation_digest

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="not-a-real-digest")

    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_packet_information_quality_score_payload(
            {
                **payload,
                "packet_count": "2",
            },
        )


def test_public_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    evidence = _evidence("frozen-packet")

    with pytest.raises(FrozenInstanceError):
        evidence.packet_id = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(evidence, paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        replace(_config(), report_only=False)

    for dataclass_type in (
        ResearchPacketInformationQualityScoreConfig,
        ResearchPacketInformationQualitySourceEvidence,
        ResearchPacketInformationQualityScoreRow,
        ResearchPacketInformationQualityScoreReport,
    ):
        assert is_dataclass(dataclass_type)
        assert dataclass_type.__dataclass_params__.frozen is True
        annotations = dataclass_type.__annotations__.values()
        assert all("float" not in str(annotation) for annotation in annotations)
        assert all("int" not in str(annotation) for annotation in annotations)


def test_validates_decimals_datetimes_duplicates_future_inputs_and_payload_flags() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        ResearchPacketInformationQualityScoreConfig(
            fresh_source_max_age_seconds=3600,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="timezone-aware"):
        _evidence(
            "naive-packet",
            source_published_at=datetime(2026, 7, 6, 11, 50),
        )

    with pytest.raises(ValueError, match="future"):
        build_research_packet_information_quality_score_report(
            (_evidence("future-packet", source_published_at=GENERATED_AT + timedelta(seconds=1)),),
            config=_config(),
            generated_at=GENERATED_AT,
        )

    duplicate = _evidence("duplicate-packet", source_id="same-source")
    with pytest.raises(ValueError, match="duplicate source_id"):
        build_research_packet_information_quality_score_report(
            (duplicate, duplicate),
            config=_config(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="paper_only must be True"):
        research_packet_information_quality_score_payload(
            {
                "report_only": True,
                "readonly": True,
            },
        )

    class NoneOffsetTimezone(tzinfo):
        def utcoffset(self, dt: datetime | None) -> None:
            return None

        def dst(self, dt: datetime | None) -> None:
            return None

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        research_packet_information_quality_score_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "generated_at": datetime(2026, 7, 6, 12, 0, tzinfo=NoneOffsetTimezone()),
            },
        )


def test_rejects_unsafe_public_keys_and_values() -> None:
    for unsafe_key in (
        "live_mode",
        "auth_token",
        "wallet_address",
        "order_id",
        "network_endpoint",
        "database_url",
        "persist_path",
        "signing_key",
        "mutation_request",
        "buy_button",
        "sell_ticket",
        "trade_route",
    ):
        with pytest.raises(ValueError, match="unsafe public surface"):
            research_packet_information_quality_score_payload(
                {
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                    unsafe_key: "redacted",
                },
            )

    for unsafe_value in (
        "live mode enabled",
        "auth bearer token",
        "wallet signer",
        "order placement",
        "network endpoint",
        "database connection",
        "persist to storage",
        "signing request",
        "mutation request",
        "buy action",
        "sell action",
        "trade route",
    ):
        with pytest.raises(ValueError, match="unsafe public surface"):
            research_packet_information_quality_score_payload(
                {
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                    "diagnostic": unsafe_value,
                },
            )


def test_module_scope_has_no_network_auth_storage_or_process_imports() -> None:
    source = inspect.getsource(score_module)
    forbidden_terms = (
        "requests",
        "httpx",
        "socket",
        "psycopg",
        "sqlite3",
        "subprocess",
        "open(",
    )

    for term in forbidden_terms:
        assert term not in source


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
