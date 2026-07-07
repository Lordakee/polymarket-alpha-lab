from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, localcontext
import json
from pathlib import Path
from typing import Any, get_args, get_type_hints

import pytest

from polymarket_alpha_lab import market_close_resolution_source_alignment_report as module
from polymarket_alpha_lab.market_close_resolution_source_alignment_report import (
    DEFAULT_MARKET_CLOSE_RESOLUTION_SOURCE_ALIGNMENT_REPORT_CONFIG_VERSION,
    MarketCloseResolutionSourceAlignmentConfig,
    MarketCloseResolutionSourceAlignmentInputRow,
    MarketCloseResolutionSourceAlignmentReport,
    MarketCloseResolutionSourceAlignmentRow,
    build_market_close_resolution_source_alignment_report,
    market_close_resolution_source_alignment_report_payload,
)


NOW = datetime(2026, 2, 3, 12, 0, tzinfo=UTC)
UNSAFE_SURFACE_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "account",
    "broker",
    "order",
    "submit",
    "cancel",
    "signing",
    "advice",
    "trading",
    "network",
    "database",
    "persist",
)


def _at(**kwargs: int) -> datetime:
    return NOW - timedelta(**kwargs)


def _input_row(
    market_id: str,
    *,
    team_id: str = "macro-team",
    source_id: str = "official-source",
    market_close_at: datetime | None = None,
    resolution_source_refreshed_at: datetime | None = None,
    resolution_source_timestamp_at: datetime | None = None,
    team_acknowledged_at: datetime | None = None,
    resolution_criteria_ambiguous: bool = False,
    expected_source_refresh_window_seconds: Decimal | None = None,
) -> MarketCloseResolutionSourceAlignmentInputRow:
    return MarketCloseResolutionSourceAlignmentInputRow(
        team_id=team_id,
        market_id=market_id,
        source_id=source_id,
        market_close_at=market_close_at,
        resolution_source_refreshed_at=resolution_source_refreshed_at,
        resolution_source_timestamp_at=resolution_source_timestamp_at,
        team_acknowledged_at=team_acknowledged_at,
        resolution_criteria_ambiguous=resolution_criteria_ambiguous,
        expected_source_refresh_window_seconds=expected_source_refresh_window_seconds,
    )


def _mixed_report() -> MarketCloseResolutionSourceAlignmentReport:
    rows = (
        _input_row(
            "m-clear",
            market_close_at=_at(hours=2),
            resolution_source_refreshed_at=_at(minutes=30),
            resolution_source_timestamp_at=_at(minutes=15),
            team_acknowledged_at=_at(minutes=10),
        ),
        _input_row(
            "m-ambiguous",
            market_close_at=_at(hours=2),
            resolution_source_refreshed_at=_at(minutes=10),
            resolution_source_timestamp_at=_at(hours=1),
            team_acknowledged_at=_at(hours=1),
            resolution_criteria_ambiguous=True,
        ),
        _input_row(
            "m-missing-close",
            market_close_at=None,
            resolution_source_refreshed_at=_at(minutes=15),
            resolution_source_timestamp_at=_at(minutes=10),
            team_acknowledged_at=_at(minutes=5),
        ),
        _input_row(
            "m-missing-ack",
            market_close_at=_at(hours=2),
            resolution_source_refreshed_at=_at(minutes=10),
            resolution_source_timestamp_at=_at(hours=1),
            team_acknowledged_at=None,
        ),
        _input_row(
            "m-source-before",
            market_close_at=_at(hours=3),
            resolution_source_refreshed_at=_at(minutes=10),
            resolution_source_timestamp_at=_at(hours=4),
            team_acknowledged_at=_at(hours=2),
        ),
        _input_row(
            "m-stale",
            market_close_at=_at(hours=4),
            resolution_source_refreshed_at=_at(hours=2),
            resolution_source_timestamp_at=_at(hours=1),
            team_acknowledged_at=_at(hours=1),
        ),
    )
    return build_market_close_resolution_source_alignment_report(
        rows,
        config=MarketCloseResolutionSourceAlignmentConfig(
            expected_source_refresh_window_seconds=Decimal("3600.000000"),
        ),
        generated_at=NOW,
    )


def test_build_report_flags_alignment_gaps_with_decimal_metrics_and_stable_sorting() -> None:
    report = _mixed_report()

    assert report.generated_at == NOW
    assert report.config_version == (
        DEFAULT_MARKET_CLOSE_RESOLUTION_SOURCE_ALIGNMENT_REPORT_CONFIG_VERSION
    )
    assert report.report_status == "blocked"
    assert report.reason_codes == (
        "market_close_time_missing",
        "official_resolution_source_timestamp_before_close",
        "team_resolution_acknowledgement_missing",
        "official_resolution_source_refresh_stale",
        "resolution_criteria_ambiguous",
    )
    assert report.market_count == Decimal("6.000000")
    assert report.pass_market_count == Decimal("1.000000")
    assert report.watch_market_count == Decimal("2.000000")
    assert report.blocked_market_count == Decimal("3.000000")
    assert report.missing_close_time_count == Decimal("1.000000")
    assert report.stale_source_refresh_count == Decimal("1.000000")
    assert report.source_timestamp_before_close_count == Decimal("1.000000")
    assert report.missing_team_acknowledgement_count == Decimal("1.000000")
    assert report.ambiguous_resolution_criteria_count == Decimal("1.000000")
    assert report.issue_ratio == Decimal("0.833333")
    assert report.max_market_close_age_seconds == Decimal("14400.000000")
    assert report.max_source_refresh_age_seconds == Decimal("7200.000000")
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)
    assert tuple(row.market_id for row in report.rows) == (
        "m-missing-close",
        "m-source-before",
        "m-missing-ack",
        "m-stale",
        "m-ambiguous",
        "m-clear",
    )

    stale_row = next(row for row in report.rows if row.market_id == "m-stale")
    assert stale_row.alignment_status == "watch"
    assert stale_row.source_refresh_age_seconds == Decimal("7200.000000")
    assert stale_row.source_refresh_delay_seconds == Decimal("7200.000000")
    assert stale_row.reason_codes == ("official_resolution_source_refresh_stale",)

    before_row = next(row for row in report.rows if row.market_id == "m-source-before")
    assert before_row.source_timestamp_before_close_seconds == Decimal("3600.000000")
    assert before_row.reason_codes == (
        "official_resolution_source_timestamp_before_close",
    )

    for value in _decimal_public_values(report):
        assert value is None or type(value) is Decimal
    for row in report.rows:
        for value in _decimal_public_values(row):
            assert value is None or type(value) is Decimal
        assert row.paper_only is True
        assert row.report_only is True
        assert row.readonly is True
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_empty_report_is_report_only_and_deterministic() -> None:
    report = build_market_close_resolution_source_alignment_report(
        (),
        config=MarketCloseResolutionSourceAlignmentConfig(),
        generated_at=NOW,
    )

    assert report.report_status == "empty"
    assert report.reason_codes == ("empty_market_close_resolution_source_alignment_input",)
    assert report.market_count == Decimal("0.000000")
    assert report.issue_ratio == Decimal("0.000000")
    assert report.max_market_close_age_seconds is None
    assert report.max_source_refresh_age_seconds is None
    assert len(report.derived_validation_digest) == 64
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_json_ready_report_payload_contains_no_float_values() -> None:
    report = _mixed_report()

    data = market_close_resolution_source_alignment_report_payload(report)

    json.dumps(data, sort_keys=True)
    assert _float_paths(data) == ()
    assert data["market_count"] == "6.000000"
    assert data["issue_ratio"] == "0.833333"
    assert data["derived_validation_digest"] == report.derived_validation_digest
    assert data["paper_only"] is True
    assert data["report_only"] is True
    assert data["readonly"] is True
    assert data["rows"][0]["market_id"] == "m-missing-close"
    assert data["rows"][0]["market_close_age_seconds"] is None
    assert data["rows"][3]["source_refresh_delay_seconds"] == "7200.000000"


def test_derived_validation_digest_is_payload_bound_and_tamper_evident() -> None:
    report = _mixed_report()
    duplicate = _mixed_report()

    assert duplicate.derived_validation_digest == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert report.derived_validation_digest != "0" * 64

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_public_dataclasses_are_frozen_and_safe_report_contracts() -> None:
    for contract_class in (
        MarketCloseResolutionSourceAlignmentConfig,
        MarketCloseResolutionSourceAlignmentInputRow,
        MarketCloseResolutionSourceAlignmentRow,
        MarketCloseResolutionSourceAlignmentReport,
    ):
        assert is_dataclass(contract_class)
        assert contract_class.__dataclass_params__.frozen is True
        defaults = {field.name: field.default for field in fields(contract_class)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True
        for field in fields(contract_class):
            assert field.name not in _forbidden_public_field_names()
        for field_name, hint in get_type_hints(contract_class).items():
            if field_name in {"paper_only", "report_only", "readonly"}:
                continue
            assert not _type_uses_float(hint)

    row = _input_row(
        "m-frozen",
        market_close_at=_at(hours=1),
        resolution_source_refreshed_at=_at(minutes=5),
        resolution_source_timestamp_at=_at(minutes=4),
        team_acknowledged_at=_at(minutes=3),
    )
    with pytest.raises(FrozenInstanceError):
        row.market_id = "changed"  # type: ignore[misc]


def test_validation_rejects_naive_datetimes_non_decimal_windows_and_hard_flag_changes() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        _input_row(
            "m-naive",
            market_close_at=datetime(2026, 2, 3, 10, 0),
            resolution_source_refreshed_at=_at(minutes=10),
            resolution_source_timestamp_at=_at(minutes=9),
            team_acknowledged_at=_at(minutes=8),
        )

    with pytest.raises(ValueError, match="Decimal"):
        MarketCloseResolutionSourceAlignmentConfig(
            expected_source_refresh_window_seconds=3600,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="paper_only"):
        MarketCloseResolutionSourceAlignmentConfig(paper_only=False)

    with pytest.raises(ValueError, match="bool"):
        _input_row(
            "m-bool",
            market_close_at=_at(hours=1),
            resolution_source_refreshed_at=_at(minutes=10),
            resolution_source_timestamp_at=_at(minutes=9),
            team_acknowledged_at=_at(minutes=8),
            resolution_criteria_ambiguous=1,  # type: ignore[arg-type]
        )

    class DerivedDateTime(datetime):
        pass

    with pytest.raises(ValueError, match="datetime"):
        _input_row(
            "m-derived-datetime",
            market_close_at=DerivedDateTime(2026, 2, 3, 10, 0, tzinfo=UTC),
            resolution_source_refreshed_at=_at(minutes=10),
            resolution_source_timestamp_at=_at(minutes=9),
            team_acknowledged_at=_at(minutes=8),
        )

    with pytest.raises(ValueError, match="generated_at"):
        build_market_close_resolution_source_alignment_report(
            (
                _input_row(
                    "m-future",
                    market_close_at=NOW + timedelta(seconds=1),
                    resolution_source_refreshed_at=None,
                    resolution_source_timestamp_at=None,
                    team_acknowledged_at=None,
                ),
            ),
            config=MarketCloseResolutionSourceAlignmentConfig(),
            generated_at=NOW,
        )


def test_public_numeric_contract_rejects_float_int_and_unserialized_decimal_payloads() -> None:
    report = _mixed_report()

    with pytest.raises(ValueError, match="market_count"):
        MarketCloseResolutionSourceAlignmentReport(
            generated_at=report.generated_at,
            config_version=report.config_version,
            report_status=report.report_status,
            reason_codes=report.reason_codes,
            market_count=6,  # type: ignore[arg-type]
            pass_market_count=report.pass_market_count,
            watch_market_count=report.watch_market_count,
            blocked_market_count=report.blocked_market_count,
            missing_close_time_count=report.missing_close_time_count,
            stale_source_refresh_count=report.stale_source_refresh_count,
            source_timestamp_before_close_count=(
                report.source_timestamp_before_close_count
            ),
            missing_team_acknowledgement_count=(
                report.missing_team_acknowledgement_count
            ),
            ambiguous_resolution_criteria_count=(
                report.ambiguous_resolution_criteria_count
            ),
            issue_ratio=report.issue_ratio,
            max_market_close_age_seconds=report.max_market_close_age_seconds,
            max_source_refresh_age_seconds=report.max_source_refresh_age_seconds,
            rows=report.rows,
        )

    with pytest.raises(ValueError, match="issue_ratio"):
        MarketCloseResolutionSourceAlignmentReport(
            generated_at=report.generated_at,
            config_version=report.config_version,
            report_status=report.report_status,
            reason_codes=report.reason_codes,
            market_count=report.market_count,
            pass_market_count=report.pass_market_count,
            watch_market_count=report.watch_market_count,
            blocked_market_count=report.blocked_market_count,
            missing_close_time_count=report.missing_close_time_count,
            stale_source_refresh_count=report.stale_source_refresh_count,
            source_timestamp_before_close_count=(
                report.source_timestamp_before_close_count
            ),
            missing_team_acknowledgement_count=(
                report.missing_team_acknowledgement_count
            ),
            ambiguous_resolution_criteria_count=(
                report.ambiguous_resolution_criteria_count
            ),
            issue_ratio=0.5,  # type: ignore[arg-type]
            max_market_close_age_seconds=report.max_market_close_age_seconds,
            max_source_refresh_age_seconds=report.max_source_refresh_age_seconds,
            rows=report.rows,
        )

    payload = market_close_resolution_source_alignment_report_payload(report)
    assert _decimal_paths(payload) == ()
    assert _int_paths(payload) == ()


def test_decimal_normalization_is_independent_of_ambient_decimal_context() -> None:
    with localcontext(Context(prec=4)):
        report = build_market_close_resolution_source_alignment_report(
            (
                _input_row(
                    "m-context",
                    market_close_at=_at(hours=4),
                    resolution_source_refreshed_at=_at(hours=2),
                    resolution_source_timestamp_at=_at(hours=1),
                    team_acknowledged_at=_at(minutes=30),
                ),
            ),
            config=MarketCloseResolutionSourceAlignmentConfig(
                expected_source_refresh_window_seconds=Decimal("3600.000000"),
            ),
            generated_at=NOW,
        )

    assert report.market_count == Decimal("1.000000")
    assert report.max_market_close_age_seconds == Decimal("14400.000000")
    assert report.max_source_refresh_age_seconds == Decimal("7200.000000")
    assert report.issue_ratio == Decimal("1.000000")


@pytest.mark.parametrize("unsafe_fragment", UNSAFE_SURFACE_FRAGMENTS)
def test_public_identifier_and_payload_surface_rejects_unsafe_terms(
    unsafe_fragment: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError, match="unsafe"):
        _input_row(
            "m-safe",
            team_id=f"{unsafe_fragment}-team",
            market_close_at=_at(hours=1),
            resolution_source_refreshed_at=_at(minutes=10),
            resolution_source_timestamp_at=_at(minutes=9),
            team_acknowledged_at=_at(minutes=8),
        )

    report = _mixed_report()
    monkeypatch.setattr(
        module,
        "json_ready_no_floats",
        lambda value: {
            "generated_at": NOW.isoformat(),
            "config_version": (
                DEFAULT_MARKET_CLOSE_RESOLUTION_SOURCE_ALIGNMENT_REPORT_CONFIG_VERSION
            ),
            "report_status": "pass",
            "reason_codes": [
                "market_close_resolution_source_alignment_passed",
            ],
            "market_count": "1.000000",
            "derived_validation_digest": report.derived_validation_digest,
            f"{unsafe_fragment}_surface": "rejected",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )

    with pytest.raises(ValueError, match="unsafe"):
        market_close_resolution_source_alignment_report_payload(report)


def test_duplicate_market_ids_and_manual_report_inconsistency_are_rejected() -> None:
    duplicate = _input_row(
        "m-duplicate",
        market_close_at=_at(hours=1),
        resolution_source_refreshed_at=_at(minutes=10),
        resolution_source_timestamp_at=_at(minutes=9),
        team_acknowledged_at=_at(minutes=8),
    )

    with pytest.raises(ValueError, match="unique"):
        build_market_close_resolution_source_alignment_report(
            (duplicate, duplicate),
            config=MarketCloseResolutionSourceAlignmentConfig(),
            generated_at=NOW,
        )

    report = _mixed_report()
    with pytest.raises(ValueError, match="market_count"):
        MarketCloseResolutionSourceAlignmentReport(
            generated_at=report.generated_at,
            config_version=report.config_version,
            report_status=report.report_status,
            reason_codes=report.reason_codes,
            market_count=Decimal("7.000000"),
            pass_market_count=report.pass_market_count,
            watch_market_count=report.watch_market_count,
            blocked_market_count=report.blocked_market_count,
            missing_close_time_count=report.missing_close_time_count,
            stale_source_refresh_count=report.stale_source_refresh_count,
            source_timestamp_before_close_count=(
                report.source_timestamp_before_close_count
            ),
            missing_team_acknowledgement_count=(
                report.missing_team_acknowledgement_count
            ),
            ambiguous_resolution_criteria_count=(
                report.ambiguous_resolution_criteria_count
            ),
            issue_ratio=report.issue_ratio,
            max_market_close_age_seconds=report.max_market_close_age_seconds,
            max_source_refresh_age_seconds=report.max_source_refresh_age_seconds,
            rows=report.rows,
        )


def test_module_exports_and_source_surface_stay_report_only() -> None:
    assert module.__all__ == (
        "DEFAULT_MARKET_CLOSE_RESOLUTION_SOURCE_ALIGNMENT_REPORT_CONFIG_VERSION",
        "MarketCloseResolutionSourceAlignmentConfig",
        "MarketCloseResolutionSourceAlignmentInputRow",
        "MarketCloseResolutionSourceAlignmentReport",
        "MarketCloseResolutionSourceAlignmentRow",
        "build_market_close_resolution_source_alignment_report",
        "market_close_resolution_source_alignment_report_payload",
    )

    source = Path(module.__file__).read_text(encoding="utf-8").lower()
    assert "requests" not in source
    assert "httpx" not in source
    assert "socket" not in source
    assert "web3" not in source
    assert "py_clob_client" not in source
    assert "psycopg" not in source
    for fragment in _unsafe_surface_fragments():
        assert fragment not in source


def _decimal_public_values(value: object) -> tuple[Decimal | None, ...]:
    values: list[Decimal | None] = []
    for field in fields(value):
        if (
            field.name.endswith("_count")
            or field.name.endswith("_ratio")
            or field.name.endswith("_seconds")
        ):
            item = getattr(value, field.name)
            if item is None:
                values.append(None)
            else:
                assert type(item) is Decimal
                values.append(item)
    return tuple(values)


def _float_paths(value: Any, *, prefix: str = "$") -> tuple[str, ...]:
    if type(value) is float:
        return (prefix,)
    if isinstance(value, dict):
        return tuple(
            path
            for key, item in value.items()
            for path in _float_paths(item, prefix=f"{prefix}.{key}")
        )
    if isinstance(value, list):
        return tuple(
            path
            for index, item in enumerate(value)
            for path in _float_paths(item, prefix=f"{prefix}[{index}]")
        )
    return ()


def _decimal_paths(value: Any, *, prefix: str = "$") -> tuple[str, ...]:
    if type(value) is Decimal:
        return (prefix,)
    if isinstance(value, dict):
        return tuple(
            path
            for key, item in value.items()
            for path in _decimal_paths(item, prefix=f"{prefix}.{key}")
        )
    if isinstance(value, list):
        return tuple(
            path
            for index, item in enumerate(value)
            for path in _decimal_paths(item, prefix=f"{prefix}[{index}]")
        )
    return ()


def _int_paths(value: Any, *, prefix: str = "$") -> tuple[str, ...]:
    if type(value) is int and type(value) is not bool:
        return (prefix,)
    if isinstance(value, dict):
        return tuple(
            path
            for key, item in value.items()
            for path in _int_paths(item, prefix=f"{prefix}.{key}")
        )
    if isinstance(value, list):
        return tuple(
            path
            for index, item in enumerate(value)
            for path in _int_paths(item, prefix=f"{prefix}[{index}]")
        )
    return ()


def _type_uses_float(value: object) -> bool:
    if value is float:
        return True
    return any(_type_uses_float(item) for item in get_args(value))


def _forbidden_public_field_names() -> tuple[str, ...]:
    return (
        _join("market", "slug"),
        "question",
        "payload",
        "dsn",
        _join("li", "ve"),
        _join("or", "der"),
        "recommendation",
        "position",
    )


def _unsafe_surface_fragments() -> tuple[str, ...]:
    return UNSAFE_SURFACE_FRAGMENTS


def _join(*parts: str) -> str:
    return "".join(parts)
