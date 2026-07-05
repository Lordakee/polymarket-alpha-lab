from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 4, 18, 0, tzinfo=UTC)
BASE_OBSERVED_AT = datetime(2026, 7, 4, 16, 0, tzinfo=UTC)
CONFIG_VERSION = "market-research-baseball-bullpen-fatigue-digest-v0"


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTZ(tzinfo):
    def utcoffset(self, dt):  # noqa: ANN001
        return None

    def dst(self, dt):  # noqa: ANN001
        return None


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_baseball_bullpen_fatigue_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides):
    digest = module()
    values = {
        "config_version": CONFIG_VERSION,
        "workload_index_watch_threshold": d("0.700000"),
        "back_to_back_outing_watch_threshold": d("3.000000"),
        "rest_day_shortage_watch_threshold": d("2.000000"),
        "high_leverage_outing_watch_threshold": d("2.000000"),
        "min_snapshot_count": d("2.000000"),
    }
    values.update(overrides)
    return digest.MarketResearchBaseballBullpenFatigueDigestConfig(**values)


def snapshot(
    bullpen_key: str = "bullpen.nyy",
    team_key: str = "nyy",
    *,
    observed_at: datetime = BASE_OBSERVED_AT,
    recent_relief_innings: Decimal = d("5.000000"),
    back_to_back_outing_count: Decimal = d("1.000000"),
    rest_day_shortage_count: Decimal = d("1.000000"),
    high_leverage_outing_count: Decimal = d("1.000000"),
    available_reliever_count: Decimal = d("8.000000"),
    source_count: Decimal = d("2.000000"),
    source_config_version: str = "bullpen-fatigue-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    digest = module()
    return digest.MarketResearchBaseballBullpenFatigueDigestSnapshot(
        bullpen_key=bullpen_key,
        team_key=team_key,
        observed_at=observed_at,
        recent_relief_innings=recent_relief_innings,
        back_to_back_outing_count=back_to_back_outing_count,
        rest_day_shortage_count=rest_day_shortage_count,
        high_leverage_outing_count=high_leverage_outing_count,
        available_reliever_count=available_reliever_count,
        source_count=source_count,
        source_config_version=source_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*snapshots, **overrides):
    digest = module()
    values = {
        "snapshots": snapshots,
        "config": config(),
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return digest.build_market_research_baseball_bullpen_fatigue_digest(**values)


def test_digest_flags_bullpen_workload_rest_and_leverage_fatigue() -> None:
    report = build_report(
        snapshot(
            "bullpen.nyy",
            "nyy",
            observed_at=GENERATED_AT - timedelta(hours=4),
            recent_relief_innings=d("5.000000"),
            back_to_back_outing_count=d("1.000000"),
            rest_day_shortage_count=d("1.000000"),
            high_leverage_outing_count=d("1.000000"),
            available_reliever_count=d("8.000000"),
            source_config_version="bullpen-feed-v0",
        ),
        snapshot(
            "bullpen.nyy",
            "nyy",
            observed_at=GENERATED_AT - timedelta(hours=2),
            recent_relief_innings=d("11.000000"),
            back_to_back_outing_count=d("3.000000"),
            rest_day_shortage_count=d("2.000000"),
            high_leverage_outing_count=d("2.000000"),
            available_reliever_count=d("7.000000"),
            source_config_version="bullpen-feed-v1",
        ),
        snapshot(
            "bullpen.sf",
            "sf",
            observed_at=GENERATED_AT - timedelta(minutes=50),
            recent_relief_innings=d("3.000000"),
            back_to_back_outing_count=d("0.000000"),
            rest_day_shortage_count=d("0.000000"),
            high_leverage_outing_count=d("1.000000"),
            available_reliever_count=d("8.000000"),
        ),
        snapshot(
            "bullpen.sf",
            "sf",
            observed_at=GENERATED_AT - timedelta(minutes=20),
            recent_relief_innings=d("4.000000"),
            back_to_back_outing_count=d("1.000000"),
            rest_day_shortage_count=d("0.000000"),
            high_leverage_outing_count=d("1.000000"),
            available_reliever_count=d("8.000000"),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.digest_status == "watch"
    assert report.recommended_next_step == (
        "review_report_only_baseball_bullpen_fatigue_digest"
    )
    assert report.bullpen_count == d("2")
    assert report.fatigued_bullpen_count == d("1")
    assert report.clear_bullpen_count == d("1")
    assert report.snapshot_count == d("4")
    assert report.high_workload_bullpen_count == d("1")
    assert report.back_to_back_bullpen_count == d("1")
    assert report.rest_shortage_bullpen_count == d("1")
    assert report.high_leverage_bullpen_count == d("1")
    assert report.max_workload_index == d("0.733333")
    assert report.max_recent_relief_innings == d("11.000000")
    assert report.min_available_reliever_count == d("7.000000")
    assert report.reason_codes == (
        "baseball_bullpen_fatigue_back_to_back_usage",
        "baseball_bullpen_fatigue_leverage_high",
        "baseball_bullpen_fatigue_rest_shortage",
        "baseball_bullpen_fatigue_workload_high",
    )
    assert report.source_config_versions == (
        ("bullpen.nyy", "bullpen-feed-v0"),
        ("bullpen.nyy", "bullpen-feed-v1"),
        ("bullpen.sf", "bullpen-fatigue-source-v0"),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.bullpen_key for row in report.rows) == (
        "bullpen.nyy",
        "bullpen.sf",
    )
    nyy = report.rows[0]
    assert nyy.digest_status == "fatigued"
    assert nyy.latest_observed_at == GENERATED_AT - timedelta(hours=2)
    assert nyy.workload_index == d("0.733333")
    assert nyy.max_recent_relief_innings == d("11.000000")
    assert nyy.min_available_reliever_count == d("7")
    assert nyy.reason_codes == (
        "baseball_bullpen_fatigue_back_to_back_usage",
        "baseball_bullpen_fatigue_leverage_high",
        "baseball_bullpen_fatigue_rest_shortage",
        "baseball_bullpen_fatigue_workload_high",
    )
    assert report.rows[1].digest_status == "clear"
    assert report.rows[1].reason_codes == ("baseball_bullpen_fatigue_clear",)


def test_digest_passes_for_empty_clear_and_limited_history_inputs() -> None:
    empty_report = build_report()

    assert empty_report.digest_status == "blocked"
    assert empty_report.recommended_next_step == (
        "block_report_only_baseball_bullpen_fatigue_digest"
    )
    assert empty_report.bullpen_count == d("0.000000")
    assert empty_report.snapshot_count == d("0.000000")
    assert empty_report.rows == ()
    assert empty_report.max_workload_index is None
    assert empty_report.reason_codes == ("baseball_bullpen_fatigue_empty",)
    assert empty_report.reason_code_counts == (
        module().MarketResearchBaseballBullpenFatigueDigestReasonCodeCount(
            reason_code="baseball_bullpen_fatigue_empty",
            bullpen_count=d("1.000000"),
            bullpen_ratio=d("0.000000"),
        ),
    )

    stable_report = build_report(
        snapshot("bullpen.alpha", "lad", recent_relief_innings=d("2.000000")),
        snapshot(
            "bullpen.alpha",
            "lad",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            recent_relief_innings=d("3.000000"),
            available_reliever_count=d("8.000000"),
        ),
        snapshot("bullpen.beta", "bos"),
    )

    assert stable_report.digest_status == "pass"
    assert stable_report.reason_codes == (
        "baseball_bullpen_fatigue_limited_history",
        "baseball_bullpen_fatigue_passed",
    )
    assert tuple((row.bullpen_key, row.digest_status) for row in stable_report.rows) == (
        ("bullpen.beta", "limited_history"),
        ("bullpen.alpha", "clear"),
    )


def test_payload_helper_uses_json_ready_scalars_without_sensitive_surface() -> None:
    digest = module()
    report = build_report(
        snapshot(
            "bullpen.payload",
            "sea",
            observed_at=datetime(2026, 7, 4, 10, 0, tzinfo=timezone(timedelta(hours=-4))),
            recent_relief_innings=d("4.000000"),
        ),
        snapshot(
            "bullpen.payload",
            "sea",
            observed_at=GENERATED_AT - timedelta(minutes=30),
            recent_relief_innings=d("7.000000"),
            back_to_back_outing_count=d("3.000000"),
        ),
    )

    payload = digest.market_research_baseball_bullpen_fatigue_digest_payload(report)
    json.dumps(payload, sort_keys=True)

    with pytest.raises(
        ValueError,
        match="report must be exactly MarketResearchBaseballBullpenFatigueDigestReport",
    ):
        digest.market_research_baseball_bullpen_fatigue_digest_payload(config())  # type: ignore[arg-type]

    assert payload["generated_at"] == "2026-07-04T18:00:00+00:00"
    assert payload["bullpen_count"] == "1.000000"
    assert payload["rows"][0]["latest_observed_at"] == "2026-07-04T17:30:00+00:00"
    assert payload["rows"][0]["workload_index"] == "0.437500"
    assert payload["rows"][0]["snapshot_count"] == "2.000000"
    assert payload["reason_code_counts"][0]["bullpen_count"] == "1.000000"
    assert payload["reason_code_counts"][0]["bullpen_ratio"] == "1.000000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))

    payload_text = repr(payload).lower()
    for forbidden in (
        "wallet",
        "broker",
        "order",
        "account",
        "advice",
        "auth",
        "signing",
        "submit",
        "cancel",
        "secret",
        "token",
    ):
        assert forbidden not in payload_text


def test_payload_revalidates_nested_public_dataclasses_before_serialization() -> None:
    digest = module()

    row_flag_report = build_report(
        snapshot("bullpen.payload-row-flag", "sea"),
        snapshot(
            "bullpen.payload-row-flag",
            "sea",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            recent_relief_innings=d("12.000000"),
            available_reliever_count=d("7.000000"),
        ),
    )
    object.__setattr__(row_flag_report.rows[0], "paper_only", False)
    with pytest.raises(ValueError, match="row paper_only must be True"):
        digest.market_research_baseball_bullpen_fatigue_digest_payload(row_flag_report)

    reason_flag_report = build_report(
        snapshot("bullpen.payload-reason-flag", "nym"),
        snapshot(
            "bullpen.payload-reason-flag",
            "nym",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            recent_relief_innings=d("12.000000"),
            available_reliever_count=d("7.000000"),
        ),
    )
    object.__setattr__(reason_flag_report.reason_code_counts[0], "readonly", False)
    with pytest.raises(ValueError, match="reason_code_count readonly must be True"):
        digest.market_research_baseball_bullpen_fatigue_digest_payload(reason_flag_report)

    decimal_report = build_report(
        snapshot("bullpen.payload-decimal", "ari"),
        snapshot(
            "bullpen.payload-decimal",
            "ari",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            recent_relief_innings=d("12.000000"),
            available_reliever_count=d("7.000000"),
        ),
    )
    object.__setattr__(decimal_report.rows[0], "workload_index", d("0.1234567"))
    with pytest.raises(ValueError, match="workload_index must be six-decimal"):
        digest.market_research_baseball_bullpen_fatigue_digest_payload(decimal_report)


def test_dataclasses_validate_decimal_datetime_flags_consistency_and_types() -> None:
    digest = module()

    row = snapshot()
    with pytest.raises(FrozenInstanceError):
        row.recent_relief_innings = d("3.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="recent_relief_innings must be a Decimal"):
        snapshot(recent_relief_innings=3.2)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        snapshot(observed_at=datetime(2026, 7, 4, 16, 0))

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        snapshot(observed_at=datetime(2026, 7, 4, 16, 0, tzinfo=_NoneOffsetTZ()))

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        build_report(
            snapshot(),
            generated_at=_DatetimeSubclass(2026, 7, 4, 18, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="workload_index_watch_threshold"):
        config(workload_index_watch_threshold=_DecimalSubclass("0.700000"))

    with pytest.raises(ValueError, match="config_version"):
        config(config_version="market-research-baseball-bullpen-fatigue-digest-v9")

    with pytest.raises(ValueError, match="min_snapshot_count"):
        config(min_snapshot_count=d("1.500000"))

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        config(report_only=False)

    none_config_report = build_report(
        snapshot("bullpen.default-config", "col"),
        config=None,
    )
    assert none_config_report.config_version == CONFIG_VERSION

    with pytest.raises(
        ValueError,
        match="config must be exactly MarketResearchBaseballBullpenFatigueDigestConfig",
    ):
        build_report(snapshot("bullpen.bad-config", "col"), config=False)

    with pytest.raises(ValueError, match="snapshots must not contain duplicate"):
        build_report(snapshot(source_config_version="v0"), snapshot(source_config_version="v1"))

    with pytest.raises(ValueError, match="team_key must match within bullpen_key"):
        build_report(
            snapshot("bullpen.same", "nyy"),
            snapshot(
                "bullpen.same",
                "bos",
                observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            ),
        )

    report = build_report(
        snapshot("bullpen.gamma", "stl"),
        snapshot(
            "bullpen.gamma",
            "stl",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
        ),
    )
    bad_report_values = {
        field.name: getattr(report, field.name)
        for field in fields(report)
    }
    bad_report_values["bullpen_count"] = d("2")
    with pytest.raises(ValueError, match="bullpen_count"):
        digest.MarketResearchBaseballBullpenFatigueDigestReport(**bad_report_values)


def test_public_dataclasses_are_frozen_exact_type_and_reject_subclassing() -> None:
    digest = module()
    public_types = (
        digest.MarketResearchBaseballBullpenFatigueDigestConfig,
        digest.MarketResearchBaseballBullpenFatigueDigestSnapshot,
        digest.MarketResearchBaseballBullpenFatigueDigestReasonCodeCount,
        digest.MarketResearchBaseballBullpenFatigueDigestRow,
        digest.MarketResearchBaseballBullpenFatigueDigestReport,
    )

    report = build_report(
        snapshot("bullpen.typecheck", "nym"),
        snapshot(
            "bullpen.typecheck",
            "nym",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            recent_relief_innings=d("12.000000"),
            back_to_back_outing_count=d("3.000000"),
            rest_day_shortage_count=d("2.000000"),
            high_leverage_outing_count=d("2.000000"),
            available_reliever_count=d("7.000000"),
        ),
    )
    public_records = (
        config(),
        snapshot("bullpen.snapshot", "ari"),
        report.reason_code_counts[0],
        report.rows[0],
        report,
    )

    for public_type, public_record in zip(public_types, public_records, strict=True):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"{public_type.__name__}Subclass", (public_type,), {})

    source_text = Path(
        "src/polymarket_alpha_lab/market_research_baseball_bullpen_fatigue_digest.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source_text)
    exact_type_post_inits: set[str] = set()
    public_type_names = {public_type.__name__ for public_type in public_types}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name not in public_type_names:
            continue
        for child in node.body:
            if not isinstance(child, ast.FunctionDef) or child.name != "__post_init__":
                continue
            for call_node in ast.walk(child):
                if not isinstance(call_node, ast.Call):
                    continue
                if not isinstance(call_node.func, ast.Name):
                    continue
                if call_node.func.id != "_require_exact_type":
                    continue
                if len(call_node.args) < 2:
                    continue
                expected_type_arg = call_node.args[1]
                if isinstance(expected_type_arg, ast.Name):
                    exact_type_post_inits.add(expected_type_arg.id)
    assert exact_type_post_inits == public_type_names


def test_public_constructors_reject_noncanonical_sequences() -> None:
    digest = module()
    report = build_report(
        snapshot(
            "bullpen.det-fatigue",
            "nyy",
            observed_at=GENERATED_AT - timedelta(hours=3),
            recent_relief_innings=d("5.000000"),
            available_reliever_count=d("7.000000"),
        ),
        snapshot(
            "bullpen.det-fatigue",
            "nyy",
            observed_at=GENERATED_AT - timedelta(hours=2),
            recent_relief_innings=d("12.000000"),
            back_to_back_outing_count=d("3.000000"),
            rest_day_shortage_count=d("2.000000"),
            high_leverage_outing_count=d("2.000000"),
            available_reliever_count=d("7.000000"),
        ),
        snapshot("bullpen.det-clear", "sea", recent_relief_innings=d("3.000000")),
        snapshot(
            "bullpen.det-clear",
            "sea",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=45),
            recent_relief_innings=d("4.000000"),
            available_reliever_count=d("8.000000"),
        ),
    )

    row_values = {
        field.name: getattr(report.rows[0], field.name)
        for field in fields(report.rows[0])
    }
    row_values["reason_codes"] = tuple(reversed(report.rows[0].reason_codes))
    with pytest.raises(ValueError, match="reason_codes must be canonical"):
        digest.MarketResearchBaseballBullpenFatigueDigestRow(**row_values)

    report_values = {
        field.name: getattr(report, field.name)
        for field in fields(report)
    }
    report_values["rows"] = tuple(reversed(report.rows))
    with pytest.raises(ValueError, match="rows must be canonical"):
        digest.MarketResearchBaseballBullpenFatigueDigestReport(**report_values)

    report_values = {
        field.name: getattr(report, field.name)
        for field in fields(report)
    }
    report_values["reason_code_counts"] = tuple(reversed(report.reason_code_counts))
    with pytest.raises(ValueError, match="reason_code_counts must be canonical"):
        digest.MarketResearchBaseballBullpenFatigueDigestReport(**report_values)

    report_values = {
        field.name: getattr(report, field.name)
        for field in fields(report)
    }
    report_values["source_config_versions"] = tuple(
        reversed(report.source_config_versions),
    )
    with pytest.raises(ValueError, match="source_config_versions must be canonical"):
        digest.MarketResearchBaseballBullpenFatigueDigestReport(**report_values)

    with pytest.raises(ValueError, match="bullpen_count must be positive"):
        digest.MarketResearchBaseballBullpenFatigueDigestReasonCodeCount(
            reason_code="baseball_bullpen_fatigue_workload_high",
            bullpen_count=d("0.000000"),
            bullpen_ratio=d("0.000000"),
        )


def test_public_numeric_count_and_ratio_fields_are_decimal_only() -> None:
    report = build_report(snapshot("bullpen.delta", "mia"))
    row = report.rows[0]

    for value in (report, row):
        for field in fields(value):
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_index")
                or field.name.endswith("_innings")
            ):
                field_value = getattr(value, field.name)
                if field_value is not None:
                    assert type(field_value) is Decimal


def test_module_scope_has_no_io_live_trading_float_or_durable_store_surface() -> None:
    source_text = Path(
        "src/polymarket_alpha_lab/market_research_baseball_bullpen_fatigue_digest.py",
    ).read_text(encoding="utf-8")
    lowered = source_text.lower()

    for forbidden in (
        "live trading",
        "wallet",
        "broker",
        "signing",
        "submit_",
        "cancel_",
        "order_",
        "replace_",
        "exchange",
        "account",
        "advice",
        "auth",
        "api_key",
        "secret_key",
        "secret",
        "token",
        "asdict",
        "open(",
        "read_text(",
        "write_text(",
        "requests",
        "http",
        "socket",
        "psycopg",
        "sqlite",
        "sql",
        "float(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
    forbidden_import_fragments = (
        "db",
        "env",
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _walk_payload_values(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk_payload_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_payload_values(item)
    else:
        yield value
