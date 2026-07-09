from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_event_source_update_watch_window_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_source_update_watch_window_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": (
            module.DEFAULT_RESEARCH_EVENT_SOURCE_UPDATE_WATCH_WINDOW_REPORT_CONFIG_VERSION
        ),
        "cadence_watch_overrun_ratio": d("1.000000"),
        "cadence_block_overrun_ratio": d("2.000000"),
        "stale_evidence_watch_age_seconds": d("3600.000000"),
        "stale_evidence_block_age_seconds": d("7200.000000"),
        "contradiction_watch_pressure": d("0.400000"),
        "contradiction_block_pressure": d("0.700000"),
        "resolution_deadline_watch_window_seconds": d("1800.000000"),
        "resolution_deadline_block_window_seconds": d("300.000000"),
        "watch_score_threshold": d("0.400000"),
        "block_score_threshold": d("0.700000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchEventSourceUpdateWatchWindowConfig(**values)


def update_input(
    scope: str,
    *,
    authority_tier: str,
    cadence_seconds: str,
    stale_age_seconds: str,
    deadline_seconds: str,
    contradiction_pressure: str,
):
    module = api()
    return module.ResearchEventSourceUpdateWatchWindowInput(
        event_scope=scope,
        authority_tier=authority_tier,
        expected_update_cadence_seconds=d(cadence_seconds),
        stale_evidence_age_seconds=d(stale_age_seconds),
        resolution_deadline_seconds=d(deadline_seconds),
        contradiction_pressure=d(contradiction_pressure),
    )


def report(*updates: object, cfg: object | None = None):
    module = api()
    return module.build_research_event_source_update_watch_window_report(
        updates,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def test_empty_report_blocks_with_zero_windows_and_hard_flags() -> None:
    module = api()
    update_report = report()

    assert type(update_report) is module.ResearchEventSourceUpdateWatchWindowReport
    assert is_dataclass(update_report)
    assert update_report.__dataclass_params__.frozen is True
    assert update_report.generated_at == GENERATED_AT
    assert update_report.config_version == (
        module.DEFAULT_RESEARCH_EVENT_SOURCE_UPDATE_WATCH_WINDOW_REPORT_CONFIG_VERSION
    )
    assert update_report.input_count == ZERO
    assert update_report.row_count == ZERO
    assert update_report.pass_count == ZERO
    assert update_report.watch_count == ZERO
    assert update_report.block_count == ZERO
    assert update_report.average_watch_window_score == ZERO
    assert update_report.max_watch_window_score == ZERO
    assert update_report.min_next_update_watch_window_seconds == ZERO
    assert update_report.max_stale_evidence_age_seconds == ZERO
    assert update_report.max_contradiction_pressure == ZERO
    assert update_report.status == "block"
    assert update_report.reason_codes == ("no_event_source_update_watch_window_inputs",)
    assert update_report.rows == ()
    assert update_report.paper_only is True
    assert update_report.report_only is True
    assert update_report.readonly is True
    assert len(update_report.derived_validation_digest) == 64


def test_update_watch_windows_classify_pass_watch_and_block_deterministically() -> None:
    module = api()
    update_report = report(
        update_input(
            "event-update-alpha",
            authority_tier="official",
            cadence_seconds="3600.000000",
            stale_age_seconds="900.000000",
            deadline_seconds="7200.000000",
            contradiction_pressure="0.050000",
        ),
        update_input(
            "event-update-bravo",
            authority_tier="secondary",
            cadence_seconds="1800.000000",
            stale_age_seconds="2100.000000",
            deadline_seconds="900.000000",
            contradiction_pressure="0.450000",
        ),
        update_input(
            "event-update-charlie",
            authority_tier="low",
            cadence_seconds="3600.000000",
            stale_age_seconds="8000.000000",
            deadline_seconds="200.000000",
            contradiction_pressure="0.750000",
        ),
    )

    payload = module.research_event_source_update_watch_window_report_payload(
        update_report,
    )
    repeat_payload = module.research_event_source_update_watch_window_report_payload(
        update_report,
    )

    assert update_report.status == "block"
    assert update_report.input_count == d("3.000000")
    assert update_report.row_count == d("3.000000")
    assert update_report.pass_count == ONE
    assert update_report.watch_count == ONE
    assert update_report.block_count == ONE
    assert update_report.average_watch_window_score == d("0.447917")
    assert update_report.max_watch_window_score == d("0.845833")
    assert update_report.min_next_update_watch_window_seconds == ZERO
    assert update_report.max_stale_evidence_age_seconds == d("8000.000000")
    assert update_report.max_contradiction_pressure == d("0.750000")
    assert update_report.reason_codes == (
        "cadence_overrun_block",
        "stale_evidence_age_block",
        "contradiction_pressure_block",
        "resolution_deadline_proximity_block",
        "low_authority_tier_present",
        "event_source_update_watch_window_row_block",
    )

    block_row, watch_row, pass_row = update_report.rows
    assert (block_row.event_scope, block_row.status) == (
        "event-update-charlie",
        "block",
    )
    assert (watch_row.event_scope, watch_row.status) == (
        "event-update-bravo",
        "watch",
    )
    assert (pass_row.event_scope, pass_row.status) == (
        "event-update-alpha",
        "pass",
    )
    assert block_row.cadence_overrun_ratio == d("2.222222")
    assert block_row.next_update_watch_window_seconds == ZERO
    assert block_row.watch_window_score == d("0.845833")
    assert watch_row.cadence_overrun_ratio == d("1.166667")
    assert watch_row.next_update_watch_window_seconds == ZERO
    assert watch_row.watch_window_score == d("0.429167")
    assert pass_row.cadence_overrun_ratio == d("0.250000")
    assert pass_row.next_update_watch_window_seconds == d("2700.000000")
    assert pass_row.watch_window_score == d("0.068750")
    assert payload == repeat_payload
    assert payload["derived_validation_digest"] == (
        update_report.derived_validation_digest
    )
    assert payload["rows"][0]["watch_window_score"] == "0.845833"
    assert payload["rows"][2]["next_update_watch_window_seconds"] == "2700.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not _has_forbidden_public_surface(payload)
    assert not any(type(value) in (float, int) for value in _walk_payload_values(payload))
    assert json.dumps(payload, sort_keys=True) == json.dumps(repeat_payload, sort_keys=True)
    assert module.validate_research_event_source_update_watch_window_report_payload(payload)


def test_digest_validation_rejects_tampered_public_payload() -> None:
    module = api()
    update_report = report(
        update_input(
            "event-update-alpha",
            authority_tier="primary",
            cadence_seconds="3600.000000",
            stale_age_seconds="1200.000000",
            deadline_seconds="5400.000000",
            contradiction_pressure="0.100000",
        ),
    )
    payload = module.research_event_source_update_watch_window_report_payload(
        update_report,
    )
    tampered = json.loads(json.dumps(payload, sort_keys=True))
    tampered["rows"][0]["status"] = "watch"

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_event_source_update_watch_window_report_payload(
            tampered,
        )

    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_research_event_source_update_watch_window_report_payload(
            {
                "raw_" + "url": "blocked",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_payload_validation_rejects_resigned_non_report_only_contracts() -> None:
    module = api()
    update_report = report(
        update_input(
            "event-update-alpha",
            authority_tier="primary",
            cadence_seconds="3600.000000",
            stale_age_seconds="1200.000000",
            deadline_seconds="5400.000000",
            contradiction_pressure="0.100000",
        ),
    )
    payload = module.research_event_source_update_watch_window_report_payload(
        update_report,
    )

    missing_flag = json.loads(json.dumps(payload, sort_keys=True))
    del missing_flag["readonly"]
    _resign_payload(missing_flag)

    with pytest.raises(ValueError, match="readonly"):
        module.validate_research_event_source_update_watch_window_report_payload(
            missing_flag,
        )

    invalid_report_status = json.loads(json.dumps(payload, sort_keys=True))
    invalid_report_status["status"] = "clear"
    _resign_payload(invalid_report_status)

    with pytest.raises(ValueError, match="status"):
        module.validate_research_event_source_update_watch_window_report_payload(
            invalid_report_status,
        )

    invalid_row_status = json.loads(json.dumps(payload, sort_keys=True))
    invalid_row_status["rows"][0]["status"] = "clear"
    _resign_payload(invalid_row_status)

    with pytest.raises(ValueError, match="status"):
        module.validate_research_event_source_update_watch_window_report_payload(
            invalid_row_status,
        )


def test_payload_validation_rejects_resigned_exact_schema_drift() -> None:
    module = api()
    update_report = report(
        update_input(
            "event-update-alpha",
            authority_tier="primary",
            cadence_seconds="3600.000000",
            stale_age_seconds="1200.000000",
            deadline_seconds="5400.000000",
            contradiction_pressure="0.100000",
        ),
    )
    payload = module.research_event_source_update_watch_window_report_payload(
        update_report,
    )

    extra_report_field = json.loads(json.dumps(payload, sort_keys=True))
    extra_report_field["audit_note"] = "safe"
    _resign_payload(extra_report_field)

    with pytest.raises(ValueError, match="exact public schema"):
        module.validate_research_event_source_update_watch_window_report_payload(
            extra_report_field,
        )

    extra_row_field = json.loads(json.dumps(payload, sort_keys=True))
    extra_row_field["rows"][0]["review_note"] = "safe"
    _resign_payload(extra_row_field)

    with pytest.raises(ValueError, match="exact public schema"):
        module.validate_research_event_source_update_watch_window_report_payload(
            extra_row_field,
        )

    missing_report_field = json.loads(json.dumps(payload, sort_keys=True))
    del missing_report_field["max_contradiction_pressure"]
    _resign_payload(missing_report_field)

    with pytest.raises(ValueError, match="exact public schema"):
        module.validate_research_event_source_update_watch_window_report_payload(
            missing_report_field,
        )


def test_payload_validation_rejects_resigned_semantic_drift() -> None:
    module = api()
    update_report = report(
        update_input(
            "event-update-alpha",
            authority_tier="primary",
            cadence_seconds="3600.000000",
            stale_age_seconds="1200.000000",
            deadline_seconds="5400.000000",
            contradiction_pressure="0.100000",
        ),
    )
    payload = module.research_event_source_update_watch_window_report_payload(
        update_report,
    )

    invalid_decimal = json.loads(json.dumps(payload, sort_keys=True))
    invalid_decimal["input_count"] = "one"
    _resign_payload(invalid_decimal)

    with pytest.raises(ValueError, match="input_count"):
        module.validate_research_event_source_update_watch_window_report_payload(
            invalid_decimal,
        )

    inconsistent_count = json.loads(json.dumps(payload, sort_keys=True))
    inconsistent_count["pass_count"] = "2.000000"
    _resign_payload(inconsistent_count)

    with pytest.raises(ValueError, match="pass_count"):
        module.validate_research_event_source_update_watch_window_report_payload(
            inconsistent_count,
        )

    inconsistent_row = json.loads(json.dumps(payload, sort_keys=True))
    inconsistent_row["rows"][0]["next_update_watch_window_seconds"] = "1.000000"
    _resign_payload(inconsistent_row)

    with pytest.raises(ValueError, match="next_update_watch_window_seconds"):
        module.validate_research_event_source_update_watch_window_report_payload(
            inconsistent_row,
        )


def test_validation_rejects_bad_numerics_tiers_counts_flags_and_payloads() -> None:
    module = api()
    with pytest.raises(ValueError, match="cadence_watch_overrun_ratio"):
        config(cadence_watch_overrun_ratio=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="contradiction_watch_pressure"):
        config(contradiction_watch_pressure=_DecimalSubclass("0.400000"))
    with pytest.raises(ValueError, match="cadence_block_overrun_ratio"):
        config(cadence_block_overrun_ratio=d("1.000000"))
    with pytest.raises(ValueError, match="authority_tier"):
        update_input(
            "event-update-alpha",
            authority_tier="anonymous",
            cadence_seconds="3600.000000",
            stale_age_seconds="900.000000",
            deadline_seconds="7200.000000",
            contradiction_pressure="0.050000",
        )
    with pytest.raises(ValueError, match="event_scope"):
        update_input(
            "market-slug-leak",
            authority_tier="official",
            cadence_seconds="3600.000000",
            stale_age_seconds="900.000000",
            deadline_seconds="7200.000000",
            contradiction_pressure="0.050000",
        )
    with pytest.raises(ValueError, match="event_scope"):
        update_input(
            "file-execution-persistence-alpha",
            authority_tier="official",
            cadence_seconds="3600.000000",
            stale_age_seconds="900.000000",
            deadline_seconds="7200.000000",
            contradiction_pressure="0.050000",
        )
    with pytest.raises(ValueError, match="expected_update_cadence_seconds"):
        update_input(
            "event-update-alpha",
            authority_tier="official",
            cadence_seconds="0.000000",
            stale_age_seconds="900.000000",
            deadline_seconds="7200.000000",
            contradiction_pressure="0.050000",
        )
    with pytest.raises(ValueError, match="stale_evidence_age_seconds"):
        update_input(
            "event-update-alpha",
            authority_tier="official",
            cadence_seconds="3600.000000",
            stale_age_seconds="-1.000000",
            deadline_seconds="7200.000000",
            contradiction_pressure="0.050000",
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(
            update_input(
                "event-update-alpha",
                authority_tier="official",
                cadence_seconds="3600.000000",
                stale_age_seconds="900.000000",
                deadline_seconds="7200.000000",
                contradiction_pressure="0.050000",
            ),
            paper_only=False,
        )


def test_public_dataclasses_are_frozen_exact_decimal_only_and_side_effect_free() -> None:
    module = api()
    update_report = report(
        update_input(
            "event-update-alpha",
            authority_tier="official",
            cadence_seconds="3600.000000",
            stale_age_seconds="900.000000",
            deadline_seconds="7200.000000",
            contradiction_pressure="0.050000",
        ),
    )

    public_classes = (
        module.ResearchEventSourceUpdateWatchWindowConfig,
        module.ResearchEventSourceUpdateWatchWindowInput,
        module.ResearchEventSourceUpdateWatchWindowRow,
        module.ResearchEventSourceUpdateWatchWindowReport,
    )
    assert all(is_dataclass(public_class) for public_class in public_classes)
    assert all(public_class.__dataclass_params__.frozen is True for public_class in public_classes)
    for public_class in public_classes:
        for field in fields(public_class):
            if field.name.endswith("_count") or field.name.endswith("_ratio"):
                assert field.type in (Decimal, "Decimal")
            if field.name.endswith("_seconds") or field.name.endswith("_score"):
                assert field.type in (Decimal, "Decimal")
            if field.name.endswith("_pressure"):
                assert field.type in (Decimal, "Decimal")

    with pytest.raises(FrozenInstanceError):
        update_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        update_report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(update_report.rows[0], status="watch")
    with pytest.raises(ValueError, match="pass_count"):
        replace(update_report, pass_count=ZERO)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(update_report, derived_validation_digest="0" * 64)

    source = MODULE_PATH.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "open(",
        "connect(",
        "raw_" + "url",
        "source_" + "url",
        "source_" + "text",
        "market_" + "id",
        "market_" + "slug",
        "candidate_" + "id",
        "ques" + "tion",
        "dsn",
        "table_name",
        "database",
        "fi" + "le",
        "fi" + "le_path",
        "fi" + "lesystem",
        "per" + "sistence",
        "exec" + "ution",
        "private_token",
        "token",
        "wallet",
        "order",
        "live",
        "trade",
    )
    assert all(term not in source for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)


def _has_forbidden_public_surface(value: Any) -> bool:
    forbidden = (
        "raw_" + "url",
        "source_" + "url",
        "source_" + "text",
        "market_" + "id",
        "market_" + "slug",
        "candidate_" + "id",
        "ques" + "tion",
        "dsn",
        "table_name",
        "fi" + "le",
        "per" + "sistence",
        "exec" + "ution",
        "private_token",
        "token",
        "wallet",
        "order",
        "live",
        "trade",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            if any(term in str(key).lower() for term in forbidden):
                return True
            if _has_forbidden_public_surface(item):
                return True
    if isinstance(value, list):
        return any(_has_forbidden_public_surface(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower()
        return any(term in lowered for term in forbidden)
    return False


def _resign_payload(payload: dict[str, Any]) -> None:
    for row in payload.get("rows", []):
        row["derived_validation_digest"] = _payload_digest(row)
    payload["derived_validation_digest"] = _payload_digest(payload)


def _payload_digest(payload: dict[str, Any]) -> str:
    unsigned = {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }
    return sha256(
        json.dumps(
            unsigned,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()
