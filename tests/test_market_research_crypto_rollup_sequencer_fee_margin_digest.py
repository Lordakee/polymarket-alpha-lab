from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from types import MappingProxyType

import pytest

from polymarket_alpha_lab.market_research_crypto_rollup_sequencer_fee_margin_digest import (
    DEFAULT_MARKET_RESEARCH_CRYPTO_ROLLUP_SEQUENCER_FEE_MARGIN_DIGEST_CONFIG_VERSION,
    MarketResearchCryptoRollupSequencerFeeMarginDigestConfig,
    MarketResearchCryptoRollupSequencerFeeMarginDigestReasonCodeCount,
    MarketResearchCryptoRollupSequencerFeeMarginDigestReport,
    MarketResearchCryptoRollupSequencerFeeMarginDigestRow,
    MarketResearchCryptoRollupSequencerFeeMarginObservation,
    build_market_research_crypto_rollup_sequencer_fee_margin_digest,
    market_research_crypto_rollup_sequencer_fee_margin_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
BASE_REASON = "market_research_crypto_rollup_sequencer_fee_margin_digest_"
READY_REASON = BASE_REASON + "ready"
NO_INPUTS_REASON = BASE_REASON + "no_inputs"
MARGIN_COMPRESSION_USD_REASON = BASE_REASON + "margin_compression_usd"
MARGIN_COMPRESSION_RATIO_REASON = BASE_REASON + "margin_compression_ratio"
FEE_MARGIN_RATIO_GAP_REASON = BASE_REASON + "fee_margin_ratio_gap"
TRANSACTION_COUNT_GAP_REASON = BASE_REASON + "transaction_count_gap"
SOURCE_GAP_REASON = BASE_REASON + "source_gap"
CONFIDENCE_GAP_REASON = BASE_REASON + "confidence_gap"
STALE_SOURCE_REASON = BASE_REASON + "stale_source"


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(
    **overrides: object,
) -> MarketResearchCryptoRollupSequencerFeeMarginDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_CRYPTO_ROLLUP_SEQUENCER_FEE_MARGIN_DIGEST_CONFIG_VERSION
        ),
        "max_observation_age_seconds": d("7200.000000"),
        "min_source_count": d("2.000000"),
        "watch_margin_compression_usd": d("250000.000000"),
        "blocked_margin_compression_usd": d("1000000.000000"),
        "watch_margin_compression_ratio": d("0.250000"),
        "blocked_margin_compression_ratio": d("0.600000"),
        "min_fee_margin_ratio": d("0.150000"),
        "min_transaction_count": d("50000.000000"),
        "min_confidence": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchCryptoRollupSequencerFeeMarginDigestConfig(**values)


def _observation(
    rollup_id: str = "rollup_alpha",
    margin_id: str = "rollup_alpha_sequencer_fee_margin",
    *,
    asset_symbol: str = "ETH",
    observed_at: datetime = GENERATED_AT,
    sequencer_fee_revenue_usd: Decimal = d("900000.000000"),
    data_availability_cost_usd: Decimal = d("300000.000000"),
    baseline_sequencer_fee_margin_usd: Decimal = d("700000.000000"),
    transaction_count: Decimal = d("150000.000000"),
    source_count: Decimal = d("3.000000"),
    confidence: Decimal = d("0.820000"),
    source_config_version: str = "crypto-rollup-sequencer-fee-margin-source-v0",
) -> MarketResearchCryptoRollupSequencerFeeMarginObservation:
    return MarketResearchCryptoRollupSequencerFeeMarginObservation(
        rollup_id=rollup_id,
        margin_id=margin_id,
        asset_symbol=asset_symbol,
        observed_at=observed_at,
        sequencer_fee_revenue_usd=sequencer_fee_revenue_usd,
        data_availability_cost_usd=data_availability_cost_usd,
        baseline_sequencer_fee_margin_usd=baseline_sequencer_fee_margin_usd,
        transaction_count=transaction_count,
        source_count=source_count,
        confidence=confidence,
        source_config_version=source_config_version,
    )


def _report(
    *observations: MarketResearchCryptoRollupSequencerFeeMarginObservation,
    generated_at: datetime = GENERATED_AT,
    config: MarketResearchCryptoRollupSequencerFeeMarginDigestConfig | None = None,
) -> MarketResearchCryptoRollupSequencerFeeMarginDigestReport:
    return build_market_research_crypto_rollup_sequencer_fee_margin_digest(
        observations,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_report_only_blocked_digest() -> None:
    report = _report()

    assert isinstance(report, MarketResearchCryptoRollupSequencerFeeMarginDigestReport)
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-crypto-rollup-sequencer-fee-margin-digest-v0"
    )
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_rollup_sequencer_fee_margin_digest"
    )
    assert report.observation_count == d("0.000000")
    assert report.ready_observation_count == d("0.000000")
    assert report.watch_observation_count == d("0.000000")
    assert report.blocked_observation_count == d("0.000000")
    assert report.total_margin_compression_usd == d("0.000000")
    assert report.average_margin_compression_ratio == d("0.000000")
    assert report.average_fee_margin_ratio == d("0.000000")
    assert report.average_confidence == d("0.000000")
    assert report.max_observation_age_seconds == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (NO_INPUTS_REASON,)
    assert report.reason_code_counts == (
        MarketResearchCryptoRollupSequencerFeeMarginDigestReasonCodeCount(
            reason_code=NO_INPUTS_REASON,
            count=d("1.000000"),
            observation_ratio=d("0.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_rollup_sequencer_fee_margin_compression_blocks_screening() -> None:
    report = _report(
        _observation(
            "rollup_base",
            "base_sequencer_fee_margin_pressure",
            asset_symbol="ETH",
            observed_at=GENERATED_AT - timedelta(seconds=9000),
            sequencer_fee_revenue_usd=d("500000.000000"),
            data_availability_cost_usd=d("450000.000000"),
            baseline_sequencer_fee_margin_usd=d("1800000.000000"),
            transaction_count=d("40000.000000"),
            source_count=d("1.000000"),
            confidence=d("0.550000"),
        ),
        _observation(),
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_rollup_sequencer_fee_margin_digest"
    )
    assert report.observation_count == d("2.000000")
    assert report.ready_observation_count == d("1.000000")
    assert report.watch_observation_count == d("0.000000")
    assert report.blocked_observation_count == d("1.000000")
    assert report.margin_compression_usd_observation_count == d("1.000000")
    assert report.margin_compression_ratio_observation_count == d("1.000000")
    assert report.fee_margin_ratio_gap_observation_count == d("1.000000")
    assert report.transaction_count_gap_observation_count == d("1.000000")
    assert report.source_gap_observation_count == d("1.000000")
    assert report.confidence_gap_observation_count == d("1.000000")
    assert report.stale_source_observation_count == d("1.000000")
    assert report.total_margin_compression_usd == d("1850000.000000")
    assert report.average_margin_compression_ratio == d("0.557540")
    assert report.average_fee_margin_ratio == d("0.383334")
    assert report.average_confidence == d("0.685000")
    assert report.max_observation_age_seconds == d("9000.000000")

    assert tuple((row.rollup_id, row.margin_id) for row in report.rows) == (
        ("rollup_base", "base_sequencer_fee_margin_pressure"),
        ("rollup_alpha", "rollup_alpha_sequencer_fee_margin"),
    )
    base = report.rows[0]
    assert base.digest_status == "blocked"
    assert base.observation_age_seconds == d("9000.000000")
    assert base.sequencer_fee_margin_usd == d("50000.000000")
    assert base.margin_compression_usd == d("1750000.000000")
    assert base.margin_compression_ratio == d("0.972222")
    assert base.fee_margin_ratio == d("0.100000")
    assert base.reason_codes == (
        MARGIN_COMPRESSION_USD_REASON,
        MARGIN_COMPRESSION_RATIO_REASON,
        FEE_MARGIN_RATIO_GAP_REASON,
        TRANSACTION_COUNT_GAP_REASON,
        SOURCE_GAP_REASON,
        CONFIDENCE_GAP_REASON,
        STALE_SOURCE_REASON,
    )
    assert report.reason_codes == base.reason_codes


def test_timezone_normalization_reason_counts_and_source_versions() -> None:
    generated_at = datetime(2026, 7, 6, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    observed_at = datetime(2026, 7, 6, 14, 0, tzinfo=timezone(timedelta(hours=2)))

    report = _report(
        _observation(
            "rollup_sol",
            "sol_rollup_fee_margin_watch",
            asset_symbol="SOL",
            observed_at=observed_at,
            source_count=d("1.000000"),
        ),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].observed_at == GENERATED_AT
    assert report.rows[0].observation_age_seconds == d("0.000000")
    assert report.digest_status == "watch"
    assert report.reason_code_counts == (
        MarketResearchCryptoRollupSequencerFeeMarginDigestReasonCodeCount(
            reason_code=SOURCE_GAP_REASON,
            count=d("1.000000"),
            observation_ratio=d("1.000000"),
        ),
    )
    assert report.source_config_versions == (
        ("sol_rollup_fee_margin_watch", "crypto-rollup-sequencer-fee-margin-source-v0"),
    )


def test_rows_reason_codes_and_public_tuples_require_canonical_sequence() -> None:
    beta = _observation(
        "rollup_beta",
        "beta_rollup_fee_margin_watch",
        sequencer_fee_revenue_usd=d("800000.000000"),
        data_availability_cost_usd=d("450000.000000"),
        baseline_sequencer_fee_margin_usd=d("700000.000000"),
    )
    alpha = _observation(
        "rollup_alpha_watch",
        "alpha_rollup_fee_margin_watch",
        sequencer_fee_revenue_usd=d("800000.000000"),
        data_availability_cost_usd=d("450000.000000"),
        baseline_sequencer_fee_margin_usd=d("700000.000000"),
    )

    forward = _report(beta, alpha)
    reverse = _report(alpha, beta)

    assert forward == reverse
    assert tuple(row.margin_id for row in forward.rows) == (
        "alpha_rollup_fee_margin_watch",
        "beta_rollup_fee_margin_watch",
    )
    for row in forward.rows:
        assert row.digest_status == "watch"
        assert row.reason_codes == (
            MARGIN_COMPRESSION_USD_REASON,
            MARGIN_COMPRESSION_RATIO_REASON,
        )
    assert forward.reason_codes == forward.rows[0].reason_codes
    assert tuple(item.reason_code for item in forward.reason_code_counts) == (
        MARGIN_COMPRESSION_USD_REASON,
        MARGIN_COMPRESSION_RATIO_REASON,
    )

    with pytest.raises(ValueError, match="rows must be a tuple"):
        replace(forward, rows=list(forward.rows))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_code_counts must be a tuple"):
        replace(
            forward,
            reason_code_counts=list(forward.reason_code_counts),  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        replace(
            forward.rows[0],
            reason_codes=list(forward.rows[0].reason_codes),  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="rows must use canonical sequence"):
        replace(forward, rows=tuple(reversed(forward.rows)))
    with pytest.raises(ValueError, match="reason_codes must use canonical sequence"):
        replace(forward.rows[0], reason_codes=tuple(reversed(forward.rows[0].reason_codes)))
    with pytest.raises(ValueError, match="source_config_versions must use canonical sequence"):
        replace(forward, source_config_versions=tuple(reversed(forward.source_config_versions)))


def test_non_default_thresholds_can_downgrade_moderate_compression() -> None:
    cfg = _config(
        watch_margin_compression_usd=d("2000000.000000"),
        blocked_margin_compression_usd=d("3000000.000000"),
        watch_margin_compression_ratio=d("0.980000"),
        blocked_margin_compression_ratio=d("0.990000"),
        min_fee_margin_ratio=d("0.050000"),
        min_transaction_count=d("10000.000000"),
        min_confidence=d("0.500000"),
    )

    report = _report(
        _observation(
            "rollup_moderate",
            "moderate_rollup_fee_margin",
            sequencer_fee_revenue_usd=d("500000.000000"),
            data_availability_cost_usd=d("450000.000000"),
            baseline_sequencer_fee_margin_usd=d("1800000.000000"),
            transaction_count=d("40000.000000"),
            confidence=d("0.750000"),
        ),
        config=cfg,
    )

    assert report.digest_status == "ready"
    assert report.recommended_next_step == (
        "allow_report_only_market_research_crypto_rollup_sequencer_fee_margin_digest"
    )
    assert report.rows[0].digest_status == "ready"
    assert report.rows[0].reason_codes == (READY_REASON,)
    assert report.reason_codes == (READY_REASON,)


def test_validation_rejects_bad_inputs_subclasses_and_inconsistent_records() -> None:
    assert MarketResearchCryptoRollupSequencerFeeMarginDigestConfig.__dataclass_params__.frozen
    assert MarketResearchCryptoRollupSequencerFeeMarginObservation.__dataclass_params__.frozen
    assert MarketResearchCryptoRollupSequencerFeeMarginDigestRow.__dataclass_params__.frozen
    assert MarketResearchCryptoRollupSequencerFeeMarginDigestReasonCodeCount.__dataclass_params__.frozen
    assert MarketResearchCryptoRollupSequencerFeeMarginDigestReport.__dataclass_params__.frozen

    with pytest.raises(TypeError, match="does not support subclassing"):
        type("ConfigSubclass", (MarketResearchCryptoRollupSequencerFeeMarginDigestConfig,), {})
    with pytest.raises(TypeError, match="does not support subclassing"):
        type("ObservationSubclass", (MarketResearchCryptoRollupSequencerFeeMarginObservation,), {})
    with pytest.raises(TypeError, match="does not support subclassing"):
        type("RowSubclass", (MarketResearchCryptoRollupSequencerFeeMarginDigestRow,), {})
    with pytest.raises(TypeError, match="does not support subclassing"):
        type(
            "ReasonCodeCountSubclass",
            (MarketResearchCryptoRollupSequencerFeeMarginDigestReasonCodeCount,),
            {},
        )
    with pytest.raises(TypeError, match="does not support subclassing"):
        type("ReportSubclass", (MarketResearchCryptoRollupSequencerFeeMarginDigestReport,), {})

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("crypto-rollup-fee-margin-v0"))
    with pytest.raises(ValueError, match="watch_margin_compression_usd"):
        _config(
            watch_margin_compression_usd=d("3000000.000000"),
            blocked_margin_compression_usd=d("2000000.000000"),
        )
    with pytest.raises(ValueError, match="watch_margin_compression_ratio"):
        _config(
            watch_margin_compression_ratio=d("0.900000"),
            blocked_margin_compression_ratio=d("0.800000"),
        )
    with pytest.raises(ValueError, match="min_confidence"):
        _config(min_confidence=1)
    with pytest.raises(ValueError, match="sequencer_fee_revenue_usd"):
        _observation(sequencer_fee_revenue_usd=_DecimalSubclass("900000.000000"))
    with pytest.raises(ValueError, match="confidence"):
        _observation(confidence=Decimal("0.8200001"))
    with pytest.raises(ValueError, match="confidence"):
        _observation(confidence=Decimal("0.82"))
    with pytest.raises(ValueError, match="rollup_id"):
        _observation(rollup_id=_StringSubclass("rollup_alpha"))
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _observation(),
            generated_at=_DateTimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _observation(),
            generated_at=datetime(2026, 7, 6, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="observed_at"):
        _observation(observed_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="future"):
        _report(_observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="unique"):
        _report(
            _observation(margin_id="duplicate_margin"),
            _observation(rollup_id="rollup_b", margin_id="duplicate_margin"),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        build_market_research_crypto_rollup_sequencer_fee_margin_digest(
            ("not-an-observation",),  # type: ignore[arg-type]
            config=_config(),
            generated_at=GENERATED_AT,
        )

    valid_row = _report(_observation()).rows[0]
    with pytest.raises(ValueError, match="sequencer_fee_margin_usd"):
        replace(valid_row, sequencer_fee_margin_usd=d("999.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(valid_row, reason_codes=(READY_REASON, MARGIN_COMPRESSION_USD_REASON))

    frozen_observation = _observation("rollup_frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.rollup_id = "changed"  # type: ignore[misc]


def test_reason_counts_reject_zero_fractional_and_must_reconcile_with_rows() -> None:
    report = _report(_observation("rollup_reason_counts"))

    with pytest.raises(ValueError, match="count must be positive"):
        MarketResearchCryptoRollupSequencerFeeMarginDigestReasonCodeCount(
            reason_code=READY_REASON,
            count=d("0.000000"),
            observation_ratio=d("0.000000"),
        )
    with pytest.raises(ValueError, match="count must be integral"):
        MarketResearchCryptoRollupSequencerFeeMarginDigestReasonCodeCount(
            reason_code=READY_REASON,
            count=d("1.500000"),
            observation_ratio=d("1.000000"),
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            report,
            reason_code_counts=(
                replace(report.reason_code_counts[0], count=d("2.000000")),
            ),
        )


def test_hard_flags_are_enforced_on_all_public_records() -> None:
    report = _report(_observation("rollup_flags"))
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in report.rows)
    assert all(
        item.paper_only and item.report_only and item.readonly
        for item in report.reason_code_counts
    )

    with pytest.raises(ValueError, match="config paper_only must be True"):
        _config(paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(_observation("rollup_report_only"), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="reason code count paper_only must be True"):
        replace(report.reason_code_counts[0], paper_only=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(report, paper_only=False)


def test_public_numerics_payload_serialization_and_tamper_revalidation() -> None:
    report = _report(_observation("rollup_payload"))

    for public_record in (
        _config(),
        _observation("rollup_numeric"),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            value = getattr(public_record, field.name)
            if _is_public_numeric_field(field.name):
                assert type(value) is Decimal, field.name

    payload = market_research_crypto_rollup_sequencer_fee_margin_digest_payload(report)
    payload_text = repr(payload).lower()
    for forbidden in (
        "as" + "dict",
        "market" + "_" + "slug",
        "ques" + "tion",
        "payload" + "_" + "json",
        "wa" + "llet",
        "or" + "der",
        "au" + "th",
        "private",
    ):
        assert forbidden not in payload_text
    assert isinstance(payload, MappingProxyType)
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["observation_count"] == "1.000000"
    assert payload["total_margin_compression_usd"] == "100000.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["observed_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][0]["sequencer_fee_margin_usd"] == "600000.000000"
    assert payload["rows"][0]["paper_only"] is True
    with pytest.raises(TypeError):
        payload["observation_count"] = "0.000000"  # type: ignore[index]
    with pytest.raises(TypeError):
        payload["rows"][0]["sequencer_fee_margin_usd"] = "0.000000"  # type: ignore[index]

    tampered_report = _report(_observation("rollup_bad_numeric"))
    object.__setattr__(tampered_report, "observation_count", 1)
    with pytest.raises(ValueError, match="observation_count must be a Decimal"):
        market_research_crypto_rollup_sequencer_fee_margin_digest_payload(tampered_report)

    tampered_report = _report(_observation("rollup_bad_time"))
    object.__setattr__(
        tampered_report,
        "generated_at",
        datetime(2026, 7, 6, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    with pytest.raises(ValueError, match="generated_at must be UTC"):
        market_research_crypto_rollup_sequencer_fee_margin_digest_payload(tampered_report)

    tampered_report = _report(
        _observation(
            "rollup_nested_tamper",
            "nested_tamper_rollup_fee_margin",
            sequencer_fee_revenue_usd=d("800000.000000"),
            data_availability_cost_usd=d("450000.000000"),
            baseline_sequencer_fee_margin_usd=d("700000.000000"),
        ),
    )
    object.__setattr__(
        tampered_report.rows[0],
        "reason_codes",
        tuple(reversed(tampered_report.rows[0].reason_codes)),
    )
    with pytest.raises(ValueError, match="reason_codes must use canonical sequence"):
        market_research_crypto_rollup_sequencer_fee_margin_digest_payload(tampered_report)

    tampered_report = _report(_observation("rollup_reason_count_payload_tamper"))
    object.__setattr__(tampered_report.reason_code_counts[0], "count", d("0.000000"))
    with pytest.raises(ValueError, match="count|reason_code_counts"):
        market_research_crypto_rollup_sequencer_fee_margin_digest_payload(tampered_report)


def test_module_scope_excludes_forbidden_surfaces() -> None:
    module = __import__(
        "polymarket_alpha_lab.market_research_crypto_rollup_sequencer_fee_margin_digest",
        fromlist=["_"],
    )
    source_text = module.__loader__.get_source(module.__name__)
    assert source_text is not None
    lowered = source_text.lower()
    tree = ast.parse(source_text)

    forbidden_literals = (
        "as" + "dict",
        "market" + "_" + "slug",
        "ques" + "tion",
        "payload" + "_" + "json",
        "wa" + "llet",
        "or" + "der",
        "au" + "th",
        "private",
        "database",
        "supabase",
        "persist",
        "sqlite",
        "broker",
        "signing",
        "submit",
        "cancel",
    )
    assert not any(token in lowered for token in forbidden_literals)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            callee_name = ""
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in {
                "open",
                "read",
                "write",
                "submit",
                "cancel",
                "replace",
                "connect",
                "execute",
                "getenv",
            }
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_fragments = (
        "db",
        "env",
        "cli",
        "psycopg",
        "requests",
        "socket",
        "urllib",
        "sqlite",
        "subprocess",
        "httpx",
        "pathlib",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _is_public_numeric_field(field_name: str) -> bool:
    return field_name not in {
        "rollup_id",
        "margin_id",
        "asset_symbol",
        "observed_at",
        "generated_at",
        "digest_status",
        "recommended_next_step",
        "config_version",
        "rows",
        "source_config_versions",
        "reason_code_counts",
        "reason_codes",
        "reason_code",
        "source_config_version",
        "paper_only",
        "report_only",
        "readonly",
    }
