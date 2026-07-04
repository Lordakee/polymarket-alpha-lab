from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 4, 14, 15, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def digest():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_oracle_outage_latency_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str = "oracle-feed-alpha",
    *,
    oracle_name: str = "chainlink-btc-usd",
    asset_symbol: str = "btc",
    market_slug: str = "bitcoin-above-100k-july",
    update_latency_seconds: str | Decimal = "42.000000",
    missed_heartbeat_count: str | Decimal = "0.000000",
    stale_price_age_seconds: str | Decimal = "55.000000",
    expected_source_count: str | Decimal = "4.000000",
    observed_source_count: str | Decimal = "4.000000",
    confidence_score: str | Decimal = "0.920000",
    data_timestamp: datetime = datetime(2026, 7, 4, 13, 50, tzinfo=UTC),
    upstream_reason_codes: tuple[str, ...] = ("public_oracle_status",),
):
    module = digest()
    return module.CryptoOracleOutageLatencyObservation(
        source_id=source_id,
        oracle_name=oracle_name,
        asset_symbol=asset_symbol,
        market_slug=market_slug,
        update_latency_seconds=(
            update_latency_seconds
            if isinstance(update_latency_seconds, Decimal)
            else d(update_latency_seconds)
        ),
        missed_heartbeat_count=(
            missed_heartbeat_count
            if isinstance(missed_heartbeat_count, Decimal)
            else d(missed_heartbeat_count)
        ),
        stale_price_age_seconds=(
            stale_price_age_seconds
            if isinstance(stale_price_age_seconds, Decimal)
            else d(stale_price_age_seconds)
        ),
        expected_source_count=(
            expected_source_count
            if isinstance(expected_source_count, Decimal)
            else d(expected_source_count)
        ),
        observed_source_count=(
            observed_source_count
            if isinstance(observed_source_count, Decimal)
            else d(observed_source_count)
        ),
        confidence_score=(
            confidence_score
            if isinstance(confidence_score, Decimal)
            else d(confidence_score)
        ),
        data_timestamp=data_timestamp,
        upstream_reason_codes=upstream_reason_codes,
    )


def report(*rows: object, cfg: object | None = None):
    module = digest()
    return module.build_market_research_crypto_oracle_outage_latency_digest(
        rows,
        config=cfg or module.CryptoOracleOutageLatencyDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    module = digest()

    digest_report = report()

    assert isinstance(digest_report, module.CryptoOracleOutageLatencyDigestReport)
    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-crypto-oracle-outage-latency-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_crypto_oracle_outage_latency_screening"
    )
    assert digest_report.input_count == d("0.000000")
    assert digest_report.row_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.high_latency_count == d("0.000000")
    assert digest_report.missed_heartbeat_row_count == d("0.000000")
    assert digest_report.stale_price_count == d("0.000000")
    assert digest_report.quorum_gap_count == d("0.000000")
    assert digest_report.confidence_pressure_count == d("0.000000")
    assert digest_report.max_update_latency_seconds == d("0.000000")
    assert digest_report.average_update_latency_seconds == d("0.000000")
    assert digest_report.max_stale_price_age_seconds == d("0.000000")
    assert digest_report.max_source_quorum_gap == d("0.000000")
    assert digest_report.max_confidence_pressure == d("0.000000")
    assert digest_report.outage_risk_score == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == ("crypto_oracle_outage_latency_digest_empty",)
    assert digest_report.reason_code_counts == (
        module.CryptoOracleOutageLatencyReasonCodeCount(
            reason_code="crypto_oracle_outage_latency_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_high_pressure_oracle_outage_blocks_crypto_probability_screening() -> None:
    module = digest()

    digest_report = report(
        observation(
            "oracle-feed-btc-primary",
            update_latency_seconds="420.000000",
            missed_heartbeat_count="6.000000",
            stale_price_age_seconds="720.000000",
            expected_source_count="5.000000",
            observed_source_count="2.000000",
            confidence_score="0.480000",
            data_timestamp=datetime(
                2026,
                7,
                4,
                9,
                45,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        observation(
            "oracle-feed-eth-watch",
            oracle_name="pyth-eth-usd",
            asset_symbol="eth",
            market_slug="ethereum-above-5k-july",
            update_latency_seconds="150.000000",
            missed_heartbeat_count="2.000000",
            stale_price_age_seconds="250.000000",
            expected_source_count="4.000000",
            observed_source_count="3.000000",
            confidence_score="0.700000",
        ),
        observation(
            "oracle-feed-sol-pass",
            oracle_name="chainlink-sol-usd",
            asset_symbol="sol",
            market_slug="solana-above-250-july",
            update_latency_seconds="30.000000",
            stale_price_age_seconds="45.000000",
            expected_source_count="3.000000",
            observed_source_count="3.000000",
            confidence_score="0.930000",
        ),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_crypto_oracle_outage_latency_screening"
    )
    assert digest_report.input_count == d("3.000000")
    assert digest_report.row_count == d("3.000000")
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.high_latency_count == d("1.000000")
    assert digest_report.missed_heartbeat_row_count == d("1.000000")
    assert digest_report.stale_price_count == d("1.000000")
    assert digest_report.quorum_gap_count == d("1.000000")
    assert digest_report.confidence_pressure_count == d("1.000000")
    assert digest_report.max_update_latency_seconds == d("420.000000")
    assert digest_report.average_update_latency_seconds == d("200.000000")
    assert digest_report.max_stale_price_age_seconds == d("720.000000")
    assert digest_report.max_source_quorum_gap == d("3.000000")
    assert digest_report.max_confidence_pressure == d("0.520000")
    assert digest_report.outage_risk_score == d("1.000000")
    assert digest_report.reason_codes == (
        "crypto_oracle_outage_latency_high_latency_present",
        "crypto_oracle_outage_latency_missed_heartbeat_present",
        "crypto_oracle_outage_latency_stale_price_present",
        "crypto_oracle_outage_latency_quorum_gap_present",
        "crypto_oracle_outage_latency_confidence_pressure_present",
    )
    assert tuple(row.market_slug for row in digest_report.rows) == (
        "bitcoin-above-100k-july",
        "ethereum-above-5k-july",
        "solana-above-250-july",
    )

    blocked, watched, passed = digest_report.rows
    assert blocked.latency_status == "blocked"
    assert blocked.source_quorum_gap == d("3.000000")
    assert blocked.confidence_pressure == d("0.520000")
    assert blocked.data_timestamp == datetime(2026, 7, 4, 13, 45, tzinfo=UTC)
    assert blocked.reason_codes == (
        "crypto_oracle_outage_latency_high_latency",
        "crypto_oracle_outage_latency_missed_heartbeat",
        "crypto_oracle_outage_latency_stale_price",
        "crypto_oracle_outage_latency_quorum_gap",
        "crypto_oracle_outage_latency_confidence_pressure",
    )
    assert watched.latency_status == "watch"
    assert watched.source_quorum_gap == d("1.000000")
    assert watched.confidence_pressure == d("0.300000")
    assert watched.reason_codes == (
        "crypto_oracle_outage_latency_watch_latency",
        "crypto_oracle_outage_latency_watch_missed_heartbeat",
        "crypto_oracle_outage_latency_watch_stale_price",
        "crypto_oracle_outage_latency_watch_quorum_gap",
        "crypto_oracle_outage_latency_watch_confidence_pressure",
    )
    assert passed.latency_status == "pass"
    assert passed.reason_codes == ("crypto_oracle_outage_latency_inline",)


def test_rows_and_reason_codes_are_sorted_deterministically() -> None:
    first = observation(
        "oracle-feed-watch-b",
        asset_symbol="eth",
        market_slug="beta-watch",
        update_latency_seconds="150.000000",
        expected_source_count="3.000000",
        observed_source_count="3.000000",
    )
    second = observation(
        "oracle-feed-blocked",
        asset_symbol="btc",
        market_slug="alpha-blocked",
        update_latency_seconds="360.000000",
        missed_heartbeat_count="6.000000",
        expected_source_count="4.000000",
        observed_source_count="2.000000",
    )
    third = observation(
        "oracle-feed-watch-a",
        asset_symbol="btc",
        market_slug="alpha-watch",
        update_latency_seconds="150.000000",
        expected_source_count="3.000000",
        observed_source_count="3.000000",
    )

    forward = report(first, second, third)
    reverse = report(third, second, first)

    assert forward == reverse
    assert tuple(row.market_slug for row in forward.rows) == (
        "alpha-blocked",
        "alpha-watch",
        "beta-watch",
    )
    for row in forward.rows:
        assert row.reason_codes == tuple(sorted(row.reason_codes))
    assert forward.reason_codes == (
        "crypto_oracle_outage_latency_high_latency_present",
        "crypto_oracle_outage_latency_missed_heartbeat_present",
        "crypto_oracle_outage_latency_quorum_gap_present",
    )
    assert tuple(item.reason_code for item in forward.reason_code_counts) == (
        "crypto_oracle_outage_latency_high_latency_present",
        "crypto_oracle_outage_latency_missed_heartbeat_present",
        "crypto_oracle_outage_latency_quorum_gap_present",
    )


def test_non_default_thresholds_can_downgrade_moderate_oracle_pressure() -> None:
    module = digest()
    cfg = module.CryptoOracleOutageLatencyDigestConfig(
        watch_update_latency_seconds=d("180.000000"),
        blocked_update_latency_seconds=d("600.000000"),
        watch_stale_price_age_seconds=d("360.000000"),
        blocked_stale_price_age_seconds=d("900.000000"),
        watch_missed_heartbeat_count=d("4.000000"),
        blocked_missed_heartbeat_count=d("8.000000"),
        watch_source_quorum_gap=d("2.000000"),
        blocked_source_quorum_gap=d("4.000000"),
        watch_confidence_score=d("0.650000"),
        blocked_confidence_score=d("0.400000"),
    )

    digest_report = report(
        observation(
            "oracle-feed-moderate",
            update_latency_seconds="125.000000",
            missed_heartbeat_count="1.000000",
            stale_price_age_seconds="220.000000",
            expected_source_count="4.000000",
            observed_source_count="3.000000",
            confidence_score="0.700000",
        ),
        cfg=cfg,
    )

    assert digest_report.digest_status == "pass"
    assert digest_report.recommended_next_step == (
        "allow_report_only_crypto_oracle_outage_latency_screening"
    )
    assert digest_report.rows[0].latency_status == "pass"
    assert digest_report.rows[0].reason_codes == (
        "crypto_oracle_outage_latency_inline",
    )
    assert digest_report.outage_risk_score == d("0.000000")
    assert digest_report.reason_codes == ("crypto_oracle_outage_latency_digest_clear",)


def test_validation_rejects_bad_inputs_and_inconsistent_public_records() -> None:
    module = digest()

    with pytest.raises(ValueError, match="update_latency_seconds must be a Decimal"):
        observation(update_latency_seconds=_DecimalSubclass("42.000000"))
    with pytest.raises(ValueError, match="missed_heartbeat_count must be nonnegative"):
        observation(missed_heartbeat_count="-1.000000")
    with pytest.raises(ValueError, match="confidence_score must be between zero and one"):
        observation(confidence_score="1.100000")
    with pytest.raises(ValueError, match="observed_source_count must not exceed"):
        observation(expected_source_count="2.000000", observed_source_count="3.000000")
    with pytest.raises(ValueError, match="data_timestamp must be timezone-aware"):
        observation(data_timestamp=datetime(2026, 7, 4, 13, 50))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_crypto_oracle_outage_latency_digest(
            (),
            config=module.CryptoOracleOutageLatencyDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 14, 15, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        report("not-an-observation")
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(observation("oracle-feed-dupe"), observation("oracle-feed-dupe"))
    with pytest.raises(ValueError, match="watch_update_latency_seconds"):
        module.CryptoOracleOutageLatencyDigestConfig(
            watch_update_latency_seconds=d("600.000000"),
            blocked_update_latency_seconds=d("300.000000"),
        )

    valid_row = report(observation("oracle-feed-valid")).rows[0]
    with pytest.raises(ValueError, match="source_quorum_gap must match"):
        replace(valid_row, source_quorum_gap=d("9.000000"))
    with pytest.raises(ValueError, match="confidence_pressure must match"):
        replace(valid_row, confidence_pressure=d("0.990000"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(
            valid_row,
            reason_codes=(
                "crypto_oracle_outage_latency_inline",
                "crypto_oracle_outage_latency_watch_latency",
            ),
        )

    frozen_observation = observation("oracle-feed-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]


def test_hard_flags_are_enforced_on_config_rows_and_report() -> None:
    module = digest()

    digest_report = report(observation("oracle-feed-hard-flags"))
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in digest_report.rows)

    with pytest.raises(ValueError, match="config paper_only must be True"):
        module.CryptoOracleOutageLatencyDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(observation("oracle-feed-report-only"), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(digest_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(digest_report, paper_only=False)


def test_payload_uses_string_numerics_and_module_has_no_durable_or_live_surfaces() -> None:
    module = digest()
    digest_report = report(observation("oracle-feed-payload"))

    payload = module.market_research_crypto_oracle_outage_latency_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["update_latency_seconds"] == "42.000000"
    assert payload["rows"][0]["data_timestamp"] == "2026-07-04T13:50:00+00:00"

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                assert "private_key" not in lowered
                assert "wallet" not in lowered
                assert "credential" not in lowered
                assert "auth" not in lowered
                assert "order" not in lowered
                assert "cancel" not in lowered
                assert "replace" not in lowered
                assert "exchange" not in lowered
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))

    walk_payload(payload)

    for public_record in (
        module.CryptoOracleOutageLatencyDigestConfig(),
        observation("oracle-feed-dataclass"),
        digest_report.rows[0],
        digest_report.reason_code_counts[0],
        digest_report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if _is_public_numeric(field_value):
                assert type(field_value) is Decimal, field.name

    source = Path(
        "src/polymarket_alpha_lab/market_research_crypto_oracle_outage_latency_digest.py",
    ).read_text()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    sensitive_private_key = "private" + "_key"
    sensitive_fragments = (
        sensitive_private_key,
        "wallet",
        "credential",
        "auth",
        "urlopen",
        "connect(",
        "execute(",
        "live trading",
        "submit_" + "order",
        "cancel_" + "order",
        "replace_" + "order",
        "exchange mutation",
    )
    lowered_source = source.lower()
    assert not any(fragment in lowered_source for fragment in sensitive_fragments)


def _is_public_numeric(value: object) -> bool:
    return isinstance(value, Decimal)
