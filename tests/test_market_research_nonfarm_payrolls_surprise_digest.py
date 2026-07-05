from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_research_nonfarm_payrolls_surprise_digest import (
    DEFAULT_MARKET_RESEARCH_NONFARM_PAYROLLS_SURPRISE_DIGEST_CONFIG_VERSION,
    MarketResearchNonfarmPayrollsSurpriseDigestConfig,
    MarketResearchNonfarmPayrollsSurpriseDigestInputRow,
    MarketResearchNonfarmPayrollsSurpriseDigestReasonCodeCount,
    MarketResearchNonfarmPayrollsSurpriseDigestReport,
    MarketResearchNonfarmPayrollsSurpriseDigestRow,
    build_market_research_nonfarm_payrolls_surprise_digest,
    market_research_nonfarm_payrolls_surprise_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
_UNSET = object()


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _MissingOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchNonfarmPayrollsSurpriseDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_NONFARM_PAYROLLS_SURPRISE_DIGEST_CONFIG_VERSION
        ),
        "fresh_release_max_age_seconds": d("7200.000000"),
        "material_surprise_threshold_jobs": d("50000.000000"),
        "min_source_count": d("2.000000"),
        "max_acknowledgement_lag_seconds": d("1800.000000"),
        "probability_repricing_threshold": d("0.050000"),
    }
    values.update(overrides)
    return MarketResearchNonfarmPayrollsSurpriseDigestConfig(**values)


def input_row(
    research_key: str = "research.nfp.bls",
    *,
    condition_id: str = "condition_nfp_surprise",
    payroll_series_key: str = "ces.total_nonfarm_payrolls",
    release_reference: str = "public-bls-employment-situation",
    released_at: datetime | None = None,
    acknowledged_at: object = _UNSET,
    source_count: Decimal = d("3.000000"),
    actual_payroll_jobs: Decimal = d("185000.000000"),
    consensus_payroll_jobs: Decimal = d("170000.000000"),
    previous_payroll_jobs: Decimal = d("150000.000000"),
    market_probability_before: Decimal = d("0.460000"),
    market_probability_after: Decimal = d("0.500000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchNonfarmPayrollsSurpriseDigestInputRow:
    return MarketResearchNonfarmPayrollsSurpriseDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        payroll_series_key=payroll_series_key,
        release_reference=release_reference,
        released_at=released_at or GENERATED_AT - timedelta(minutes=45),
        acknowledged_at=(
            GENERATED_AT - timedelta(minutes=30)
            if acknowledged_at is _UNSET
            else acknowledged_at
        ),
        source_count=source_count,
        actual_payroll_jobs=actual_payroll_jobs,
        consensus_payroll_jobs=consensus_payroll_jobs,
        previous_payroll_jobs=previous_payroll_jobs,
        market_probability_before=market_probability_before,
        market_probability_after=market_probability_after,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketResearchNonfarmPayrollsSurpriseDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchNonfarmPayrollsSurpriseDigestReport:
    return build_market_research_nonfarm_payrolls_surprise_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_nonfarm_payrolls_surprise_digest_reduces_rows_redacts_refs_and_sorts() -> None:
    summary = report(
        (
            input_row(
                "research.nfp.regional",
                condition_id="condition_regional_payrolls",
                payroll_series_key="regional.nonfarm_payrolls",
                release_reference=(
                    "https://vendor.example/payrolls?feed=regional&token=secret"
                ),
                released_at=GENERATED_AT - timedelta(hours=3),
                acknowledged_at=GENERATED_AT - timedelta(minutes=70),
                source_count=d("1.000000"),
                actual_payroll_jobs=d("120000.000000"),
                consensus_payroll_jobs=d("190000.000000"),
                previous_payroll_jobs=d("160000.000000"),
                market_probability_before=d("0.410000"),
                market_probability_after=d("0.520000"),
            ),
            input_row(
                "research.nfp.bls",
                condition_id="condition_nfp_surprise",
                payroll_series_key="ces.total_nonfarm_payrolls",
                release_reference="public-bls-employment-situation",
                released_at=GENERATED_AT - timedelta(minutes=45),
                acknowledged_at=GENERATED_AT - timedelta(minutes=30),
                source_count=d("3.000000"),
                actual_payroll_jobs=d("185000.000000"),
                consensus_payroll_jobs=d("170000.000000"),
                previous_payroll_jobs=d("150000.000000"),
                market_probability_before=d("0.460000"),
                market_probability_after=d("0.500000"),
            ),
            input_row(
                "research.nfp.private",
                condition_id="condition_private_payrolls",
                payroll_series_key="adp.private_nonfarm_payrolls",
                release_reference="private-nfp-feed",
                released_at=GENERATED_AT - timedelta(hours=5),
                acknowledged_at=None,
                source_count=d("2.000000"),
                actual_payroll_jobs=d("250000.000000"),
                consensus_payroll_jobs=d("180000.000000"),
                previous_payroll_jobs=d("190000.000000"),
                market_probability_before=d("0.300000"),
                market_probability_after=d("0.340000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_NONFARM_PAYROLLS_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_nonfarm_payrolls_surprise_digest"
    )
    assert summary.release_count == d("3.000000")
    assert summary.ready_release_count == d("1.000000")
    assert summary.watch_release_count == d("1.000000")
    assert summary.blocked_release_count == d("1.000000")
    assert summary.positive_surprise_count == d("2.000000")
    assert summary.negative_surprise_count == d("1.000000")
    assert summary.material_surprise_count == d("2.000000")
    assert summary.stale_release_count == d("2.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.missing_acknowledgement_count == d("1.000000")
    assert summary.slow_acknowledgement_count == d("1.000000")
    assert summary.probability_repricing_count == d("1.000000")
    assert summary.positive_surprise_ratio == d("0.666667")
    assert summary.negative_surprise_ratio == d("0.333333")
    assert summary.material_surprise_ratio == d("0.666667")
    assert summary.average_abs_surprise_jobs == d("51666.666667")
    assert summary.max_release_age_seconds == d("18000.000000")
    assert summary.average_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.payroll_series_key, row.research_key) for row in summary.rows) == (
        ("adp.private_nonfarm_payrolls", "research.nfp.private"),
        ("regional.nonfarm_payrolls", "research.nfp.regional"),
        ("ces.total_nonfarm_payrolls", "research.nfp.bls"),
    )

    private = summary.rows[0]
    assert private.surprise_status == "blocked"
    assert private.release_age_seconds == d("18000.000000")
    assert private.acknowledgement_lag_seconds is None
    assert private.payroll_surprise_jobs == d("70000.000000")
    assert private.payroll_surprise_abs_jobs == d("70000.000000")
    assert private.payroll_surprise_ratio == d("0.388889")
    assert private.previous_payroll_delta_jobs == d("60000.000000")
    assert private.probability_delta == d("0.040000")
    assert private.redacted_release_reference == "sha256:fdc7f92b72d1"
    assert private.reason_codes == (
        "market_research_nonfarm_payrolls_surprise_digest_material_surprise",
        "market_research_nonfarm_payrolls_surprise_digest_positive_surprise",
        "market_research_nonfarm_payrolls_surprise_digest_missing_acknowledgement",
        "market_research_nonfarm_payrolls_surprise_digest_stale_release",
    )

    regional = summary.rows[1]
    assert regional.surprise_status == "watch"
    assert regional.release_age_seconds == d("10800.000000")
    assert regional.acknowledgement_lag_seconds == d("6600.000000")
    assert regional.payroll_surprise_jobs == d("-70000.000000")
    assert regional.payroll_surprise_abs_jobs == d("70000.000000")
    assert regional.payroll_surprise_ratio == d("0.368421")
    assert regional.previous_payroll_delta_jobs == d("-40000.000000")
    assert regional.probability_delta == d("0.110000")
    assert regional.redacted_release_reference == "sha256:68f05251bfb8"
    assert regional.reason_codes == (
        "market_research_nonfarm_payrolls_surprise_digest_material_surprise",
        "market_research_nonfarm_payrolls_surprise_digest_negative_surprise",
        "market_research_nonfarm_payrolls_surprise_digest_probability_repricing",
        "market_research_nonfarm_payrolls_surprise_digest_slow_acknowledgement",
        "market_research_nonfarm_payrolls_surprise_digest_stale_release",
        "market_research_nonfarm_payrolls_surprise_digest_thin_sources",
    )

    bls = summary.rows[2]
    assert bls.surprise_status == "ready"
    assert bls.release_age_seconds == d("2700.000000")
    assert bls.acknowledgement_lag_seconds == d("900.000000")
    assert bls.payroll_surprise_jobs == d("15000.000000")
    assert bls.payroll_surprise_abs_jobs == d("15000.000000")
    assert bls.payroll_surprise_ratio == d("0.088235")
    assert bls.previous_payroll_delta_jobs == d("35000.000000")
    assert bls.probability_delta == d("0.040000")
    assert bls.redacted_release_reference == "public-bls-employment-situation"
    assert bls.reason_codes == (
        "market_research_nonfarm_payrolls_surprise_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchNonfarmPayrollsSurpriseDigestReasonCodeCount(
            reason_code="market_research_nonfarm_payrolls_surprise_digest_material_surprise",
            count=d("2.000000"),
            release_ratio=d("0.666667"),
        ),
        MarketResearchNonfarmPayrollsSurpriseDigestReasonCodeCount(
            reason_code="market_research_nonfarm_payrolls_surprise_digest_positive_surprise",
            count=d("1.000000"),
            release_ratio=d("0.333333"),
        ),
        MarketResearchNonfarmPayrollsSurpriseDigestReasonCodeCount(
            reason_code="market_research_nonfarm_payrolls_surprise_digest_negative_surprise",
            count=d("1.000000"),
            release_ratio=d("0.333333"),
        ),
        MarketResearchNonfarmPayrollsSurpriseDigestReasonCodeCount(
            reason_code="market_research_nonfarm_payrolls_surprise_digest_probability_repricing",
            count=d("1.000000"),
            release_ratio=d("0.333333"),
        ),
        MarketResearchNonfarmPayrollsSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_nonfarm_payrolls_surprise_digest_"
                "missing_acknowledgement"
            ),
            count=d("1.000000"),
            release_ratio=d("0.333333"),
        ),
        MarketResearchNonfarmPayrollsSurpriseDigestReasonCodeCount(
            reason_code="market_research_nonfarm_payrolls_surprise_digest_slow_acknowledgement",
            count=d("1.000000"),
            release_ratio=d("0.333333"),
        ),
        MarketResearchNonfarmPayrollsSurpriseDigestReasonCodeCount(
            reason_code="market_research_nonfarm_payrolls_surprise_digest_stale_release",
            count=d("2.000000"),
            release_ratio=d("0.666667"),
        ),
        MarketResearchNonfarmPayrollsSurpriseDigestReasonCodeCount(
            reason_code="market_research_nonfarm_payrolls_surprise_digest_thin_sources",
            count=d("1.000000"),
            release_ratio=d("0.333333"),
        ),
        MarketResearchNonfarmPayrollsSurpriseDigestReasonCodeCount(
            reason_code="market_research_nonfarm_payrolls_surprise_digest_ready",
            count=d("1.000000"),
            release_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )

    serialized = repr(asdict(summary)).lower()
    for token in (
        "vendor.example",
        "token",
        "secret",
        "https://",
        "private-nfp-feed",
    ):
        assert token not in serialized


def test_empty_input_blocks_with_no_inputs_count_and_zero_ratio() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_nonfarm_payrolls_surprise_digest"
    )
    assert summary.reason_codes == (
        "market_research_nonfarm_payrolls_surprise_digest_no_inputs",
    )
    assert summary.release_count == ZERO
    assert summary.ready_release_count == ZERO
    assert summary.watch_release_count == ZERO
    assert summary.blocked_release_count == ZERO
    assert summary.positive_surprise_count == ZERO
    assert summary.negative_surprise_count == ZERO
    assert summary.material_surprise_count == ZERO
    assert summary.positive_surprise_ratio == ZERO
    assert summary.negative_surprise_ratio == ZERO
    assert summary.material_surprise_ratio == ZERO
    assert summary.average_abs_surprise_jobs == ZERO
    assert summary.max_release_age_seconds == ZERO
    assert summary.average_source_count == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        MarketResearchNonfarmPayrollsSurpriseDigestReasonCodeCount(
            reason_code="market_research_nonfarm_payrolls_surprise_digest_no_inputs",
            count=d("1.000000"),
            release_ratio=d("0.000000"),
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_payload_is_json_ready_uses_six_decimal_strings_and_no_raw_refs() -> None:
    summary = report((input_row(),))
    payload = market_research_nonfarm_payrolls_surprise_digest_payload(summary)
    unsafe_public_summary = report(
        (
            input_row(
                release_reference="public-token-secret-payroll-feed",
            ),
        ),
    )
    unsafe_public_payload = market_research_nonfarm_payrolls_surprise_digest_payload(
        unsafe_public_summary,
    )

    assert json.loads(json.dumps(payload))["digest_status"] == "ready"
    assert payload["generated_at"] == "2026-07-03T16:00:00+00:00"
    assert payload["release_count"] == "1.000000"
    assert payload["positive_surprise_ratio"] == "1.000000"
    assert payload["rows"][0]["released_at"] == "2026-07-03T15:15:00+00:00"
    assert payload["rows"][0]["acknowledgement_lag_seconds"] == "900.000000"
    assert payload["rows"][0]["payroll_surprise_abs_jobs"] == "15000.000000"
    assert payload["reason_code_counts"][0]["release_ratio"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert isinstance(payload["rows"], list)
    assert isinstance(payload["rows"][0]["reason_codes"], list)
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert not any(type(value) is int for value in walk_values(payload))
    assert "'release_reference':" not in repr(payload)
    assert "private" not in repr(payload).lower()
    assert unsafe_public_summary.rows[0].redacted_release_reference.startswith("sha256:")
    assert "public-token-secret-payroll-feed" not in repr(unsafe_public_payload)
    assert "token" not in repr(unsafe_public_payload).lower()
    assert "secret" not in repr(unsafe_public_payload).lower()

    for value in (config(), input_row(), summary.rows[0], summary.reason_code_counts[0], summary):
        assert_decimal_numeric_fields(value)

    with pytest.raises(ValueError, match="report must be exactly"):
        market_research_nonfarm_payrolls_surprise_digest_payload(object())  # type: ignore[arg-type]


def test_public_dataclasses_are_frozen_exact_type_and_validate_inputs() -> None:
    summary = report((input_row(),))

    with pytest.raises(FrozenInstanceError):
        summary.digest_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].surprise_status = "watch"  # type: ignore[misc]

    assert type(summary) is MarketResearchNonfarmPayrollsSurpriseDigestReport
    assert type(summary.rows[0]) is MarketResearchNonfarmPayrollsSurpriseDigestRow
    assert is_dataclass(MarketResearchNonfarmPayrollsSurpriseDigestConfig)
    assert is_dataclass(MarketResearchNonfarmPayrollsSurpriseDigestInputRow)
    assert is_dataclass(MarketResearchNonfarmPayrollsSurpriseDigestReasonCodeCount)

    with pytest.raises(TypeError, match="does not support subclassing"):

        class ConfigSubclass(MarketResearchNonfarmPayrollsSurpriseDigestConfig):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class InputSubclass(MarketResearchNonfarmPayrollsSurpriseDigestInputRow):
            pass

    aware_plus_one = datetime(2026, 7, 3, 17, 0, tzinfo=timezone(timedelta(hours=1)))
    row = input_row(released_at=aware_plus_one, acknowledged_at=aware_plus_one)
    assert row.released_at == GENERATED_AT
    assert row.released_at.tzinfo is UTC
    assert row.acknowledged_at == GENERATED_AT
    assert row.acknowledged_at.tzinfo is UTC

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report((input_row(),), generated_at=datetime(2026, 7, 3, 16, 0))
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report((input_row(),), generated_at=_DatetimeSubclass(2026, 7, 3, 16, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(
            (input_row(),),
            generated_at=datetime(2026, 7, 3, 16, 0, tzinfo=_MissingOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="released_at must be timezone-aware"):
        input_row(released_at=datetime(2026, 7, 3, 15, 0))
    with pytest.raises(ValueError, match="acknowledged_at must be exactly datetime"):
        input_row(acknowledged_at=_DatetimeSubclass(2026, 7, 3, 15, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="acknowledged_at must not precede released_at"):
        input_row(
            released_at=GENERATED_AT - timedelta(minutes=10),
            acknowledged_at=GENERATED_AT - timedelta(minutes=20),
        )
    with pytest.raises(ValueError, match="released_at must not be after generated_at"):
        report(
            (
                input_row(
                    released_at=GENERATED_AT + timedelta(seconds=1),
                    acknowledged_at=GENERATED_AT + timedelta(seconds=2),
                ),
            ),
        )
    with pytest.raises(ValueError, match="config must be exactly"):
        report((input_row(),), cfg=object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="config_version"):
        config(config_version="market_research_nonfarm_payrolls_surprise_digest.v0")
    with pytest.raises(ValueError, match="input row must be exactly"):
        report((object(),))
    with pytest.raises(ValueError, match="source_count must be exactly Decimal"):
        input_row(source_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="actual_payroll_jobs must be exactly Decimal"):
        input_row(actual_payroll_jobs=_DecimalSubclass("185000.000000"))
    with pytest.raises(ValueError, match="source_count must be a whole-count Decimal"):
        input_row(source_count=d("1.500000"))
    with pytest.raises(ValueError, match="market_probability_before must be between"):
        input_row(market_probability_before=d("1.000001"))
    with pytest.raises(ValueError, match="release_reference contains forbidden text"):
        input_row(release_reference="wallet-private-source")
    with pytest.raises(ValueError, match="research_key must be a plain string"):
        input_row(research_key=_StringSubclass("research.nfp.subclass"))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(summary.rows[0], paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(summary.reason_code_counts[0], report_only=False)


def test_manual_constructors_reject_noncanonical_ordering_and_inconsistency() -> None:
    risky_summary = report(
        (
            input_row(
                "research.nfp.regional",
                condition_id="condition_regional_payrolls",
                payroll_series_key="regional.nonfarm_payrolls",
                released_at=GENERATED_AT - timedelta(hours=3),
                acknowledged_at=GENERATED_AT - timedelta(minutes=70),
                source_count=d("1.000000"),
                actual_payroll_jobs=d("120000.000000"),
                consensus_payroll_jobs=d("190000.000000"),
                previous_payroll_jobs=d("160000.000000"),
                market_probability_before=d("0.410000"),
                market_probability_after=d("0.520000"),
            ),
            input_row(
                "research.nfp.private",
                condition_id="condition_private_payrolls",
                payroll_series_key="adp.private_nonfarm_payrolls",
                released_at=GENERATED_AT - timedelta(hours=5),
                acknowledged_at=None,
                source_count=d("2.000000"),
                actual_payroll_jobs=d("250000.000000"),
                consensus_payroll_jobs=d("180000.000000"),
                previous_payroll_jobs=d("190000.000000"),
                market_probability_before=d("0.300000"),
                market_probability_after=d("0.340000"),
            ),
        ),
    )
    ready_summary = report(
        (
            input_row(
                "research.nfp.z",
                condition_id="condition_z",
                payroll_series_key="ces.z",
            ),
            input_row(
                "research.nfp.a",
                condition_id="condition_a",
                payroll_series_key="ces.a",
            ),
        ),
    )
    risky_row = risky_summary.rows[1]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(risky_row, reason_codes=tuple(reversed(risky_row.reason_codes)))
    with pytest.raises(ValueError, match="surprise_status"):
        replace(risky_row, surprise_status="blocked")
    with pytest.raises(ValueError, match="payroll_surprise_jobs"):
        replace(risky_row, payroll_surprise_jobs=d("9.000000"))
    with pytest.raises(ValueError, match="acknowledgement_lag_seconds"):
        replace(risky_row, acknowledged_at=None)

    with pytest.raises(ValueError, match="rows"):
        replace(ready_summary, rows=tuple(reversed(ready_summary.rows)))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(risky_summary, reason_codes=tuple(reversed(risky_summary.reason_codes)))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            risky_summary,
            reason_code_counts=tuple(reversed(risky_summary.reason_code_counts)),
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            risky_summary,
            reason_code_counts=risky_summary.reason_code_counts[:-1],
        )
    with pytest.raises(ValueError, match="ready_release_count"):
        replace(ready_summary, ready_release_count=ZERO)


def test_module_has_no_io_durable_store_or_live_mutation_surfaces() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_nonfarm_payrolls_surprise_digest",
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    serialized_source = source.lower()
    serialized_report = repr(
        asdict(
            build_market_research_nonfarm_payrolls_surprise_digest(
                (input_row(),),
                config=config(),
                generated_at=GENERATED_AT,
            ),
        ),
    ).lower()

    forbidden_source_literals = (
        "auth",
        "broker",
        "cancel",
        "database",
        "execute",
        "exchange",
        "live",
        "order",
        "persist",
        "secret",
        "store",
        "token",
        "trade",
        "wallet",
    )
    assert not any(token in serialized_source for token in forbidden_source_literals)
    assert not any(token in serialized_report for token in forbidden_source_literals)

    imported_modules: set[str] = set()
    call_names: list[str] = []
    attribute_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    forbidden_import_fragments = (
        "http",
        "psycopg",
        "requests",
        "socket",
        "sqlite",
        "supabase",
        "urllib",
        "web3",
    )
    forbidden_call_or_attribute_names = {
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "getenv",
        "open",
        "rollback",
        "send",
        "write",
    }
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    assert not (set(call_names) & forbidden_call_or_attribute_names)
    assert not (set(attribute_names) & forbidden_call_or_attribute_names)


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in walk_values(nested))
    return (value,)


def assert_decimal_numeric_fields(value: object) -> None:
    numeric_name_fragments = (
        "age",
        "count",
        "jobs",
        "lag",
        "probability",
        "ratio",
        "seconds",
        "threshold",
    )
    for field in fields(value):
        if any(fragment in field.name for fragment in numeric_name_fragments):
            field_value = getattr(value, field.name)
            if isinstance(field_value, datetime):
                continue
            if isinstance(field_value, tuple):
                continue
            if field_value is None:
                continue
            assert type(field_value) is Decimal, field.name
