from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re

import pytest

from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition import (
    build_paper_autonomous_screening_decision_support_gate_transition_report,
)
from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_trend import (
    PaperAutonomousScreeningDecisionSupportGateTransitionTrendReport,
    build_paper_autonomous_screening_decision_support_gate_transition_trend_report,
)
from tests.test_paper_autonomous_screening_decision_support_gate_transition import (
    _gate_report,
)


GENERATED_AT = datetime(2026, 6, 26, 12, 0, tzinfo=UTC)
FIRST_TRANSITION_AT = datetime(2026, 6, 24, 12, 0, tzinfo=UTC)
LATEST_TRANSITION_AT = datetime(2026, 6, 25, 12, 0, tzinfo=UTC)
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


class TrendReportSubclass(
    PaperAutonomousScreeningDecisionSupportGateTransitionTrendReport,
):
    pass


def _transition_report(
    *,
    generated_at: datetime,
    first_gate_at: datetime,
    second_gate_at: datetime,
    from_status: str = "pass",
    to_status: str = "watch",
):
    return build_paper_autonomous_screening_decision_support_gate_transition_report(
        [
            _gate_report(generated_at=first_gate_at, gate_status=from_status),
            _gate_report(generated_at=second_gate_at, gate_status=to_status),
        ],
        generated_at=generated_at,
    )


def _trend_report(
    *,
    config_version: str = (
        "paper-autonomous-screening-decision-support-gate-transition-trend-v0"
    ),
) -> PaperAutonomousScreeningDecisionSupportGateTransitionTrendReport:
    first = _transition_report(
        generated_at=FIRST_TRANSITION_AT,
        first_gate_at=datetime(2026, 6, 22, 12, 0, tzinfo=UTC),
        second_gate_at=datetime(2026, 6, 23, 12, 0, tzinfo=UTC),
        from_status="pass",
        to_status="pass",
    )
    latest = _transition_report(
        generated_at=LATEST_TRANSITION_AT,
        first_gate_at=datetime(2026, 6, 23, 12, 0, tzinfo=UTC),
        second_gate_at=datetime(2026, 6, 24, 12, 0, tzinfo=UTC),
        from_status="pass",
        to_status="watch",
    )
    return build_paper_autonomous_screening_decision_support_gate_transition_trend_report(
        [first, latest],
        config_version=config_version,
        generated_at=GENERATED_AT,
    )


def _empty_trend_report() -> PaperAutonomousScreeningDecisionSupportGateTransitionTrendReport:
    return build_paper_autonomous_screening_decision_support_gate_transition_trend_report(
        [],
        generated_at=GENERATED_AT,
    )


def _row_values(row: object) -> dict[str, object]:
    return dict(row.__dict__)


def _canonical_payload_sha256(payload_json: dict[str, object]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _assert_json_clean(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("trend DB JSON contains floats")
    if isinstance(value, Decimal):
        pytest.fail("trend DB JSON contains raw Decimal values")
    if isinstance(value, datetime):
        pytest.fail("trend DB JSON contains raw datetime values")
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            _assert_json_clean(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_json_clean(item)


def test_trend_db_row_serializes_canonical_payload_and_round_trips() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_trend_db_row as codec

    report = _trend_report()

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperAutonomousScreeningDecisionSupportGateTransitionTrendDbRow
    assert SHA256_RE.fullmatch(row.report_sha256)
    assert row.generated_at == GENERATED_AT
    assert (
        row.config_version
        == "paper-autonomous-screening-decision-support-gate-transition-trend-v0"
    )
    assert row.transition_report_count == 2
    assert row.first_transition_generated_at == FIRST_TRANSITION_AT
    assert row.latest_transition_generated_at == LATEST_TRANSITION_AT
    assert row.latest_from_gate_status == "pass"
    assert row.latest_to_gate_status == "watch"
    assert row.latest_introduced_reason_code_count == (
        report.latest_introduced_reason_code_count
    )
    assert row.latest_cleared_reason_code_count == (
        report.latest_cleared_reason_code_count
    )
    assert row.latest_persistent_reason_code_count == (
        report.latest_persistent_reason_code_count
    )
    assert row.latest_transition_count == 1
    assert row.latest_instability_ratio == report.latest_instability_ratio
    assert isinstance(row.latest_instability_ratio, Decimal)
    assert row.payload_json["generated_at"] == "2026-06-26T12:00:00+00:00"
    assert (
        row.payload_json["latest_instability_ratio"]
        == f"{report.latest_instability_ratio:.6f}"
    )
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.payload_json["readonly"] is True
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.report_sha256 == _canonical_payload_sha256(row.payload_json)
    _assert_json_clean(row.payload_json)

    assert codec.from_db_row(row) == report
    assert (
        codec.paper_autonomous_screening_decision_support_gate_transition_trend_report_to_db_row(
            report,
        )
        == row
    )
    assert (
        codec.paper_autonomous_screening_decision_support_gate_transition_trend_report_from_db_row(
            row,
        )
        == report
    )


def test_trend_db_row_preserves_empty_trend_report() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_trend_db_row as codec

    report = _empty_trend_report()

    row = codec.to_db_row(report)

    assert row.transition_report_count == 0
    assert row.first_transition_generated_at is None
    assert row.latest_transition_generated_at is None
    assert row.latest_from_gate_status is None
    assert row.latest_to_gate_status is None
    assert row.latest_introduced_reason_code_count == 0
    assert row.latest_cleared_reason_code_count == 0
    assert row.latest_persistent_reason_code_count == 0
    assert row.latest_transition_count == 0
    assert row.latest_instability_ratio is None
    assert row.payload_json["latest_instability_ratio"] is None
    assert codec.from_db_row(row) == report


def test_trend_db_row_hash_is_deterministic_for_equivalent_decimal_payloads() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_trend_db_row as codec

    report = _trend_report()
    equivalent_report = PaperAutonomousScreeningDecisionSupportGateTransitionTrendReport(
        **{
            **report.__dict__,
            "latest_instability_ratio": Decimal(
                f"{report.latest_instability_ratio:.7f}",
            ),
        },
    )
    different_report = _trend_report(
        config_version=(
            "paper-autonomous-screening-decision-support-gate-transition-trend-v1"
        ),
    )

    first = codec.to_db_row(report)
    second = codec.to_db_row(equivalent_report)
    third = codec.to_db_row(different_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_trend_db_row_is_frozen() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_trend_db_row as codec

    row = codec.to_db_row(_trend_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_trend_db_row_rejects_wrong_report_types_and_subclasses() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_trend_db_row as codec

    with pytest.raises(
        ValueError,
        match="PaperAutonomousScreeningDecisionSupportGateTransitionTrendReport",
    ):
        codec.to_db_row(object())

    report = _trend_report()
    subclass = TrendReportSubclass(**report.__dict__)
    with pytest.raises(
        ValueError,
        match="PaperAutonomousScreeningDecisionSupportGateTransitionTrendReport",
    ):
        codec.to_db_row(subclass)


def test_trend_db_row_rejects_wrong_row_types_and_subclasses() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_trend_db_row as codec

    row = codec.to_db_row(_trend_report())

    class TrendDbRowSubclass(
        codec.PaperAutonomousScreeningDecisionSupportGateTransitionTrendDbRow,
    ):
        pass

    with pytest.raises(
        ValueError,
        match="PaperAutonomousScreeningDecisionSupportGateTransitionTrendDbRow",
    ):
        codec.from_db_row(object())
    with pytest.raises(
        ValueError,
        match="PaperAutonomousScreeningDecisionSupportGateTransitionTrendDbRow",
    ):
        codec.from_db_row(TrendDbRowSubclass(**_row_values(row)))


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_trend_db_row_rejects_false_report_flags_before_write(
    flag_name: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_trend_db_row as codec

    report = _trend_report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


def test_trend_db_row_rejects_corrupted_stored_payload_flags() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_trend_db_row as codec

    row = codec.to_db_row(_trend_report())
    payload = {
        **row.payload_json,
        "readonly": False,
    }
    values = {
        **_row_values(row),
        "report_sha256": _canonical_payload_sha256(payload),
        "payload_json": payload,
    }

    with pytest.raises(ValueError, match="readonly"):
        codec.PaperAutonomousScreeningDecisionSupportGateTransitionTrendDbRow(**values)
    with pytest.raises(ValueError, match="readonly"):
        replace(row, **values)

    malformed = object.__new__(
        codec.PaperAutonomousScreeningDecisionSupportGateTransitionTrendDbRow,
    )
    for field_name, value in values.items():
        object.__setattr__(malformed, field_name, value)

    with pytest.raises(ValueError, match="readonly"):
        codec.from_db_row(malformed)


def test_trend_db_row_rejects_recursive_floats_and_decimals_in_json_payload() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_trend_db_row as codec

    row = codec.to_db_row(_trend_report())

    with pytest.raises(ValueError, match="payload_json"):
        replace(row, payload_json={**row.payload_json, "bad_float": 0.1})
    with pytest.raises(ValueError, match="payload_json"):
        replace(row, payload_json={**row.payload_json, "bad_decimal": Decimal("0.1")})


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 26, 12, 1, tzinfo=UTC)}, "generated_at"),
        ({"config_version": "trend-v1"}, "config_version"),
        ({"transition_report_count": 3}, "transition_report_count"),
        (
            {"first_transition_generated_at": datetime(2026, 6, 23, tzinfo=UTC)},
            "first_transition_generated_at",
        ),
        (
            {"latest_transition_generated_at": datetime(2026, 6, 26, tzinfo=UTC)},
            "latest_transition_generated_at",
        ),
        ({"latest_from_gate_status": "blocked"}, "latest_from_gate_status"),
        ({"latest_to_gate_status": "blocked"}, "latest_to_gate_status"),
        (
            {"latest_introduced_reason_code_count": 99},
            "latest_introduced_reason_code_count",
        ),
        (
            {"latest_cleared_reason_code_count": 99},
            "latest_cleared_reason_code_count",
        ),
        (
            {"latest_persistent_reason_code_count": 99},
            "latest_persistent_reason_code_count",
        ),
        ({"latest_transition_count": 99}, "latest_transition_count"),
        (
            {"latest_instability_ratio": Decimal("0.999999")},
            "latest_instability_ratio",
        ),
    ),
)
def test_trend_db_row_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_trend_db_row as codec

    row = codec.to_db_row(_trend_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperAutonomousScreeningDecisionSupportGateTransitionTrendDbRow(
            **{**_row_values(row), **overrides},
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "bad"}, "report_sha256"),
        ({"config_version": ""}, "config_version"),
        ({"transition_report_count": True}, "transition_report_count"),
        ({"latest_introduced_reason_code_count": -1}, "latest_introduced"),
        ({"latest_transition_count": -1}, "latest_transition_count"),
        ({"latest_from_gate_status": "paused"}, "latest_from_gate_status"),
        ({"latest_instability_ratio": Decimal("1.000001")}, "latest_instability_ratio"),
        ({"latest_instability_ratio": 0.5}, "latest_instability_ratio"),
        ({"payload_json": []}, "payload_json"),
        ({"paper_only": False}, "paper_only"),
    ),
)
def test_trend_db_row_validates_row_shape(
    overrides: dict[str, object],
    message: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_trend_db_row as codec

    row = codec.to_db_row(_trend_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperAutonomousScreeningDecisionSupportGateTransitionTrendDbRow(
            **{**_row_values(row), **overrides},
        )


@pytest.mark.parametrize(
    ("base_report_factory", "overrides", "message"),
    (
        (
            _empty_trend_report,
            {
                "first_transition_generated_at": FIRST_TRANSITION_AT,
                "latest_transition_generated_at": LATEST_TRANSITION_AT,
            },
            "transition_report_count",
        ),
        (
            _trend_report,
            {
                "first_transition_generated_at": None,
                "latest_transition_generated_at": None,
            },
            "transition_report_count",
        ),
        (
            _empty_trend_report,
            {
                "latest_from_gate_status": "pass",
                "latest_to_gate_status": "watch",
            },
            "latest_transition_count",
        ),
        (
            _trend_report,
            {
                "latest_from_gate_status": None,
                "latest_to_gate_status": None,
            },
            "latest_transition_count",
        ),
    ),
)
def test_trend_db_row_matches_migration_count_nullability_constraints(
    base_report_factory: object,
    overrides: dict[str, object],
    message: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_trend_db_row as codec

    row = codec.to_db_row(base_report_factory())
    payload = {**row.payload_json, **{key: codec._json_ready(value) for key, value in overrides.items()}}

    with pytest.raises(ValueError, match=message):
        codec.PaperAutonomousScreeningDecisionSupportGateTransitionTrendDbRow(
            **{
                **_row_values(row),
                **overrides,
                "payload_json": payload,
                "report_sha256": _canonical_payload_sha256(payload),
            },
        )


def test_trend_db_row_module_is_pure_codec() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_trend_db_row as codec

    assert codec.__name__.endswith("_db_row")
    source = Path(
        "src/polymarket_alpha_lab/"
        "paper_autonomous_screening_decision_support_gate_transition_trend_db_row.py",
    ).read_text(encoding="utf-8")

    for banned in (
        "psycopg",
        "network",
        "client",
        "auth",
        "wallet",
        "account",
        "signing",
        "submission",
        "cancellation",
        "replacement",
        "exchange",
        "live_trading",
    ):
        assert banned not in source.lower()
