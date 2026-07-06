from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.research_packet_event_update_completeness_gate_v2 import (
    DEFAULT_RESEARCH_PACKET_EVENT_UPDATE_COMPLETENESS_GATE_V2_CONFIG_VERSION,
    ResearchPacketEventUpdateCompletenessGateV2Config,
    ResearchPacketEventUpdateCompletenessGateV2Observation,
    ResearchPacketEventUpdateCompletenessGateV2Report,
    ResearchPacketEventUpdateCompletenessGateV2Row,
    build_research_packet_event_update_completeness_gate_v2,
    research_packet_event_update_completeness_gate_v2_payload,
    validate_research_packet_event_update_completeness_gate_v2_public_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def _fragment(*parts: str) -> str:
    return "".join(parts)


def _config(**overrides: object) -> ResearchPacketEventUpdateCompletenessGateV2Config:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_PACKET_EVENT_UPDATE_COMPLETENESS_GATE_V2_CONFIG_VERSION
        ),
        "missing_update_penalty": Decimal("0.250000"),
        "official_update_boost": Decimal("0.100000"),
        "min_pass_score": Decimal("0.800000"),
    }
    values.update(overrides)
    return ResearchPacketEventUpdateCompletenessGateV2Config(**values)


def _observation(
    packet_id: str,
    event_id: str,
    *,
    team_id: str = "politics",
    packet_generated_at: datetime | None = None,
    official_update_observed_at: datetime | None = None,
    event_status_update_observed_at: datetime | None = None,
    resolution_update_observed_at: datetime | None = None,
    forecast_update_observed_at: datetime | None = None,
) -> ResearchPacketEventUpdateCompletenessGateV2Observation:
    return ResearchPacketEventUpdateCompletenessGateV2Observation(
        packet_id=packet_id,
        event_id=event_id,
        team_id=team_id,
        packet_generated_at=(
            packet_generated_at
            if packet_generated_at is not None
            else GENERATED_AT - timedelta(minutes=30)
        ),
        official_update_observed_at=official_update_observed_at,
        event_status_update_observed_at=event_status_update_observed_at,
        resolution_update_observed_at=resolution_update_observed_at,
        forecast_update_observed_at=forecast_update_observed_at,
        source_config_version="research-packet-event-update-completeness-source-v0",
    )


def _complete_observation(
    packet_id: str,
    event_id: str,
    *,
    team_id: str = "politics",
) -> ResearchPacketEventUpdateCompletenessGateV2Observation:
    return _observation(
        packet_id,
        event_id,
        team_id=team_id,
        official_update_observed_at=GENERATED_AT - timedelta(minutes=20),
        event_status_update_observed_at=GENERATED_AT - timedelta(minutes=15),
        resolution_update_observed_at=GENERATED_AT - timedelta(minutes=10),
        forecast_update_observed_at=GENERATED_AT - timedelta(minutes=5),
    )


def _assert_no_float_values(value: Any) -> None:
    assert not isinstance(value, float)
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_float_values(item)


def test_gate_scores_event_update_completeness_with_penalties_and_boosts() -> None:
    report = build_research_packet_event_update_completeness_gate_v2(
        (
            _observation(
                "boosted_pass",
                "event_2",
                official_update_observed_at=GENERATED_AT - timedelta(minutes=20),
                event_status_update_observed_at=GENERATED_AT - timedelta(minutes=15),
                resolution_update_observed_at=GENERATED_AT - timedelta(minutes=10),
                forecast_update_observed_at=None,
            ),
            _observation(
                "blocked_missing_official",
                "event_1",
                team_id="sports_soccer",
                official_update_observed_at=None,
                event_status_update_observed_at=GENERATED_AT - timedelta(minutes=15),
                resolution_update_observed_at=GENERATED_AT - timedelta(minutes=10),
                forecast_update_observed_at=GENERATED_AT - timedelta(minutes=5),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, ResearchPacketEventUpdateCompletenessGateV2Report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        DEFAULT_RESEARCH_PACKET_EVENT_UPDATE_COMPLETENESS_GATE_V2_CONFIG_VERSION
    )
    assert report.gate_status == "blocked"
    assert report.next_step == "hold_research_packet_until_event_updates_complete"
    assert report.packet_count == Decimal("2.000000")
    assert report.event_count == Decimal("2.000000")
    assert report.team_count == Decimal("2.000000")
    assert report.pass_row_count == Decimal("1.000000")
    assert report.blocked_row_count == Decimal("1.000000")
    assert report.required_update_count == Decimal("8.000000")
    assert report.present_update_count == Decimal("6.000000")
    assert report.missing_update_count == Decimal("2.000000")
    assert report.missing_row_count == Decimal("2.000000")
    assert report.average_completeness_score == Decimal("0.800000")
    assert report.min_completeness_score == Decimal("0.750000")
    assert report.max_missing_update_count == Decimal("1.000000")
    assert report.reason_codes == (
        "research_packet_event_update_completeness_gate_v2_passed",
        "research_packet_event_update_completeness_missing_update",
        "research_packet_event_update_completeness_official_update_boost",
        "research_packet_event_update_completeness_score_below_threshold",
    )
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    blocked, boosted = report.rows
    assert blocked == ResearchPacketEventUpdateCompletenessGateV2Row(
        packet_id="blocked_missing_official",
        event_id="event_1",
        team_id="sports_soccer",
        row_status="blocked",
        packet_generated_at=GENERATED_AT - timedelta(minutes=30),
        official_update_observed_at=None,
        event_status_update_observed_at=GENERATED_AT - timedelta(minutes=15),
        resolution_update_observed_at=GENERATED_AT - timedelta(minutes=10),
        forecast_update_observed_at=GENERATED_AT - timedelta(minutes=5),
        latest_update_observed_at=GENERATED_AT - timedelta(minutes=5),
        latest_update_age_seconds=Decimal("300.000000"),
        required_update_count=Decimal("4.000000"),
        present_update_count=Decimal("3.000000"),
        missing_update_count=Decimal("1.000000"),
        missing_update_penalty_total=Decimal("0.250000"),
        official_update_boost=Decimal("0.000000"),
        completeness_score=Decimal("0.750000"),
        missing_update_codes=("missing_official_update",),
        reason_codes=(
            "research_packet_event_update_completeness_missing_update",
            "research_packet_event_update_completeness_score_below_threshold",
        ),
        source_config_version="research-packet-event-update-completeness-source-v0",
    )
    assert boosted.row_status == "pass"
    assert boosted.missing_update_codes == ("missing_forecast_update",)
    assert boosted.missing_update_penalty_total == Decimal("0.250000")
    assert boosted.official_update_boost == Decimal("0.100000")
    assert boosted.completeness_score == Decimal("0.850000")


def test_gate_passes_complete_inputs_and_blocks_empty_inputs() -> None:
    pass_report = build_research_packet_event_update_completeness_gate_v2(
        (
            _complete_observation("packet_two", "event_two", team_id="sports_soccer"),
            _complete_observation("packet_one", "event_one"),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert pass_report.gate_status == "pass"
    assert pass_report.next_step == "use_research_packet_event_update_report"
    assert pass_report.missing_update_count == Decimal("0.000000")
    assert pass_report.average_completeness_score == Decimal("1.000000")
    assert pass_report.min_completeness_score == Decimal("1.000000")
    assert tuple((row.team_id, row.event_id, row.packet_id) for row in pass_report.rows) == (
        ("politics", "event_one", "packet_one"),
        ("sports_soccer", "event_two", "packet_two"),
    )

    empty_report = build_research_packet_event_update_completeness_gate_v2(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    assert empty_report.gate_status == "blocked"
    assert empty_report.packet_count == Decimal("0.000000")
    assert empty_report.average_completeness_score == Decimal("0.000000")
    assert empty_report.min_completeness_score == Decimal("1.000000")
    assert empty_report.reason_codes == (
        "research_packet_event_update_completeness_gate_v2_empty",
    )


def test_payload_serializes_decimals_as_strings_and_validates_digest() -> None:
    generated_at = datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    observed_at = datetime(2026, 7, 2, 7, 55, tzinfo=timezone(timedelta(hours=-4)))
    report = build_research_packet_event_update_completeness_gate_v2(
        (
            _observation(
                "offset_packet",
                "offset_event",
                official_update_observed_at=observed_at,
                event_status_update_observed_at=observed_at,
                resolution_update_observed_at=observed_at,
                forecast_update_observed_at=observed_at,
            ),
        ),
        config=_config(),
        generated_at=generated_at,
    )

    payload = research_packet_event_update_completeness_gate_v2_payload(report)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["packet_count"] == "1.000000"
    assert payload["average_completeness_score"] == "1.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"][0]["official_update_observed_at"] == (
        "2026-07-02T11:55:00+00:00"
    )
    assert payload["rows"][0]["latest_update_age_seconds"] == "300.000000"
    assert payload["rows"][0]["official_update_boost"] == "0.100000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_no_float_values(payload)

    with pytest.raises(ValueError, match="report"):
        research_packet_event_update_completeness_gate_v2_payload(object())  # type: ignore[arg-type]


def test_dataclasses_are_frozen_decimal_only_and_enforce_hard_flags() -> None:
    with pytest.raises(ValueError, match="config_version"):
        ResearchPacketEventUpdateCompletenessGateV2Config(
            config_version=_StringSubclass(
                DEFAULT_RESEARCH_PACKET_EVENT_UPDATE_COMPLETENESS_GATE_V2_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="missing_update_penalty"):
        _config(missing_update_penalty=0.25)
    with pytest.raises(ValueError, match="official_update_boost"):
        _config(official_update_boost=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="min_pass_score"):
        _config(min_pass_score=Decimal("0.000000"))
    with pytest.raises(ValueError, match="readonly"):
        replace(_config(), readonly=False)
    with pytest.raises(ValueError, match="packet_generated_at"):
        _observation("naive_packet", "event", packet_generated_at=datetime(2026, 7, 2))
    with pytest.raises(ValueError, match="generated_at"):
        build_research_packet_event_update_completeness_gate_v2(
            (_complete_observation("packet", "event"),),
            config=_config(),
            generated_at=_DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        build_research_packet_event_update_completeness_gate_v2(
            (
                _observation(
                    "future_packet",
                    "event",
                    official_update_observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )

    report = build_research_packet_event_update_completeness_gate_v2(
        (_complete_observation("packet", "event"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    for value in (_config(), _complete_observation("frozen", "event"), report.rows[0], report):
        with pytest.raises(FrozenInstanceError):
            value.readonly = False
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report.rows[0], report_only=False)

    for dataclass_type in (
        ResearchPacketEventUpdateCompletenessGateV2Config,
        ResearchPacketEventUpdateCompletenessGateV2Row,
        ResearchPacketEventUpdateCompletenessGateV2Report,
    ):
        instance = (
            report
            if dataclass_type is ResearchPacketEventUpdateCompletenessGateV2Report
            else report.rows[0]
            if dataclass_type is ResearchPacketEventUpdateCompletenessGateV2Row
            else _config()
        )
        for field in fields(dataclass_type):
            if (
                field.name.endswith("_count")
                or field.name.endswith("_score")
                or field.name.endswith("_seconds")
                or field.name.endswith("_penalty")
                or field.name.endswith("_boost")
                or field.name.endswith("_total")
            ):
                value = getattr(instance, field.name)
                assert value is None or type(value) is Decimal


def test_derived_validation_digest_rejects_tampering() -> None:
    report = build_research_packet_event_update_completeness_gate_v2(
        (_complete_observation("packet", "event"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            report,
            rows=(
                replace(
                    report.rows[0],
                    packet_id="packet_rewritten",
                ),
            ),
        )


def test_unsafe_public_keys_and_values_are_rejected() -> None:
    for fragment in (
        _fragment("li", "ve"),
        _fragment("au", "th"),
        _fragment("wa", "llet"),
        _fragment("or", "der"),
        _fragment("net", "work"),
        _fragment("data", "base"),
        _fragment("per", "sist"),
        _fragment("sig", "ning"),
        _fragment("muta", "tion"),
        _fragment("b", "uy"),
        _fragment("se", "ll"),
        _fragment("tra", "de"),
    ):
        with pytest.raises(ValueError, match="unsafe public key"):
            validate_research_packet_event_update_completeness_gate_v2_public_payload(
                {f"{fragment}_field": "safe_value"},
            )
        with pytest.raises(ValueError, match="unsafe public value"):
            validate_research_packet_event_update_completeness_gate_v2_public_payload(
                {"safe_field": f"value_{fragment}"},
            )

    with pytest.raises(ValueError, match="unsafe public value"):
        _observation(f"{_fragment('tra', 'de')}_packet", "event")
    with pytest.raises(ValueError, match="must use Decimal string values"):
        validate_research_packet_event_update_completeness_gate_v2_public_payload(
            {"safe_field": 1},
        )
    with pytest.raises(ValueError, match="readonly"):
        validate_research_packet_event_update_completeness_gate_v2_public_payload(
            {"readonly": False},
        )


def test_module_scope_excludes_unsafe_runtime_surfaces() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.research_packet_event_update_completeness_gate_v2",
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    public_names = set(module.__all__)
    unsafe_fragments = (
        _fragment("li", "ve"),
        _fragment("au", "th"),
        _fragment("wa", "llet"),
        _fragment("or", "der"),
        _fragment("net", "work"),
        _fragment("data", "base"),
        _fragment("per", "sist"),
        _fragment("sig", "ning"),
        _fragment("muta", "tion"),
        _fragment("b", "uy"),
        _fragment("se", "ll"),
        _fragment("tra", "de"),
    )
    assert not any(
        fragment in public_name.lower()
        for public_name in public_names
        for fragment in unsafe_fragments
    )

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "cli",
        "http",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
