from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.strategy_team_information_velocity_digest import (
    StrategyTeamInformationVelocityDigestConfig,
    StrategyTeamInformationVelocityDigestReasonCodeCount,
    StrategyTeamInformationVelocityDigestReport,
    StrategyTeamInformationVelocityInput,
    build_strategy_team_information_velocity_digest,
    strategy_team_information_velocity_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
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


def config(**overrides: object) -> StrategyTeamInformationVelocityDigestConfig:
    values: dict[str, object] = {
        "config_version": "strategy-team-information-velocity-digest-v0",
        "target_update_count": d("6.000000"),
        "watch_update_count": d("2.000000"),
        "maximum_current_cadence_seconds": d("3600.000000"),
        "watch_cadence_seconds": d("7200.000000"),
        "maximum_fresh_evidence_age_seconds": d("1800.000000"),
        "watch_evidence_age_seconds": d("7200.000000"),
        "minimum_distinct_source_count": d("2.000000"),
        "accelerate_information_velocity_score": d("0.750000"),
        "watch_information_velocity_score": d("0.400000"),
    }
    values.update(overrides)
    return StrategyTeamInformationVelocityDigestConfig(**values)


def info_row(
    category_id: str = "politics",
    *,
    team_id: str = "politics_team",
    coverage_window_started_at: datetime = GENERATED_AT - timedelta(hours=6),
    latest_evidence_at: datetime = GENERATED_AT - timedelta(minutes=15),
    update_count: Decimal = d("12.000000"),
    evidence_item_count: Decimal = d("18.000000"),
    distinct_source_count: Decimal = d("4.000000"),
    public_reference: str = "public-coverage-ticket",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> StrategyTeamInformationVelocityInput:
    return StrategyTeamInformationVelocityInput(
        team_id=team_id,
        category_id=category_id,
        coverage_window_started_at=coverage_window_started_at,
        latest_evidence_at=latest_evidence_at,
        update_count=update_count,
        evidence_item_count=evidence_item_count,
        distinct_source_count=distinct_source_count,
        public_reference=public_reference,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(
    *rows: StrategyTeamInformationVelocityInput,
    cfg: StrategyTeamInformationVelocityDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> StrategyTeamInformationVelocityDigestReport:
    return build_strategy_team_information_velocity_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_public_numeric_fields_are_decimal(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if type(item) is bool:
            continue
        assert type(item) is not float
        assert type(item) is not int
        if isinstance(item, tuple):
            for nested in item:
                if is_dataclass(nested):
                    assert_public_numeric_fields_are_decimal(nested)


def assert_no_float_values(value: object) -> None:
    assert type(value) is not float
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_digest_scores_team_category_information_velocity() -> None:
    result = digest(
        info_row(
            "sports",
            team_id="sports_team",
            coverage_window_started_at=GENERATED_AT - timedelta(hours=10),
            latest_evidence_at=GENERATED_AT - timedelta(hours=8),
            update_count=d("1.000000"),
            evidence_item_count=d("2.000000"),
            distinct_source_count=d("1.000000"),
            public_reference="wallet://private-key",
        ),
        info_row(
            "macro",
            team_id="macro_team",
            coverage_window_started_at=GENERATED_AT - timedelta(hours=6),
            latest_evidence_at=GENERATED_AT - timedelta(hours=1),
            update_count=d("3.000000"),
            evidence_item_count=d("6.000000"),
            distinct_source_count=d("2.000000"),
        ),
        info_row(
            "politics",
            team_id="politics_team",
            public_reference="https://example.test/feed?api_key=secret",
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.generated_at.tzinfo is UTC
    assert result.config_version == "strategy-team-information-velocity-digest-v0"
    assert result.team_category_count == d("3.000000")
    assert result.team_count == d("3.000000")
    assert result.category_count == d("3.000000")
    assert result.accelerate_count == d("1.000000")
    assert result.maintain_count == d("1.000000")
    assert result.pause_count == d("1.000000")
    assert result.max_information_velocity_score == d("0.906250")
    assert result.average_information_velocity_score == d("0.482639")
    assert result.digest_status == "accelerate"
    assert result.next_step == "accelerate_paper_research_coverage"
    assert result.accelerated_team_category_ids == ("politics_team:politics",)
    assert result.reason_codes == (
        "evidence_fresh",
        "evidence_stale_pause",
        "evidence_stale_watch",
        "information_velocity_accelerate",
        "information_velocity_high",
        "information_velocity_low",
        "information_velocity_maintain",
        "information_velocity_pause",
        "information_velocity_watch",
        "source_depth_low",
        "source_depth_sufficient",
        "strategy_team_information_velocity_accelerate",
        "update_cadence_current",
        "update_cadence_slow_pause",
        "update_cadence_slow_watch",
    )
    assert result.reason_code_counts[0] == StrategyTeamInformationVelocityDigestReasonCodeCount(
        reason_code="source_depth_sufficient",
        count=d("2.000000"),
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_public_numeric_fields_are_decimal(result)

    assert tuple(row.category_id for row in result.rows) == (
        "politics",
        "macro",
        "sports",
    )

    top = result.rows[0]
    assert top.rank == d("1.000000")
    assert top.team_id == "politics_team"
    assert top.velocity_status == "accelerate"
    assert top.window_age_seconds == d("21600.000000")
    assert top.update_cadence_seconds == d("1800.000000")
    assert top.evidence_age_seconds == d("900.000000")
    assert top.information_velocity_score == d("0.906250")
    assert top.redacted_public_reference == "[redacted-reference]"
    assert top.reason_codes == (
        "evidence_fresh",
        "information_velocity_accelerate",
        "information_velocity_high",
        "source_depth_sufficient",
        "update_cadence_current",
    )

    middle = result.rows[1]
    assert middle.velocity_status == "maintain"
    assert middle.information_velocity_score == d("0.425000")
    assert middle.reason_codes == (
        "evidence_stale_watch",
        "information_velocity_maintain",
        "information_velocity_watch",
        "source_depth_sufficient",
        "update_cadence_slow_watch",
    )

    paused = result.rows[2]
    assert paused.velocity_status == "pause"
    assert paused.information_velocity_score == d("0.116667")
    assert paused.reason_codes == (
        "evidence_stale_pause",
        "information_velocity_low",
        "information_velocity_pause",
        "source_depth_low",
        "update_cadence_slow_pause",
    )


def test_empty_digest_is_report_only_readonly_and_decimal_zeroed() -> None:
    result = digest()

    assert result.digest_status == "pause"
    assert result.next_step == "pause_paper_research_coverage"
    assert result.team_category_count == ZERO
    assert result.team_count == ZERO
    assert result.category_count == ZERO
    assert result.accelerate_count == ZERO
    assert result.maintain_count == ZERO
    assert result.pause_count == ZERO
    assert result.max_information_velocity_score == ZERO
    assert result.average_information_velocity_score == ZERO
    assert result.accelerated_team_category_ids == ()
    assert result.rows == ()
    assert result.reason_codes == (
        "strategy_team_information_velocity_digest_empty",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_public_numeric_fields_are_decimal(result)


def test_payload_uses_decimal_strings_utc_datetimes_and_redacted_references() -> None:
    result = digest(
        info_row(public_reference="https://example.test/feed?token=secret"),
        generated_at=datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    payload = strategy_team_information_velocity_digest_payload(result)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["team_category_count"] == "1.000000"
    assert payload["max_information_velocity_score"] == "0.906250"
    assert payload["rows"][0]["rank"] == "1.000000"
    assert payload["rows"][0]["latest_evidence_at"] == "2026-07-04T11:45:00+00:00"
    assert payload["rows"][0]["information_velocity_score"] == "0.906250"
    assert payload["rows"][0]["redacted_public_reference"] == "[redacted-reference]"
    assert "public_reference" not in payload["rows"][0]
    assert "token" not in encoded.lower()
    assert "secret" not in encoded.lower()
    assert "0.906250" in encoded
    assert_no_float_values(payload)


def test_payload_dict_path_enforces_phase1_boundaries() -> None:
    payload = strategy_team_information_velocity_digest_payload(digest(info_row()))

    assert strategy_team_information_velocity_digest_payload(payload) == payload

    nested_flag_payload = dict(payload)
    nested_flag_payload["rows"] = [{**payload["rows"][0], "readonly": False}]
    with pytest.raises(ValueError, match="readonly.*True"):
        strategy_team_information_velocity_digest_payload(nested_flag_payload)

    with pytest.raises(ValueError, match="team_category_count.*Decimal"):
        strategy_team_information_velocity_digest_payload(
            {**payload, "team_category_count": 1},
        )

    with pytest.raises(ValueError, match="float"):
        strategy_team_information_velocity_digest_payload(
            {**payload, "average_information_velocity_score": 0.4},
        )

    with pytest.raises(ValueError, match="timezone-aware"):
        strategy_team_information_velocity_digest_payload(
            {**payload, "generated_at": datetime(2026, 7, 4, 12, 0)},
        )

    with pytest.raises(ValueError, match="JSON object keys"):
        strategy_team_information_velocity_digest_payload({1: "x", **payload})

    with pytest.raises(ValueError, match="unsafe"):
        strategy_team_information_velocity_digest_payload(
            {**payload, "reason_codes": ["api_key_secret_token"]},
        )


def test_inputs_config_and_report_reject_decimal_datetime_and_flag_drift() -> None:
    with pytest.raises(ValueError, match="update_count must be a Decimal"):
        info_row(update_count=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="update_count must be a Decimal"):
        info_row(update_count=_DecimalSubclass("1.000000"))

    with pytest.raises(ValueError, match="latest_evidence_at must be exactly datetime"):
        info_row(latest_evidence_at=_DatetimeSubclass(2026, 7, 4, 12, tzinfo=UTC))

    with pytest.raises(ValueError, match="latest_evidence_at must be timezone-aware"):
        info_row(
            latest_evidence_at=datetime(
                2026,
                7,
                4,
                12,
                0,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )

    with pytest.raises(ValueError, match="coverage_window_started_at must not be after"):
        info_row(
            coverage_window_started_at=GENERATED_AT - timedelta(minutes=5),
            latest_evidence_at=GENERATED_AT - timedelta(minutes=10),
        )

    with pytest.raises(ValueError, match="paper_only"):
        info_row(paper_only=False)

    with pytest.raises(ValueError, match="config must be"):
        build_strategy_team_information_velocity_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        digest(info_row(), generated_at=_DatetimeSubclass(2026, 7, 4, 12, tzinfo=UTC))

    with pytest.raises(ValueError, match="latest_evidence_at must not be after"):
        digest(
            info_row(latest_evidence_at=GENERATED_AT + timedelta(seconds=1)),
        )

    with pytest.raises(ValueError, match="duplicate team and category"):
        digest(info_row("macro"), info_row("macro"))

    with pytest.raises(ValueError, match="accelerate_information_velocity_score"):
        config(accelerate_information_velocity_score=_DecimalSubclass("0.750000"))

    result = digest(info_row())
    with pytest.raises(ValueError, match="team_category_count must be a Decimal"):
        replace(result, team_category_count=1)


def test_public_dataclasses_are_frozen_and_references_do_not_leak_from_repr() -> None:
    row = info_row(public_reference="https://example.test/feed?api_key=secret")
    result = digest(row)

    for cls in (
        StrategyTeamInformationVelocityDigestConfig,
        StrategyTeamInformationVelocityDigestReasonCodeCount,
        StrategyTeamInformationVelocityDigestReport,
        StrategyTeamInformationVelocityInput,
        type(result.rows[0]),
    ):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        row.team_id = "changed"  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        result.rows[0].velocity_status = "pause"  # type: ignore[misc]

    assert row.public_reference == "[redacted-reference]"
    combined_repr = f"{row!r} {result!r}".lower()
    assert "api_key" not in combined_repr
    assert "secret" not in combined_repr
    assert "token" not in combined_repr


def test_module_has_no_io_runtime_surface_or_float_public_logic() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "strategy_team_information_velocity_digest.py"
    )
    source = module_path.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live_trading",
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "signing",
        "advice",
        "trade",
        "execute",
        "client",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
        "sqlite3",
        "psycopg",
        "supabase",
        "private_key",
        "api_key",
        "secret",
        "token",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_import_roots = {
        "http",
        "json",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    forbidden_calls = {"connect", "execute", "float", "open", "print", "request"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_import_roots
