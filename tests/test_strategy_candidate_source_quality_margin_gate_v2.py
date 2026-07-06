from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _api() -> Any:
    return import_module(
        "polymarket_alpha_lab.strategy_candidate_source_quality_margin_gate_v2",
    )


def _config(**overrides: object) -> Any:
    api = _api()
    values = {
        "min_source_count": d("2"),
        "min_quality_score": d("0.700000"),
        "min_quality_margin": d("0.050000"),
        "official_source_boost_per_source": d("0.080000"),
        "independent_source_boost_per_source": d("0.040000"),
        "weak_source_penalty_per_source": d("0.150000"),
    }
    values.update(overrides)
    return api.StrategyCandidateSourceQualityMarginGateV2Config(**values)


def _signal(
    source_id: str,
    *,
    candidate_id: str = "candidate-alpha",
    source_kind: str = "independent",
    quality_score: Decimal = d("0.720000"),
    observed_at: datetime | None = None,
    public_note: str | None = None,
) -> Any:
    api = _api()
    return api.StrategyCandidateSourceQualitySignal(
        candidate_id=candidate_id,
        source_id=source_id,
        source_kind=source_kind,
        observed_at=observed_at or GENERATED_AT - timedelta(seconds=60),
        quality_score=quality_score,
        public_note=public_note,
    )


def _payload_item(key: str = "review_note", value: str = "source checks complete") -> Any:
    api = _api()
    return api.StrategyCandidateSourceQualityPublicPayloadItem(key=key, value=value)


def _report(signals: tuple[Any, ...] | list[Any], **overrides: object) -> Any:
    api = _api()
    return api.build_strategy_candidate_source_quality_margin_gate_v2(
        signals,
        config=_config(**overrides),
        generated_at=GENERATED_AT,
        public_payload=(_payload_item(),),
    )


def _bypassed_row(row: object, **overrides: object) -> object:
    malformed = object.__new__(type(row))
    for field in fields(row):
        object.__setattr__(malformed, field.name, getattr(row, field.name))
    for key, value in overrides.items():
        object.__setattr__(malformed, key, value)
    return malformed


def _assert_json_ready(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            assert type(key) is str
            _assert_json_ready(nested)
        return
    if isinstance(value, list):
        for nested in value:
            _assert_json_ready(nested)
        return
    assert value is None or type(value) in (str, bool)


def _walk_strings(value: object) -> tuple[str, ...]:
    if isinstance(value, dict):
        strings: list[str] = []
        for key, nested in value.items():
            strings.append(key)
            strings.extend(_walk_strings(nested))
        return tuple(strings)
    if isinstance(value, list):
        strings = []
        for nested in value:
            strings.extend(_walk_strings(nested))
        return tuple(strings)
    if type(value) is str:
        return (value,)
    return ()


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_public_numbers_are_decimal(value: object) -> None:
    if isinstance(value, Decimal):
        assert type(value) is Decimal
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_public_numbers_are_decimal(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_public_numbers_are_decimal(getattr(value, field.name))


def test_source_quality_margin_scoring_passes_with_official_and_independent_boosts() -> None:
    report = _report(
        (
            _signal(
                "official-source",
                source_kind="official",
                quality_score=d("0.760000"),
                observed_at=datetime(
                    2026,
                    7,
                    6,
                    7,
                    59,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
            ),
            _signal(
                "independent-source",
                source_kind="independent",
                quality_score=d("0.720000"),
            ),
        ),
    )

    assert report.gate_status == "pass"
    assert report.recommended_next_step == "retain_candidate_for_paper_review"
    assert report.candidate_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("0.000000")
    assert report.blocked_count == d("0.000000")
    assert report.signal_count == d("2.000000")
    assert report.reason_codes == (
        "official_source_boost",
        "independent_source_boost",
        "source_quality_margin_pass",
    )

    row = report.rows[0]
    assert row.candidate_id == "candidate-alpha"
    assert row.signal_count == d("2.000000")
    assert row.official_source_count == d("1.000000")
    assert row.independent_source_count == d("1.000000")
    assert row.weak_source_count == d("0.000000")
    assert row.average_quality_score == d("0.740000")
    assert row.official_source_boost == d("0.080000")
    assert row.independent_source_boost == d("0.040000")
    assert row.weak_source_penalty == d("0.000000")
    assert row.adjusted_quality_score == d("0.860000")
    assert row.source_quality_margin_score == d("0.160000")
    assert row.gate_status == "pass"
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_weak_source_penalties_block_or_watch_source_quality_margin() -> None:
    blocked_report = _report(
        (
            _signal(
                "weak-source-a",
                source_kind="weak",
                quality_score=d("0.760000"),
            ),
            _signal(
                "weak-source-b",
                source_kind="weak",
                quality_score=d("0.740000"),
            ),
        ),
    )

    assert blocked_report.gate_status == "blocked"
    assert blocked_report.blocked_count == d("1.000000")
    assert blocked_report.max_weak_source_penalty == d("0.300000")
    assert blocked_report.rows[0].adjusted_quality_score == d("0.450000")
    assert blocked_report.rows[0].source_quality_margin_score == d("-0.250000")
    assert blocked_report.rows[0].reason_codes == (
        "weak_source_penalty",
        "insufficient_source_quality_margin",
    )

    watch_report = _report(
        (
            _signal(
                "independent-source-a",
                source_kind="independent",
                quality_score=d("0.660000"),
            ),
            _signal(
                "independent-source-b",
                source_kind="independent",
                quality_score=d("0.660000"),
            ),
        ),
    )

    assert watch_report.gate_status == "watch"
    assert watch_report.watch_count == d("1.000000")
    assert watch_report.rows[0].adjusted_quality_score == d("0.740000")
    assert watch_report.rows[0].source_quality_margin_score == d("0.040000")


def test_empty_and_insufficient_sources_are_report_only_blocks() -> None:
    api = _api()

    empty_report = _report(())

    assert empty_report.gate_status == "blocked"
    assert empty_report.candidate_count == d("0.000000")
    assert empty_report.signal_count == d("0.000000")
    assert empty_report.rows == ()
    assert empty_report.reason_codes == ("empty_source_set",)

    thin_report = _report((_signal("single-source"),), min_source_count=d("2"))

    assert thin_report.gate_status == "blocked"
    assert thin_report.rows[0].reason_codes == (
        "insufficient_source_count",
        "independent_source_boost",
    )

    assert api.__all__ == (
        "DEFAULT_STRATEGY_CANDIDATE_SOURCE_QUALITY_MARGIN_GATE_V2_CONFIG_VERSION",
        "StrategyCandidateSourceQualityMarginGateV2Config",
        "StrategyCandidateSourceQualitySignal",
        "StrategyCandidateSourceQualityPublicPayloadItem",
        "StrategyCandidateSourceQualityMarginGateRow",
        "StrategyCandidateSourceQualityMarginGateReport",
        "build_strategy_candidate_source_quality_margin_gate_v2",
        "strategy_candidate_source_quality_margin_gate_v2_payload",
    )


def test_serialization_uses_decimal_strings_and_hard_phase_flags() -> None:
    api = _api()
    report = _report(
        (
            _signal("official-source", source_kind="official", quality_score=d("0.760000")),
            _signal(
                "independent-source",
                source_kind="independent",
                quality_score=d("0.720000"),
            ),
        ),
    )

    _assert_public_numbers_are_decimal(report)
    payload = api.strategy_candidate_source_quality_margin_gate_v2_payload(report)
    _assert_json_ready(payload)
    _assert_no_decimal_objects(payload)
    json.dumps(payload, sort_keys=True)

    assert payload == report.payload
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["candidate_count"] == "1.000000"
    assert payload["signal_count"] == "2.000000"
    assert payload["average_source_quality_margin_score"] == "0.160000"
    assert payload["max_weak_source_penalty"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["source_quality_margin_score"] == "0.160000"
    assert payload["public_payload"] == [
        {
            "key": "review_note",
            "value": "source checks complete",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]


def test_dataclasses_are_frozen_and_decimal_only() -> None:
    api = _api()
    config = _config()
    signal = _signal("official-source", source_kind="official")
    payload_item = _payload_item()

    with pytest.raises(FrozenInstanceError):
        config.min_source_count = d("3")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        signal.source_id = "other-source"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        payload_item.value = "other"  # type: ignore[misc]

    with pytest.raises(ValueError, match="min_source_count must be a Decimal"):
        api.StrategyCandidateSourceQualityMarginGateV2Config(
            min_source_count=2,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="quality_score must be a Decimal"):
        _signal("decimal-subclass", quality_score=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        _signal(
            "datetime-subclass",
            observed_at=_DateTimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )


def test_derived_validation_digest_rejects_object_and_payload_tampering() -> None:
    api = _api()
    report = _report(
        (
            _signal("official-source", source_kind="official", quality_score=d("0.760000")),
            _signal(
                "independent-source",
                source_kind="independent",
                quality_score=d("0.720000"),
            ),
        ),
    )

    malformed_report = _bypassed_row(report, pass_count=d("2.000000"))
    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        api.strategy_candidate_source_quality_margin_gate_v2_payload(malformed_report)

    malformed_report = _bypassed_row(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        api.strategy_candidate_source_quality_margin_gate_v2_payload(malformed_report)

    payload = api.strategy_candidate_source_quality_margin_gate_v2_payload(report)
    tampered_payload = dict(payload)
    tampered_payload["signal_count"] = "99.000000"
    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        api.strategy_candidate_source_quality_margin_gate_v2_payload(tampered_payload)


def test_unsafe_public_payload_keys_values_and_false_flags_are_rejected() -> None:
    api = _api()
    signal = _signal("official-source", source_kind="official")

    with pytest.raises(ValueError, match="signals must be a list or tuple"):
        api.build_strategy_candidate_source_quality_margin_gate_v2(
            (row for row in (signal,)),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="signals items must be"):
        api.build_strategy_candidate_source_quality_margin_gate_v2(
            [object()],
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        api.build_strategy_candidate_source_quality_margin_gate_v2(
            [signal],
            config=_config(),
            generated_at=datetime(2026, 7, 6, 12, 0),
        )
    with pytest.raises(ValueError, match="signal observed_at must not be after generated_at"):
        _report((_signal("future-source", observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="signal readonly must be True"):
        _report((_bypassed_row(signal, readonly=False),))
    with pytest.raises(ValueError, match="candidate_id contains unsafe detail"):
        _signal("unsafe-source", candidate_id="live-candidate")
    with pytest.raises(ValueError, match="value contains unsafe detail"):
        _payload_item(value="requires signing")

    payload = api.strategy_candidate_source_quality_margin_gate_v2_payload(
        _report((_signal("official-source", source_kind="official"), _signal("other-source"))),
    )
    unsafe_key_payload = dict(payload)
    unsafe_key_payload["wallet_key"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public field"):
        api.strategy_candidate_source_quality_margin_gate_v2_payload(unsafe_key_payload)

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["review_note"] = "requires signing"
    with pytest.raises(ValueError, match="unsafe public value"):
        api.strategy_candidate_source_quality_margin_gate_v2_payload(unsafe_value_payload)


def test_no_unsafe_public_or_external_surfaces_are_exposed() -> None:
    api = _api()
    report = _report(
        (
            _signal("official-source", source_kind="official", quality_score=d("0.760000")),
            _signal(
                "independent-source",
                source_kind="independent",
                quality_score=d("0.720000"),
            ),
        ),
    )
    payload = api.strategy_candidate_source_quality_margin_gate_v2_payload(report)

    forbidden = {
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    }
    public_names = set(api.__all__)
    for dataclass_type in (
        api.StrategyCandidateSourceQualityMarginGateV2Config,
        api.StrategyCandidateSourceQualitySignal,
        api.StrategyCandidateSourceQualityPublicPayloadItem,
        api.StrategyCandidateSourceQualityMarginGateRow,
        api.StrategyCandidateSourceQualityMarginGateReport,
    ):
        public_names.update(field.name for field in fields(dataclass_type))
    public_names.update(_walk_strings(payload))

    for name in public_names:
        lowered = name.lower()
        assert all(token not in lowered for token in forbidden)

    for forbidden_name in (
        "requests",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
        "session",
        "client",
        "submit",
        "execute",
    ):
        assert not hasattr(api, forbidden_name)

    source_path = Path(api.__file__)
    assert source_path.name == "strategy_candidate_source_quality_margin_gate_v2.py"
    source_text = source_path.read_text(encoding="utf-8")
    assert "requests" not in source_text
    assert "sqlite3" not in source_text
    assert "sqlalchemy" not in source_text
    assert "web3" not in source_text
