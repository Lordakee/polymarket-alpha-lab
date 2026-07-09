from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_NAME = (
    "polymarket_alpha_lab.research_event_resolution_authority_signal_decay_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_resolution_authority_signal_decay_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _StrSubclass(str):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "watch_signal_age_seconds": d("3600.000000"),
        "block_signal_age_seconds": d("14400.000000"),
        "watch_signal_score_threshold": d("0.500000"),
        "block_signal_score_threshold": d("0.250000"),
        "blocking_conflict_threshold": d("0.750000"),
    }
    values.update(overrides)
    return module.ResearchEventResolutionAuthoritySignalDecayConfig(**values)


def observation(
    raw_candidate_ref: str,
    *,
    authority_family: str = "official_resolution_authority",
    observed_seconds_ago: int = 600,
    authority_observed_at: datetime | None = None,
    authority_score: Decimal = d("0.950000"),
    source_consensus_score: Decimal = d("0.950000"),
    contradictory_resolution_score: Decimal = d("0.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    if authority_observed_at is None:
        authority_observed_at = GENERATED_AT - timedelta(seconds=observed_seconds_ago)
    return module.ResearchEventResolutionAuthoritySignalObservation(
        raw_candidate_ref=raw_candidate_ref,
        authority_family=authority_family,
        authority_observed_at=authority_observed_at,
        authority_score=authority_score,
        source_consensus_score=source_consensus_score,
        contradictory_resolution_score=contradictory_resolution_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_event_resolution_authority_signal_decay_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def test_empty_report_is_readonly_decimal_digest_and_json_safe() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchEventResolutionAuthoritySignalDecayReport
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen is True
    assert report.generated_at == GENERATED_AT
    assert report.status == "pass"
    assert report.signal_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.average_authority_signal_score is None
    assert report.max_signal_age_seconds == d("0.000000")
    assert report.reason_codes == ("event_resolution_authority_signal_decay_empty",)
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    payload = module.research_event_resolution_authority_signal_decay_report_payload(
        report,
    )
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["signal_count"] == "0.000000"
    assert payload["average_authority_signal_score"] is None
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    module.validate_research_event_resolution_authority_signal_decay_public_payload(
        payload,
    )
    json.dumps(payload, sort_keys=True)
    _assert_no_public_float_or_int(payload)


def test_status_rollups_reason_codes_rows_and_redactions_are_deterministic() -> None:
    module = api()
    report = build_report(
        observation("candidate-pass-alpha", observed_seconds_ago=600),
        observation("candidate-watch-beta", observed_seconds_ago=7200),
        observation(
            "candidate-block-gamma",
            observed_seconds_ago=18000,
            contradictory_resolution_score=d("0.800000"),
        ),
    )

    assert report.status == "block"
    assert report.reason_codes == (
        "event_resolution_authority_signal_watch_decay",
        "event_resolution_authority_signal_block_decay",
        "event_resolution_authority_signal_conflict",
    )
    assert report.signal_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_authority_signal_score == d("0.438715")
    assert report.max_signal_age_seconds == d("18000.000000")

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.authority_family for row in report.rows) == (
        "official_resolution_authority",
        "official_resolution_authority",
        "official_resolution_authority",
    )
    assert tuple(row.signal_age_seconds for row in report.rows) == (
        d("18000.000000"),
        d("7200.000000"),
        d("600.000000"),
    )
    assert tuple(row.decay_score for row in report.rows) == (
        d("0.000000"),
        d("0.500000"),
        d("0.958333"),
    )
    assert tuple(row.authority_signal_score for row in report.rows) == (
        d("0.000000"),
        d("0.451250"),
        d("0.864896"),
    )
    assert all(row.redacted_candidate_ref.startswith("sha256:") for row in report.rows)

    payload = module.research_event_resolution_authority_signal_decay_report_payload(
        report,
    )
    payload_text = json.dumps(payload, sort_keys=True)
    assert "candidate-pass-alpha" not in payload_text
    assert "candidate-watch-beta" not in payload_text
    assert "candidate-block-gamma" not in payload_text
    _assert_no_forbidden_public_surface(payload)


def test_dataclasses_are_frozen_exact_decimal_only_and_flags_are_hard() -> None:
    module = api()
    report = build_report(
        observation("candidate-pass-alpha"),
        observation("candidate-watch-beta", observed_seconds_ago=7200),
    )

    for cls in (
        module.ResearchEventResolutionAuthoritySignalDecayConfig,
        module.ResearchEventResolutionAuthoritySignalObservation,
        module.ResearchEventResolutionAuthoritySignalDecayRow,
        module.ResearchEventResolutionAuthoritySignalDecayReport,
    ):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True

    _assert_decimal_public_fields(report)
    for row in report.rows:
        _assert_decimal_public_fields(row)

    with pytest.raises(ValueError, match="watch_signal_age_seconds"):
        config(watch_signal_age_seconds=3600)
    with pytest.raises(ValueError, match="block_signal_age_seconds"):
        config(block_signal_age_seconds=_DecimalSubclass("14400.000000"))
    with pytest.raises(ValueError, match="authority_score"):
        observation("candidate-int-score", authority_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_consensus_score"):
        observation("candidate-subclass-score", source_consensus_score=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="paper_only"):
        observation("candidate-flag-case", paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="ready")
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status=_StrSubclass(report.rows[0].status))
    with pytest.raises(ValueError, match="reason_codes must be unique"):
        replace(
            report.rows[0],
            reason_codes=(
                "event_resolution_authority_signal_watch_decay",
                "event_resolution_authority_signal_watch_decay",
            ),
        )
    with pytest.raises(ValueError, match="reason_codes must use deterministic sequence"):
        replace(
            build_report(
                observation(
                    "candidate-block-sequence",
                    observed_seconds_ago=18000,
                    contradictory_resolution_score=d("0.800000"),
                ),
            ).rows[0],
            reason_codes=(
                "event_resolution_authority_signal_conflict",
                "event_resolution_authority_signal_block_decay",
            ),
        )

    multi_row_report = build_report(
        observation("candidate-pass-sequence"),
        observation("candidate-watch-sequence", observed_seconds_ago=7200),
    )
    with pytest.raises(ValueError, match="rows must use deterministic sort order"):
        replace(multi_row_report, rows=tuple(reversed(multi_row_report.rows)))


def test_datetime_normalization_future_rejection_and_public_string_validation() -> None:
    module = api()
    offset = timezone(timedelta(hours=-4))
    normalized = observation(
        "candidate-offset-time",
        authority_observed_at=datetime(2026, 7, 8, 7, 0, tzinfo=offset),
    )

    assert normalized.authority_observed_at == datetime(2026, 7, 8, 11, 0, tzinfo=UTC)
    assert build_report(normalized).rows[0].signal_age_seconds == d("3600.000000")

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_event_resolution_authority_signal_decay_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="authority_observed_at must be timezone-aware"):
        observation(
            "candidate-naive-time",
            authority_observed_at=datetime(2026, 7, 8, 11, 0),
        )
    with pytest.raises(ValueError, match="authority_observed_at must not be in the future"):
        build_report(observation("candidate-future-time", observed_seconds_ago=-1))
    with pytest.raises(ValueError, match="raw_candidate_ref"):
        observation(" wallet")
    with pytest.raises(ValueError, match="authority_family"):
        observation("candidate-unsafe-family", authority_family="network_client")
    with pytest.raises(ValueError, match="authority_family"):
        observation(
            "candidate-url-family",
            authority_family="https://example.invalid/resolution-source",
        )
    with pytest.raises(ValueError, match="config_version"):
        config(config_version="postgresql://user:pass@example.invalid/research")


def test_public_payload_validator_rejects_unsafe_surface_values_and_numerics() -> None:
    module = api()
    payload = module.research_event_resolution_authority_signal_decay_report_payload(
        build_report(observation("candidate-pass-alpha")),
    )

    module.validate_research_event_resolution_authority_signal_decay_public_payload(payload)
    with pytest.raises(ValueError, match="unsafe live surface field"):
        module.validate_research_event_resolution_authority_signal_decay_public_payload(
            {**payload, "wallet": "paper"},
        )
    with pytest.raises(ValueError, match="unsafe public value"):
        module.validate_research_event_resolution_authority_signal_decay_public_payload(
            {**payload, "authority_family": "source_url"},
        )
    with pytest.raises(ValueError, match="Decimal-derived"):
        module.validate_research_event_resolution_authority_signal_decay_public_payload(
            {**payload, "signal_count": 1},
        )
    with pytest.raises(ValueError, match="readonly"):
        module.validate_research_event_resolution_authority_signal_decay_public_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_event_resolution_authority_signal_decay_public_payload(
            {**payload, "signal_count": "9.000000"},
        )


def test_module_scope_is_readonly_report_only_and_external_io_free() -> None:
    module = api()

    assert set(module.__all__) == {
        "DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_SIGNAL_DECAY_CONFIG_VERSION",
        "ResearchEventResolutionAuthoritySignalDecayConfig",
        "ResearchEventResolutionAuthoritySignalObservation",
        "ResearchEventResolutionAuthoritySignalDecayRow",
        "ResearchEventResolutionAuthoritySignalDecayReport",
        "build_research_event_resolution_authority_signal_decay_report",
        "research_event_resolution_authority_signal_decay_report_payload",
        "validate_research_event_resolution_authority_signal_decay_public_payload",
    }

    tree = ast.parse(MODULE_PATH.read_text())
    imported_roots: set[str] = set()
    called_names: set[str] = set()
    assigned_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)
        elif isinstance(node, ast.Name):
            assigned_names.add(node.id)

    assert not imported_roots.intersection(
        {
            "requests",
            "urllib",
            "httpx",
            "socket",
            "websocket",
            "psycopg",
            "sqlite3",
            "sqlalchemy",
            "supabase",
            "subprocess",
        },
    )
    assert not called_names.intersection(
        {
            "open",
            "connect",
            "request",
            "post",
            "put",
            "patch",
            "delete",
            "execute",
            "commit",
            "rollback",
            "place_order",
            "submit_order",
            "cancel_order",
            "size_position",
            "recommend",
        },
    )
    assert not assigned_names.intersection(
        {
            "live_trading",
            "wallet",
            "auth",
            "order_client",
            "network_client",
            "database",
            "persistence",
            "position_size",
            "recommendation",
        },
    )


def _assert_decimal_public_fields(value: Any) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if isinstance(item, Decimal):
            assert type(item) is Decimal


def _assert_no_public_float_or_int(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_public_float_or_int(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_public_float_or_int(item)


def _assert_no_forbidden_public_surface(value: Any) -> None:
    forbidden_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
    )
    encoded = json.dumps(value, sort_keys=True).lower()
    for fragment in forbidden_fragments:
        assert fragment not in encoded
