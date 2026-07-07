from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
import inspect
from json import dumps

import pytest

import polymarket_alpha_lab.market_probability_context_refresh_pressure_report as report_module
from polymarket_alpha_lab.market_probability_context_refresh_pressure_report import (
    MarketProbabilityContextRefreshPressureConfig,
    MarketProbabilityContextRefreshPressureReport,
    MarketProbabilityContextRefreshPressureRow,
    MarketProbabilityContextRefreshPressureSnapshot,
    build_market_probability_context_refresh_pressure_report,
    market_probability_context_refresh_pressure_report_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def _snapshot(
    market_id: str,
    *,
    probability_delta: Decimal = Decimal("0.150000"),
    previous_probability: Decimal = Decimal("0.400000"),
    current_probability: Decimal | None = None,
    probability_observed_at: datetime | None = None,
    context_refreshed_at: datetime | None = None,
    evidence_refreshed_at: datetime | None = None,
    acknowledged_at: datetime | None = None,
    source_count: Decimal = Decimal("2"),
) -> MarketProbabilityContextRefreshPressureSnapshot:
    return MarketProbabilityContextRefreshPressureSnapshot(
        market_id=market_id,
        probability_observed_at=(
            GENERATED_AT - timedelta(seconds=30)
            if probability_observed_at is None
            else probability_observed_at
        ),
        previous_probability=previous_probability,
        current_probability=(
            previous_probability + probability_delta
            if current_probability is None
            else current_probability
        ),
        probability_delta=probability_delta,
        context_refreshed_at=context_refreshed_at,
        evidence_refreshed_at=evidence_refreshed_at,
        acknowledged_at=acknowledged_at,
        source_count=source_count,
    )


def test_report_flags_material_unacknowledged_probability_moves_by_pressure() -> None:
    report = build_market_probability_context_refresh_pressure_report(
        (
            _snapshot(
                "fresh-acknowledged",
                probability_delta=Decimal("0.180000"),
                context_refreshed_at=GENERATED_AT - timedelta(seconds=10),
                evidence_refreshed_at=GENERATED_AT - timedelta(seconds=12),
                acknowledged_at=GENERATED_AT - timedelta(seconds=5),
            ),
            _snapshot(
                "stale-watch",
                probability_delta=Decimal("0.110000"),
                context_refreshed_at=GENERATED_AT - timedelta(seconds=120),
                evidence_refreshed_at=GENERATED_AT - timedelta(seconds=90),
            ),
            _snapshot(
                "missing-blocked",
                probability_delta=Decimal("-0.220000"),
                previous_probability=Decimal("0.620000"),
                current_probability=Decimal("0.400000"),
            ),
            _snapshot(
                "immaterial",
                probability_delta=Decimal("0.030000"),
                context_refreshed_at=GENERATED_AT - timedelta(seconds=1),
                evidence_refreshed_at=GENERATED_AT - timedelta(seconds=1),
            ),
        ),
        config=MarketProbabilityContextRefreshPressureConfig(
            material_probability_delta=Decimal("0.100000"),
            max_context_age_seconds=Decimal("60.000000"),
            max_evidence_age_seconds=Decimal("60.000000"),
            max_unacknowledged_age_seconds=Decimal("45.000000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert report.status == "blocked"
    assert report.reason_codes == (
        "market_probability_context_refresh_missing",
        "market_probability_context_refresh_stale",
        "market_probability_move_unacknowledged",
    )
    assert report.market_count == Decimal("4")
    assert report.material_move_count == Decimal("3")
    assert report.blocked_count == Decimal("1")
    assert report.watch_count == Decimal("1")
    assert report.pass_count == Decimal("2")
    assert report.refresh_pressure_count == Decimal("2")
    assert report.refresh_pressure_ratio == Decimal("0.500000")
    assert tuple(row.market_id for row in report.rows) == (
        "missing-blocked",
        "stale-watch",
        "fresh-acknowledged",
        "immaterial",
    )
    assert tuple(row.status for row in report.rows) == (
        "blocked",
        "watch",
        "pass",
        "pass",
    )
    assert report.rows[0].absolute_probability_delta == Decimal("0.220000")
    assert report.rows[0].context_age_seconds is None
    assert report.rows[0].reason_codes == (
        "market_probability_context_refresh_missing",
        "market_probability_move_unacknowledged",
    )
    assert report.rows[1].context_age_seconds == Decimal("120.000000")
    assert report.rows[1].evidence_age_seconds == Decimal("90.000000")
    assert report.rows[1].unacknowledged_age_seconds == Decimal("30.000000")
    assert report.rows[1].reason_codes == (
        "market_probability_context_refresh_stale",
        "market_probability_evidence_refresh_stale",
        "market_probability_move_unacknowledged",
    )
    assert report.rows[2].reason_codes == ("market_probability_context_current",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_report_status_blocks_when_unacknowledged_material_move_exceeds_sla() -> None:
    report = build_market_probability_context_refresh_pressure_report(
        (
            _snapshot(
                "overdue-acknowledgement",
                probability_observed_at=GENERATED_AT - timedelta(seconds=120),
                context_refreshed_at=GENERATED_AT - timedelta(seconds=5),
                evidence_refreshed_at=GENERATED_AT - timedelta(seconds=5),
            ),
        ),
        config=MarketProbabilityContextRefreshPressureConfig(
            material_probability_delta=Decimal("0.100000"),
            max_context_age_seconds=Decimal("300.000000"),
            max_evidence_age_seconds=Decimal("300.000000"),
            max_unacknowledged_age_seconds=Decimal("60.000000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert report.rows[0].reason_codes == (
        "market_probability_move_unacknowledged",
    )
    assert report.rows[0].status == "blocked"
    assert report.blocked_count == Decimal("1")
    assert report.reason_codes == ("market_probability_move_unacknowledged",)
    assert report.status == "blocked"


def test_timezone_aware_datetimes_normalize_to_utc_for_age_seconds() -> None:
    eastern = timezone(timedelta(hours=-4))

    report = build_market_probability_context_refresh_pressure_report(
        (
            _snapshot(
                "offset-market",
                probability_observed_at=datetime(
                    2026,
                    7,
                    2,
                    7,
                    59,
                    30,
                    tzinfo=eastern,
                ),
                context_refreshed_at=datetime(
                    2026,
                    7,
                    2,
                    7,
                    59,
                    0,
                    tzinfo=eastern,
                ),
                evidence_refreshed_at=datetime(
                    2026,
                    7,
                    2,
                    7,
                    59,
                    15,
                    tzinfo=eastern,
                ),
                acknowledged_at=datetime(
                    2026,
                    7,
                    2,
                    7,
                    59,
                    45,
                    tzinfo=eastern,
                ),
            ),
        ),
        config=MarketProbabilityContextRefreshPressureConfig(
            material_probability_delta=Decimal("0.100000"),
            max_context_age_seconds=Decimal("120.000000"),
            max_evidence_age_seconds=Decimal("120.000000"),
            max_unacknowledged_age_seconds=Decimal("120.000000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert report.rows[0].probability_observed_at == datetime(
        2026,
        7,
        2,
        11,
        59,
        30,
        tzinfo=UTC,
    )
    assert report.rows[0].context_age_seconds == Decimal("60.000000")
    assert report.rows[0].evidence_age_seconds == Decimal("45.000000")
    assert report.rows[0].unacknowledged_age_seconds == Decimal("15.000000")


def test_payload_helper_is_json_ready_without_float_values() -> None:
    report = build_market_probability_context_refresh_pressure_report(
        (
            _snapshot(
                "payload-market",
                context_refreshed_at=GENERATED_AT - timedelta(seconds=90),
                evidence_refreshed_at=GENERATED_AT - timedelta(seconds=30),
            ),
        ),
        config=MarketProbabilityContextRefreshPressureConfig(
            material_probability_delta=Decimal("0.100000"),
            max_context_age_seconds=Decimal("60.000000"),
            max_evidence_age_seconds=Decimal("60.000000"),
            max_unacknowledged_age_seconds=Decimal("60.000000"),
        ),
        generated_at=GENERATED_AT,
    )

    payload = market_probability_context_refresh_pressure_report_payload(report)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["market_count"] == "1"
    assert payload["refresh_pressure_ratio"] == "1.000000"
    assert payload["rows"][0]["context_age_seconds"] == "90.000000"
    assert payload["rows"][0]["probability_delta"] == "0.150000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _float_paths(payload) == ()
    dumps(payload, sort_keys=True)


def test_report_exposes_deterministic_derived_validation_digest() -> None:
    report = build_market_probability_context_refresh_pressure_report(
        (
            _snapshot(
                "digest-market",
                context_refreshed_at=GENERATED_AT - timedelta(seconds=90),
                evidence_refreshed_at=GENERATED_AT - timedelta(seconds=30),
            ),
        ),
        config=MarketProbabilityContextRefreshPressureConfig(
            material_probability_delta=Decimal("0.100000"),
            max_context_age_seconds=Decimal("60.000000"),
            max_evidence_age_seconds=Decimal("60.000000"),
            max_unacknowledged_age_seconds=Decimal("60.000000"),
        ),
        generated_at=GENERATED_AT,
    )
    repeated = build_market_probability_context_refresh_pressure_report(
        (
            _snapshot(
                "digest-market",
                context_refreshed_at=GENERATED_AT - timedelta(seconds=90),
                evidence_refreshed_at=GENERATED_AT - timedelta(seconds=30),
            ),
        ),
        config=MarketProbabilityContextRefreshPressureConfig(
            material_probability_delta=Decimal("0.100000"),
            max_context_age_seconds=Decimal("60.000000"),
            max_evidence_age_seconds=Decimal("60.000000"),
            max_unacknowledged_age_seconds=Decimal("60.000000"),
        ),
        generated_at=GENERATED_AT,
    )
    changed = build_market_probability_context_refresh_pressure_report(
        (
            _snapshot(
                "digest-market",
                context_refreshed_at=GENERATED_AT - timedelta(seconds=90),
                evidence_refreshed_at=GENERATED_AT - timedelta(seconds=30),
            ),
        ),
        config=MarketProbabilityContextRefreshPressureConfig(
            material_probability_delta=Decimal("0.200000"),
            max_context_age_seconds=Decimal("60.000000"),
            max_evidence_age_seconds=Decimal("60.000000"),
            max_unacknowledged_age_seconds=Decimal("60.000000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)
    assert report.derived_validation_digest == repeated.derived_validation_digest
    assert report.derived_validation_digest != changed.derived_validation_digest

    payload = market_probability_context_refresh_pressure_report_payload(report)
    assert payload["derived_validation_digest"] == report.derived_validation_digest

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="not-a-real-digest")


def test_report_rejects_rows_with_tampered_derived_age_fields() -> None:
    report = build_market_probability_context_refresh_pressure_report(
        (
            _snapshot(
                "tampered-age-market",
                probability_observed_at=GENERATED_AT - timedelta(seconds=30),
                context_refreshed_at=GENERATED_AT - timedelta(seconds=10),
                evidence_refreshed_at=GENERATED_AT - timedelta(seconds=20),
                acknowledged_at=GENERATED_AT - timedelta(seconds=5),
            ),
        ),
        config=MarketProbabilityContextRefreshPressureConfig(
            material_probability_delta=Decimal("0.100000"),
            max_context_age_seconds=Decimal("60.000000"),
            max_evidence_age_seconds=Decimal("60.000000"),
            max_unacknowledged_age_seconds=Decimal("60.000000"),
        ),
        generated_at=GENERATED_AT,
    )
    rows = (
        replace(
            report.rows[0],
            context_age_seconds=Decimal("11.000000"),
        ),
    )
    derived_validation_digest = report_module._derived_validation_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        material_probability_delta=report.material_probability_delta,
        max_context_age_seconds=report.max_context_age_seconds,
        max_evidence_age_seconds=report.max_evidence_age_seconds,
        max_unacknowledged_age_seconds=report.max_unacknowledged_age_seconds,
        status=report.status,
        market_count=report.market_count,
        material_move_count=report.material_move_count,
        blocked_count=report.blocked_count,
        watch_count=report.watch_count,
        pass_count=report.pass_count,
        refresh_pressure_count=report.refresh_pressure_count,
        refresh_pressure_ratio=report.refresh_pressure_ratio,
        reason_codes=report.reason_codes,
        rows=rows,
    )

    with pytest.raises(ValueError, match="context_age_seconds must match timestamps"):
        replace(
            report,
            rows=rows,
            derived_validation_digest=derived_validation_digest,
        )


def test_public_dataclasses_are_frozen_and_avoid_float_or_int_annotations() -> None:
    for dataclass_type in (
        MarketProbabilityContextRefreshPressureConfig,
        MarketProbabilityContextRefreshPressureSnapshot,
        MarketProbabilityContextRefreshPressureRow,
        MarketProbabilityContextRefreshPressureReport,
    ):
        assert is_dataclass(dataclass_type)
        assert dataclass_type.__dataclass_params__.frozen is True
        annotations = dataclass_type.__annotations__.values()
        assert all("float" not in str(annotation) for annotation in annotations)
        assert all("int" not in str(annotation) for annotation in annotations)


def test_validates_safety_flags_datetimes_decimals_future_rows_and_duplicates() -> None:
    snapshot = _snapshot("dup-market")

    with pytest.raises(FrozenInstanceError):
        snapshot.market_id = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(snapshot, paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(MarketProbabilityContextRefreshPressureConfig(), readonly=False)

    with pytest.raises(ValueError, match="timezone-aware"):
        _snapshot(
            "naive-market",
            probability_observed_at=datetime(2026, 7, 2, 11, 59, 30),
        )

    with pytest.raises(ValueError, match="Decimal"):
        MarketProbabilityContextRefreshPressureConfig(
            material_probability_delta=0.1,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="future"):
        build_market_probability_context_refresh_pressure_report(
            (
                _snapshot(
                    "future-market",
                    probability_observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
            config=MarketProbabilityContextRefreshPressureConfig(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="duplicate market_id"):
        build_market_probability_context_refresh_pressure_report(
            (snapshot, snapshot),
            config=MarketProbabilityContextRefreshPressureConfig(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="unsafe live surface"):
        market_probability_context_refresh_pressure_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "broker_order_submit_advice": "never",
            },
        )


def test_rejects_payload_ints_naive_datetimes_missing_flags_and_unsafe_surfaces() -> None:
    with pytest.raises(ValueError, match="paper_only must be True"):
        market_probability_context_refresh_pressure_report_payload(
            {
                "report_only": True,
                "readonly": True,
            },
        )

    with pytest.raises(ValueError, match="report_only must be True"):
        market_probability_context_refresh_pressure_report_payload(
            {
                "paper_only": True,
                "report_only": False,
                "readonly": True,
            },
        )

    with pytest.raises(ValueError, match="public numeric values must be Decimal strings"):
        market_probability_context_refresh_pressure_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "market_count": 1,
            },
        )

    with pytest.raises(ValueError, match="public numeric values must be Decimal strings"):
        market_probability_context_refresh_pressure_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "refresh_pressure_ratio": 0.5,
            },
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        market_probability_context_refresh_pressure_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "generated_at": datetime(2026, 7, 2, 12, 0),
            },
        )

    class NoneOffsetTimezone(tzinfo):
        def utcoffset(self, dt: datetime | None) -> None:
            return None

        def dst(self, dt: datetime | None) -> None:
            return None

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        market_probability_context_refresh_pressure_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "generated_at": datetime(
                    2026,
                    7,
                    2,
                    12,
                    0,
                    tzinfo=NoneOffsetTimezone(),
                ),
            },
        )

    class DatetimeSubclass(datetime):
        pass

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        market_probability_context_refresh_pressure_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "generated_at": DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
            },
        )

    with pytest.raises(ValueError, match="unsafe live surface"):
        market_probability_context_refresh_pressure_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "rows": [{"market_id": "wallet-market"}],
            },
        )

    with pytest.raises(ValueError, match="readonly must be True"):
        market_probability_context_refresh_pressure_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "rows": [
                    {
                        "market_id": "nested-flag-market",
                        "paper_only": True,
                        "report_only": True,
                        "readonly": False,
                    },
                ],
            },
        )

    for unsafe_key in (
        "live_mode",
        "auth_token",
        "wallet_address",
        "order_id",
        "network_endpoint",
        "database_url",
        "persist_path",
    ):
        with pytest.raises(ValueError, match="unsafe live surface"):
            market_probability_context_refresh_pressure_report_payload(
                {
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                    unsafe_key: "redacted",
                },
            )

    for unsafe_value in (
        "live trading enabled",
        "auth bearer token",
        "wallet signer",
        "order placement",
        "network://polymarket.example",
        "database connection string",
        "persist report to disk",
    ):
        with pytest.raises(ValueError, match="unsafe live surface"):
            market_probability_context_refresh_pressure_report_payload(
                {
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                    "diagnostic": unsafe_value,
                },
            )


def test_module_scope_has_no_live_network_storage_or_process_imports() -> None:
    source = inspect.getsource(report_module)
    forbidden_terms = (
        "psycopg",
        "supabase",
        "requests",
        "httpx",
        "socket",
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
