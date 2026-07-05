from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTzInfo(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_real_personal_spending_surprise_digest",
    )


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": (
            "market-research-real-personal-spending-surprise-digest-v0"
        ),
        "min_abs_surprise": Decimal("0.003000"),
        "min_abs_surprise_ratio": Decimal("0.250000"),
        "max_source_age_seconds": Decimal("300.000000"),
        "stale_confidence_cap": Decimal("0.250000"),
        "inline_confidence_cap": Decimal("0.500000"),
    }
    values.update(overrides)
    return module.MarketResearchRealPersonalSpendingSurpriseDigestConfig(**values)


def observation(
    market_slug: str = "real-personal-spending-market",
    *,
    question: str = "Will real personal spending surprise to the upside?",
    actual_change_pct: Decimal = Decimal("0.009000"),
    consensus_change_pct: Decimal = Decimal("0.001000"),
    previous_change_pct: Decimal = Decimal("0.002000"),
    release_observed_at: datetime = GENERATED_AT - timedelta(seconds=60),
    base_confidence: Decimal = Decimal("0.900000"),
    release_reference: str = "bea/public/release",
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.RealPersonalSpendingSurpriseObservation(
        market_slug=market_slug,
        question=question,
        actual_change_pct=actual_change_pct,
        consensus_change_pct=consensus_change_pct,
        previous_change_pct=previous_change_pct,
        release_observed_at=release_observed_at,
        base_confidence=base_confidence,
        release_reference=release_reference,
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(inputs: tuple[Any, ...], *, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_market_research_real_personal_spending_surprise_digest(
        inputs,
        config=config(),
        generated_at=generated_at,
    )


def assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("public payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_no_floats(item)


def test_builds_material_surprise_digest_with_decimal_counts_utc_sorting_and_reason_codes() -> None:
    report = digest(
        (
            observation(
                "beta-inline",
                actual_change_pct=Decimal("0.002000"),
                consensus_change_pct=Decimal("0.001800"),
                upstream_reason_codes=("watchlist",),
            ),
            observation(
                "alpha-downside",
                actual_change_pct=Decimal("-0.004000"),
                consensus_change_pct=Decimal("0.002000"),
                release_observed_at=GENERATED_AT - timedelta(seconds=600),
            ),
            observation(
                "zeta-upside",
                release_observed_at=datetime(
                    2026,
                    7,
                    3,
                    7,
                    59,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                upstream_reason_codes=("bea_release", "spending_watch"),
            ),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        "market-research-real-personal-spending-surprise-digest-v0"
    )
    assert report.input_count == Decimal("3.000000")
    assert report.row_count == Decimal("3.000000")
    assert report.material_surprise_count == Decimal("2.000000")
    assert report.upside_surprise_count == Decimal("1.000000")
    assert report.downside_surprise_count == Decimal("1.000000")
    assert report.inline_count == Decimal("1.000000")
    assert report.stale_source_count == Decimal("1.000000")
    assert report.max_absolute_surprise_ratio == Decimal("8.000000")
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_real_personal_spending_surprise_screening"
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert [
        (row.market_slug, row.surprise_status, row.absolute_surprise_ratio)
        for row in report.rows
    ] == [
        ("zeta-upside", "material_surprise", Decimal("8.000000")),
        ("alpha-downside", "material_surprise", Decimal("3.000000")),
        ("beta-inline", "inline", Decimal("0.111111")),
    ]

    upside = report.rows[0]
    assert upside.release_observed_at == datetime(2026, 7, 3, 11, 59, tzinfo=UTC)
    assert upside.source_age_seconds == Decimal("60.000000")
    assert upside.surprise_delta == Decimal("0.008000")
    assert upside.surprise_ratio == Decimal("8.000000")
    assert upside.capped_confidence == Decimal("0.900000")
    assert upside.reason_codes == (
        "bea_release",
        "real_personal_spending_material_surprise",
        "source_fresh",
        "spending_watch",
        "surprise_direction_upside",
    )

    downside = report.rows[1]
    assert downside.surprise_delta == Decimal("-0.006000")
    assert downside.surprise_ratio == Decimal("-3.000000")
    assert downside.source_age_seconds == Decimal("600.000000")
    assert downside.confidence_cap == Decimal("0.250000")
    assert downside.capped_confidence == Decimal("0.250000")
    assert downside.reason_codes == (
        "real_personal_spending_material_surprise",
        "source_stale",
        "surprise_direction_downside",
    )

    assert report.reason_codes == (
        "bea_release",
        "real_personal_spending_inline",
        "real_personal_spending_material_surprise",
        "source_fresh",
        "source_stale",
        "spending_watch",
        "surprise_direction_downside",
        "surprise_direction_inline",
        "surprise_direction_upside",
        "watchlist",
    )
    assert tuple(item.reason_code for item in report.reason_code_counts) == (
        "bea_release",
        "real_personal_spending_inline",
        "real_personal_spending_material_surprise",
        "source_fresh",
        "source_stale",
        "spending_watch",
        "surprise_direction_downside",
        "surprise_direction_inline",
        "surprise_direction_upside",
        "watchlist",
    )
    assert tuple(item.count for item in report.reason_code_counts) == (
        Decimal("1.000000"),
        Decimal("1.000000"),
        Decimal("2.000000"),
        Decimal("2.000000"),
        Decimal("1.000000"),
        Decimal("1.000000"),
        Decimal("1.000000"),
        Decimal("1.000000"),
        Decimal("1.000000"),
        Decimal("1.000000"),
    )
    assert tuple(item.row_ratio for item in report.reason_code_counts) == (
        Decimal("0.333333"),
        Decimal("0.333333"),
        Decimal("0.666667"),
        Decimal("0.666667"),
        Decimal("0.333333"),
        Decimal("0.333333"),
        Decimal("0.333333"),
        Decimal("0.333333"),
        Decimal("0.333333"),
        Decimal("0.333333"),
    )


def test_empty_digest_and_payload_are_decimal_stringed_report_only_readonly() -> None:
    module = api()
    report = digest(())
    payload = module.market_research_real_personal_spending_surprise_digest_payload(
        report,
    )
    json.dumps(payload, sort_keys=True)

    assert report.input_count == Decimal("0.000000")
    assert report.row_count == Decimal("0.000000")
    assert report.material_surprise_count == Decimal("0.000000")
    assert report.max_absolute_surprise_ratio == Decimal("0.000000")
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_real_personal_spending_surprise_screening"
    )
    assert report.reason_codes == ("real_personal_spending_surprise_digest_empty",)
    assert report.reason_code_counts == (
        module.RealPersonalSpendingSurpriseReasonCodeCount(
            reason_code="real_personal_spending_surprise_digest_empty",
            count=Decimal("1.000000"),
            row_ratio=Decimal("0.000000"),
        ),
    )
    assert report.rows == ()
    assert payload["generated_at"] == "2026-07-03T12:00:00+00:00"
    assert payload["row_count"] == "0.000000"
    assert payload["max_absolute_surprise_ratio"] == "0.000000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["reason_code_counts"][0]["row_ratio"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_floats(payload)


def test_rejects_float_public_inputs_naive_datetimes_subclasses_future_rows_and_bad_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="actual_change_pct"):
        observation(actual_change_pct=Decimal("NaN"))

    with pytest.raises(ValueError, match="actual_change_pct"):
        observation(actual_change_pct=_DecimalSubclass("0.009000"))

    with pytest.raises(ValueError, match="consensus_change_pct"):
        observation(consensus_change_pct=0.001)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="min_abs_surprise"):
        config(min_abs_surprise=0.003)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="UTC-aware"):
        observation(release_observed_at=datetime(2026, 7, 3, 12, 0))

    with pytest.raises(ValueError, match="UTC-aware"):
        observation(
            release_observed_at=datetime(2026, 7, 3, 12, 0, tzinfo=_NoneOffsetTzInfo()),
        )

    with pytest.raises(ValueError, match="UTC-aware"):
        digest(
            (observation(),),
            generated_at=datetime(2026, 7, 3, 12, 0, tzinfo=_NoneOffsetTzInfo()),
        )

    with pytest.raises(ValueError, match="datetime"):
        observation(release_observed_at=_DatetimeSubclass(2026, 7, 3, tzinfo=UTC))

    with pytest.raises(ValueError, match="release_observed_at must not be after generated_at"):
        digest((observation(release_observed_at=GENERATED_AT + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="observation paper_only must be True"):
        observation(paper_only=False)

    with pytest.raises(ValueError, match="config report_only must be True"):
        config(report_only=False)

    report = digest((observation(),))
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="reason code count report_only must be True"):
        replace(report.reason_code_counts[0], report_only=False)
    with pytest.raises(FrozenInstanceError):
        report.rows = ()  # type: ignore[misc]

    classes = (
        module.MarketResearchRealPersonalSpendingSurpriseDigestConfig,
        module.RealPersonalSpendingSurpriseObservation,
        module.RealPersonalSpendingSurpriseDigestRow,
        module.RealPersonalSpendingSurpriseReasonCodeCount,
        module.RealPersonalSpendingSurpriseDigestReport,
    )
    for type_ in classes:
        assert type_.__dataclass_params__.frozen is True
        for field in fields(type_):
            public_type = str(field.type).lower()
            assert "float" not in public_type
            assert "int" not in public_type


def test_rejects_unsupported_config_reason_codes_and_unsafe_public_text() -> None:
    with pytest.raises(ValueError, match="config_version must be the supported"):
        config(config_version="real-personal-spending-surprise-digest-v1")

    with pytest.raises(ValueError, match="upstream_reason_codes"):
        observation(upstream_reason_codes=("unexpected_vendor_reason",))

    with pytest.raises(ValueError, match="upstream_reason_codes"):
        observation(upstream_reason_codes=("watchlist", "bea_release"))

    with pytest.raises(ValueError, match="market_slug must be public and redacted"):
        observation(market_slug="wallet-linked-market")

    with pytest.raises(ValueError, match="release_reference must be public and redacted"):
        observation(release_reference="private-key-feed")

    report = digest((observation(),))
    with pytest.raises(ValueError, match="reason_codes must be supported"):
        replace(report.rows[0], reason_codes=("unexpected_reason_code",))


def test_public_payload_and_dataclass_values_have_only_decimal_public_numerics() -> None:
    module = api()
    report = digest((observation(),))
    payload = module.market_research_real_personal_spending_surprise_digest_payload(
        report,
    )

    assert payload["rows"][0]["actual_change_pct"] == "0.009000"
    assert payload["rows"][0]["source_age_seconds"] == "60.000000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["reason_code_counts"][0]["row_ratio"] == "1.000000"
    assert_no_floats(payload)

    def walk_public_values(value: object) -> None:
        if is_dataclass(value) and not isinstance(value, type):
            for field in fields(value):
                walk_public_values(getattr(value, field.name))
            return
        if isinstance(value, tuple):
            for item in value:
                walk_public_values(item)
            return
        if isinstance(value, bool):
            return
        if isinstance(value, (int, float)):
            pytest.fail(f"public numeric value must be Decimal: {value!r}")

    walk_public_values(module.MarketResearchRealPersonalSpendingSurpriseDigestConfig())
    walk_public_values(observation())
    walk_public_values(report)


def test_report_only_screening_fields_are_consistent_with_rows() -> None:
    module = api()

    inline_report = digest(
        (
            observation(
                actual_change_pct=Decimal("0.002000"),
                consensus_change_pct=Decimal("0.001800"),
            ),
        ),
    )

    assert inline_report.digest_status == "pass"
    assert inline_report.recommended_next_step == (
        "allow_report_only_real_personal_spending_surprise_screening"
    )

    material_report = digest((observation(),))
    assert material_report.digest_status == "watch"
    assert material_report.recommended_next_step == (
        "monitor_report_only_real_personal_spending_surprise_screening"
    )

    with pytest.raises(ValueError, match="digest_status must match rows"):
        replace(material_report, digest_status="pass")
    with pytest.raises(ValueError, match="recommended_next_step must match digest_status"):
        replace(material_report, recommended_next_step="allow_report_only_screening")
    with pytest.raises(ValueError, match="reason_code_counts must match reason_codes"):
        replace(
            material_report,
            reason_code_counts=(
                module.RealPersonalSpendingSurpriseReasonCodeCount(
                    reason_code="real_personal_spending_material_surprise",
                    count=Decimal("999.000000"),
                    row_ratio=Decimal("1.000000"),
                ),
            ),
        )


def test_rows_and_reason_codes_are_stable_across_input_order() -> None:
    first = observation(
        "beta-inline",
        actual_change_pct=Decimal("0.002000"),
        consensus_change_pct=Decimal("0.001800"),
        upstream_reason_codes=("watchlist",),
    )
    second = observation(
        "alpha-downside",
        actual_change_pct=Decimal("-0.004000"),
        consensus_change_pct=Decimal("0.002000"),
        release_observed_at=GENERATED_AT - timedelta(seconds=600),
    )
    third = observation(
        "zeta-upside",
        upstream_reason_codes=("bea_release", "spending_watch"),
    )

    forward = digest((first, second, third))
    reverse = digest((third, second, first))

    assert forward == reverse
    assert tuple(row.market_slug for row in forward.rows) == (
        "zeta-upside",
        "alpha-downside",
        "beta-inline",
    )
    assert forward.reason_codes == reverse.reason_codes

    with pytest.raises(ValueError, match="reason_codes"):
        replace(forward.rows[0], reason_codes=tuple(reversed(forward.rows[0].reason_codes)))
    with pytest.raises(ValueError, match="rows"):
        replace(forward, rows=tuple(reversed(forward.rows)))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(forward, reason_code_counts=tuple(reversed(forward.reason_code_counts)))
    with pytest.raises(ValueError, match="input_count"):
        replace(forward, input_count=Decimal("1.500000"))
    with pytest.raises(ValueError, match="count"):
        replace(forward.reason_code_counts[0], count=Decimal("1.500000"))


def test_module_scope_is_pure_in_memory_without_network_storage_or_trading_actions() -> None:
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
        "place_order",
        "cancel_order",
        "replace_order",
        "auth",
        "authentication",
        "api_key",
        "private_key",
        "live trading",
    ):
        assert forbidden not in source

    source_text = Path(
        "src/polymarket_alpha_lab"
        "/market_research_real_personal_spending_surprise_digest.py",
    ).read_text()
    tree = ast.parse(source_text)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            function_name = ""
            if isinstance(node.func, ast.Name):
                function_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                function_name = node.func.attr
            assert function_name not in {
                "open",
                "connect",
                "execute",
                "request",
                "urlopen",
                "trade",
                "submit",
                "cancel",
                "sign",
            }
    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "pathlib",
        "sqlite3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
