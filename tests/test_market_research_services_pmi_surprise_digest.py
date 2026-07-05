from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timezone, timedelta, tzinfo
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_research_services_pmi_surprise_digest import (
    DEFAULT_MARKET_RESEARCH_SERVICES_PMI_SURPRISE_DIGEST_CONFIG_VERSION,
    MarketResearchServicesPmiSurpriseDigestConfig,
    MarketResearchServicesPmiSurpriseDigestReport,
    PmiSurpriseDigestObservation,
    PmiSurpriseDigestRow,
    build_market_research_services_pmi_surprise_digest,
)


GENERATED_AT = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def test_pmi_surprise_digest_buckets_services_observations_deterministically() -> None:
    report = build_market_research_services_pmi_surprise_digest(
        (
            _observation(
                region="us",
                source_name="ISM",
                period="2026-06",
                actual_pmi=Decimal("52.3"),
                consensus_pmi=Decimal("50.0"),
                prior_pmi=Decimal("49.7"),
                observed_at=datetime(2026, 7, 3, 9, 0, tzinfo=timezone(timedelta(hours=-4))),
            ),
            _observation(
                region="eurozone",
                source_name="HCOB",
                period="2026-06",
                actual_pmi=Decimal("49.8"),
                consensus_pmi=Decimal("51.0"),
                prior_pmi=Decimal("51.4"),
                observed_at=datetime(2026, 7, 3, 14, 0, tzinfo=timezone(timedelta(hours=2))),
            ),
            _observation(
                region="japan",
                source_name="Jibun",
                period="2026-06",
                actual_pmi=Decimal("50.0"),
                consensus_pmi=Decimal("50.0"),
                prior_pmi=Decimal("49.9"),
                observed_at=datetime(2026, 7, 3, 21, 30, tzinfo=timezone(timedelta(hours=9))),
            ),
        ),
        config=MarketResearchServicesPmiSurpriseDigestConfig(),
        generated_at=datetime(2026, 7, 3, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert isinstance(report, MarketResearchServicesPmiSurpriseDigestReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        DEFAULT_MARKET_RESEARCH_SERVICES_PMI_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert report.summary_status == "watch"
    assert report.summary_next_step == "review_services_pmi_surprises"
    assert report.observation_count == Decimal("3")
    assert report.upside_surprise_count == Decimal("1")
    assert report.downside_surprise_count == Decimal("1")
    assert report.inline_surprise_count == Decimal("1")
    assert report.expansion_count == Decimal("2")
    assert report.contraction_count == Decimal("1")
    assert report.average_surprise_pmi == Decimal("0.366667")
    assert report.average_abs_surprise_pmi == Decimal("1.166667")
    assert report.max_abs_surprise_pmi == Decimal("2.300000")
    assert report.upside_surprise_ratio == Decimal("0.333333")
    assert report.downside_surprise_ratio == Decimal("0.333333")
    assert report.expansion_ratio == Decimal("0.666667")
    assert report.reason_codes == (
        "services_pmi_downside_surprise_present",
        "services_pmi_upside_surprise_present",
    )
    assert report.rows == (
        PmiSurpriseDigestRow(
            region="us",
            source_name="ISM",
            period="2026-06",
            actual_pmi=Decimal("52.300000"),
            consensus_pmi=Decimal("50.000000"),
            prior_pmi=Decimal("49.700000"),
            surprise_pmi=Decimal("2.300000"),
            abs_surprise_pmi=Decimal("2.300000"),
            momentum_pmi=Decimal("2.600000"),
            surprise_direction="upside",
            activity_status="expansion",
            observed_at=datetime(2026, 7, 3, 13, 0, tzinfo=UTC),
        ),
        PmiSurpriseDigestRow(
            region="eurozone",
            source_name="HCOB",
            period="2026-06",
            actual_pmi=Decimal("49.800000"),
            consensus_pmi=Decimal("51.000000"),
            prior_pmi=Decimal("51.400000"),
            surprise_pmi=Decimal("-1.200000"),
            abs_surprise_pmi=Decimal("1.200000"),
            momentum_pmi=Decimal("-1.600000"),
            surprise_direction="downside",
            activity_status="contraction",
            observed_at=datetime(2026, 7, 3, 12, 0, tzinfo=UTC),
        ),
        PmiSurpriseDigestRow(
            region="japan",
            source_name="Jibun",
            period="2026-06",
            actual_pmi=Decimal("50.000000"),
            consensus_pmi=Decimal("50.000000"),
            prior_pmi=Decimal("49.900000"),
            surprise_pmi=Decimal("0.000000"),
            abs_surprise_pmi=Decimal("0.000000"),
            momentum_pmi=Decimal("0.100000"),
            surprise_direction="inline",
            activity_status="expansion",
            observed_at=datetime(2026, 7, 3, 12, 30, tzinfo=UTC),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    _assert_public_numeric_fields_are_exact_six_decimal_decimals(report)
    for row in report.rows:
        _assert_public_numeric_fields_are_exact_six_decimal_decimals(row)

    serialized = repr(asdict(report)).lower()
    for token in ("trade", "order", "wallet", "auth", "buy", "sell", "position"):
        assert token not in serialized


def test_empty_pmi_surprise_digest_blocks_with_decimal_zeroes() -> None:
    report = build_market_research_services_pmi_surprise_digest(
        (),
        config=MarketResearchServicesPmiSurpriseDigestConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.summary_status == "blocked"
    assert report.reason_codes == ("services_pmi_surprise_digest_empty",)
    assert report.observation_count == Decimal("0")
    assert report.upside_surprise_count == Decimal("0")
    assert report.downside_surprise_count == Decimal("0")
    assert report.inline_surprise_count == Decimal("0")
    assert report.expansion_count == Decimal("0")
    assert report.contraction_count == Decimal("0")
    assert report.average_surprise_pmi == Decimal("0.000000")
    assert report.average_abs_surprise_pmi == Decimal("0.000000")
    assert report.max_abs_surprise_pmi == Decimal("0.000000")
    assert report.upside_surprise_ratio == Decimal("0.000000")
    assert report.downside_surprise_ratio == Decimal("0.000000")
    assert report.expansion_ratio == Decimal("0.000000")
    assert report.rows == ()
    _assert_public_numeric_fields_are_exact_six_decimal_decimals(report)


def test_all_inline_expansion_inputs_pass_with_single_reason_code() -> None:
    report = build_market_research_services_pmi_surprise_digest(
        (
            _observation(actual_pmi=Decimal("50.2"), consensus_pmi=Decimal("50.2")),
            _observation(
                region="eurozone",
                source_name="HCOB",
                period="2026-07",
                actual_pmi=Decimal("51.4"),
                consensus_pmi=Decimal("51.4"),
                prior_pmi=Decimal("51.0"),
            ),
        ),
        config=MarketResearchServicesPmiSurpriseDigestConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.summary_status == "pass"
    assert report.reason_codes == ("services_pmi_surprise_digest_passed",)
    assert report.observation_count == Decimal("2")
    assert report.inline_surprise_count == Decimal("2")
    assert report.expansion_count == Decimal("2")
    assert report.contraction_count == Decimal("0")
    assert report.average_surprise_pmi == Decimal("0.000000")
    assert report.average_abs_surprise_pmi == Decimal("0.000000")
    assert report.upside_surprise_ratio == Decimal("0.000000")
    assert report.downside_surprise_ratio == Decimal("0.000000")
    assert report.expansion_ratio == Decimal("1.000000")


def test_rejects_bad_types_subclasses_inconsistent_reports_and_false_hard_flags() -> None:
    with pytest.raises(ValueError, match="config_version"):
        MarketResearchServicesPmiSurpriseDigestConfig(
            config_version=_StringSubclass(
                DEFAULT_MARKET_RESEARCH_SERVICES_PMI_SURPRISE_DIGEST_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_services_pmi_surprise_digest(
            (),
            config=MarketResearchServicesPmiSurpriseDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 3, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations"):
        build_market_research_services_pmi_surprise_digest(
            (object(),),
            config=MarketResearchServicesPmiSurpriseDigestConfig(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="actual_pmi"):
        _observation(actual_pmi=_DecimalSubclass("50.0"))
    with pytest.raises(ValueError, match="actual_pmi"):
        _observation(actual_pmi=50)
    with pytest.raises(ValueError, match="observed_at"):
        _observation(observed_at=datetime(2026, 7, 3, 12, 0))
    with pytest.raises(ValueError, match="timezone-aware|aware datetime"):
        _observation(observed_at=datetime(2026, 7, 3, 12, 0, tzinfo=_NoneOffsetTz()))
    with pytest.raises(ValueError, match="timezone-aware|aware datetime"):
        build_market_research_services_pmi_surprise_digest(
            (),
            config=MarketResearchServicesPmiSurpriseDigestConfig(),
            generated_at=datetime(2026, 7, 3, 12, 0, tzinfo=_NoneOffsetTz()),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(_observation(), paper_only=False)

    good_row = PmiSurpriseDigestRow(
        region="us",
        source_name="ISM",
        period="2026-06",
        actual_pmi=Decimal("50.000000"),
        consensus_pmi=Decimal("50.000000"),
        prior_pmi=Decimal("50.000000"),
        surprise_pmi=Decimal("0.000000"),
        abs_surprise_pmi=Decimal("0.000000"),
        momentum_pmi=Decimal("0.000000"),
        surprise_direction="inline",
        activity_status="expansion",
        observed_at=GENERATED_AT,
    )
    kwargs = dict(
        generated_at=GENERATED_AT,
        config_version=DEFAULT_MARKET_RESEARCH_SERVICES_PMI_SURPRISE_DIGEST_CONFIG_VERSION,
        summary_status="pass",
        summary_next_step="review_services_pmi_surprises",
        observation_count=Decimal("1"),
        upside_surprise_count=Decimal("0"),
        downside_surprise_count=Decimal("0"),
        inline_surprise_count=Decimal("1"),
        expansion_count=Decimal("1"),
        contraction_count=Decimal("0"),
        average_surprise_pmi=Decimal("0.000000"),
        average_abs_surprise_pmi=Decimal("0.000000"),
        max_abs_surprise_pmi=Decimal("0.000000"),
        upside_surprise_ratio=Decimal("0.000000"),
        downside_surprise_ratio=Decimal("0.000000"),
        expansion_ratio=Decimal("1.000000"),
        rows=(good_row,),
        reason_codes=("services_pmi_surprise_digest_passed",),
    )

    assert MarketResearchServicesPmiSurpriseDigestReport(**kwargs).summary_status == "pass"
    with pytest.raises(ValueError, match="observation_count"):
        MarketResearchServicesPmiSurpriseDigestReport(
            **{**kwargs, "observation_count": Decimal("2")},
        )
    with pytest.raises(ValueError, match="summary_status"):
        MarketResearchServicesPmiSurpriseDigestReport(
            **{**kwargs, "summary_status": "watch"},
        )
    with pytest.raises(ValueError, match="rows"):
        MarketResearchServicesPmiSurpriseDigestReport(
            **{**kwargs, "rows": (replace(good_row, region=" eurozone"),)},
        )


def test_dataclasses_are_frozen() -> None:
    values = (
        MarketResearchServicesPmiSurpriseDigestConfig(),
        _observation(),
        PmiSurpriseDigestRow(
            region="us",
            source_name="ISM",
            period="2026-06",
            actual_pmi=Decimal("50.000000"),
            consensus_pmi=Decimal("50.000000"),
            prior_pmi=Decimal("50.000000"),
            surprise_pmi=Decimal("0.000000"),
            abs_surprise_pmi=Decimal("0.000000"),
            momentum_pmi=Decimal("0.000000"),
            surprise_direction="inline",
            activity_status="expansion",
            observed_at=GENERATED_AT,
        ),
        build_market_research_services_pmi_surprise_digest(
            (_observation(),),
            config=MarketResearchServicesPmiSurpriseDigestConfig(),
            generated_at=GENERATED_AT,
        ),
    )

    for value in values:
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False


def test_manual_report_construction_normalizes_rows_deterministically() -> None:
    report = build_market_research_services_pmi_surprise_digest(
        (
            _observation(
                region="z-region",
                source_name="Z Source",
                actual_pmi=Decimal("51.2"),
                consensus_pmi=Decimal("50.0"),
            ),
            _observation(
                region="a-region",
                source_name="A Source",
                actual_pmi=Decimal("52.0"),
                consensus_pmi=Decimal("50.0"),
            ),
            _observation(
                region="m-region",
                source_name="M Source",
                actual_pmi=Decimal("50.0"),
                consensus_pmi=Decimal("50.0"),
            ),
        ),
        config=MarketResearchServicesPmiSurpriseDigestConfig(),
        generated_at=GENERATED_AT,
    )

    normalized = replace(report, rows=tuple(reversed(report.rows)))

    assert normalized.rows == report.rows
    assert normalized.reason_codes == (
        "services_pmi_upside_surprise_present",
    )


def test_rejects_each_false_hard_flag_surface() -> None:
    report = build_market_research_services_pmi_surprise_digest(
        (_observation(),),
        config=MarketResearchServicesPmiSurpriseDigestConfig(),
        generated_at=GENERATED_AT,
    )
    row = report.rows[0]

    false_flag_cases = (
        lambda: MarketResearchServicesPmiSurpriseDigestConfig(paper_only=False),
        lambda: MarketResearchServicesPmiSurpriseDigestConfig(report_only=False),
        lambda: MarketResearchServicesPmiSurpriseDigestConfig(readonly=False),
        lambda: _observation(paper_only=False),
        lambda: _observation(report_only=False),
        lambda: _observation(readonly=False),
        lambda: replace(row, paper_only=False),
        lambda: replace(row, report_only=False),
        lambda: replace(row, readonly=False),
        lambda: replace(report, paper_only=False),
        lambda: replace(report, report_only=False),
        lambda: replace(report, readonly=False),
    )

    for make_value in false_flag_cases:
        with pytest.raises(ValueError, match="must be True"):
            make_value()


def test_payload_uses_six_decimal_strings_and_json_safe_values() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_services_pmi_surprise_digest",
    )
    report = build_market_research_services_pmi_surprise_digest(
        (_observation(actual_pmi=Decimal("52.3"), consensus_pmi=Decimal("50.0")),),
        config=MarketResearchServicesPmiSurpriseDigestConfig(),
        generated_at=GENERATED_AT,
    )

    payload = module.market_research_services_pmi_surprise_digest_payload(report)

    json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["observation_count"] == "1.000000"
    assert payload["average_surprise_pmi"] == "2.300000"
    assert payload["upside_surprise_ratio"] == "1.000000"
    assert payload["rows"][0]["actual_pmi"] == "52.300000"
    assert payload["rows"][0]["observed_at"] == GENERATED_AT.isoformat()

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered_key = str(key).lower()
                assert "private_key" not in lowered_key
                assert "wallet" not in lowered_key
                assert "auth" not in lowered_key
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))

    walk_payload(payload)

    for public_record in (
        MarketResearchServicesPmiSurpriseDigestConfig(),
        _observation(),
        report.rows[0],
        report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        _assert_public_numeric_fields_are_exact_six_decimal_decimals(public_record)

    with pytest.raises(ValueError, match="report"):
        module.market_research_services_pmi_surprise_digest_payload(object())


def test_module_scope_excludes_network_durable_store_and_execution_surfaces() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_services_pmi_surprise_digest",
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    forbidden_literals = (
        "api_key",
        "cancel_order",
        "connect(",
        "live",
        "trading",
        "auth",
        "wallet",
        "order",
        "place_order",
        "private_key",
        "replace_order",
        "secret",
        "submit_order",
        "token",
        "buy",
        "sell",
        "position",
        "recommend",
        "database",
        "exchange",
    )
    lowered_source = source.lower()
    assert not any(token in lowered_source for token in forbidden_literals)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "db",
        "env",
        "cli",
        "psycopg",
        "requests",
        "http",
        "socket",
        "supabase",
        "urllib",
        "pathlib",
        "sqlite",
        "sqlalchemy",
        "subprocess",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )

    forbidden_calls = {"open", "connect", "request", "urlopen", "Session"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_calls
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_calls


def _observation(**overrides: object) -> PmiSurpriseDigestObservation:
    values = {
        "region": "us",
        "source_name": "ISM",
        "period": "2026-06",
        "actual_pmi": Decimal("50.0"),
        "consensus_pmi": Decimal("50.0"),
        "prior_pmi": Decimal("50.0"),
        "observed_at": GENERATED_AT,
    }
    values.update(overrides)
    return PmiSurpriseDigestObservation(**values)


def _assert_public_numeric_fields_are_exact_six_decimal_decimals(instance: object) -> None:
    for field in fields(instance):
        value = getattr(instance, field.name)
        if field.name.endswith(("_count", "_pmi", "_ratio")):
            assert type(value) is Decimal, (field.name, value, type(value))
            assert value.as_tuple().exponent == -6, (field.name, value)
