from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import importlib
import inspect
import json
from typing import get_args, get_type_hints

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_event_settlement_risk_watchlist_report"
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _api():
    return importlib.import_module(MODULE_NAME)


def _input(
    event_label: str,
    *,
    resolution_clarity_score: Decimal = d("0.900000"),
    evidence_conflict_score: Decimal = d("0.050000"),
    oracle_delay_hours: Decimal = d("1.000000"),
    dispute_likelihood_score: Decimal = d("0.020000"),
    hours_to_expiry: Decimal = d("240.000000"),
):
    api = _api()
    return api.ResearchEventSettlementRiskWatchlistInput(
        event_label=event_label,
        resolution_clarity_score=resolution_clarity_score,
        evidence_conflict_score=evidence_conflict_score,
        oracle_delay_hours=oracle_delay_hours,
        dispute_likelihood_score=dispute_likelihood_score,
        hours_to_expiry=hours_to_expiry,
    )


def _config():
    return _api().ResearchEventSettlementRiskWatchlistConfig()


def _report(*inputs):
    return _api().build_research_event_settlement_risk_watchlist_report(
        inputs,
        config=_config(),
        generated_at=GENERATED_AT,
    )


def test_build_report_classifies_settlement_risk_rows_and_totals_deterministically() -> None:
    api = _api()
    block = _input(
        "event-block",
        resolution_clarity_score=d("0.300000"),
        evidence_conflict_score=d("0.700000"),
        oracle_delay_hours=d("80.000000"),
        dispute_likelihood_score=d("0.500000"),
        hours_to_expiry=d("6.000000"),
    )
    watch = _input(
        "event-watch",
        resolution_clarity_score=d("0.650000"),
        evidence_conflict_score=d("0.200000"),
        oracle_delay_hours=d("4.000000"),
        dispute_likelihood_score=d("0.100000"),
        hours_to_expiry=d("24.000000"),
    )
    passed = _input("event-pass")

    report = _report(watch, passed, block)
    repeated = _report(block, passed, watch)

    assert report.status == "block"
    assert report.reason_codes == (
        "low_resolution_clarity_present",
        "evidence_conflict_present",
        "oracle_delay_present",
        "dispute_likelihood_present",
        "expiry_proximity_present",
    )
    assert report.event_count == d("3.000000")
    assert report.pass_event_count == d("1.000000")
    assert report.watch_event_count == d("1.000000")
    assert report.block_event_count == d("1.000000")
    assert report.flagged_event_count == d("2.000000")
    assert report.flagged_event_ratio == d("0.666667")
    assert report.max_oracle_delay_hours == d("80.000000")
    assert report.min_hours_to_expiry == d("6.000000")
    assert report.rows == repeated.rows
    assert report.derived_validation_digest == repeated.derived_validation_digest

    assert tuple(row.event_label for row in report.rows) == (
        "event-block",
        "event-watch",
        "event-pass",
    )
    block_row = report.rows[0]
    assert block_row.status == "block"
    assert block_row.risk_flag_count == d("5.000000")
    assert block_row.low_resolution_clarity is True
    assert block_row.evidence_conflict is True
    assert block_row.oracle_delay is True
    assert block_row.dispute_likelihood is True
    assert block_row.expiry_proximity is True
    assert block_row.reason_codes == (
        "low_resolution_clarity",
        "evidence_conflict",
        "oracle_delay",
        "dispute_likelihood",
        "expiry_proximity",
    )

    watch_row = report.rows[1]
    assert watch_row.status == "watch"
    assert watch_row.reason_codes == (
        "low_resolution_clarity",
        "expiry_proximity",
    )

    pass_row = report.rows[2]
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == ("settlement_risk_pass",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = api.research_event_settlement_risk_watchlist_report_to_payload(report)
    json.dumps(payload, sort_keys=True)
    assert _float_paths(payload) == ()
    assert payload == api.research_event_settlement_risk_watchlist_report_to_payload(repeated)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["event_count"] == "3.000000"
    assert payload["flagged_event_ratio"] == "0.666667"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True


def test_empty_report_passes_with_decimal_zeroes_and_stable_digest() -> None:
    report = _report()
    repeated = _report()

    assert report.status == "pass"
    assert report.reason_codes == ("settlement_risk_pass",)
    assert report.event_count == d("0.000000")
    assert report.flagged_event_count == d("0.000000")
    assert report.flagged_event_ratio == d("0.000000")
    assert report.max_oracle_delay_hours == d("0.000000")
    assert report.min_hours_to_expiry == d("0.000000")
    assert report.rows == ()
    assert report.derived_validation_digest == repeated.derived_validation_digest


def test_public_dataclasses_are_frozen_decimal_only_and_flags_are_hard_required() -> None:
    api = _api()
    contract_classes = (
        api.ResearchEventSettlementRiskWatchlistConfig,
        api.ResearchEventSettlementRiskWatchlistInput,
        api.ResearchEventSettlementRiskWatchlistRow,
        api.ResearchEventSettlementRiskWatchlistReport,
    )
    for contract_class in contract_classes:
        assert is_dataclass(contract_class)
        assert contract_class.__dataclass_params__.frozen is True
        defaults = {field.name: field.default for field in fields(contract_class)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True
        for field_name, hint in get_type_hints(contract_class).items():
            if field_name in {"paper_only", "report_only", "readonly"}:
                continue
            assert not _type_uses_float(hint)

    input_row = _input("event-frozen")
    with pytest.raises(FrozenInstanceError):
        input_row.event_label = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="resolution_clarity_watch_threshold"):
        api.ResearchEventSettlementRiskWatchlistConfig(
            resolution_clarity_watch_threshold=0.7,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="oracle_delay_hours"):
        _input("event-float", oracle_delay_hours=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="hours_to_expiry"):
        _input("event-int", hours_to_expiry=24)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        api.build_research_event_settlement_risk_watchlist_report(
            (),
            config=_config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="report_only"):
        replace(input_row, report_only=False)


def test_public_surface_rejects_raw_references_sensitive_terms_and_bad_digest() -> None:
    api = _api()

    with pytest.raises(ValueError, match="event_label"):
        _input("0x" + "a" * 64)
    with pytest.raises(ValueError, match="event_label"):
        _input("market_id:123")
    with pytest.raises(ValueError, match="event_label"):
        _input("source_id:abc")
    with pytest.raises(ValueError, match="event_label"):
        _input(_join_parts("wal", "let") + "-review")

    report = _report(_input("event-digest"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.ResearchEventSettlementRiskWatchlistReport(
            generated_at=report.generated_at,
            config_version=report.config_version,
            status=report.status,
            reason_codes=report.reason_codes,
            event_count=report.event_count,
            pass_event_count=report.pass_event_count,
            watch_event_count=report.watch_event_count,
            block_event_count=report.block_event_count,
            flagged_event_count=report.flagged_event_count,
            low_resolution_clarity_event_count=report.low_resolution_clarity_event_count,
            evidence_conflict_event_count=report.evidence_conflict_event_count,
            oracle_delay_event_count=report.oracle_delay_event_count,
            dispute_likelihood_event_count=report.dispute_likelihood_event_count,
            expiry_proximity_event_count=report.expiry_proximity_event_count,
            flagged_event_ratio=report.flagged_event_ratio,
            max_oracle_delay_hours=report.max_oracle_delay_hours,
            min_hours_to_expiry=report.min_hours_to_expiry,
            rows=report.rows,
            derived_validation_digest="not-the-digest",
        )


def test_module_is_pure_report_only_without_db_network_or_action_surface() -> None:
    api = _api()
    public_names = tuple(api.__all__)
    source = inspect.getsource(api).lower()
    tree = ast.parse(source)

    assert api.__all__ == (
        "DEFAULT_RESEARCH_EVENT_SETTLEMENT_RISK_WATCHLIST_REPORT_CONFIG_VERSION",
        "ResearchEventSettlementRiskWatchlistConfig",
        "ResearchEventSettlementRiskWatchlistInput",
        "ResearchEventSettlementRiskWatchlistReport",
        "ResearchEventSettlementRiskWatchlistRow",
        "build_research_event_settlement_risk_watchlist_report",
        "research_event_settlement_risk_watchlist_report_to_payload",
    )
    assert api.SETTLEMENT_RISK_STATUSES == ("pass", "watch", "block")
    assert "float(" not in source
    for banned in (
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("sig", "ning"),
        _join_parts("ad", "vice"),
    ):
        assert banned not in source
        assert all(banned not in name.lower() for name in public_names)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "buy",
                "connect",
                "execute",
                "executemany",
                "open",
                "patch",
                "place",
                "post",
                "put",
                "request",
                "sell",
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


def _float_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if isinstance(value, float):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_float_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_float_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()


def _type_uses_float(value: object) -> bool:
    if value is float:
        return True
    return any(_type_uses_float(item) for item in get_args(value))


def _join_parts(*parts: str) -> str:
    return "".join(parts)
