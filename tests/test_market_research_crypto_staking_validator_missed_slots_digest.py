from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 22, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_crypto_staking_validator_missed_slots_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**kwargs: object):
    return api().MarketResearchCryptoStakingValidatorMissedSlotsDigestConfig(**kwargs)


def observation(
    source_id: str = "source-alpha",
    *,
    validator_id: str = "validator-alpha",
    network: str = "ethereum",
    epoch_id: str = "epoch-123",
    slot_window_start: datetime = datetime(2026, 7, 4, 20, 0, tzinfo=UTC),
    slot_window_end: datetime = datetime(2026, 7, 4, 20, 32, tzinfo=UTC),
    expected_slot_count: str | Decimal = "8.000000",
    missed_slot_count: str | Decimal = "1.000000",
    proposed_slot_count: str | Decimal = "7.000000",
    attestation_participation_rate: str | Decimal = "0.970000",
    observed_at: datetime = datetime(2026, 7, 4, 21, 0, tzinfo=UTC),
    upstream_reason_codes: tuple[str, ...] = ("public_validator_monitor",),
):
    module = api()
    return module.MarketResearchCryptoStakingValidatorMissedSlotsObservation(
        source_id=source_id,
        validator_id=validator_id,
        network=network,
        epoch_id=epoch_id,
        slot_window_start=slot_window_start,
        slot_window_end=slot_window_end,
        expected_slot_count=(
            expected_slot_count
            if isinstance(expected_slot_count, Decimal)
            else d(expected_slot_count)
        ),
        missed_slot_count=(
            missed_slot_count
            if isinstance(missed_slot_count, Decimal)
            else d(missed_slot_count)
        ),
        proposed_slot_count=(
            proposed_slot_count
            if isinstance(proposed_slot_count, Decimal)
            else d(proposed_slot_count)
        ),
        attestation_participation_rate=(
            attestation_participation_rate
            if isinstance(attestation_participation_rate, Decimal)
            else d(attestation_participation_rate)
        ),
        observed_at=observed_at,
        upstream_reason_codes=upstream_reason_codes,
    )


def digest_report(*rows: object, cfg: object | None = None):
    module = api()
    return module.build_market_research_crypto_staking_validator_missed_slots_digest(
        rows,
        config=cfg or config(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    module = api()

    report = digest_report()

    assert isinstance(
        report,
        module.MarketResearchCryptoStakingValidatorMissedSlotsDigestReport,
    )
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-crypto-staking-validator-missed-slots-digest-v0"
    )
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_crypto_staking_validator_missed_slots_digest"
    )
    assert report.input_count == ZERO
    assert report.row_count == ZERO
    assert report.blocked_count == ZERO
    assert report.watch_count == ZERO
    assert report.pass_count == ZERO
    assert report.high_missed_slot_count == ZERO
    assert report.high_missed_slot_rate_count == ZERO
    assert report.low_attestation_count == ZERO
    assert report.stale_observation_count == ZERO
    assert report.total_missed_slot_count == ZERO
    assert report.max_missed_slot_rate == ZERO
    assert report.average_missed_slot_rate == ZERO
    assert report.max_missed_slot_risk_score == ZERO
    assert report.rows == ()
    assert report.reason_codes == (
        "crypto_staking_validator_missed_slots_digest_empty",
    )
    assert report.reason_code_counts == (
        module.MarketResearchCryptoStakingValidatorMissedSlotsReasonCodeCount(
            reason_code="crypto_staking_validator_missed_slots_digest_empty",
            count=ONE,
            row_ratio=ZERO,
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_missed_slots_attestation_and_stale_observations_block_digest() -> None:
    report = digest_report(
        observation(
            "source-blocked",
            validator_id="validator-blocked",
            epoch_id="epoch-200",
            expected_slot_count="8.000000",
            missed_slot_count="4.000000",
            proposed_slot_count="4.000000",
            attestation_participation_rate="0.880000",
            observed_at=datetime(2026, 7, 4, 20, 20, tzinfo=UTC),
        ),
        observation(
            "source-watch",
            validator_id="validator-watch",
            epoch_id="epoch-201",
            expected_slot_count="8.000000",
            missed_slot_count="2.000000",
            proposed_slot_count="6.000000",
            attestation_participation_rate="0.930000",
            observed_at=datetime(2026, 7, 4, 23, 0, tzinfo=timezone(timedelta(hours=2))),
        ),
        observation(
            "source-pass",
            validator_id="validator-pass",
            epoch_id="epoch-202",
            expected_slot_count="8.000000",
            missed_slot_count="0.000000",
            proposed_slot_count="8.000000",
            attestation_participation_rate="0.990000",
        ),
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_crypto_staking_validator_missed_slots_digest"
    )
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.blocked_count == ONE
    assert report.watch_count == ONE
    assert report.pass_count == ONE
    assert report.high_missed_slot_count == d("2.000000")
    assert report.high_missed_slot_rate_count == d("2.000000")
    assert report.low_attestation_count == d("2.000000")
    assert report.stale_observation_count == ONE
    assert report.total_missed_slot_count == d("6.000000")
    assert report.max_missed_slot_rate == d("0.500000")
    assert report.average_missed_slot_rate == d("0.250000")
    assert report.max_missed_slot_risk_score == d("1.000000")
    assert report.reason_codes == (
        "crypto_staking_validator_missed_slots_blocked_present",
        "crypto_staking_validator_missed_slots_high_count_present",
        "crypto_staking_validator_missed_slots_high_rate_present",
        "crypto_staking_validator_missed_slots_low_attestation_present",
        "crypto_staking_validator_missed_slots_stale_observation_present",
    )

    blocked, watched, passed = report.rows
    assert tuple(row.validator_id for row in report.rows) == (
        "validator-blocked",
        "validator-watch",
        "validator-pass",
    )
    assert blocked.row_status == "blocked"
    assert blocked.missed_slot_rate == d("0.500000")
    assert blocked.missed_slot_risk_score == d("1.000000")
    assert blocked.observation_lag_minutes == d("130.000000")
    assert blocked.reason_codes == (
        "crypto_staking_validator_missed_slots_high_count",
        "crypto_staking_validator_missed_slots_high_rate",
        "crypto_staking_validator_missed_slots_low_attestation",
        "crypto_staking_validator_missed_slots_stale_observation",
        "crypto_staking_validator_missed_slots_blocked",
    )
    assert watched.row_status == "watch"
    assert watched.observed_at == datetime(2026, 7, 4, 21, 0, tzinfo=UTC)
    assert watched.reason_codes == (
        "crypto_staking_validator_missed_slots_high_count",
        "crypto_staking_validator_missed_slots_high_rate",
        "crypto_staking_validator_missed_slots_low_attestation",
        "crypto_staking_validator_missed_slots_watch",
    )
    assert passed.row_status == "pass"
    assert passed.reason_codes == ("crypto_staking_validator_missed_slots_clear",)

    assert tuple(item.reason_code for item in report.reason_code_counts) == report.reason_codes
    assert tuple(item.count for item in report.reason_code_counts) == (
        ONE,
        d("2.000000"),
        d("2.000000"),
        d("2.000000"),
        ONE,
    )


def test_rows_and_reason_codes_are_sorted_deterministically() -> None:
    first = observation(
        "source-watch-z",
        validator_id="validator-zeta",
        missed_slot_count="2.000000",
        proposed_slot_count="6.000000",
        attestation_participation_rate="0.940000",
    )
    second = observation(
        "source-blocked-a",
        validator_id="validator-alpha",
        missed_slot_count="4.000000",
        proposed_slot_count="4.000000",
        attestation_participation_rate="0.880000",
        observed_at=datetime(2026, 7, 4, 20, 20, tzinfo=UTC),
    )
    third = observation(
        "source-watch-a",
        validator_id="validator-beta",
        missed_slot_count="2.000000",
        proposed_slot_count="6.000000",
        attestation_participation_rate="0.940000",
    )

    forward = digest_report(first, second, third)
    reverse = digest_report(third, second, first)

    assert forward == reverse
    assert tuple(row.validator_id for row in forward.rows) == (
        "validator-alpha",
        "validator-beta",
        "validator-zeta",
    )
    for row in forward.rows:
        assert row.reason_codes == tuple(
            sorted(row.reason_codes, key=api().ROW_REASON_CODES.index),
        )


def test_non_default_thresholds_can_downgrade_moderate_missed_slots() -> None:
    cfg = config(
        watch_missed_slot_count=d("3.000000"),
        blocked_missed_slot_count=d("5.000000"),
        watch_missed_slot_rate=d("0.300000"),
        blocked_missed_slot_rate=d("0.600000"),
        min_attestation_participation_rate=d("0.900000"),
    )

    report = digest_report(
        observation(
            "source-moderate",
            missed_slot_count="2.000000",
            proposed_slot_count="6.000000",
            attestation_participation_rate="0.930000",
        ),
        cfg=cfg,
    )

    assert report.digest_status == "pass"
    assert report.recommended_next_step == (
        "allow_report_only_crypto_staking_validator_missed_slots_digest"
    )
    assert report.rows[0].row_status == "pass"
    assert report.rows[0].reason_codes == (
        "crypto_staking_validator_missed_slots_clear",
    )
    assert report.reason_codes == (
        "crypto_staking_validator_missed_slots_digest_clear",
    )


def test_validation_rejects_bad_inputs_and_inconsistent_public_records() -> None:
    module = api()

    with pytest.raises(ValueError, match="expected_slot_count must be a Decimal"):
        observation(expected_slot_count=_DecimalSubclass("8.000000"))
    with pytest.raises(ValueError, match="missed_slot_count must be nonnegative"):
        observation(missed_slot_count="-1.000000")
    with pytest.raises(ValueError, match="proposed_slot_count must match expected less missed"):
        observation(expected_slot_count="8.000000", missed_slot_count="3.000000")
    with pytest.raises(ValueError, match="attestation_participation_rate must be no greater"):
        observation(attestation_participation_rate="1.100000")
    with pytest.raises(ValueError, match="slot_window_end must be after slot_window_start"):
        observation(
            slot_window_start=datetime(2026, 7, 4, 20, 0, tzinfo=UTC),
            slot_window_end=datetime(2026, 7, 4, 20, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 4, 21, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_crypto_staking_validator_missed_slots_digest(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 22, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations must be a tuple"):
        module.build_market_research_crypto_staking_validator_missed_slots_digest(
            [observation("source-list")],
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="observations must contain"):
        digest_report("not-an-observation")
    with pytest.raises(ValueError, match="duplicate source_id"):
        digest_report(observation("source-dupe"), observation("source-dupe"))
    with pytest.raises(ValueError, match="watch_missed_slot_count"):
        config(
            watch_missed_slot_count=d("5.000000"),
            blocked_missed_slot_count=d("4.000000"),
        )

    valid_row = digest_report(observation("source-valid")).rows[0]
    with pytest.raises(ValueError, match="missed_slot_rate must match missed"):
        replace(valid_row, missed_slot_rate=d("0.990000"))
    with pytest.raises(ValueError, match="reason_codes must match row_status"):
        replace(
            valid_row,
            reason_codes=(
                "crypto_staking_validator_missed_slots_blocked",
                "crypto_staking_validator_missed_slots_clear",
            ),
        )

    frozen_observation = observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]


def test_hard_flags_and_exact_type_subclass_rejection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = api()
    public_classes = (
        module.MarketResearchCryptoStakingValidatorMissedSlotsDigestConfig,
        module.MarketResearchCryptoStakingValidatorMissedSlotsObservation,
        module.MarketResearchCryptoStakingValidatorMissedSlotsDigestRow,
        module.MarketResearchCryptoStakingValidatorMissedSlotsReasonCodeCount,
        module.MarketResearchCryptoStakingValidatorMissedSlotsDigestReport,
    )
    for public_class in public_classes:
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"{public_class.__name__}Subclass", (public_class,), {})

    report = digest_report(observation("source-hard-flags"))
    public_records = (
        config(),
        observation("source-public-observation"),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    )
    labels = ("config", "observation", "row", "reason_code_count", "report")

    def allow_subclass(cls: type[object], **kwargs: object) -> None:
        return None

    for public_class, public_record, label in zip(
        public_classes,
        public_records,
        labels,
        strict=True,
    ):
        monkeypatch.setattr(public_class, "__init_subclass__", classmethod(allow_subclass))
        public_subclass = type(f"Allowed{public_class.__name__}Subclass", (public_class,), {})
        with pytest.raises(ValueError, match=f"{label} must be exactly"):
            public_subclass(
                **{
                    field.name: getattr(public_record, field.name)
                    for field in fields(public_record)
                },
            )

    assert all(record.paper_only and record.report_only and record.readonly for record in public_records)
    with pytest.raises(ValueError, match="config paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(observation("source-report-only"), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="reason_code_count count must be positive"):
        module.MarketResearchCryptoStakingValidatorMissedSlotsReasonCodeCount(
            reason_code="crypto_staking_validator_missed_slots_watch_present",
            count=ZERO,
            row_ratio=ZERO,
        )
    with pytest.raises(ValueError, match="reason_code_count count must be whole"):
        module.MarketResearchCryptoStakingValidatorMissedSlotsReasonCodeCount(
            reason_code="crypto_staking_validator_missed_slots_watch_present",
            count=d("1.500000"),
            row_ratio=ONE,
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(
            "source-none-offset",
            observed_at=datetime(2026, 7, 4, 21, 0, tzinfo=_NoneOffsetTimezone()),
        )


def test_payload_uses_six_decimal_strings_and_revalidates_tampered_nested_records() -> None:
    module = api()
    report = digest_report(
        observation(
            "source-payload",
            missed_slot_count="4.000000",
            proposed_slot_count="4.000000",
            attestation_participation_rate="0.880000",
            observed_at=datetime(2026, 7, 4, 20, 20, tzinfo=UTC),
        ),
    )

    payload = module.market_research_crypto_staking_validator_missed_slots_digest_payload(
        report,
    )

    assert json.loads(json.dumps(payload, allow_nan=False, sort_keys=True)) == payload
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["generated_at"] == "2026-07-04T22:30:00+00:00"
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["missed_slot_rate"] == "0.500000"
    assert payload["rows"][0]["observation_lag_minutes"] == "130.000000"
    assert payload["reason_code_counts"][0]["row_ratio"] == "1.000000"
    walk_payload(payload)
    assert_no_exposed_public_names(payload)

    flag_report = digest_report(observation("source-payload-flag"))
    object.__setattr__(flag_report.rows[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly must be True"):
        module.market_research_crypto_staking_validator_missed_slots_digest_payload(
            flag_report,
        )

    consistency_report = digest_report(observation("source-payload-consistency"))
    object.__setattr__(consistency_report.rows[0], "row_status", "blocked")
    with pytest.raises(ValueError, match="row_status must match reason_codes"):
        module.market_research_crypto_staking_validator_missed_slots_digest_payload(
            consistency_report,
        )

    decimal_report = digest_report(observation("source-payload-decimal"))
    object.__setattr__(decimal_report.rows[0], "missed_slot_rate", d("0.1234567"))
    with pytest.raises(ValueError, match="missed_slot_rate must be six-decimal"):
        module.market_research_crypto_staking_validator_missed_slots_digest_payload(
            decimal_report,
        )

    timezone_report = digest_report(observation("source-payload-timezone"))
    object.__setattr__(
        timezone_report.rows[0],
        "observed_at",
        datetime(2026, 7, 4, 18, 10, tzinfo=timezone(timedelta(hours=-4))),
    )
    with pytest.raises(ValueError, match="observed_at must be UTC"):
        module.market_research_crypto_staking_validator_missed_slots_digest_payload(
            timezone_report,
        )

    count_flag_report = digest_report(observation("source-payload-count-flag"))
    object.__setattr__(count_flag_report.reason_code_counts[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly must be True"):
        module.market_research_crypto_staking_validator_missed_slots_digest_payload(
            count_flag_report,
        )

    fractional_count_report = digest_report(
        observation("source-payload-count-fractional"),
    )
    object.__setattr__(
        fractional_count_report.reason_code_counts[0],
        "count",
        d("1.500000"),
    )
    with pytest.raises(ValueError, match="count must be whole"):
        module.market_research_crypto_staking_validator_missed_slots_digest_payload(
            fractional_count_report,
        )

    zero_count_report = digest_report(observation("source-payload-count-zero"))
    object.__setattr__(
        zero_count_report.reason_code_counts[0],
        "count",
        ZERO,
    )
    with pytest.raises(ValueError, match="count must be positive"):
        module.market_research_crypto_staking_validator_missed_slots_digest_payload(
            zero_count_report,
        )


def test_public_numeric_fields_are_decimal_only_and_reason_counts_reconcile() -> None:
    module = api()
    report = digest_report(
        observation(
            "source-reconcile-blocked",
            missed_slot_count="4.000000",
            proposed_slot_count="4.000000",
            attestation_participation_rate="0.880000",
            observed_at=datetime(2026, 7, 4, 20, 20, tzinfo=UTC),
        ),
        observation(
            "source-reconcile-watch",
            missed_slot_count="2.000000",
            proposed_slot_count="6.000000",
            attestation_participation_rate="0.940000",
        ),
    )

    public_records = (
        config(),
        observation("source-decimal-observation"),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    )
    for public_record in public_records:
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        assert_public_numbers_are_decimal(public_record)

    public_classes = (
        module.MarketResearchCryptoStakingValidatorMissedSlotsDigestConfig,
        module.MarketResearchCryptoStakingValidatorMissedSlotsObservation,
        module.MarketResearchCryptoStakingValidatorMissedSlotsDigestRow,
        module.MarketResearchCryptoStakingValidatorMissedSlotsReasonCodeCount,
        module.MarketResearchCryptoStakingValidatorMissedSlotsDigestReport,
    )
    numeric_name_fragments = (
        "count",
        "minutes",
        "ratio",
        "score",
        "threshold",
    )
    for public_class in public_classes:
        for field in fields(public_class):
            if field.name in ("rows", "reason_code_counts", "reason_codes"):
                continue
            if (
                any(fragment in field.name for fragment in numeric_name_fragments)
                or field.name.endswith("_rate")
            ):
                assert field.type in (Decimal, "Decimal"), field.name
            assert field.name not in unsafe_public_names()

    expected_counts = {
        "crypto_staking_validator_missed_slots_blocked_present": report.blocked_count,
        "crypto_staking_validator_missed_slots_high_count_present": (
            report.high_missed_slot_count
        ),
        "crypto_staking_validator_missed_slots_high_rate_present": (
            report.high_missed_slot_rate_count
        ),
        "crypto_staking_validator_missed_slots_low_attestation_present": (
            report.low_attestation_count
        ),
        "crypto_staking_validator_missed_slots_stale_observation_present": (
            report.stale_observation_count
        ),
    }
    assert {item.reason_code: item.count for item in report.reason_code_counts} == expected_counts
    assert tuple(item.reason_code for item in report.reason_code_counts) == report.reason_codes

    bad_values = {field.name: getattr(report, field.name) for field in fields(report)}
    bad_values["reason_code_counts"] = (
        module.MarketResearchCryptoStakingValidatorMissedSlotsReasonCodeCount(
            reason_code="crypto_staking_validator_missed_slots_high_count_present",
            count=ONE,
            row_ratio=d("0.500000"),
        ),
    )
    with pytest.raises(ValueError, match="reason_code_counts must summarize rows"):
        module.MarketResearchCryptoStakingValidatorMissedSlotsDigestReport(**bad_values)


def test_module_scope_excludes_io_mutation_float_asdict_and_named_public_surfaces() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    lowered_source = source.lower()

    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )
    assert _join("as", "dict") not in lowered_source
    for forbidden in unsafe_public_names():
        assert forbidden not in lowered_source

    imported_modules: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            if isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "http",
        "psycopg",
        _join("re", "quests"),
        "socket",
        "sqlite",
        _join("sub", "process"),
        "supabase",
        "urllib",
        "web3",
    )
    forbidden_call_names = {
        "connect",
        "execute",
        "executemany",
        _join("op", "en"),
        _join("re", "quest"),
        "post",
        "put",
        "patch",
        "delete",
        "send",
        _join("wr", "ite"),
    }
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    assert not (called_names & forbidden_call_names)


def walk_payload(value: Any) -> None:
    if isinstance(value, dict):
        for child in value.values():
            walk_payload(child)
        return
    if isinstance(value, list):
        for child in value:
            walk_payload(child)
        return
    if type(value) is bool:
        return
    assert not isinstance(value, (Decimal, datetime, float))
    assert type(value) is not int


def assert_public_numbers_are_decimal(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numbers_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, tuple):
        for item in value:
            assert_public_numbers_are_decimal(item)
        return
    if isinstance(value, Decimal):
        assert type(value) is Decimal


def assert_no_exposed_public_names(payload: dict[str, Any]) -> None:
    payload_text = repr(payload).lower()
    for forbidden in unsafe_public_names():
        assert forbidden not in payload_text


def unsafe_public_names() -> tuple[str, ...]:
    return (
        _join("market", "_", "slug"),
        _join("quest", "ion"),
        _join("payload", "_", "json"),
    )


def _join(*parts: str) -> str:
    return "".join(parts)
