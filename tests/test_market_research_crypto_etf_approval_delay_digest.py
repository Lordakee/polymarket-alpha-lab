from __future__ import annotations

import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from types import ModuleType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_etf_approval_delay_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": "market-research-crypto-etf-approval-delay-digest-v0",
        "watch_delay_probability": d("0.400000"),
        "blocked_delay_probability": d("0.700000"),
        "max_source_age_seconds": d("1800.000000"),
        "stale_confidence_cap": d("0.300000"),
        "routine_confidence_cap": d("0.650000"),
    }
    values.update(overrides)
    return module.CryptoEtfApprovalDelayDigestConfig(**values)


def observation(
    source_id: str = "source-alpha",
    *,
    proposal_id: str = "spot-eth-staking-etf",
    issuer_name: str = "alpha issuer",
    asset_symbol: str = "eth",
    review_stage: str = "final_review",
    days_until_deadline: Decimal = d("8.000000"),
    delay_probability: Decimal = d("0.550000"),
    comment_volume_z_score: Decimal = d("1.500000"),
    amendment_age_days: Decimal = d("32.000000"),
    source_confidence: Decimal = d("0.850000"),
    observed_at: datetime = GENERATED_AT - timedelta(seconds=2400),
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.CryptoEtfApprovalDelayObservation(
        source_id=source_id,
        proposal_id=proposal_id,
        issuer_name=issuer_name,
        asset_symbol=asset_symbol,
        review_stage=review_stage,
        days_until_deadline=days_until_deadline,
        delay_probability=delay_probability,
        comment_volume_z_score=comment_volume_z_score,
        amendment_age_days=amendment_age_days,
        source_confidence=source_confidence,
        observed_at=observed_at,
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(inputs: tuple[Any, ...], *, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_market_research_crypto_etf_approval_delay_digest(
        inputs,
        config=config(),
        generated_at=generated_at,
    )


def assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail(f"public payload must not contain floats: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_floats(item)
    elif isinstance(value, list | tuple):
        for item in value:
            assert_no_floats(item)


def test_builds_report_only_crypto_etf_delay_digest_deterministically() -> None:
    report = digest(
        (
            observation(
                "beta-routine",
                proposal_id="spot-btc-covered-call-etf",
                issuer_name="beta issuer",
                asset_symbol="btc",
                review_stage="initial_review",
                days_until_deadline=d("75.000000"),
                delay_probability=d("0.150000"),
                comment_volume_z_score=d("0.400000"),
                amendment_age_days=d("7.000000"),
                source_confidence=d("0.800000"),
                observed_at=GENERATED_AT - timedelta(seconds=60),
                upstream_reason_codes=("desk_note",),
            ),
            observation(
                "alpha-watch",
                proposal_id="spot-eth-staking-etf",
                issuer_name="alpha issuer",
                asset_symbol="eth",
                review_stage="final_review",
                days_until_deadline=d("8.000000"),
                delay_probability=d("0.550000"),
                comment_volume_z_score=d("1.500000"),
                amendment_age_days=d("32.000000"),
                observed_at=GENERATED_AT - timedelta(seconds=2400),
            ),
            observation(
                "zeta-blocked",
                proposal_id="spot-sol-etf",
                issuer_name="zeta issuer",
                asset_symbol="sol",
                review_stage="final_review",
                days_until_deadline=d("3.000000"),
                delay_probability=d("0.820000"),
                comment_volume_z_score=d("2.600000"),
                amendment_age_days=d("55.000000"),
                source_confidence=d("0.900000"),
                observed_at=datetime(
                    2026,
                    7,
                    4,
                    7,
                    59,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                upstream_reason_codes=("regulatory_calendar_cluster",),
            ),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        "market-research-crypto-etf-approval-delay-digest-v0"
    )
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.blocked_delay_count == d("1.000000")
    assert report.watch_delay_count == d("1.000000")
    assert report.routine_count == d("1.000000")
    assert report.stale_source_count == d("1.000000")
    assert report.near_deadline_count == d("2.000000")
    assert report.max_delay_probability == d("0.820000")
    assert report.average_delay_probability == d("0.506667")
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_etf_approval_delay_digest"
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert [
        (row.source_id, row.delay_status, row.delay_probability)
        for row in report.rows
    ] == [
        ("zeta-blocked", "blocked", d("0.820000")),
        ("alpha-watch", "watch", d("0.550000")),
        ("beta-routine", "pass", d("0.150000")),
    ]

    blocked, watch, passed = report.rows
    assert blocked.observed_at == datetime(2026, 7, 4, 11, 59, tzinfo=UTC)
    assert blocked.source_age_seconds == d("60.000000")
    assert blocked.delay_direction == "approval_delay"
    assert blocked.confidence_cap == d("1.000000")
    assert blocked.capped_confidence == d("0.900000")
    assert blocked.reason_codes == (
        "approval_delay_blocked",
        "comment_volume_pressure",
        "deadline_near",
        "delayed_amendment_cycle",
        "regulatory_calendar_cluster",
        "source_fresh",
    )

    assert watch.delay_direction == "approval_delay"
    assert watch.source_age_seconds == d("2400.000000")
    assert watch.confidence_cap == d("0.300000")
    assert watch.capped_confidence == d("0.300000")
    assert watch.reason_codes == (
        "approval_delay_watch",
        "deadline_near",
        "delayed_amendment_cycle",
        "source_stale",
    )

    assert passed.delay_direction == "approval_routine"
    assert passed.confidence_cap == d("0.650000")
    assert passed.capped_confidence == d("0.650000")
    assert passed.reason_codes == (
        "approval_delay_calm",
        "desk_note",
        "source_fresh",
    )

    assert report.reason_codes == (
        "approval_delay_blocked",
        "approval_delay_calm",
        "approval_delay_watch",
        "comment_volume_pressure",
        "deadline_near",
        "delayed_amendment_cycle",
        "desk_note",
        "regulatory_calendar_cluster",
        "source_fresh",
        "source_stale",
    )
    assert report.reason_code_counts[0].reason_code == "approval_delay_blocked"
    assert report.reason_code_counts[0].count == d("1.000000")
    assert report.reason_code_counts[0].row_ratio == d("0.333333")


def test_empty_digest_and_payload_are_decimal_stringed_report_only_readonly() -> None:
    module = api()
    report = digest(())
    payload = module.market_research_crypto_etf_approval_delay_digest_payload(report)
    json.dumps(payload, sort_keys=True)

    assert report.input_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.blocked_delay_count == d("0.000000")
    assert report.max_delay_probability == d("0.000000")
    assert report.average_delay_probability == d("0.000000")
    assert report.digest_status == "blocked"
    assert report.reason_codes == ("crypto_etf_approval_delay_digest_empty",)
    assert report.reason_code_counts == (
        module.CryptoEtfApprovalDelayReasonCodeCount(
            reason_code="crypto_etf_approval_delay_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert report.rows == ()
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["row_count"] == "0.000000"
    assert payload["reason_code_counts"][0]["row_ratio"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_floats(payload)


def test_rejects_bad_public_types_datetimes_duplicates_future_rows_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="delay_probability"):
        observation(delay_probability=_DecimalSubclass("0.500000"))

    with pytest.raises(ValueError, match="delay_probability"):
        observation(delay_probability=d("1.100000"))

    with pytest.raises(ValueError, match="watch_delay_probability"):
        config(watch_delay_probability=0.4)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="UTC-aware"):
        observation(observed_at=datetime(2026, 7, 4, 12, 0))

    with pytest.raises(ValueError, match="datetime"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 4, tzinfo=UTC))

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        digest((observation(observed_at=GENERATED_AT + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="inputs must not contain duplicate"):
        digest((observation("dupe"), observation("dupe")))

    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)

    report = digest((observation(),))
    with pytest.raises(FrozenInstanceError):
        report.rows = ()  # type: ignore[misc]

    classes = (
        module.CryptoEtfApprovalDelayDigestConfig,
        module.CryptoEtfApprovalDelayObservation,
        module.CryptoEtfApprovalDelayDigestRow,
        module.CryptoEtfApprovalDelayReasonCodeCount,
        module.CryptoEtfApprovalDelayDigestReport,
    )
    for type_ in classes:
        assert type_.__dataclass_params__.frozen is True
        for field in fields(type_):
            public_type = str(field.type).lower()
            assert "float" not in public_type
            assert "int" not in public_type


def test_rejects_false_phase1_hard_flags_on_all_public_dataclasses() -> None:
    report = digest((observation(),))
    instances = (
        config(),
        observation(),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    )

    for instance in instances:
        for flag_name in ("paper_only", "report_only", "readonly"):
            kwargs = {field.name: getattr(instance, field.name) for field in fields(instance)}
            kwargs[flag_name] = False
            with pytest.raises(ValueError, match=flag_name):
                type(instance)(**kwargs)


def test_module_scope_is_pure_in_memory_without_live_or_durable_surfaces() -> None:
    source = inspect.getsource(api()).lower()

    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "open(",
        "path(",
        "connect(",
        "cursor(",
        "execute(",
        "web3",
        "wallet",
        "private_key",
        "api_key",
        "secret",
        "place_order",
        "cancel_order",
        "replace_order",
    ):
        assert forbidden not in source
