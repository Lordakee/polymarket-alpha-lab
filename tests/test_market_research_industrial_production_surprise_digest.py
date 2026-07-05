import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timezone, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab import (
    market_research_industrial_production_surprise_digest as industrial_digest,
)
from polymarket_alpha_lab.market_research_industrial_production_surprise_digest import (
    IndustrialProductionSurpriseDigestConfig,
    IndustrialProductionSurpriseInput,
    IndustrialProductionSurpriseReasonCodeCount,
    IndustrialProductionSurpriseRow,
    build_market_research_industrial_production_surprise_digest,
)


def _release(
    *,
    market_id: str = "ip-growth-dec",
    release_at: datetime = datetime(2026, 1, 15, 8, 30, tzinfo=timezone(timedelta(hours=-5))),
    actual_index_level: Decimal | str = "104.2",
    consensus_index_level: Decimal | str = "103.7",
    previous_index_level: Decimal | str = "103.0",
    market_probability: Decimal | str = "0.61",
    threshold_probability: Decimal | str = "0.50",
    source_count: Decimal | str = "3",
) -> IndustrialProductionSurpriseInput:
    return IndustrialProductionSurpriseInput(
        market_id=market_id,
        release_at=release_at,
        actual_index_level=Decimal(actual_index_level),
        consensus_index_level=Decimal(consensus_index_level),
        previous_index_level=Decimal(previous_index_level),
        market_probability=Decimal(market_probability),
        threshold_probability=Decimal(threshold_probability),
        source_count=Decimal(source_count),
    )


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


class _DecimalSubclass(Decimal):
    pass


def _contains_float(value: object) -> bool:
    if type(value) is float:
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, list | tuple):
        return any(_contains_float(item) for item in value)
    return False


def _assert_decimal_only_public_numerics(value: object, path: str = "value") -> None:
    if isinstance(value, bool):
        return
    if type(value) is Decimal:
        return
    assert type(value) is not float, path
    assert type(value) is not int, path
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


def _call_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def test_digest_sorts_inputs_and_emits_deterministic_surprise_rows_reason_codes_and_ratios(
) -> None:
    inputs = (
        _release(
            market_id="ip-negative",
            release_at=datetime(2026, 3, 17, 12, 30, tzinfo=UTC),
            actual_index_level="98.8",
            consensus_index_level="99.3",
            previous_index_level="100.0",
            market_probability="0.41",
            threshold_probability="0.50",
            source_count="2",
        ),
        _release(market_id="ip-positive"),
        _release(
            market_id="ip-inline",
            release_at=datetime(2026, 2, 16, 13, 30, tzinfo=UTC),
            actual_index_level="105.0",
            consensus_index_level="105.0",
            previous_index_level="104.5",
            market_probability="0.50",
            threshold_probability="0.50",
            source_count="1",
        ),
    )
    report = build_market_research_industrial_production_surprise_digest(
        inputs,
        config=IndustrialProductionSurpriseDigestConfig(
            config_version="industrial-production-surprise-v1",
        ),
        generated_at=datetime(2026, 4, 1, 9, 0, tzinfo=timezone(timedelta(hours=2))),
    )
    reverse_report = build_market_research_industrial_production_surprise_digest(
        tuple(reversed(inputs)),
        config=IndustrialProductionSurpriseDigestConfig(
            config_version="industrial-production-surprise-v1",
        ),
        generated_at=datetime(2026, 4, 1, 9, 0, tzinfo=timezone(timedelta(hours=2))),
    )

    assert report == reverse_report
    assert report.generated_at == datetime(2026, 4, 1, 7, 0, tzinfo=UTC)
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "industrial-production-surprise-v1"
    assert report.digest_status == "watch"
    assert report.recommended_next_step == "review_industrial_production_surprise_markets"
    assert report.input_count == Decimal("3")
    assert report.positive_surprise_count == Decimal("1")
    assert report.negative_surprise_count == Decimal("1")
    assert report.inline_count == Decimal("1")
    assert report.total_source_count == Decimal("6")
    assert report.positive_surprise_ratio == Decimal("0.333333")
    assert report.negative_surprise_ratio == Decimal("0.333333")
    assert report.market_probability_edge_ratio == Decimal("0.333333")
    assert report.largest_abs_surprise_market_id == "ip-negative"
    assert report.largest_abs_surprise_ratio == Decimal("0.005000")
    assert report.reason_codes == (
        "industrial_production_surprise_negative_present",
        "industrial_production_surprise_positive_present",
        "industrial_production_surprise_probability_edge_present",
    )
    assert report.reason_code_counts == (
        IndustrialProductionSurpriseReasonCodeCount(
            reason_code="industrial_production_surprise_negative_present",
            count=Decimal("1.000000"),
            input_ratio=Decimal("0.333333"),
        ),
        IndustrialProductionSurpriseReasonCodeCount(
            reason_code="industrial_production_surprise_positive_present",
            count=Decimal("1.000000"),
            input_ratio=Decimal("0.333333"),
        ),
        IndustrialProductionSurpriseReasonCodeCount(
            reason_code="industrial_production_surprise_probability_edge_present",
            count=Decimal("1.000000"),
            input_ratio=Decimal("0.333333"),
        ),
    )
    assert tuple(row.market_id for row in report.surprise_rows) == (
        "ip-positive",
        "ip-inline",
        "ip-negative",
    )
    assert report.surprise_rows[0].release_at == datetime(2026, 1, 15, 13, 30, tzinfo=UTC)
    assert report.surprise_rows[0].surprise_index_points == Decimal("0.5")
    assert report.surprise_rows[0].surprise_ratio == Decimal("0.004821")
    assert report.surprise_rows[0].market_probability_edge == Decimal("0.11")
    assert report.surprise_rows[0].surprise_direction == "positive"
    assert report.surprise_rows[1].surprise_direction == "inline"
    assert report.surprise_rows[2].surprise_direction == "negative"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert not any(
        hasattr(report, unsafe_name)
        for unsafe_name in ("auth", "wallet", "order", "private_key", "account", "persisted")
    )


def test_public_dataclasses_are_frozen_and_expose_only_decimal_public_numerics() -> None:
    first_input = _release(
        market_id="ip-positive",
        actual_index_level="104.200000",
        consensus_index_level="103.700000",
    )
    second_input = _release(
        market_id="ip-negative",
        release_at=datetime(2026, 2, 16, 13, 30, tzinfo=UTC),
        actual_index_level="98.800000",
        consensus_index_level="99.300000",
    )
    report = build_market_research_industrial_production_surprise_digest(
        (first_input, second_input),
        config=IndustrialProductionSurpriseDigestConfig(),
        generated_at=datetime(2026, 4, 1, 9, 0, tzinfo=UTC),
    )

    for public_record in (
        IndustrialProductionSurpriseDigestConfig(),
        first_input,
        report.surprise_rows[0],
        report.reason_code_counts[0],
        report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        _assert_decimal_only_public_numerics(public_record)


def test_row_and_report_consistency_guards_reject_tampered_public_records() -> None:
    report = build_market_research_industrial_production_surprise_digest(
        (_release(),),
        config=IndustrialProductionSurpriseDigestConfig(),
        generated_at=datetime(2026, 4, 1, 9, 0, tzinfo=UTC),
    )
    row = report.surprise_rows[0]

    with pytest.raises(ValueError, match="surprise_index_points must match"):
        replace(row, surprise_index_points=Decimal("999.000000"))
    with pytest.raises(ValueError, match="surprise_ratio must match"):
        replace(row, surprise_ratio=Decimal("0.990000"))
    with pytest.raises(ValueError, match="market_probability_edge must match"):
        replace(row, market_probability_edge=Decimal("0.990000"))
    with pytest.raises(ValueError, match="surprise_direction must match"):
        replace(row, surprise_direction="negative")

    with pytest.raises(ValueError, match="surprise_rows must be sorted"):
        replace(
            report,
            surprise_rows=(
                IndustrialProductionSurpriseRow(
                    market_id="later",
                    release_at=datetime(2026, 4, 2, 9, 0, tzinfo=UTC),
                    actual_index_level=Decimal("104.000000"),
                    consensus_index_level=Decimal("103.000000"),
                    previous_index_level=Decimal("102.000000"),
                    market_probability=Decimal("0.600000"),
                    threshold_probability=Decimal("0.500000"),
                    source_count=Decimal("1.000000"),
                    surprise_direction="positive",
                    surprise_index_points=Decimal("1.000000"),
                    surprise_ratio=Decimal("0.009708"),
                    market_probability_edge=Decimal("0.100000"),
                ),
                row,
            ),
        )
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(report, reason_codes=("industrial_production_surprise_no_surprises",))
    with pytest.raises(ValueError, match="reason_code_counts must match"):
        replace(report, reason_code_counts=())
    with pytest.raises(ValueError, match="reason_code_counts must use canonical sequence"):
        replace(report, reason_code_counts=tuple(reversed(report.reason_code_counts)))
    with pytest.raises(ValueError, match="reason_code_counts must be unique"):
        replace(
            report,
            reason_code_counts=report.reason_code_counts + (report.reason_code_counts[0],),
        )
    with pytest.raises(ValueError, match="digest_status must match"):
        replace(report, digest_status="pass")
    with pytest.raises(ValueError, match="recommended_next_step must match"):
        replace(report, recommended_next_step="continue_industrial_production_surprise_monitoring")
    with pytest.raises(ValueError, match="config_version"):
        replace(report, config_version="unsupported")


def test_empty_digest_is_blocked_with_decimal_zero_counts_no_ratios_and_empty_reason() -> None:
    report = build_market_research_industrial_production_surprise_digest(
        (),
        config=IndustrialProductionSurpriseDigestConfig(),
        generated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == "collect_industrial_production_surprise_inputs"
    assert report.input_count == Decimal("0")
    assert report.positive_surprise_count == Decimal("0")
    assert report.negative_surprise_count == Decimal("0")
    assert report.inline_count == Decimal("0")
    assert report.total_source_count == Decimal("0")
    assert report.positive_surprise_ratio is None
    assert report.negative_surprise_ratio is None
    assert report.market_probability_edge_ratio is None
    assert report.largest_abs_surprise_market_id is None
    assert report.largest_abs_surprise_ratio is None
    assert report.surprise_rows == ()
    assert report.reason_code_counts == (
        IndustrialProductionSurpriseReasonCodeCount(
            reason_code="industrial_production_surprise_digest_empty",
            count=Decimal("1.000000"),
            input_ratio=Decimal("0.000000"),
        ),
    )
    assert report.reason_codes == ("industrial_production_surprise_digest_empty",)


def test_payload_serializes_decimal_public_numbers_as_six_place_strings_without_live_surface(
) -> None:
    report = build_market_research_industrial_production_surprise_digest(
        [_release()],
        config=IndustrialProductionSurpriseDigestConfig(),
        generated_at=datetime(2026, 1, 16, 11, 0, tzinfo=timezone(timedelta(hours=1))),
    )

    assert hasattr(
        industrial_digest,
        "market_research_industrial_production_surprise_digest_payload",
    )
    payload = industrial_digest.market_research_industrial_production_surprise_digest_payload(
        report,
    )

    assert payload["generated_at"] == "2026-01-16T10:00:00+00:00"
    assert payload["input_count"] == "1.000000"
    assert payload["positive_surprise_count"] == "1.000000"
    assert payload["negative_surprise_count"] == "0.000000"
    assert payload["inline_count"] == "0.000000"
    assert payload["total_source_count"] == "3.000000"
    assert payload["positive_surprise_ratio"] == "1.000000"
    assert payload["negative_surprise_ratio"] == "0.000000"
    assert payload["market_probability_edge_ratio"] == "1.000000"
    assert payload["largest_abs_surprise_ratio"] == "0.004854"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["reason_code_counts"][0]["input_ratio"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    row = payload["surprise_rows"][0]
    assert row["release_at"] == "2026-01-15T13:30:00+00:00"
    assert row["actual_index_level"] == "104.200000"
    assert row["consensus_index_level"] == "103.700000"
    assert row["previous_index_level"] == "103.000000"
    assert row["market_probability"] == "0.610000"
    assert row["threshold_probability"] == "0.500000"
    assert row["source_count"] == "3.000000"
    assert row["surprise_index_points"] == "0.500000"
    assert row["surprise_ratio"] == "0.004821"
    assert row["market_probability_edge"] == "0.110000"
    assert _contains_float(payload) is False
    serialized = repr(payload).lower()
    assert not any(
        token in serialized
        for token in ("auth", "wallet", "order", "private_key", "cancel", "replace", "exchange")
    )


def test_inputs_config_rows_and_report_are_frozen_and_reject_non_decimal_public_numbers() -> None:
    item = _release()
    with pytest.raises(FrozenInstanceError):
        item.market_id = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="actual_index_level must be a Decimal"):
        IndustrialProductionSurpriseInput(
            market_id="bad",
            release_at=datetime(2026, 1, 1, tzinfo=UTC),
            actual_index_level=104,  # type: ignore[arg-type]
            consensus_index_level=Decimal("103"),
            previous_index_level=Decimal("102"),
            market_probability=Decimal("0.5"),
            threshold_probability=Decimal("0.5"),
            source_count=Decimal("1"),
        )
    with pytest.raises(ValueError, match="actual_index_level must be a Decimal"):
        IndustrialProductionSurpriseInput(
            market_id="bad-decimal-subclass",
            release_at=datetime(2026, 1, 1, tzinfo=UTC),
            actual_index_level=_DecimalSubclass("104.000000"),
            consensus_index_level=Decimal("103.000000"),
            previous_index_level=Decimal("102.000000"),
            market_probability=Decimal("0.500000"),
            threshold_probability=Decimal("0.500000"),
            source_count=Decimal("1.000000"),
        )

    with pytest.raises(ValueError, match="source_count must be an integral Decimal"):
        _release(source_count="1.5")

    with pytest.raises(
        ValueError,
        match="config must be an IndustrialProductionSurpriseDigestConfig",
    ):
        build_market_research_industrial_production_surprise_digest(
            [item],
            config=object(),  # type: ignore[arg-type]
            generated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="config_version"):
        IndustrialProductionSurpriseDigestConfig(config_version="unsupported")

    report = build_market_research_industrial_production_surprise_digest(
        [item],
        config=IndustrialProductionSurpriseDigestConfig(),
        generated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    with pytest.raises(FrozenInstanceError):
        report.digest_status = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.surprise_rows[0].market_id = "changed"  # type: ignore[misc]
    assert type(report.input_count) is Decimal
    assert type(report.surprise_rows[0].source_count) is Decimal


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_public_dataclasses_reject_false_hard_flags(flag_name: str) -> None:
    false_flag = {flag_name: False}
    item = _release()
    report = build_market_research_industrial_production_surprise_digest(
        [item],
        config=IndustrialProductionSurpriseDigestConfig(),
        generated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    row = report.surprise_rows[0]

    flag_rejection_cases = (
        lambda: IndustrialProductionSurpriseDigestConfig(**false_flag),
        lambda: replace(item, **false_flag),
        lambda: replace(row, **false_flag),
        lambda: replace(report, **false_flag),
    )

    for reject_false_flag in flag_rejection_cases:
        with pytest.raises(ValueError, match=flag_name):
            reject_false_flag()


def test_rejects_naive_datetimes_false_hard_flags_probability_bounds_and_bad_collections() -> None:
    with pytest.raises(ValueError, match="release_at must be timezone-aware"):
        _release(release_at=datetime(2026, 1, 1))
    with pytest.raises(ValueError, match="release_at must be timezone-aware"):
        _release(release_at=datetime(2026, 1, 1, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_market_research_industrial_production_surprise_digest(
            [_release()],
            config=IndustrialProductionSurpriseDigestConfig(),
            generated_at=datetime(2026, 1, 1, tzinfo=_NoneOffsetTimezone()),
        )

    with pytest.raises(ValueError, match="IndustrialProductionSurpriseInput must be paper_only"):
        IndustrialProductionSurpriseInput(
            market_id="unsafe",
            release_at=datetime(2026, 1, 1, tzinfo=UTC),
            actual_index_level=Decimal("104"),
            consensus_index_level=Decimal("103"),
            previous_index_level=Decimal("102"),
            market_probability=Decimal("0.5"),
            threshold_probability=Decimal("0.5"),
            source_count=Decimal("1"),
            paper_only=False,
        )

    with pytest.raises(ValueError, match="market_probability must be between 0 and 1"):
        _release(market_probability="1.01")

    with pytest.raises(ValueError, match="inputs must be a list or tuple"):
        build_market_research_industrial_production_surprise_digest(
            "bad",  # type: ignore[arg-type]
            config=IndustrialProductionSurpriseDigestConfig(),
            generated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

    with pytest.raises(
        ValueError,
        match="inputs must contain IndustrialProductionSurpriseInput values",
    ):
        build_market_research_industrial_production_surprise_digest(
            [object()],  # type: ignore[list-item]
            config=IndustrialProductionSurpriseDigestConfig(),
            generated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )


def test_module_has_no_db_file_network_live_trading_auth_or_secret_surfaces() -> None:
    source_path = Path(
        "src/polymarket_alpha_lab/market_research_industrial_production_surprise_digest.py",
    )
    source = source_path.read_text()
    lowered_source = source.lower()
    tree = ast.parse(source)
    imported_modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and type(node.value) is float:
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            assert _call_name(node.func) not in {
                "open",
                "read_text",
                "write_text",
                "connect",
                "execute",
                "executemany",
                "urlopen",
                "request",
                "post",
                "put",
                "patch",
                "delete",
                "submit_order",
                "cancel_order",
                "replace_order",
                "create_order",
                "place_order",
                "sign_order",
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
        "clob",
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
        assert forbidden not in lowered_source
