from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, get_args, get_origin, get_type_hints

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
EASTERN = timezone(timedelta(hours=-4))
MODULE_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "team_specialist_source_reliability_decay_watch_v2.py"
)


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_source_reliability_decay_watch_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def hidden_word(hex_value: str) -> str:
    return bytes.fromhex(hex_value).decode("ascii")


def input_row(
    *,
    team_id: str = "macro_rates",
    specialist_id: str = "inflation_researcher",
    source_id: str = "source-cpi-agency",
    source_family: str = "official_release",
    category_id: str = "finance.macro.rates",
    expected_category_id: str = "finance.macro.rates",
    observed_at: datetime = GENERATED_AT - timedelta(hours=1),
    source_last_verified_at: datetime = GENERATED_AT - timedelta(days=1),
    official_source_last_checked_at: datetime = GENERATED_AT - timedelta(hours=1),
    recent_miss_count: str = "0",
    contradiction_miss_count: str = "0",
    sample_count: str = "8",
    public_source_refs: tuple[str, ...] = ("official:cpi-public-release",),
) -> Any:
    module = api()
    return module.TeamSpecialistSourceReliabilityDecayWatchInputV2(
        team_id=team_id,
        specialist_id=specialist_id,
        source_id=source_id,
        source_family=source_family,
        category_id=category_id,
        expected_category_id=expected_category_id,
        observed_at=observed_at,
        source_last_verified_at=source_last_verified_at,
        official_source_last_checked_at=official_source_last_checked_at,
        recent_miss_count=d(recent_miss_count),
        contradiction_miss_count=d(contradiction_miss_count),
        sample_count=d(sample_count),
        public_source_refs=public_source_refs,
    )


def build_report(*rows: Any, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_team_specialist_source_reliability_decay_watch_v2(
        rows,
        config=module.TeamSpecialistSourceReliabilityDecayWatchV2Config(),
        generated_at=generated_at,
    )


def test_exports_and_default_config_are_phase_1_readonly_contract() -> None:
    module = api()
    config = module.TeamSpecialistSourceReliabilityDecayWatchV2Config()

    assert module.__all__ == (
        "DEFAULT_TEAM_SPECIALIST_SOURCE_RELIABILITY_DECAY_WATCH_V2_CONFIG_VERSION",
        "TEAM_SPECIALIST_SOURCE_RELIABILITY_DECAY_WATCH_V2_STATUSES",
        "TeamSpecialistSourceReliabilityDecayWatchV2Config",
        "TeamSpecialistSourceReliabilityDecayWatchInputV2",
        "TeamSpecialistSourceReliabilityDecayWatchRowV2",
        "TeamSpecialistSourceReliabilityDecayWatchReportV2",
        "build_team_specialist_source_reliability_decay_watch_v2",
        "team_specialist_source_reliability_decay_watch_v2_payload",
    )
    assert config.config_version == (
        "team-specialist-source-reliability-decay-watch-v2-phase-1"
    )
    assert config.recent_miss_weight == d("0.300000")
    assert config.stale_source_use_weight == d("0.200000")
    assert config.contradiction_miss_weight == d("0.200000")
    assert config.official_source_lag_weight == d("0.150000")
    assert config.category_mismatch_weight == d("0.100000")
    assert config.sample_size_weight == d("0.050000")
    assert config.stale_source_use_threshold_seconds == d("604800.000000")
    assert config.max_stale_source_use_seconds == d("2419200.000000")
    assert config.official_source_lag_threshold_seconds == d("86400.000000")
    assert config.max_official_source_lag_seconds == d("604800.000000")
    assert config.min_sample_count == d("5")
    assert config.watch_decay_score == d("0.250000")
    assert config.critical_decay_score == d("0.650000")
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistSourceReliabilityDecayWatchV2Config(paper_only=False)


def test_decay_watch_flags_recent_misses_stale_use_contradictions_lag_and_category_mismatch() -> None:
    report = build_report(
        input_row(
            source_id="source-cpi-secondary-summary",
            source_family="secondary_summary",
            category_id="finance.crypto.btc",
            expected_category_id="finance.macro.rates",
            source_last_verified_at=GENERATED_AT - timedelta(days=35),
            official_source_last_checked_at=GENERATED_AT - timedelta(days=8),
            recent_miss_count="4",
            contradiction_miss_count="3",
            sample_count="5",
            public_source_refs=(
                "source:cpi-secondary-summary",
                "official:cpi-public-release",
            ),
        ),
        input_row(
            source_id="source-cpi-official-release",
            source_family="official_release",
            recent_miss_count="0",
            contradiction_miss_count="0",
            sample_count="8",
            public_source_refs=("official:cpi-public-release",),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.team_count == d("1")
    assert report.specialist_team_count == d("1")
    assert report.source_count == d("2")
    assert report.observation_count == d("2")
    assert report.critical_count == d("1")
    assert report.watch_count == d("0")
    assert report.clear_count == d("1")
    assert report.recent_miss_source_count == d("1")
    assert report.stale_source_use_count == d("1")
    assert report.contradiction_miss_source_count == d("1")
    assert report.official_source_lag_count == d("1")
    assert report.category_mismatch_count == d("1")
    assert report.low_sample_size_count == d("0")
    assert report.average_decay_score == d("0.405000")
    assert report.status == "critical"
    assert report.reason_codes == (
        "source_reliability_decay_watch_critical",
        "recent_source_misses",
        "stale_source_use",
        "contradiction_misses",
        "official_source_lag",
        "category_mismatch",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    assert tuple(row.source_id for row in report.rows) == (
        "source-cpi-secondary-summary",
        "source-cpi-official-release",
    )
    risky = report.rows[0]
    assert risky.row_status == "critical"
    assert risky.recent_miss_ratio == d("0.800000")
    assert risky.contradiction_miss_ratio == d("0.600000")
    assert risky.stale_source_use_component == d("1.000000")
    assert risky.official_source_lag_component == d("1.000000")
    assert risky.sample_size_gap == d("0.000000")
    assert risky.category_mismatch is True
    assert risky.decay_score == d("0.810000")
    assert risky.source_verification_age_seconds == d("3024000.000000")
    assert risky.official_source_lag_seconds == d("691200.000000")
    assert risky.reason_codes == (
        "recent_source_misses",
        "stale_source_use",
        "contradiction_misses",
        "official_source_lag",
        "category_mismatch",
    )
    assert len(risky.derived_validation_digest) == 64

    clear = report.rows[1]
    assert clear.row_status == "clear"
    assert clear.decay_score == d("0.000000")
    assert clear.category_mismatch is False
    assert clear.reason_codes == ("source_reliability_decay_clear",)


def test_low_sample_size_alone_keeps_row_on_watch_even_with_small_score() -> None:
    report = build_report(input_row(sample_count="2"))

    assert report.status == "watch"
    assert report.watch_count == d("1")
    assert report.clear_count == d("0")
    assert report.low_sample_size_count == d("1")
    assert report.average_decay_score == d("0.030000")
    assert report.reason_codes == (
        "source_reliability_decay_watch_active",
        "low_source_sample_size",
    )
    assert report.rows[0].row_status == "watch"
    assert report.rows[0].sample_size_gap == d("0.600000")
    assert report.rows[0].reason_codes == ("low_source_sample_size",)


def test_empty_report_is_watch_with_public_decimal_zero_values() -> None:
    report = build_report(generated_at=datetime(2026, 7, 6, 8, 0, tzinfo=EASTERN))

    assert report.generated_at == GENERATED_AT
    assert report.team_count == d("0")
    assert report.specialist_team_count == d("0")
    assert report.source_count == d("0")
    assert report.observation_count == d("0")
    assert report.critical_count == d("0")
    assert report.watch_count == d("0")
    assert report.clear_count == d("0")
    assert report.average_decay_score == d("0.000000")
    assert report.status == "watch"
    assert report.reason_codes == ("source_reliability_decay_watch_empty_sources",)
    assert report.rows == ()


def test_payload_uses_decimal_strings_tuple_collections_and_deterministic_digests() -> None:
    report = build_report(
        input_row(
            source_id="source-cpi-secondary-summary",
            source_family="secondary_summary",
            category_id="finance.crypto.btc",
            source_last_verified_at=GENERATED_AT - timedelta(days=35),
            official_source_last_checked_at=GENERATED_AT - timedelta(days=8),
            recent_miss_count="4",
            contradiction_miss_count="3",
            sample_count="5",
            public_source_refs=(
                "source:cpi-secondary-summary",
                "official:cpi-public-release",
            ),
        ),
    )

    payload = api().team_specialist_source_reliability_decay_watch_v2_payload(report)
    payload_text = repr(payload)

    assert payload["average_decay_score"] == "0.810000"
    assert payload["source_count"] == "1"
    assert payload["rows"][0]["decay_score"] == "0.810000"
    assert payload["rows"][0]["sample_count"] == "5"
    assert payload["rows"][0]["source_verification_age_seconds"] == "3024000.000000"
    assert payload["rows"][0]["official_source_lag_seconds"] == "691200.000000"
    assert payload["rows"][0]["public_source_refs"] == (
        "official:cpi-public-release",
        "source:cpi-secondary-summary",
    )
    assert payload["rows"][0]["derived_validation_digest"] == (
        report.rows[0].derived_validation_digest
    )
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert "Decimal" not in payload_text
    _assert_no_public_numbers(payload)
    json.dumps(payload)


def test_frozen_dataclasses_hard_flags_digest_tampering_and_decimal_validation() -> None:
    module = api()

    with pytest.raises(ValueError, match="recent_miss_count must be a Decimal"):
        module.TeamSpecialistSourceReliabilityDecayWatchInputV2(
            team_id="macro_rates",
            specialist_id="inflation_researcher",
            source_id="source-cpi-agency",
            source_family="official_release",
            category_id="finance.macro.rates",
            expected_category_id="finance.macro.rates",
            observed_at=GENERATED_AT,
            source_last_verified_at=GENERATED_AT,
            official_source_last_checked_at=GENERATED_AT,
            recent_miss_count=0.5,
            contradiction_miss_count=d("0"),
            sample_count=d("8"),
            public_source_refs=("official:cpi-public-release",),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_report(input_row(), generated_at=datetime(2026, 7, 6, 12, 0))

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        input_row(observed_at=datetime(2026, 7, 6, 12, 0))

    with pytest.raises(ValueError, match="observed_at must be on or before generated_at"):
        build_report(input_row(observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="source_last_verified_at must be on or before"):
        build_report(
            input_row(source_last_verified_at=GENERATED_AT + timedelta(seconds=1)),
        )

    with pytest.raises(ValueError, match="official_source_last_checked_at must be on or before"):
        build_report(
            input_row(official_source_last_checked_at=GENERATED_AT + timedelta(seconds=1)),
        )

    with pytest.raises(ValueError, match="recent_miss_count must not exceed sample_count"):
        input_row(recent_miss_count="9", sample_count="8")

    with pytest.raises(ValueError, match="contradiction_miss_count must not exceed sample_count"):
        input_row(contradiction_miss_count="9", sample_count="8")

    with pytest.raises(ValueError, match="public_source_refs must not be empty"):
        input_row(public_source_refs=())

    with pytest.raises(ValueError, match="report_only must be True"):
        replace(input_row(), report_only=False)

    with pytest.raises(FrozenInstanceError):
        input_row().sample_count = d("1")  # type: ignore[misc]

    report = build_report(input_row())
    with pytest.raises(FrozenInstanceError):
        report.status = "clear"  # type: ignore[misc]

    with pytest.raises(ValueError, match="derived_validation_digest must match watch row fields"):
        replace(report.rows[0], decay_score=d("0.123456"))

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, average_decay_score=d("0.123456"))

    with pytest.raises(ValueError, match="config"):
        module.build_team_specialist_source_reliability_decay_watch_v2(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )


def test_public_dataclasses_are_frozen_and_numeric_surface_uses_decimal_only() -> None:
    module = api()

    report = build_report(input_row())
    assert is_dataclass(report)
    with pytest.raises(FrozenInstanceError):
        report.average_decay_score = d("0.100000")  # type: ignore[misc]

    dataclass_types = (
        module.TeamSpecialistSourceReliabilityDecayWatchV2Config,
        module.TeamSpecialistSourceReliabilityDecayWatchInputV2,
        module.TeamSpecialistSourceReliabilityDecayWatchRowV2,
        module.TeamSpecialistSourceReliabilityDecayWatchReportV2,
    )
    for dataclass_type in dataclass_types:
        hints = get_type_hints(dataclass_type, include_extras=True)
        for field in fields(dataclass_type):
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_score")
                or field.name.endswith("_seconds")
                or field.name.endswith("_weight")
            ):
                annotation = hints[field.name]
                args = get_args(annotation)
                assert annotation is Decimal or (
                    get_origin(annotation) is type(Decimal | None)
                    and Decimal in args
                    and type(None) in args
                )


def test_unsafe_public_values_and_keys_are_rejected() -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public value"):
        input_row(team_id=f"macro_{hidden_word('77616c6c6574')}")

    with pytest.raises(ValueError, match="unsafe public value"):
        input_row(public_source_refs=(f"source:{hidden_word('7472616465')}-path",))

    with pytest.raises(ValueError, match="unsafe public key"):
        module._reject_public_payload(  # noqa: SLF001
            "test payload",
            {f"public_{hidden_word('6f72646572')}": "safe"},
        )

    with pytest.raises(ValueError, match="unsafe public value"):
        module._reject_public_payload(  # noqa: SLF001
            "test payload",
            {"safe": f"public-{hidden_word('61757468')}"},
        )


def test_module_scope_is_pure_reducer_without_io_or_live_execution_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    lowered = source.lower()
    for forbidden in (
        "requests",
        "urllib",
        "httpx",
        "websocket",
        "psycopg",
        "sqlite",
        "supabase",
        "os.environ",
        "subprocess",
        "socket",
        "asyncio",
        "open(",
        "path(",
        "write",
        "wallet",
        "auth",
        "private_key",
        "api_key",
        "place_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "live_trading",
        "fast_mode",
        "fast ",
    ):
        assert forbidden not in lowered

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
            }
    forbidden_import_fragments = (
        "db",
        "env",
        "cli",
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "supabase",
        "subprocess",
        "pathlib",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for hidden in (
        "6c697665",
        "61757468",
        "77616c6c6574",
        "6f72646572",
        "6e6574776f726b",
        "6461746162617365",
        "70657273697374",
        "7369676e696e67",
        "6d75746174696f6e",
        "627579",
        "73656c6c",
        "7472616465",
    ):
        assert hidden_word(hidden) not in lowered


def _assert_no_public_numbers(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"unexpected public numeric value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_public_numbers(item)
    if isinstance(value, list | tuple):
        for item in value:
            _assert_no_public_numbers(item)
