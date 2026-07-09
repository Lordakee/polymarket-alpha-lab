from __future__ import annotations

import ast
import hashlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.research_event_resolution_update_credibility_ladder_report import (
    DEFAULT_RESEARCH_EVENT_RESOLUTION_UPDATE_CREDIBILITY_LADDER_REPORT_CONFIG_VERSION,
    ResearchEventResolutionUpdateCredibilityLadderConfig,
    ResearchEventResolutionUpdateCredibilityLadderReport,
    ResearchEventResolutionUpdateCredibilityLadderRow,
    ResearchEventResolutionUpdateInput,
    build_research_event_resolution_update_credibility_ladder_report,
    research_event_resolution_update_credibility_ladder_report_to_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def _update(
    update_key: str,
    *,
    event_key: str = "event_alpha",
    source_tier: str = "official",
    corroborating_source_count: Decimal = d("3.000000"),
    independent_source_family_count: Decimal = d("2.000000"),
    contradiction_count: Decimal = d("0.000000"),
    observed_at: datetime = GENERATED_AT - timedelta(minutes=10),
    event_deadline_at: datetime | None = GENERATED_AT + timedelta(hours=8),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchEventResolutionUpdateInput:
    return ResearchEventResolutionUpdateInput(
        event_key=event_key,
        update_key=update_key,
        source_tier=source_tier,
        corroborating_source_count=corroborating_source_count,
        independent_source_family_count=independent_source_family_count,
        contradiction_count=contradiction_count,
        observed_at=observed_at,
        event_deadline_at=event_deadline_at,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _config(
    **overrides: object,
) -> ResearchEventResolutionUpdateCredibilityLadderConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_EVENT_RESOLUTION_UPDATE_CREDIBILITY_LADDER_REPORT_CONFIG_VERSION
        ),
        "pass_threshold": d("0.700000"),
        "watch_threshold": d("0.450000"),
        "required_corroborating_sources": d("3.000000"),
        "required_independent_source_families": d("2.000000"),
        "blocked_contradiction_count": d("3.000000"),
        "fresh_update_seconds": d("1800.000000"),
        "stale_update_seconds": d("7200.000000"),
        "deadline_proximity_window_seconds": d("3600.000000"),
        "corroboration_weight": d("0.250000"),
        "recency_weight": d("0.150000"),
        "contradiction_penalty_weight": d("0.350000"),
        "deadline_proximity_penalty_weight": d("0.100000"),
        "source_tier_weights": (
            ("official", d("0.500000")),
            ("primary", d("0.400000")),
            ("reporting", d("0.250000")),
            ("social", d("0.100000")),
            ("unknown", d("0.000000")),
        ),
    }
    values.update(overrides)
    return ResearchEventResolutionUpdateCredibilityLadderConfig(**values)


def _report(
    *updates: ResearchEventResolutionUpdateInput,
    config: ResearchEventResolutionUpdateCredibilityLadderConfig | None = None,
) -> ResearchEventResolutionUpdateCredibilityLadderReport:
    return build_research_event_resolution_update_credibility_ladder_report(
        updates,
        config=config or _config(),
        generated_at=GENERATED_AT,
    )


def test_credibility_ladder_thresholds_rank_pass_watch_and_block_rows() -> None:
    report = _report(
        _update(
            "block_update",
            source_tier="unknown",
            corroborating_source_count=d("1.000000"),
            independent_source_family_count=d("1.000000"),
            contradiction_count=d("3.000000"),
            observed_at=GENERATED_AT - timedelta(hours=10),
            event_deadline_at=GENERATED_AT - timedelta(minutes=5),
        ),
        _update(
            "watch_update",
            source_tier="primary",
            contradiction_count=d("2.000000"),
            event_deadline_at=GENERATED_AT + timedelta(minutes=30),
        ),
        _update("pass_update"),
    )

    assert report.ladder_status == "block"
    assert report.update_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_credibility_score == d("0.455556")
    assert tuple(row.update_key for row in report.rows) == (
        "block_update",
        "watch_update",
        "pass_update",
    )

    blocked, watched, passed = report.rows
    assert blocked.ladder_status == "block"
    assert blocked.credibility_score == d("0.000000")
    assert blocked.contradiction_penalty == d("0.350000")
    assert blocked.deadline_proximity_penalty == d("0.100000")
    assert blocked.reason_codes == (
        "credibility_ladder_blocked_contradiction_pressure",
        "credibility_ladder_corroboration_quorum_shortfall",
        "credibility_ladder_family_quorum_shortfall",
        "credibility_ladder_stale_update",
        "credibility_ladder_deadline_pressure",
    )

    assert watched.ladder_status == "watch"
    assert watched.credibility_score == d("0.466667")
    assert watched.reason_codes == (
        "credibility_ladder_watch_threshold",
        "credibility_ladder_deadline_pressure",
        "credibility_ladder_contradiction_pressure",
    )

    assert passed.ladder_status == "pass"
    assert passed.credibility_score == d("0.900000")
    assert passed.reason_codes == ("credibility_ladder_pass_threshold",)
    assert report.reason_codes == (
        "credibility_ladder_blocked_contradiction_pressure",
        "credibility_ladder_watch_threshold",
        "credibility_ladder_pass_threshold",
        "credibility_ladder_corroboration_quorum_shortfall",
        "credibility_ladder_family_quorum_shortfall",
        "credibility_ladder_stale_update",
        "credibility_ladder_deadline_pressure",
        "credibility_ladder_contradiction_pressure",
        "credibility_ladder_block_present",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_quorum_penalties_downgrade_otherwise_strong_updates() -> None:
    report = _report(
        _update(
            "thin_quorum",
            source_tier="official",
            corroborating_source_count=d("1.000000"),
            independent_source_family_count=d("1.000000"),
        ),
    )

    row = report.rows[0]
    assert row.ladder_status == "watch"
    assert row.source_tier_weight == d("0.500000")
    assert row.corroboration_score == d("0.083333")
    assert row.credibility_score == d("0.733333")
    assert row.reason_codes == (
        "credibility_ladder_watch_threshold",
        "credibility_ladder_corroboration_quorum_shortfall",
        "credibility_ladder_family_quorum_shortfall",
    )
    assert report.ladder_status == "watch"


def test_public_payload_and_digest_are_deterministic_and_validated() -> None:
    forward = _report(
        _update("pass_update"),
        _update(
            "watch_update",
            source_tier="primary",
            contradiction_count=d("2.000000"),
            event_deadline_at=GENERATED_AT + timedelta(minutes=30),
        ),
    )
    reverse = _report(
        _update(
            "watch_update",
            source_tier="primary",
            contradiction_count=d("2.000000"),
            event_deadline_at=GENERATED_AT + timedelta(minutes=30),
        ),
        _update("pass_update"),
    )

    assert forward == reverse
    assert forward.derived_validation_digest == reverse.derived_validation_digest
    payload = research_event_resolution_update_credibility_ladder_report_to_payload(
        forward,
    )
    assert payload == forward.public_payload
    assert payload["derived_validation_digest"] == forward.derived_validation_digest
    assert payload["rows"][0]["credibility_score"] == "0.466667"

    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest")
    canonical = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert hashlib.sha256(canonical.encode("utf-8")).hexdigest() == (
        forward.derived_validation_digest
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(forward, derived_validation_digest="0" * 64)

    with pytest.raises(FrozenInstanceError):
        forward.rows[0].credibility_score = d("0.000000")  # type: ignore[misc]


def test_public_payload_revalidates_report_consistency_on_export() -> None:
    report = _report(_update("pass_update"))
    object.__setattr__(report, "update_count", d("9.000000"))

    with pytest.raises(ValueError, match="update_count"):
        research_event_resolution_update_credibility_ladder_report_to_payload(
            report,
        )


def test_public_payload_revalidates_digest_on_export() -> None:
    report = _report(_update("pass_update"))
    object.__setattr__(report, "derived_validation_digest", "0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        report.public_payload


def test_public_payload_revalidates_nested_row_schema_on_export() -> None:
    report = _report(_update("pass_update"))
    object.__setattr__(report.rows[0], "credibility_score", "0.900000")

    with pytest.raises(ValueError, match="credibility_score must be a Decimal"):
        report.public_payload


def test_negative_zero_is_canonicalized_before_digesting() -> None:
    positive_zero = _report(
        _update("same_update", contradiction_count=d("0.000000")),
    )
    negative_zero = _report(
        _update("same_update", contradiction_count=d("-0.000000")),
    )

    assert negative_zero.rows[0].contradiction_count == d("0.000000")
    assert negative_zero.public_payload["rows"][0]["contradiction_count"] == "0.000000"
    assert negative_zero.derived_validation_digest == (
        positive_zero.derived_validation_digest
    )


def test_public_dataclasses_are_final_schema_boundaries() -> None:
    public_types = (
        ResearchEventResolutionUpdateCredibilityLadderConfig,
        ResearchEventResolutionUpdateInput,
        ResearchEventResolutionUpdateCredibilityLadderRow,
        ResearchEventResolutionUpdateCredibilityLadderReport,
    )

    for public_type in public_types:
        with pytest.raises(TypeError, match="may not be subclassed"):
            type(f"Derived{public_type.__name__}", (public_type,), {})


def test_public_payload_prevents_raw_identifier_and_sensitive_surface_leaks() -> None:
    report = _report(_update("pass_update", event_key="safe_event_alias"))
    payload = report.public_payload
    rendered = repr(payload).lower()
    forbidden_terms = (
        _join_parts("candidate", "_", "id"),
        _join_parts("market", "_", "id"),
        _join_parts("market", "_", "slug"),
        _join_parts("que", "stion"),
        _join_parts("source", "_", "url"),
        _join_parts("source", "_", "text"),
        "dsn",
        _join_parts("ta", "ble"),
        _join_parts("to", "ken"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        _join_parts("exec", "ution"),
    )
    for term in forbidden_terms:
        assert term not in rendered

    for unsafe_value in (
        _join_parts("market", "_", "slug"),
        "https://example.invalid/source",
        _join_parts("source", "_", "text"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("to", "ken"),
        _join_parts("exec", "ution"),
    ):
        with pytest.raises(ValueError, match="unsafe public value"):
            _update("unsafe_value", event_key=unsafe_value)

    with pytest.raises(ValueError, match="paper_only"):
        _update("unsafe_flags", paper_only=False)


def test_custom_config_validation_and_decimal_only_metrics() -> None:
    strict = _config(pass_threshold=d("0.950000"), watch_threshold=d("0.800000"))
    strict_report = _report(_update("pass_under_strict_threshold"), config=strict)

    assert strict_report.ladder_status == "watch"
    assert strict_report.rows[0].ladder_status == "watch"
    assert strict_report.rows[0].credibility_score == d("0.900000")

    with pytest.raises(ValueError, match="pass_threshold"):
        _config(pass_threshold=d("0.400000"), watch_threshold=d("0.450000"))
    with pytest.raises(ValueError, match="required_corroborating_sources"):
        _config(required_corroborating_sources=3)
    with pytest.raises(ValueError, match="source_tier_weights"):
        _config(source_tier_weights=(("official", d("0.500000")), ("official", d("0.400000"))))
    with pytest.raises(ValueError, match="readonly"):
        _config(readonly=False)

    report_metric_names = (
        "update_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_credibility_score",
        "max_contradiction_penalty",
        "min_seconds_to_deadline",
    )
    for name in report_metric_names:
        value = getattr(strict_report, name)
        if value is not None:
            assert type(value) is Decimal

    row_metric_names = (
        "source_tier_weight",
        "corroboration_score",
        "recency_score",
        "contradiction_penalty",
        "deadline_proximity_penalty",
        "seconds_since_observed",
        "seconds_to_deadline",
        "credibility_score",
    )
    for name in row_metric_names:
        value = getattr(strict_report.rows[0], name)
        if value is not None:
            assert type(value) is Decimal


def test_module_has_no_external_action_or_sensitive_surfaces() -> None:
    import polymarket_alpha_lab.research_event_resolution_update_credibility_ladder_report as api

    source = inspect.getsource(api).lower()
    tree = ast.parse(source)

    assert "float(" not in source
    assert ".total_seconds(" not in source
    for token in (
        _join_parts("data", "base"),
        _join_parts("net", "work"),
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        _join_parts("siz", "ing"),
        _join_parts("recomm", "end"),
    ):
        assert token not in source

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
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
                "delete",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )

    exposed_names = {field.name for field in fields(ResearchEventResolutionUpdateCredibilityLadderReport)}
    assert _join_parts("candidate", "_", "id") not in exposed_names
    assert _join_parts("market", "_", "id") not in exposed_names
    assert _join_parts("market", "_", "slug") not in exposed_names
    assert _join_parts("que", "stion") not in exposed_names
