from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 2, 16, 0, tzinfo=UTC)
ACKNOWLEDGED_AT = datetime(2026, 7, 2, 14, 0, tzinfo=UTC)
UPDATED_AT = datetime(2026, 7, 2, 15, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_source_ack_recheck_sla_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object):
    module = api()
    values = {
        "overdue_recheck_seconds": d("1800.000000"),
        "repeated_miss_threshold_count": d("2"),
    }
    values.update(overrides)
    return module.ResearchPacketSourceAckRecheckSlaConfig(**values)


def _ack(
    acknowledgement_id: str,
    *,
    packet_id: str = "packet-json",
    source_id: str = "source-json",
    team_id: str = "politics",
    category_id: str = "politics",
    owner_id: str | None = "owner-alpha",
    acknowledged_at: datetime = ACKNOWLEDGED_AT,
    acknowledged_value: str = "yes",
    rechecked_at: datetime | None = None,
):
    module = api()
    return module.ResearchPacketSourceAckRecheckSlaAcknowledgement(
        acknowledgement_id=acknowledgement_id,
        packet_id=packet_id,
        source_id=source_id,
        team_id=team_id,
        category_id=category_id,
        owner_id=owner_id,
        acknowledged_at=acknowledged_at,
        acknowledged_value=acknowledged_value,
        rechecked_at=rechecked_at,
    )


def _update(
    update_id: str,
    *,
    packet_id: str,
    source_id: str,
    source_kind: str,
    updated_at: datetime,
    updated_value: str | None,
):
    module = api()
    return module.ResearchPacketSourceAckRecheckSlaUpdate(
        update_id=update_id,
        packet_id=packet_id,
        source_id=source_id,
        source_kind=source_kind,
        updated_at=updated_at,
        updated_value=updated_value,
    )


def _build_report(*acks, updates=(), config=None):
    module = api()
    return module.build_research_packet_source_ack_recheck_sla_report(
        acks,
        updates,
        config=_config() if config is None else config,
        generated_at=GENERATED_AT,
    )


def test_sla_report_flags_overdue_missing_owner_contradiction_and_repeat_misses() -> None:
    report = _build_report(
        _ack(
            "ack-alpha",
            packet_id="packet-alpha",
            source_id="source-alpha",
            owner_id=None,
            acknowledged_value="yes",
        ),
        _ack(
            "ack-beta",
            packet_id="packet-beta",
            source_id="source-beta",
            acknowledged_at=ACKNOWLEDGED_AT + timedelta(minutes=5),
            acknowledged_value="no",
        ),
        _ack(
            "ack-clear",
            packet_id="packet-clear",
            source_id="source-clear",
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            acknowledged_at=GENERATED_AT - timedelta(minutes=10),
            acknowledged_value="yes",
        ),
        updates=(
            _update(
                "update-beta",
                packet_id="packet-beta",
                source_id="source-beta",
                source_kind="proxy",
                updated_at=UPDATED_AT + timedelta(minutes=5),
                updated_value="yes",
            ),
            _update(
                "update-alpha",
                packet_id="packet-alpha",
                source_id="source-alpha",
                source_kind="official",
                updated_at=UPDATED_AT,
                updated_value="no",
            ),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "blocked"
    assert report.reason_codes == (
        "source_ack_recheck_overdue",
        "source_ack_missing_owner",
        "source_ack_contradiction_after_ack",
        "source_ack_repeated_team_category_miss",
    )
    assert report.acknowledgement_count == d("3")
    assert report.update_count == d("2")
    assert report.pass_count == d("1")
    assert report.watch_count == d("0")
    assert report.blocked_count == d("2")
    assert report.overdue_recheck_count == d("2")
    assert report.missing_owner_count == d("1")
    assert report.contradiction_after_ack_count == d("2")
    assert report.repeated_team_category_miss_count == d("1")
    assert report.issue_ratio == d("0.666667")
    assert report.max_acknowledgement_age_seconds == d("7200.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.acknowledgement_id for row in report.rows) == (
        "ack-alpha",
        "ack-beta",
        "ack-clear",
    )
    alpha = report.rows[0]
    assert alpha.status == "blocked"
    assert alpha.latest_update_id == "update-alpha"
    assert alpha.latest_update_source_kind == "official"
    assert alpha.acknowledgement_age_seconds == d("7200.000000")
    assert alpha.recheck_lag_seconds == d("3600.000000")
    assert alpha.later_update_count == d("1")
    assert alpha.overdue_recheck is True
    assert alpha.missing_owner is True
    assert alpha.contradiction_after_ack is True
    assert alpha.repeated_team_category_miss is True
    assert alpha.reason_codes == (
        "source_ack_recheck_overdue",
        "source_ack_missing_owner",
        "source_ack_contradiction_after_ack",
        "source_ack_repeated_team_category_miss",
    )

    beta = report.rows[1]
    assert beta.status == "blocked"
    assert beta.latest_update_source_kind == "proxy"
    assert beta.acknowledgement_age_seconds == d("6900.000000")
    assert beta.recheck_lag_seconds == d("3600.000000")
    assert beta.reason_codes == (
        "source_ack_recheck_overdue",
        "source_ack_contradiction_after_ack",
        "source_ack_repeated_team_category_miss",
    )

    clear = report.rows[2]
    assert clear.status == "pass"
    assert clear.recheck_lag_seconds == d("0.000000")
    assert clear.reason_codes == ("source_ack_recheck_sla_clear",)

    assert report.team_category_rows == (
        api().ResearchPacketSourceAckRecheckSlaTeamCategoryRow(
            team_id="politics",
            category_id="politics",
            missed_acknowledgement_count=d("2"),
            total_acknowledgement_count=d("2"),
            miss_ratio=d("1.000000"),
            reason_codes=("source_ack_repeated_team_category_miss",),
        ),
    )


def test_rechecked_updates_clear_report_and_sort_deterministically() -> None:
    module = api()
    config = module.ResearchPacketSourceAckRecheckSlaConfig(
        overdue_recheck_seconds=d("99999.000000"),
    )
    ack_a = _ack(
        "ack-a",
        packet_id="packet-a",
        source_id="source-a",
        team_id="sports_other",
        category_id="sports.other",
        acknowledged_at=ACKNOWLEDGED_AT,
        rechecked_at=UPDATED_AT + timedelta(minutes=10),
    )
    ack_b = _ack(
        "ack-b",
        packet_id="packet-b",
        source_id="source-b",
        team_id="crypto_btc",
        category_id="finance.crypto.btc",
        acknowledged_at=ACKNOWLEDGED_AT + timedelta(minutes=1),
        rechecked_at=UPDATED_AT + timedelta(minutes=10),
    )
    update_a = _update(
        "update-a",
        packet_id="packet-a",
        source_id="source-a",
        source_kind="official",
        updated_at=UPDATED_AT,
        updated_value="no",
    )
    update_b = _update(
        "update-b",
        packet_id="packet-b",
        source_id="source-b",
        source_kind="proxy",
        updated_at=UPDATED_AT + timedelta(minutes=1),
        updated_value="no",
    )

    first = module.build_research_packet_source_ack_recheck_sla_report(
        (ack_a, ack_b),
        (update_b, update_a),
        config=config,
        generated_at=GENERATED_AT,
    )
    second = module.build_research_packet_source_ack_recheck_sla_report(
        (ack_b, ack_a),
        (update_a, update_b),
        config=config,
        generated_at=GENERATED_AT,
    )

    assert first == second
    assert first.status == "clear"
    assert first.reason_codes == ("source_ack_recheck_sla_clear",)
    assert first.issue_ratio == d("0.000000")
    assert tuple(row.acknowledgement_id for row in first.rows) == ("ack-b", "ack-a")
    assert all(row.status == "pass" for row in first.rows)
    assert all(row.reason_codes == ("source_ack_recheck_sla_clear",) for row in first.rows)


def test_empty_sla_report_returns_readonly_decimal_payload() -> None:
    report = _build_report()

    assert report.status == "empty"
    assert report.reason_codes == ("source_ack_recheck_sla_empty",)
    assert report.acknowledgement_count == d("0")
    assert report.update_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.blocked_count == d("0")
    assert report.overdue_recheck_count == d("0")
    assert report.missing_owner_count == d("0")
    assert report.contradiction_after_ack_count == d("0")
    assert report.repeated_team_category_miss_count == d("0")
    assert report.issue_ratio == d("0.000000")
    assert report.max_acknowledgement_age_seconds == d("0.000000")
    assert report.rows == ()
    assert report.team_category_rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_datetimes_decimals_flags_and_uniqueness_are_validated() -> None:
    module = api()
    local_ack_at = datetime(2026, 7, 2, 10, 0, tzinfo=timezone(timedelta(hours=-4)))
    report = _build_report(
        _ack("ack-tz", acknowledged_at=local_ack_at),
        config=module.ResearchPacketSourceAckRecheckSlaConfig(
            overdue_recheck_seconds=d("99999.000000"),
        ),
    )

    assert report.rows[0].acknowledged_at == ACKNOWLEDGED_AT
    assert type(report.acknowledgement_count) is Decimal
    assert type(report.issue_ratio) is Decimal
    assert type(report.rows[0].acknowledgement_age_seconds) is Decimal
    assert type(report.rows[0].recheck_lag_seconds) is Decimal
    assert type(report.rows[0].later_update_count) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="overdue_recheck_seconds must be a Decimal"):
        module.ResearchPacketSourceAckRecheckSlaConfig(
            overdue_recheck_seconds=_DecimalSubclass("60.000000"),
        )
    with pytest.raises(ValueError, match="repeated_miss_threshold_count must be a Decimal"):
        module.ResearchPacketSourceAckRecheckSlaConfig(
            repeated_miss_threshold_count=_DecimalSubclass("2"),
        )
    with pytest.raises(ValueError, match="acknowledged_at must be timezone-aware"):
        _ack("ack-naive", acknowledged_at=datetime(2026, 7, 2, 14, 0))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_packet_source_ack_recheck_sla_report(
            (_ack("ack-valid"),),
            (),
            config=module.ResearchPacketSourceAckRecheckSlaConfig(),
            generated_at=datetime(2026, 7, 2, 16, 0),
        )
    with pytest.raises(ValueError, match="acknowledged_at must be <= generated_at"):
        _build_report(
            _ack(
                "ack-future",
                acknowledged_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="update_id values must be unique"):
        _build_report(
            _ack("ack-update-dup"),
            updates=(
                _update(
                    "update-dup",
                    packet_id="packet-json",
                    source_id="source-json",
                    source_kind="official",
                    updated_at=UPDATED_AT,
                    updated_value="no",
                ),
                _update(
                    "update-dup",
                    packet_id="packet-json",
                    source_id="source-json",
                    source_kind="proxy",
                    updated_at=UPDATED_AT + timedelta(minutes=1),
                    updated_value="no",
                ),
            ),
        )
    with pytest.raises(ValueError, match="acknowledgement_id values must be unique"):
        _build_report(_ack("ack-dup"), _ack("ack-dup", packet_id="packet-other"))
    with pytest.raises(ValueError, match="category_id must match team_id"):
        _ack(
            "ack-category",
            team_id="crypto_btc",
            category_id="politics",
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(_ack("ack-flag"), paper_only=False)


def test_payload_helper_is_json_ready_and_contains_no_float_values() -> None:
    module = api()
    report = _build_report(
        _ack("ack-json", owner_id=None),
        updates=(
            _update(
                "update-json",
                packet_id="packet-json",
                source_id="source-json",
                source_kind="official",
                updated_at=UPDATED_AT,
                updated_value="no",
            ),
        ),
    )

    payload = module.research_packet_source_ack_recheck_sla_report_to_payload(report)

    assert payload["generated_at"] == "2026-07-02T16:00:00+00:00"
    assert payload["acknowledgement_count"] == "1"
    assert payload["issue_ratio"] == "1.000000"
    assert payload["max_acknowledgement_age_seconds"] == "7200.000000"
    assert payload["rows"][0]["recheck_lag_seconds"] == "3600.000000"
    assert payload["rows"][0]["paper_only"] is True
    assert _float_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_public_api_and_module_scope_stay_pure_in_memory_report_only() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_PACKET_SOURCE_ACK_RECHECK_SLA_CONFIG_VERSION",
        "ResearchPacketSourceAckRecheckSlaAcknowledgement",
        "ResearchPacketSourceAckRecheckSlaConfig",
        "ResearchPacketSourceAckRecheckSlaReport",
        "ResearchPacketSourceAckRecheckSlaRow",
        "ResearchPacketSourceAckRecheckSlaTeamCategoryRow",
        "ResearchPacketSourceAckRecheckSlaUpdate",
        "build_research_packet_source_ack_recheck_sla_report",
        "research_packet_source_ack_recheck_sla_report_to_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        "market_slug",
        "question",
        "wallet",
        "account",
        "broker",
        "order",
        "submit",
        "cancel",
        "signing",
        "advice",
        "private_key",
        "credential",
    ):
        assert forbidden not in lowered

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

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
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
        for fragment in forbidden_import_fragments
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
