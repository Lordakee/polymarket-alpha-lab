import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest
import polymarket_alpha_lab.market_research_personal_income_surprise_digest as digest_api

from polymarket_alpha_lab.market_research_personal_income_surprise_digest import (
    DEFAULT_PERSONAL_INCOME_SURPRISE_DIGEST_CONFIG_VERSION,
    DEFAULT_PERSONAL_INCOME_SURPRISE_DIGEST_MAX_ROWS,
    DEFAULT_PERSONAL_INCOME_SURPRISE_DIGEST_MIN_ABS_SURPRISE_RATIO,
    MarketResearchPersonalIncomeSurpriseDigestConfig,
    MarketResearchPersonalIncomeSurpriseDigestInputRow,
    MarketResearchPersonalIncomeSurpriseDigestReport,
    build_market_research_personal_income_surprise_digest,
    build_market_research_personal_income_surprise_digest_report,
)


GENERATED_AT = datetime(2026, 6, 26, 13, 0, tzinfo=UTC)


def _config(
    *,
    max_rows: Decimal = Decimal("4.000000"),
    min_abs_surprise_ratio: Decimal = Decimal("0.010000"),
) -> MarketResearchPersonalIncomeSurpriseDigestConfig:
    return MarketResearchPersonalIncomeSurpriseDigestConfig(
        config_version="market-research-personal-income-surprise-digest-v0",
        max_rows=max_rows,
        min_abs_surprise_ratio=min_abs_surprise_ratio,
    )


def _row(
    market_slug: str,
    *,
    question: str | None = None,
    category: str = "personal_income",
    event_date: datetime = datetime(2026, 6, 26, 8, 30, tzinfo=UTC),
    actual_value: Decimal = Decimal("0.500000"),
    consensus_value: Decimal = Decimal("0.300000"),
    prior_value: Decimal = Decimal("0.200000"),
    probability: Decimal = Decimal("0.550000"),
    liquidity: Decimal = Decimal("1200.000000"),
    reason_codes: tuple[str, ...] = ("fresh_release",),
) -> MarketResearchPersonalIncomeSurpriseDigestInputRow:
    return MarketResearchPersonalIncomeSurpriseDigestInputRow(
        market_slug=market_slug,
        question=question or f"Will {market_slug} settle yes?",
        category=category,
        event_date=event_date,
        actual_value=actual_value,
        consensus_value=consensus_value,
        prior_value=prior_value,
        probability=probability,
        liquidity=liquidity,
        reason_codes=reason_codes,
    )


class _NullOffsetTZ(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


class _DecimalSubclass(Decimal):
    pass


def _assert_decimal_only_public_numerics(value: object, path: str = "value") -> None:
    if isinstance(value, bool):
        return
    if type(value) is Decimal:
        return
    assert type(value) is not int, path
    assert type(value) is not float, path
    if is_dataclass(value) and not isinstance(value, type):
        assert value.__dataclass_params__.frozen
        for field in fields(value):
            _assert_decimal_only_public_numerics(
                getattr(value, field.name),
                f"{path}.{field.name}",
            )
    elif isinstance(value, tuple):
        for index, item in enumerate(value):
            _assert_decimal_only_public_numerics(item, f"{path}[{index}]")


def test_personal_income_surprise_digest_config_defaults_match_exported_constants():
    import polymarket_alpha_lab.market_research_personal_income_surprise_digest as digest

    assert {
        "DEFAULT_PERSONAL_INCOME_SURPRISE_DIGEST_CONFIG_VERSION",
        "DEFAULT_PERSONAL_INCOME_SURPRISE_DIGEST_MAX_ROWS",
        "DEFAULT_PERSONAL_INCOME_SURPRISE_DIGEST_MIN_ABS_SURPRISE_RATIO",
        "MarketResearchPersonalIncomeSurpriseReasonCodeCount",
        "market_research_personal_income_surprise_digest_payload",
    } <= set(digest.__all__)
    assert (
        DEFAULT_PERSONAL_INCOME_SURPRISE_DIGEST_CONFIG_VERSION
        == "market-research-personal-income-surprise-digest-v0"
    )
    assert DEFAULT_PERSONAL_INCOME_SURPRISE_DIGEST_MAX_ROWS == Decimal("25.000000")
    assert (
        DEFAULT_PERSONAL_INCOME_SURPRISE_DIGEST_MIN_ABS_SURPRISE_RATIO
        == Decimal("0.010000")
    )

    field_defaults = {
        field.name: field.default
        for field in fields(MarketResearchPersonalIncomeSurpriseDigestConfig)
    }
    assert (
        field_defaults["config_version"]
        == DEFAULT_PERSONAL_INCOME_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert field_defaults["max_rows"] == DEFAULT_PERSONAL_INCOME_SURPRISE_DIGEST_MAX_ROWS
    assert (
        field_defaults["min_abs_surprise_ratio"]
        == DEFAULT_PERSONAL_INCOME_SURPRISE_DIGEST_MIN_ABS_SURPRISE_RATIO
    )
    assert field_defaults["paper_only"] is True
    assert field_defaults["report_only"] is True
    assert field_defaults["readonly"] is True

    config = MarketResearchPersonalIncomeSurpriseDigestConfig()
    assert config.config_version == DEFAULT_PERSONAL_INCOME_SURPRISE_DIGEST_CONFIG_VERSION
    assert config.max_rows == Decimal("25.000000")
    assert (
        config.min_abs_surprise_ratio
        == DEFAULT_PERSONAL_INCOME_SURPRISE_DIGEST_MIN_ABS_SURPRISE_RATIO
    )
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True


def test_personal_income_surprise_digest_orders_rows_and_counts_deterministically():
    generated_at = datetime(2026, 6, 26, 9, 0, tzinfo=timezone(timedelta(hours=-4)))
    rows = (
        _row(
            "low-surprise",
            actual_value=Decimal("0.306000"),
            consensus_value=Decimal("0.300000"),
            probability=Decimal("0.520000"),
            liquidity=Decimal("500.000000"),
            reason_codes=("minor_beat",),
        ),
        _row(
            "large-miss",
            actual_value=Decimal("-0.200000"),
            consensus_value=Decimal("0.300000"),
            probability=Decimal("0.470000"),
            liquidity=Decimal("1800.000000"),
            reason_codes=("income_miss", "risk_off"),
        ),
        _row(
            "large-beat-low-liquidity",
            actual_value=Decimal("0.900000"),
            consensus_value=Decimal("0.300000"),
            probability=Decimal("0.610000"),
            liquidity=Decimal("200.000000"),
            reason_codes=("income_beat",),
        ),
        _row(
            "large-beat",
            actual_value=Decimal("0.900000"),
            consensus_value=Decimal("0.300000"),
            probability=Decimal("0.620000"),
            liquidity=Decimal("2400.000000"),
            reason_codes=("income_beat", "demand_signal"),
        ),
        _row(
            "inline",
            actual_value=Decimal("0.302000"),
            consensus_value=Decimal("0.300000"),
            probability=Decimal("0.500000"),
            liquidity=Decimal("2000.000000"),
            reason_codes=("inline_release",),
        ),
    )

    report = build_market_research_personal_income_surprise_digest_report(
        rows,
        config=_config(
            max_rows=Decimal("4.000000"),
            min_abs_surprise_ratio=Decimal("0.010000"),
        ),
        generated_at=generated_at,
    )

    assert isinstance(report, MarketResearchPersonalIncomeSurpriseDigestReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "market-research-personal-income-surprise-digest-v0"
    assert report.input_row_count == Decimal("5.000000")
    assert report.digest_row_count == Decimal("4.000000")
    assert report.included_count == Decimal("3.000000")
    assert report.skipped_count == Decimal("1.000000")
    assert report.positive_surprise_count == Decimal("2.000000")
    assert report.negative_surprise_count == Decimal("1.000000")
    assert report.neutral_surprise_count == Decimal("1.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.market_slug for row in report.digest_rows) == (
        "large-beat",
        "large-miss",
        "large-beat-low-liquidity",
        "low-surprise",
    )
    assert tuple(row.digest_rank for row in report.digest_rows) == (
        Decimal("1"),
        Decimal("2"),
        Decimal("3"),
        Decimal("4"),
    )
    assert tuple(row.surprise_direction for row in report.digest_rows) == (
        "positive",
        "negative",
        "positive",
        "neutral",
    )
    assert tuple(row.reason_codes for row in report.digest_rows) == (
        ("demand_signal", "high_liquidity", "income_beat", "large_surprise"),
        ("high_liquidity", "income_miss", "large_surprise", "risk_off"),
        ("income_beat", "large_surprise", "low_liquidity"),
        ("low_liquidity", "minor_beat", "small_surprise"),
    )
    assert report.digest_rows[0].surprise == Decimal("0.600000")
    assert report.digest_rows[0].surprise_ratio == Decimal("2.000000")
    assert report.digest_rows[1].surprise == Decimal("-0.500000")
    assert report.digest_rows[1].surprise_ratio == Decimal("-1.666667")
    assert report.reason_codes == (
        "personal_income_surprise_positive_present",
        "personal_income_surprise_negative_present",
        "personal_income_surprise_neutral_present",
        "personal_income_surprise_large_present",
        "personal_income_surprise_low_liquidity_present",
    )
    assert tuple(item.reason_code for item in report.reason_code_counts) == report.reason_codes
    assert tuple(item.count for item in report.reason_code_counts) == (
        Decimal("2.000000"),
        Decimal("1.000000"),
        Decimal("1.000000"),
        Decimal("3.000000"),
        Decimal("2.000000"),
    )
    assert tuple(item.row_ratio for item in report.reason_code_counts) == (
        Decimal("0.500000"),
        Decimal("0.250000"),
        Decimal("0.250000"),
        Decimal("0.750000"),
        Decimal("0.500000"),
    )


def test_personal_income_surprise_digest_empty_report_is_report_only_blocked() -> None:
    report = build_market_research_personal_income_surprise_digest_report(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.input_row_count == Decimal("0.000000")
    assert report.digest_row_count == Decimal("0.000000")
    assert report.included_count == Decimal("0.000000")
    assert report.skipped_count == Decimal("0.000000")
    assert report.reason_codes == ("personal_income_surprise_digest_empty",)
    assert report.reason_code_counts == (
        digest_api.MarketResearchPersonalIncomeSurpriseReasonCodeCount(
            reason_code="personal_income_surprise_digest_empty",
            count=Decimal("1.000000"),
            row_ratio=Decimal("0.000000"),
        ),
    )
    assert report.digest_rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_personal_income_surprise_digest_alias_matches_report_builder():
    row = _row("alias-row")
    config = _config()

    assert build_market_research_personal_income_surprise_digest(
        (row,),
        config=config,
        generated_at=GENERATED_AT,
    ) == build_market_research_personal_income_surprise_digest_report(
        (row,),
        config=config,
        generated_at=GENERATED_AT,
    )


def test_personal_income_surprise_digest_dataclasses_are_frozen_and_decimal_only():
    row = _row(
        "frozen-row",
        reason_codes=("zeta_source", "alpha_source", "zeta_source"),
    )
    config = _config()

    with pytest.raises(FrozenInstanceError):
        row.market_slug = "changed"
    with pytest.raises(FrozenInstanceError):
        config.max_rows = Decimal("10.000000")
    with pytest.raises(ValueError, match="max_rows must be a Decimal"):
        MarketResearchPersonalIncomeSurpriseDigestConfig(max_rows=25)
    with pytest.raises(ValueError, match="actual_value must be a Decimal"):
        _row("float-actual", actual_value=0.5)
    with pytest.raises(ValueError, match="actual_value must be a Decimal"):
        _row("subclass-actual", actual_value=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="input_row_count must be a Decimal"):
        MarketResearchPersonalIncomeSurpriseDigestReport(
            generated_at=GENERATED_AT,
            config_version="market-research-personal-income-surprise-digest-v0",
            input_row_count=1,
            digest_row_count=Decimal("0"),
            included_count=Decimal("0"),
            skipped_count=Decimal("0"),
            positive_surprise_count=Decimal("0"),
            negative_surprise_count=Decimal("0"),
            neutral_surprise_count=Decimal("0"),
            reason_code_counts=(),
            reason_codes=("personal_income_surprise_digest_empty",),
            digest_rows=(),
        )

    report = build_market_research_personal_income_surprise_digest_report(
        (row,),
        config=config,
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        report.digest_rows[0].surprise_direction = "negative"
    _assert_decimal_only_public_numerics(config, "config")
    _assert_decimal_only_public_numerics(row, "row")
    _assert_decimal_only_public_numerics(report, "report")
    assert row.reason_codes == ("alpha_source", "zeta_source")
    assert report.digest_rows[0].actual_value == Decimal("0.500000")
    assert report.digest_rows[0].surprise_ratio == Decimal("0.666667")


def test_personal_income_surprise_digest_normalizes_utc_and_rejects_unsafe_surfaces():
    report = build_market_research_personal_income_surprise_digest_report(
        (
            _row(
                "utc-row",
                event_date=datetime(
                    2026,
                    6,
                    26,
                    8,
                    30,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
            ),
        ),
        config=_config(),
        generated_at=datetime(2026, 6, 26, 9, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert report.generated_at == datetime(2026, 6, 26, 13, 0, tzinfo=UTC)
    assert report.digest_rows[0].event_date == datetime(2026, 6, 26, 12, 30, tzinfo=UTC)

    with pytest.raises(ValueError, match="event_date must be timezone-aware"):
        _row("naive-event", event_date=datetime(2026, 6, 26, 8, 30))
    with pytest.raises(ValueError, match="event_date must be timezone-aware"):
        _row(
            "null-offset-event",
            event_date=datetime(2026, 6, 26, 8, 30, tzinfo=_NullOffsetTZ()),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_market_research_personal_income_surprise_digest_report(
            (),
            config=_config(),
            generated_at=datetime(2026, 6, 26, 9, 0),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_market_research_personal_income_surprise_digest_report(
            (),
            config=_config(),
            generated_at=datetime(2026, 6, 26, 9, 0, tzinfo=_NullOffsetTZ()),
        )

    for kwargs in (
        {"paper_only": False},
        {"report_only": False},
        {"readonly": False},
    ):
        with pytest.raises(ValueError, match="must be True"):
            MarketResearchPersonalIncomeSurpriseDigestConfig(**kwargs)

    with pytest.raises(ValueError, match="consensus_value cannot be zero"):
        _row("zero-consensus", consensus_value=Decimal("0.000000"))

    digest_row = report.digest_rows[0]
    with pytest.raises(ValueError, match="digest row report_only must be True"):
        replace(digest_row, report_only=False)
    with pytest.raises(ValueError, match="digest report readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="reason code count paper_only must be True"):
        replace(report.reason_code_counts[0], paper_only=False)


def test_personal_income_surprise_digest_payload_uses_six_decimal_strings() -> None:
    report = build_market_research_personal_income_surprise_digest_report(
        (_row("payload-row"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    payload = digest_api.market_research_personal_income_surprise_digest_payload(report)

    assert payload["generated_at"] == "2026-06-26T13:00:00+00:00"
    assert payload["input_row_count"] == "1.000000"
    assert payload["digest_row_count"] == "1.000000"
    assert payload["included_count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["digest_rows"][0]["digest_rank"] == "1.000000"
    assert payload["digest_rows"][0]["actual_value"] == "0.500000"
    assert payload["digest_rows"][0]["surprise_ratio"] == "0.666667"
    assert payload["digest_rows"][0]["event_date"] == "2026-06-26T08:30:00+00:00"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["reason_code_counts"][0]["row_ratio"] == "1.000000"

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                assert "private_key" not in lowered
                assert "wallet" not in lowered
                assert "auth" not in lowered
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))
            if not isinstance(value, bool):
                assert not isinstance(value, int)

    walk_payload(payload)

    with pytest.raises(
        ValueError,
        match="report must be exactly MarketResearchPersonalIncomeSurpriseDigestReport",
    ):
        digest_api.market_research_personal_income_surprise_digest_payload(object())


def test_personal_income_surprise_digest_report_rejects_inconsistent_manual_rows():
    digest_row = build_market_research_personal_income_surprise_digest_report(
        (_row("consistent"),),
        config=_config(),
        generated_at=GENERATED_AT,
    ).digest_rows[0]

    with pytest.raises(ValueError, match="digest_row_count must match digest_rows"):
        MarketResearchPersonalIncomeSurpriseDigestReport(
            generated_at=GENERATED_AT,
            config_version="market-research-personal-income-surprise-digest-v0",
            input_row_count=Decimal("1"),
            digest_row_count=Decimal("2"),
            included_count=Decimal("1"),
            skipped_count=Decimal("0"),
            positive_surprise_count=Decimal("1"),
            negative_surprise_count=Decimal("0"),
            neutral_surprise_count=Decimal("0"),
            reason_code_counts=(),
            reason_codes=("personal_income_surprise_positive_present",),
            digest_rows=(digest_row,),
        )

    with pytest.raises(ValueError, match="digest_rows must use deterministic ordering"):
        MarketResearchPersonalIncomeSurpriseDigestReport(
            generated_at=GENERATED_AT,
            config_version="market-research-personal-income-surprise-digest-v0",
            input_row_count=Decimal("2"),
            digest_row_count=Decimal("2"),
            included_count=Decimal("2"),
            skipped_count=Decimal("0"),
            positive_surprise_count=Decimal("2"),
            negative_surprise_count=Decimal("0"),
            neutral_surprise_count=Decimal("0"),
            reason_code_counts=(
                digest_api.MarketResearchPersonalIncomeSurpriseReasonCodeCount(
                    reason_code="personal_income_surprise_positive_present",
                    count=Decimal("2.000000"),
                    row_ratio=Decimal("1.000000"),
                ),
            ),
            reason_codes=("personal_income_surprise_positive_present",),
            digest_rows=(
                digest_row,
                digest_row,
            ),
        )

    with pytest.raises(ValueError, match="reason_codes must match digest_rows"):
        MarketResearchPersonalIncomeSurpriseDigestReport(
            generated_at=GENERATED_AT,
            config_version="market-research-personal-income-surprise-digest-v0",
            input_row_count=Decimal("1"),
            digest_row_count=Decimal("1"),
            included_count=Decimal("1"),
            skipped_count=Decimal("0"),
            positive_surprise_count=Decimal("1"),
            negative_surprise_count=Decimal("0"),
            neutral_surprise_count=Decimal("0"),
            reason_code_counts=(
                digest_api.MarketResearchPersonalIncomeSurpriseReasonCodeCount(
                    reason_code="personal_income_surprise_negative_present",
                    count=Decimal("1.000000"),
                    row_ratio=Decimal("1.000000"),
                ),
            ),
            reason_codes=("personal_income_surprise_negative_present",),
            digest_rows=(digest_row,),
        )


def test_personal_income_surprise_digest_module_has_no_io_or_live_surfaces() -> None:
    source_path = Path(
        "src/polymarket_alpha_lab/market_research_personal_income_surprise_digest.py",
    )
    source = source_path.read_text()
    tree = ast.parse(source)
    imported_modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            assert call_name not in {
                "open",
                "Path",
                "read_text",
                "write_text",
                "connect",
                "execute",
                "urlopen",
                "request",
            }

    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "sqlite",
        "psycopg",
        "supabase",
        "sqlalchemy",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "private_key",
        "api_key",
        "secret",
        "wallet",
        "auth",
        "urlopen",
        "connect(",
        "execute(",
        "live trading",
        "submit_order",
        "cancel_order",
        "replace_order",
        "create_order",
        "exchange mutation",
    ):
        assert forbidden not in source.lower()


def _call_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""
