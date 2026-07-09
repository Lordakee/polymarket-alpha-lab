from __future__ import annotations

import ast
import hashlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from importlib import import_module

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def _api():
    return import_module(
        "polymarket_alpha_lab.research_event_resolution_finality_confidence_report",
    )


def _config(**overrides: object) -> object:
    api = _api()
    values = {
        "config_version": (
            api.DEFAULT_RESEARCH_EVENT_RESOLUTION_FINALITY_CONFIDENCE_REPORT_CONFIG_VERSION
        ),
        "pass_confidence_score": d("0.750000"),
        "watch_confidence_score": d("0.500000"),
        "pass_primary_evidence_score": d("0.700000"),
        "watch_primary_evidence_score": d("0.400000"),
        "pass_corroboration_score": d("0.700000"),
        "watch_corroboration_score": d("0.400000"),
        "pass_criteria_clarity_score": d("0.700000"),
        "watch_criteria_clarity_score": d("0.400000"),
        "watch_dispute_risk_score": d("0.250000"),
        "block_dispute_risk_score": d("0.600000"),
        "watch_revision_risk_score": d("0.250000"),
        "block_revision_risk_score": d("0.600000"),
        "watch_finality_lag_seconds": d("3600.000000"),
        "block_finality_lag_seconds": d("86400.000000"),
        "primary_evidence_weight": d("0.300000"),
        "corroboration_weight": d("0.250000"),
        "criteria_clarity_weight": d("0.200000"),
        "dispute_resistance_weight": d("0.150000"),
        "revision_resistance_weight": d("0.100000"),
    }
    values.update(overrides)
    return api.ResearchEventResolutionFinalityConfidenceConfig(**values)


def _row(
    event_key: str = "fed-resolution-final",
    *,
    resolution_family: str = "official-resolution",
    evidence_family: str = "primary-crosscheck",
    resolution_effective_at: datetime = GENERATED_AT - timedelta(minutes=45),
    observed_at: datetime = GENERATED_AT - timedelta(minutes=15),
    primary_evidence_score: Decimal = d("0.900000"),
    corroboration_score: Decimal = d("0.800000"),
    criteria_clarity_score: Decimal = d("0.850000"),
    dispute_risk_score: Decimal = d("0.100000"),
    revision_risk_score: Decimal = d("0.050000"),
    upstream_reason_codes: tuple[str, ...] = (),
) -> object:
    return _api().ResearchEventResolutionFinalityEvidenceRow(
        event_key=event_key,
        resolution_family=resolution_family,
        evidence_family=evidence_family,
        resolution_effective_at=resolution_effective_at,
        observed_at=observed_at,
        primary_evidence_score=primary_evidence_score,
        corroboration_score=corroboration_score,
        criteria_clarity_score=criteria_clarity_score,
        dispute_risk_score=dispute_risk_score,
        revision_risk_score=revision_risk_score,
        upstream_reason_codes=upstream_reason_codes,
    )


def _report(
    *rows: object,
    generated_at: datetime = GENERATED_AT,
    **config_overrides: object,
) -> object:
    return _api().build_research_event_resolution_finality_confidence_report(
        rows,
        config=_config(**config_overrides),
        generated_at=generated_at,
    )


def _bypassed_input_row(row: object, **overrides: object) -> object:
    values = {field.name: getattr(row, field.name) for field in fields(row)}
    values.update(overrides)
    bypassed = object.__new__(_api().ResearchEventResolutionFinalityEvidenceRow)
    for name, value in values.items():
        object.__setattr__(bypassed, name, value)
    return bypassed


def _payload_with_refreshed_digest(payload: dict[str, object]) -> dict[str, object]:
    refreshed = dict(payload)
    refreshed.pop("derived_validation_digest", None)
    encoded = json.dumps(
        refreshed,
        sort_keys=True,
        separators=(",", ":"),
    )
    refreshed["derived_validation_digest"] = hashlib.sha256(
        encoded.encode("utf-8"),
    ).hexdigest()
    return refreshed


def test_finality_confidence_report_scores_statuses_counts_and_digest() -> None:
    api = _api()

    report = _report(
        _row(
            "fed-resolution-final",
            upstream_reason_codes=("manual_reviewed",),
        ),
        _row(
            "macro-resolution-watch",
            resolution_family="agency-update",
            evidence_family="cross-family-check",
            resolution_effective_at=GENERATED_AT - timedelta(hours=2, minutes=30),
            observed_at=GENERATED_AT - timedelta(minutes=30),
            primary_evidence_score=d("0.700000"),
            corroboration_score=d("0.600000"),
            criteria_clarity_score=d("0.600000"),
            dispute_risk_score=d("0.300000"),
            revision_risk_score=d("0.200000"),
        ),
        _row(
            "election-resolution-block",
            resolution_family="ambiguous-notice",
            evidence_family="single-family-check",
            resolution_effective_at=GENERATED_AT - timedelta(hours=26),
            observed_at=GENERATED_AT - timedelta(minutes=30),
            primary_evidence_score=d("0.300000"),
            corroboration_score=d("0.200000"),
            criteria_clarity_score=d("0.250000"),
            dispute_risk_score=d("0.800000"),
            revision_risk_score=d("0.700000"),
        ),
    )

    assert type(report) is api.ResearchEventResolutionFinalityConfidenceReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        api.DEFAULT_RESEARCH_EVENT_RESOLUTION_FINALITY_CONFIDENCE_REPORT_CONFIG_VERSION
    )
    assert report.status == "block"
    assert report.event_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_finality_confidence_score == d("0.595000")
    assert report.max_finality_lag_seconds == d("91800.000000")
    assert report.reason_codes == (
        "resolution_finality_confidence_pass",
        "resolution_finality_confidence_watch",
        "resolution_finality_confidence_block",
        "finality_confidence_below_pass",
        "finality_confidence_below_watch",
        "primary_evidence_below_watch",
        "corroboration_below_pass",
        "corroboration_below_watch",
        "criteria_clarity_below_pass",
        "criteria_clarity_below_watch",
        "dispute_risk_watch",
        "dispute_risk_block",
        "revision_risk_block",
        "finality_lag_watch",
        "finality_lag_block",
        "input_manual_reviewed",
    )
    assert tuple(row.event_key for row in report.rows) == (
        "election-resolution-block",
        "macro-resolution-watch",
        "fed-resolution-final",
    )
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")

    blocked = report.rows[0]
    assert blocked.finality_lag_seconds == d("91800.000000")
    assert blocked.finality_confidence_score == d("0.250000")
    assert blocked.reason_codes == (
        "resolution_finality_confidence_block",
        "finality_confidence_below_watch",
        "primary_evidence_below_watch",
        "corroboration_below_watch",
        "criteria_clarity_below_watch",
        "dispute_risk_block",
        "revision_risk_block",
        "finality_lag_block",
    )

    watched = report.rows[1]
    assert watched.finality_lag_seconds == d("7200.000000")
    assert watched.finality_confidence_score == d("0.665000")
    assert watched.reason_codes == (
        "resolution_finality_confidence_watch",
        "finality_confidence_below_pass",
        "corroboration_below_pass",
        "criteria_clarity_below_pass",
        "dispute_risk_watch",
        "finality_lag_watch",
    )

    passed = report.rows[2]
    assert passed.finality_lag_seconds == d("1800.000000")
    assert passed.finality_confidence_score == d("0.870000")
    assert passed.reason_codes == (
        "resolution_finality_confidence_pass",
        "input_manual_reviewed",
    )
    assert report.reason_code_counts[-1] == (
        api.ResearchEventResolutionFinalityConfidenceReasonCodeCount(
            reason_code="input_manual_reviewed",
            count=d("1.000000"),
        )
    )
    assert len(report.derived_validation_digest) == 64
    assert all(
        character in "0123456789abcdef"
        for character in report.derived_validation_digest
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_empty_finality_confidence_input_blocks_readonly_report() -> None:
    api = _api()

    report = _report()

    assert report == api.ResearchEventResolutionFinalityConfidenceReport(
        generated_at=GENERATED_AT,
        config_version=(
            api.DEFAULT_RESEARCH_EVENT_RESOLUTION_FINALITY_CONFIDENCE_REPORT_CONFIG_VERSION
        ),
        event_count=d("0.000000"),
        pass_count=d("0.000000"),
        watch_count=d("0.000000"),
        block_count=d("0.000000"),
        average_finality_confidence_score=None,
        max_finality_lag_seconds=d("0.000000"),
        status="block",
        reason_codes=("no_finality_evidence",),
        rows=(),
        reason_code_counts=(
            api.ResearchEventResolutionFinalityConfidenceReasonCodeCount(
                reason_code="no_finality_evidence",
                count=d("1.000000"),
            ),
        ),
    )


def test_finality_confidence_payload_is_json_ready_and_tamper_evident() -> None:
    api = _api()
    report = _report(_row("payload-safe"))

    payload = api.research_event_resolution_finality_confidence_report_to_payload(report)

    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["event_count"] == "1.000000"
    assert payload["average_finality_confidence_score"] == "0.870000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"][0]["resolution_effective_at"] == (
        "2026-07-09T11:15:00+00:00"
    )
    assert payload["rows"][0]["finality_lag_seconds"] == "1800.000000"
    assert (
        api.validate_research_event_resolution_finality_confidence_public_payload(
            payload,
        )
        is True
    )
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert not any(type(value) is int for value in _walk_payload_values(payload))
    assert not any(type(value) is Decimal for value in _walk_payload_values(payload))

    with pytest.raises(ValueError, match="report must be"):
        api.research_event_resolution_finality_confidence_report_to_payload(object())

    tampered_payload = dict(payload)
    tampered_payload["event_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.validate_research_event_resolution_finality_confidence_public_payload(
            tampered_payload,
        )

    missing_digest_payload = dict(payload)
    missing_digest_payload.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.validate_research_event_resolution_finality_confidence_public_payload(
            missing_digest_payload,
        )

    numeric_payload = dict(payload)
    numeric_payload["event_count"] = d("1.000000")
    with pytest.raises(ValueError, match="Decimal strings"):
        api.validate_research_event_resolution_finality_confidence_public_payload(
            numeric_payload,
        )

    nested_flag_payload = dict(payload)
    nested_flag_payload["rows"] = [dict(payload["rows"][0], readonly=False)]
    nested_flag_payload = _payload_with_refreshed_digest(nested_flag_payload)
    with pytest.raises(ValueError, match="readonly"):
        api.validate_research_event_resolution_finality_confidence_public_payload(
            nested_flag_payload,
        )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


@pytest.mark.parametrize(
    "unsafe_key",
    (
        _join_parts("candidate", "_id"),
        _join_parts("market", "_id"),
        "slug",
        "question",
        _join_parts("source", "_url"),
        _join_parts("source", "_text"),
        "dsn",
        _join_parts("ta", "ble"),
        _join_parts("to", "ken"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
    ),
)
def test_finality_confidence_payload_rejects_sensitive_public_keys(
    unsafe_key: str,
) -> None:
    api = _api()
    payload = api.research_event_resolution_finality_confidence_report_to_payload(
        _report(_row("unsafe-key-check")),
    )
    unsafe_payload = dict(payload)
    unsafe_payload[unsafe_key] = "blocked"

    with pytest.raises(ValueError, match="unsafe"):
        api.validate_research_event_resolution_finality_confidence_public_payload(
            unsafe_payload,
        )


@pytest.mark.parametrize(
    "unsafe_value",
    (
        _join_parts("cand", "idate", "-raw"),
        _join_parts("market", "-raw"),
        _join_parts("https", "://example.invalid/finality"),
        _join_parts("secret", "-", "token"),
        _join_parts("wallet", "-surface"),
        _join_parts("order", "-surface"),
        _join_parts("trade", "-surface"),
    ),
)
def test_finality_confidence_payload_rejects_sensitive_public_values(
    unsafe_value: str,
) -> None:
    api = _api()
    payload = api.research_event_resolution_finality_confidence_report_to_payload(
        _report(_row("unsafe-value-check")),
    )
    unsafe_payload = dict(payload)
    unsafe_payload["rows"] = [dict(payload["rows"][0], event_key=unsafe_value)]

    with pytest.raises(ValueError, match="unsafe"):
        api.validate_research_event_resolution_finality_confidence_public_payload(
            unsafe_payload,
        )


def test_finality_confidence_validates_types_times_flags_and_consistency() -> None:
    api = _api()
    offset = timezone(timedelta(hours=-4))
    report = api.build_research_event_resolution_finality_confidence_report(
        (
            _row(
                "offset-safe",
                resolution_effective_at=datetime(2026, 7, 9, 7, 15, tzinfo=offset),
                observed_at=datetime(2026, 7, 9, 7, 45, tzinfo=offset),
            ),
        ),
        config=_config(),
        generated_at=datetime(2026, 7, 9, 8, 0, tzinfo=offset),
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].resolution_effective_at == datetime(
        2026,
        7,
        9,
        11,
        15,
        tzinfo=UTC,
    )
    assert report.rows[0].finality_lag_seconds == d("1800.000000")

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="finality_confidence_score"):
        replace(report.rows[0], finality_confidence_score=d("0.100000"))
    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=())
    with pytest.raises(ValueError, match="pass_confidence_score"):
        _config(pass_confidence_score=0.75)
    with pytest.raises(ValueError, match="watch_dispute_risk_score"):
        _config(watch_dispute_risk_score=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="generated_at"):
        _report(_row("naive-generated"), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="resolution_effective_at"):
        _row(
            "naive-resolution",
            resolution_effective_at=datetime(2026, 7, 9, 11, 15),
        )
    with pytest.raises(ValueError, match="resolution_effective_at"):
        _row(
            "subclass-resolution",
            resolution_effective_at=_DateTimeSubclass(2026, 7, 9, 11, 15, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        _row(
            "none-offset-observed",
            observed_at=datetime(2026, 7, 9, 11, 45, tzinfo=_NoneOffsetTz()),
        )
    with pytest.raises(ValueError, match="observed_at"):
        _row(
            "observed-before-resolution",
            resolution_effective_at=GENERATED_AT - timedelta(minutes=10),
            observed_at=GENERATED_AT - timedelta(minutes=11),
        )
    with pytest.raises(ValueError, match="future"):
        _report(
            _row(
                "future-observed",
                observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="event_key"):
        _report(_row("duplicate-event"), _row("duplicate-event"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(_row("flag-input"), paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    bypassed = _bypassed_input_row(_row("bypassed-input"), report_only=False)
    with pytest.raises(ValueError, match="report_only"):
        api.build_research_event_resolution_finality_confidence_report(
            (bypassed,),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_finality_confidence_uses_only_decimal_metrics() -> None:
    report = _report(_row("decimal-metrics"))

    report_metric_names = (
        "event_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_finality_confidence_score",
        "max_finality_lag_seconds",
    )
    for name in report_metric_names:
        value = getattr(report, name)
        if value is not None:
            assert type(value) is Decimal

    row_metric_names = (
        "finality_lag_seconds",
        "primary_evidence_score",
        "corroboration_score",
        "criteria_clarity_score",
        "dispute_risk_score",
        "revision_risk_score",
        "finality_confidence_score",
    )
    for name in row_metric_names:
        assert type(getattr(report.rows[0], name)) is Decimal

    for reason_count in report.reason_code_counts:
        assert type(reason_count.count) is Decimal


def test_finality_confidence_module_is_pure_report_only_surface() -> None:
    api = _api()
    public_names = tuple(api.__all__)
    source = inspect.getsource(api).lower()
    tree = ast.parse(source)

    assert ".total_seconds(" not in source
    assert "float(" not in source
    for banned in (
        _join_parts("candidate", "_id"),
        _join_parts("market", "_id"),
        "slug",
        "question",
        _join_parts("source", "_url"),
        _join_parts("source", "_text"),
        "dsn",
        _join_parts("ta", "ble"),
        _join_parts("to", "ken"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        _join_parts("si", "zing"),
        _join_parts("recomm", "endation"),
    ):
        assert banned not in source
        assert all(banned not in name.lower() for name in public_names)

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
                "read",
                "write",
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


def _walk_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        items: list[object] = []
        for child in value.values():
            items.extend(_walk_payload_values(child))
        return tuple(items)
    if isinstance(value, list):
        items = []
        for child in value:
            items.extend(_walk_payload_values(child))
        return tuple(items)
    return (value,)
