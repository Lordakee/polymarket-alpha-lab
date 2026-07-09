from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import pytest

import polymarket_alpha_lab.research_market_cost_probability_memory_guard_report as api
from polymarket_alpha_lab.research_market_cost_probability_memory_guard_report import (
    ResearchMarketCostProbabilityMemoryGuardConfig,
    ResearchMarketCostProbabilityMemoryGuardObservation,
    ResearchMarketCostProbabilityMemoryGuardPublicPayloadItem,
    ResearchMarketCostProbabilityMemoryGuardReport,
    ResearchMarketCostProbabilityMemoryGuardRow,
    build_research_market_cost_probability_memory_guard_report,
)


NOW = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    index: int,
    *,
    research_id: str = "alpha_research",
    cost_pressure: Decimal = d("0.200000"),
    probability_pressure: Decimal = d("0.300000"),
    memory_pressure: Decimal = d("0.400000"),
    observed_at: datetime | None = None,
) -> ResearchMarketCostProbabilityMemoryGuardObservation:
    return ResearchMarketCostProbabilityMemoryGuardObservation(
        research_id=research_id,
        observation_id=f"obs_{index:03d}",
        observed_at=observed_at or NOW - timedelta(minutes=index),
        cost_pressure=cost_pressure,
        probability_pressure=probability_pressure,
        memory_pressure=memory_pressure,
    )


def report(
    items: tuple[ResearchMarketCostProbabilityMemoryGuardObservation, ...],
    *,
    config: ResearchMarketCostProbabilityMemoryGuardConfig | None = None,
    public_payload: tuple[
        ResearchMarketCostProbabilityMemoryGuardPublicPayloadItem,
        ...,
    ] = (),
    generated_at: datetime = NOW,
) -> ResearchMarketCostProbabilityMemoryGuardReport:
    return build_research_market_cost_probability_memory_guard_report(
        items,
        generated_at=generated_at,
        config=config,
        public_payload=public_payload,
    )


def test_empty_input_returns_block_report_with_zero_decimal_counts() -> None:
    guard_report = report(())

    assert type(guard_report) is ResearchMarketCostProbabilityMemoryGuardReport
    assert guard_report.generated_at == NOW
    assert guard_report.status == "block"
    assert guard_report.item_count == d("0.000000")
    assert guard_report.pass_count == d("0.000000")
    assert guard_report.watch_count == d("0.000000")
    assert guard_report.block_count == d("0.000000")
    assert guard_report.average_composite_pressure == d("0.000000")
    assert guard_report.max_composite_pressure == d("0.000000")
    assert guard_report.rows == ()
    assert guard_report.reason_codes == ("no_observations",)
    assert guard_report.paper_only is True
    assert guard_report.report_only is True
    assert guard_report.readonly is True


def test_pass_watch_and_block_rows_are_built_from_decimal_inputs_only() -> None:
    guard_report = report(
        (
            observation(2, research_id="watch_research", cost_pressure=d("0.800000")),
            observation(
                3,
                research_id="block_research",
                cost_pressure=d("0.900000"),
                probability_pressure=d("0.400000"),
                memory_pressure=d("0.900000"),
            ),
            observation(1, research_id="pass_research"),
        ),
    )

    rows_by_status = {row.status: row for row in guard_report.rows}

    assert guard_report.status == "block"
    assert guard_report.item_count == d("3.000000")
    assert guard_report.pass_count == d("1.000000")
    assert guard_report.watch_count == d("1.000000")
    assert guard_report.block_count == d("1.000000")
    assert guard_report.average_composite_pressure == d("0.523333")
    assert guard_report.max_composite_pressure == d("0.750000")

    pass_row = rows_by_status["pass"]
    assert type(pass_row) is ResearchMarketCostProbabilityMemoryGuardRow
    assert pass_row.composite_pressure == d("0.290000")
    assert pass_row.reason_codes == ("memory_guard_pass",)

    watch_row = rows_by_status["watch"]
    assert watch_row.max_cost_pressure == d("0.800000")
    assert watch_row.composite_pressure == d("0.530000")
    assert watch_row.reason_codes == (
        "cost_pressure_high",
        "composite_pressure_watch",
    )

    block_row = rows_by_status["block"]
    assert block_row.max_memory_pressure == d("0.900000")
    assert block_row.composite_pressure == d("0.750000")
    assert block_row.reason_codes == (
        "cost_pressure_high",
        "memory_pressure_high",
        "composite_pressure_block",
    )
    assert {row.status for row in guard_report.rows} <= {"pass", "watch", "block"}


def test_report_payload_is_deterministic_json_ready_and_validated_by_sha256() -> None:
    guard_report = report(
        (
            observation(2, research_id="z_research", cost_pressure=d("0.500000")),
            observation(1, research_id="a_research", probability_pressure=d("0.800000")),
        ),
        public_payload=(
            ResearchMarketCostProbabilityMemoryGuardPublicPayloadItem("mode", "paper"),
            ResearchMarketCostProbabilityMemoryGuardPublicPayloadItem("phase", "alpha"),
        ),
    )

    payload = guard_report.payload
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    encoded_again = json.dumps(guard_report.payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)

    assert encoded == encoded_again
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["item_count"] == "2.000000"
    assert payload["rows"][0]["observation_count"] == "1.000000"
    assert payload["derived_validation_digest"] == guard_report.derived_validation_digest
    assert len(guard_report.derived_validation_digest) == 64
    assert all(char in "0123456789abcdef" for char in guard_report.derived_validation_digest)
    assert isinstance(payload["derived_validation_digest"], str)
    assert guard_report.rows == tuple(
        sorted(guard_report.rows, key=lambda row: row.research_digest),
    )
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(guard_report)

    values = json.loads(encoded)
    values.pop("derived_validation_digest")
    expected_digest = hashlib.sha256(
        json.dumps(values, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode(
            "utf-8",
        ),
    ).hexdigest()
    assert expected_digest == guard_report.derived_validation_digest


def test_digest_rejects_tampered_report_values_and_public_payload() -> None:
    guard_report = report((observation(1),))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(guard_report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            guard_report,
            public_payload=(
                ResearchMarketCostProbabilityMemoryGuardPublicPayloadItem("phase", "changed"),
            ),
        )

    with pytest.raises(ValueError, match="status"):
        replace(guard_report.rows[0], status="blocked")


def test_validation_enforces_frozen_dataclasses_flags_decimals_and_time() -> None:
    guard_report = report((observation(1),))

    with pytest.raises(FrozenInstanceError):
        guard_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        guard_report.rows[0].composite_pressure = d("0")  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadReport(ResearchMarketCostProbabilityMemoryGuardReport):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        ResearchMarketCostProbabilityMemoryGuardConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(observation(1), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(guard_report, readonly=False)
    with pytest.raises(ValueError, match="Decimal"):
        observation(1, cost_pressure=0.2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        observation(1, probability_pressure=_DecimalSubclass("0.2"))
    with pytest.raises(ValueError, match="between zero and one"):
        observation(1, memory_pressure=d("1.000001"))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation(1),), generated_at=_DatetimeSubclass(2026, 7, 9, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        observation(1, observed_at=datetime(2026, 7, 9))
    with pytest.raises(ValueError, match="after generated_at"):
        report((observation(1, observed_at=NOW + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="duplicate"):
        report((observation(1), observation(1)))


def test_no_raw_identifiers_or_sensitive_values_reach_public_payload() -> None:
    raw_research_id = "alpha_research"
    guard_report = report(
        (
            observation(1, research_id=raw_research_id),
            observation(2, research_id=raw_research_id, cost_pressure=d("0.700000")),
        ),
    )
    payload = guard_report.payload
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True)

    assert raw_research_id not in encoded
    assert hashlib.sha256(raw_research_id.encode("utf-8")).hexdigest() in encoded
    assert "obs_001" not in encoded
    assert "obs_002" not in encoded

    blocked_terms = (
        "candi" + "date",
        "sou" + "rce",
        "u" + "rl",
        "te" + "xt",
        "d" + "sn",
        "ta" + "ble",
        "tok" + "en",
    )
    assert all(term not in encoded.lower() for term in blocked_terms)

    for key, value in (
        ("sou" + "rce", "safe"),
        ("safe", "tok" + "en"),
        ("safe", "https://example.invalid/path"),
        ("safe", "person@example.invalid"),
        ("tra" + "de", "safe"),
        ("safe", "tra" + "de"),
    ):
        with pytest.raises(ValueError, match="sensitive public"):
            ResearchMarketCostProbabilityMemoryGuardPublicPayloadItem(key, value)


def test_public_payload_rejects_known_observation_identifiers() -> None:
    with pytest.raises(ValueError, match="public_payload"):
        report(
            (observation(1, research_id="alpha_research"),),
            public_payload=(
                ResearchMarketCostProbabilityMemoryGuardPublicPayloadItem(
                    "phase",
                    "alpha_research",
                ),
            ),
        )

    with pytest.raises(ValueError, match="public_payload"):
        report(
            (observation(1, research_id="alpha_research"),),
            public_payload=(
                ResearchMarketCostProbabilityMemoryGuardPublicPayloadItem(
                    "obs_001",
                    "paper",
                ),
            ),
        )


def test_public_payload_rejects_market_slug_and_question_terms() -> None:
    for key, value in (
        ("market_id", "safe"),
        ("market_slug", "safe"),
        ("question", "safe"),
        ("safe", "market_slug"),
        ("safe", "question_payload"),
    ):
        with pytest.raises(ValueError, match="sensitive public"):
            ResearchMarketCostProbabilityMemoryGuardPublicPayloadItem(key, value)


def test_owned_module_has_no_forbidden_operational_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_cost_probability_memory_guard_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "httpx",
        "urllib",
        "aiohttp",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
        "subprocess",
        "open(",
        "connect(",
        "db",
        "net" + "work",
        "wall" + "et",
        "au" + "th",
        "ord" + "er",
        "li" + "ve",
        "tra" + "de",
        "trad" + "ing",
        "siz" + "ing",
        "recomm" + "endation",
    )

    assert all(term not in source for term in forbidden_terms)

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert "wallet" not in lowered
        assert "recommendation" not in lowered

    for cls in (
        ResearchMarketCostProbabilityMemoryGuardConfig,
        ResearchMarketCostProbabilityMemoryGuardObservation,
        ResearchMarketCostProbabilityMemoryGuardPublicPayloadItem,
        ResearchMarketCostProbabilityMemoryGuardRow,
        ResearchMarketCostProbabilityMemoryGuardReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert "wallet" not in lowered
            assert "recommendation" not in lowered


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))
