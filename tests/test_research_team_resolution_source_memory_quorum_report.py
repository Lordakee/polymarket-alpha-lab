from __future__ import annotations

import hashlib
import inspect
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_team_resolution_source_memory_quorum_report"
)


def _module() -> Any:
    return import_module(MODULE_NAME)


def _valid_report(module: Any) -> Any:
    return module.build_research_team_resolution_source_memory_quorum_report(
        observed_memory_count=Decimal("8"),
        agreeing_memory_count=Decimal("6"),
        independent_memory_count=Decimal("5"),
        stale_memory_count=Decimal("0"),
        conflict_memory_count=Decimal("0"),
        required_quorum_count=Decimal("4"),
        min_independent_memory_count=Decimal("3"),
        max_stale_memory_count=Decimal("1"),
        max_conflict_memory_count=Decimal("0"),
    )


def _digest_for(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _with_valid_digest(payload: dict[str, Any]) -> dict[str, Any]:
    updated = dict(payload)
    updated["derived_validation_digest"] = _digest_for(updated)
    return updated


def _public_strings(value: Any) -> tuple[str, ...]:
    strings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            strings.append(str(key))
            strings.extend(_public_strings(item))
    elif isinstance(value, list):
        for item in value:
            strings.extend(_public_strings(item))
    elif isinstance(value, str):
        strings.append(value)
    return tuple(strings)


def test_builds_frozen_report_with_required_flags_and_allowed_status() -> None:
    module = _module()

    report = _valid_report(module)

    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen is True
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.status == "pass"
    assert set(module.QUORUM_STATUSES) == {"pass", "watch", "block"}
    assert report.quorum_margin == Decimal("2")
    assert report.agreement_ratio == Decimal("0.750000")


def test_public_payload_is_deterministic_and_digest_validated() -> None:
    module = _module()
    report = _valid_report(module)

    payload_one = module.research_team_resolution_source_memory_quorum_report_payload(
        report,
    )
    payload_two = module.research_team_resolution_source_memory_quorum_report_payload(
        report,
    )
    public_json = module.research_team_resolution_source_memory_quorum_report_json(
        report,
    )

    assert payload_one == payload_two
    assert public_json == json.dumps(
        payload_one,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert payload_one["derived_validation_digest"] == _digest_for(payload_one)
    assert len(payload_one["derived_validation_digest"]) == 64
    assert module.research_team_resolution_source_memory_quorum_report_payload(
        payload_one,
    ) == payload_one

    tampered = dict(payload_one)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="digest"):
        module.research_team_resolution_source_memory_quorum_report_payload(tampered)


def test_public_payload_excludes_raw_identifiers_text_urls_and_live_surfaces() -> None:
    module = _module()
    payload = module.research_team_resolution_source_memory_quorum_report_payload(
        _valid_report(module),
    )

    forbidden_fragments = (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "auth",
        "sizing",
        "recommendation",
    )
    public_text = "\n".join(_public_strings(payload)).lower()
    for fragment in forbidden_fragments:
        assert fragment not in public_text

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["candidate_id"] = "raw-candidate-7"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_team_resolution_source_memory_quorum_report_payload(
            unsafe_key_payload,
        )

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["reason_codes"] = ["https://example.invalid/raw"]
    with pytest.raises(ValueError, match="unsafe"):
        module.research_team_resolution_source_memory_quorum_report_payload(
            unsafe_value_payload,
        )


def test_rejects_non_decimal_numerics_flag_downgrades_and_bad_statuses() -> None:
    module = _module()

    with pytest.raises(ValueError, match="Decimal"):
        module.build_research_team_resolution_source_memory_quorum_report(
            observed_memory_count=8,
            agreeing_memory_count=Decimal("6"),
            independent_memory_count=Decimal("5"),
            stale_memory_count=Decimal("0"),
            conflict_memory_count=Decimal("0"),
            required_quorum_count=Decimal("4"),
            min_independent_memory_count=Decimal("3"),
            max_stale_memory_count=Decimal("1"),
            max_conflict_memory_count=Decimal("0"),
        )

    with pytest.raises(ValueError, match="finite"):
        module.build_research_team_resolution_source_memory_quorum_report(
            observed_memory_count=Decimal("NaN"),
            agreeing_memory_count=Decimal("6"),
            independent_memory_count=Decimal("5"),
            stale_memory_count=Decimal("0"),
            conflict_memory_count=Decimal("0"),
            required_quorum_count=Decimal("4"),
            min_independent_memory_count=Decimal("3"),
            max_stale_memory_count=Decimal("1"),
            max_conflict_memory_count=Decimal("0"),
        )

    report = _valid_report(module)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="status"):
        replace(report, status="skip")

    payload = module.research_team_resolution_source_memory_quorum_report_payload(
        report,
    )
    bad_status_payload = dict(payload)
    bad_status_payload["status"] = "skip"
    with pytest.raises(ValueError, match="status"):
        module.research_team_resolution_source_memory_quorum_report_payload(
            _with_valid_digest(bad_status_payload),
        )

    bad_flag_payload = dict(payload)
    bad_flag_payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.research_team_resolution_source_memory_quorum_report_payload(
            bad_flag_payload,
        )


def test_status_transitions_are_limited_to_pass_watch_and_block() -> None:
    module = _module()

    passing = _valid_report(module)
    watching = module.build_research_team_resolution_source_memory_quorum_report(
        observed_memory_count=Decimal("8"),
        agreeing_memory_count=Decimal("4"),
        independent_memory_count=Decimal("4"),
        stale_memory_count=Decimal("0"),
        conflict_memory_count=Decimal("0"),
        required_quorum_count=Decimal("4"),
        min_independent_memory_count=Decimal("3"),
        max_stale_memory_count=Decimal("1"),
        max_conflict_memory_count=Decimal("0"),
    )
    blocked = module.build_research_team_resolution_source_memory_quorum_report(
        observed_memory_count=Decimal("8"),
        agreeing_memory_count=Decimal("6"),
        independent_memory_count=Decimal("5"),
        stale_memory_count=Decimal("0"),
        conflict_memory_count=Decimal("1"),
        required_quorum_count=Decimal("4"),
        min_independent_memory_count=Decimal("3"),
        max_stale_memory_count=Decimal("1"),
        max_conflict_memory_count=Decimal("0"),
    )

    statuses = {passing.status, watching.status, blocked.status}
    assert statuses == {"pass", "watch", "block"}
    assert statuses <= set(module.QUORUM_STATUSES)


def test_no_db_network_wallet_order_trade_sizing_or_recommendation_surfaces() -> None:
    module = _module()

    public_names = set(module.__all__)
    forbidden_public_name_fragments = (
        "database",
        "network",
        "wallet",
        "auth",
        "order",
        "trade",
        "sizing",
        "recommendation",
    )
    for fragment in forbidden_public_name_fragments:
        assert all(fragment not in name.lower() for name in public_names)

    source = inspect.getsource(module)
    forbidden_imports = (
        "requests",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "eth_account",
        "py_clob_client",
    )
    for forbidden_import in forbidden_imports:
        assert forbidden_import not in source
