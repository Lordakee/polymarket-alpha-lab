from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_market_close_information_sla_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def _config(**overrides: object):
    module = api()
    values = {
        "official_update_sla_seconds": d("1800.000000"),
        "independent_confirmation_sla_seconds": d("3600.000000"),
        "close_window_hours": d("1.000000"),
    }
    values.update(overrides)
    return module.ResearchPacketMarketCloseInformationSlaV2Config(**values)


def _observation(
    packet_id: str,
    *,
    market_id: str | None = None,
    team_id: str = "politics",
    category_id: str = "politics",
    market_close_at: datetime = GENERATED_AT + timedelta(hours=2),
    official_update_at: datetime | None = GENERATED_AT - timedelta(minutes=10),
    independent_confirmation_at: datetime | None = GENERATED_AT - timedelta(minutes=20),
    unresolved_contradiction: bool = False,
    resolution_source_ready: bool = True,
):
    module = api()
    return module.ResearchPacketMarketCloseInformationSlaV2Observation(
        packet_id=packet_id,
        market_id=market_id or f"market_{packet_id}",
        team_id=team_id,
        category_id=category_id,
        market_close_at=market_close_at,
        official_update_at=official_update_at,
        independent_confirmation_at=independent_confirmation_at,
        unresolved_contradiction=unresolved_contradiction,
        resolution_source_ready=resolution_source_ready,
    )


def _build_report(*observations, config=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_packet_market_close_information_sla_v2_report(
        observations,
        config=_config() if config is None else config,
        generated_at=generated_at,
    )


def test_information_sla_flags_collection_gaps_near_close_with_priority() -> None:
    module = api()
    report = _build_report(
        _observation(
            "ready_crypto",
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            market_close_at=GENERATED_AT + timedelta(hours=2),
            official_update_at=GENERATED_AT - timedelta(minutes=5),
            independent_confirmation_at=GENERATED_AT - timedelta(minutes=5),
        ),
        _observation(
            "politics_missing",
            market_close_at=GENERATED_AT + timedelta(minutes=30),
            official_update_at=None,
            independent_confirmation_at=None,
            unresolved_contradiction=True,
            resolution_source_ready=False,
        ),
        _observation(
            "politics_stale",
            market_id="market_politics_stale",
            market_close_at=GENERATED_AT + timedelta(hours=3),
            official_update_at=GENERATED_AT - timedelta(seconds=3601),
            independent_confirmation_at=GENERATED_AT - timedelta(seconds=7201),
        ),
    )

    assert isinstance(report, module.ResearchPacketMarketCloseInformationSlaV2Report)
    assert report.generated_at == GENERATED_AT
    assert (
        report.config_version
        == module.DEFAULT_RESEARCH_PACKET_MARKET_CLOSE_INFORMATION_SLA_V2_CONFIG_VERSION
    )
    assert report.sla_status == "blocked"
    assert report.row_count == d("3.000000")
    assert report.flagged_row_count == d("2.000000")
    assert report.ready_row_count == d("1.000000")
    assert report.watch_row_count == d("1.000000")
    assert report.blocked_row_count == d("1.000000")
    assert report.official_update_missing_count == d("1.000000")
    assert report.official_update_stale_count == d("1.000000")
    assert report.independent_confirmation_missing_count == d("1.000000")
    assert report.independent_confirmation_stale_count == d("1.000000")
    assert report.unresolved_contradiction_count == d("1.000000")
    assert report.resolution_source_not_ready_count == d("1.000000")
    assert report.close_window_row_count == d("1.000000")
    assert report.p0_priority_count == d("1.000000")
    assert report.p1_priority_count == d("0.000000")
    assert report.p2_priority_count == d("1.000000")
    assert report.p3_priority_count == d("1.000000")
    assert report.flagged_ratio == d("0.666667")
    assert report.max_official_update_age_seconds == d("3601.000000")
    assert report.max_independent_confirmation_age_seconds == d("7201.000000")
    assert report.minimum_close_hours == d("0.500000")
    assert report.reason_codes == (
        "market_close_information_official_update_missing",
        "market_close_information_official_update_stale",
        "market_close_information_independent_confirmation_missing",
        "market_close_information_independent_confirmation_stale",
        "market_close_information_unresolved_contradiction",
        "market_close_information_resolution_source_not_ready",
        "market_close_information_close_window_active",
    )
    assert tuple(row.reason_code for row in report.reason_code_counts) == report.reason_codes
    assert tuple(row.count for row in report.reason_code_counts) == (
        d("1.000000"),
        d("1.000000"),
        d("1.000000"),
        d("1.000000"),
        d("1.000000"),
        d("1.000000"),
        d("1.000000"),
    )
    assert tuple(row.packet_id for row in report.rows) == (
        "politics_missing",
        "politics_stale",
        "ready_crypto",
    )

    missing = report.rows[0]
    assert missing == module.ResearchPacketMarketCloseInformationSlaV2Row(
        packet_id="politics_missing",
        market_id="market_politics_missing",
        team_id="politics",
        category_id="politics",
        market_close_at=GENERATED_AT + timedelta(minutes=30),
        official_update_at=None,
        independent_confirmation_at=None,
        official_update_age_seconds=None,
        independent_confirmation_age_seconds=None,
        close_hours=d("0.500000"),
        close_window_active=True,
        unresolved_contradiction=True,
        resolution_source_ready=False,
        sla_status="blocked",
        escalation_priority="p0",
        reason_codes=(
            "market_close_information_official_update_missing",
            "market_close_information_independent_confirmation_missing",
            "market_close_information_unresolved_contradiction",
            "market_close_information_resolution_source_not_ready",
            "market_close_information_close_window_active",
        ),
        derived_validation_digest=missing.derived_validation_digest,
    )
    assert missing.derived_validation_digest
    assert report.derived_validation_digest
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    stale = report.rows[1]
    assert stale.sla_status == "watch"
    assert stale.escalation_priority == "p2"
    assert stale.official_update_age_seconds == d("3601.000000")
    assert stale.independent_confirmation_age_seconds == d("7201.000000")
    assert stale.close_hours == d("3.000000")
    assert stale.reason_codes == (
        "market_close_information_official_update_stale",
        "market_close_information_independent_confirmation_stale",
    )


def test_information_sla_payload_and_digest_are_deterministic_and_json_ready() -> None:
    module = api()
    generated_at = datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    config = _config(close_window_hours=d("2.000000"))
    first = module.build_research_packet_market_close_information_sla_v2_report(
        (
            _observation(
                "packet_b",
                team_id="sports_other",
                category_id="sports.other",
                market_close_at=datetime(2026, 7, 2, 10, 0, tzinfo=timezone(timedelta(hours=-4))),
                official_update_at=datetime(2026, 7, 2, 7, 55, tzinfo=timezone(timedelta(hours=-4))),
                independent_confirmation_at=datetime(
                    2026,
                    7,
                    2,
                    7,
                    50,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
            ),
            _observation(
                "packet_a",
                market_close_at=GENERATED_AT + timedelta(hours=1),
            ),
        ),
        config=config,
        generated_at=generated_at,
    )
    second = module.build_research_packet_market_close_information_sla_v2_report(
        (
            _observation(
                "packet_a",
                market_close_at=GENERATED_AT + timedelta(hours=1),
            ),
            _observation(
                "packet_b",
                team_id="sports_other",
                category_id="sports.other",
                market_close_at=datetime(2026, 7, 2, 10, 0, tzinfo=timezone(timedelta(hours=-4))),
                official_update_at=datetime(2026, 7, 2, 7, 55, tzinfo=timezone(timedelta(hours=-4))),
                independent_confirmation_at=datetime(
                    2026,
                    7,
                    2,
                    7,
                    50,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
            ),
        ),
        config=config,
        generated_at=generated_at,
    )

    assert first == second
    assert len(first.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in first.derived_validation_digest)
    assert tuple(row.packet_id for row in first.rows) == ("packet_a", "packet_b")

    rendered = module.research_packet_market_close_information_sla_v2_report_to_payload(first)

    assert rendered["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert rendered["row_count"] == "2.000000"
    assert rendered["flagged_ratio"] == "0.000000"
    assert rendered["minimum_close_hours"] == "1.000000"
    assert rendered["derived_validation_digest"] == first.derived_validation_digest
    assert rendered["rows"][1]["market_close_at"] == "2026-07-02T14:00:00+00:00"
    assert rendered["rows"][1]["official_update_age_seconds"] == "300.000000"
    assert rendered["rows"][1]["independent_confirmation_age_seconds"] == "600.000000"
    assert rendered["rows"][1]["close_hours"] == "2.000000"
    assert _float_paths(rendered) == ()
    json.dumps(rendered, sort_keys=True)


def test_information_sla_validates_decimal_only_datetimes_flags_and_digests() -> None:
    module = api()

    with pytest.raises(ValueError, match="config_version"):
        module.ResearchPacketMarketCloseInformationSlaV2Config(
            config_version=_StringSubclass(
                module.DEFAULT_RESEARCH_PACKET_MARKET_CLOSE_INFORMATION_SLA_V2_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="official_update_sla_seconds"):
        module.ResearchPacketMarketCloseInformationSlaV2Config(
            official_update_sla_seconds=1800,
        )
    with pytest.raises(ValueError, match="independent_confirmation_sla_seconds"):
        module.ResearchPacketMarketCloseInformationSlaV2Config(
            independent_confirmation_sla_seconds=_DecimalSubclass("3600.000000"),
        )
    with pytest.raises(ValueError, match="market_close_at"):
        _observation("naive_close", market_close_at=datetime(2026, 7, 2, 12, 30))
    with pytest.raises(ValueError, match="generated_at"):
        _build_report(_observation("valid"), generated_at=datetime(2026, 7, 2, 12, 0))
    with pytest.raises(ValueError, match="official_update_at"):
        _build_report(
            _observation(
                "future_official",
                official_update_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="market_close_at"):
        _build_report(
            _observation(
                "past_close",
                market_close_at=GENERATED_AT - timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="category_id"):
        _observation(
            "category_mismatch",
            team_id="crypto_btc",
            category_id="politics",
        )
    with pytest.raises(ValueError, match="packet_id"):
        _observation(_join_parts("wal", "let", "_packet"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(_observation("not_paper"), paper_only=False)

    report = _build_report(_observation("ready_packet"))
    with pytest.raises(FrozenInstanceError):
        report.rows[0].sla_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report.rows[0], derived_validation_digest="bad")

    for item in (report, report.rows[0], report.reason_code_counts[0]):
        for field in fields(item):
            value = getattr(item, field.name)
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_seconds")
                or field.name.endswith("_hours")
            ) and value is not None:
                assert type(value) is Decimal


def test_information_sla_public_api_and_module_scope_stay_pure_phase_one() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_PACKET_MARKET_CLOSE_INFORMATION_SLA_V2_CONFIG_VERSION",
        "ResearchPacketMarketCloseInformationSlaV2Config",
        "ResearchPacketMarketCloseInformationSlaV2Observation",
        "ResearchPacketMarketCloseInformationSlaV2ReasonCount",
        "ResearchPacketMarketCloseInformationSlaV2Report",
        "ResearchPacketMarketCloseInformationSlaV2Row",
        "build_research_packet_market_close_information_sla_v2_report",
        "research_packet_market_close_information_sla_v2_report_to_payload",
    )
    for exported_name in module.__all__:
        exported_value = getattr(module, exported_name)
        if isinstance(exported_value, type):
            assert is_dataclass(exported_value)

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for fragment in (
        "float(",
        ".total_seconds(",
        _join_parts("li", "ve"),
        _join_parts("tra", "ding"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("sig", "ning"),
        _join_parts("ad", "vice"),
        _join_parts("pri", "vate"),
        _join_parts("cre", "dential"),
    ):
        assert fragment not in lowered

    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
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

    blocked_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in blocked_import_fragments
    )


def _float_paths(value: object, prefix: str = "") -> tuple[str, ...]:
    if isinstance(value, float):
        return (prefix or "<root>",)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, nested in value.items():
            child = str(key) if not prefix else f"{prefix}.{key}"
            paths.extend(_float_paths(nested, child))
        return tuple(paths)
    if isinstance(value, list | tuple):
        paths = []
        for index, nested in enumerate(value):
            child = str(index) if not prefix else f"{prefix}.{index}"
            paths.extend(_float_paths(nested, child))
        return tuple(paths)
    return ()
