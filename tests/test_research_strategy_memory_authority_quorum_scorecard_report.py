from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_memory_authority_quorum_scorecard_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_memory_authority_quorum_scorecard_report.py",
)
GENERATED_AT = datetime(2026, 7, 9, 14, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 13, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _module() -> Any:
    spec = importlib.util.find_spec(MODULE_NAME)
    assert spec is not None, "memory authority quorum scorecard module is missing"
    return importlib.import_module(MODULE_NAME)


def _public_name(suffix: str = "") -> str:
    stem = "research_strategy_memory_authority_quorum_scorecard_report"
    return f"{stem}{suffix}"


def _config(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_MEMORY_AUTHORITY_QUORUM_SCORECARD_CONFIG_VERSION
        ),
        "pass_min_score": d("0.800000"),
        "watch_min_score": d("0.600000"),
        "min_pass_memory_match_score": d("0.800000"),
        "min_watch_memory_match_score": d("0.600000"),
        "min_pass_source_rank_score": d("0.750000"),
        "min_watch_source_rank_score": d("0.550000"),
        "required_quorum_count": d("3.000000"),
        "min_pass_independent_count": d("3.000000"),
        "min_watch_independent_count": d("2.000000"),
        "max_pass_contradiction_risk_score": d("0.200000"),
        "max_watch_contradiction_risk_score": d("0.450000"),
        "memory_match_weight": d("0.350000"),
        "source_rank_weight": d("0.250000"),
        "quorum_weight": d("0.250000"),
        "contradiction_safety_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.ResearchStrategyMemoryAuthorityQuorumScorecardConfig(**values)


def _input(module: Any, item_ref: str = "private-item-alpha", **overrides: object) -> Any:
    values = {
        "item_ref": item_ref,
        "memory_match_score": d("0.950000"),
        "source_rank_score": d("0.900000"),
        "independent_source_count": d("4.000000"),
        "contradiction_risk_score": d("0.100000"),
        "observed_at": OBSERVED_AT,
        "reason_codes": ("memory_snapshot_ready",),
    }
    values.update(overrides)
    return module.ResearchStrategyMemoryAuthorityQuorumInput(**values)


def _build(module: Any, rows: tuple[Any, ...], **overrides: object) -> Any:
    values = {
        "items": rows,
        "generated_at": GENERATED_AT,
        "config": _config(module),
        "public_notes": (),
    }
    values.update(overrides)
    return getattr(module, f"build_{_public_name()}")(**values)


def _payload(module: Any, value: Any) -> dict[str, Any]:
    return getattr(module, f"{_public_name()}_public_payload")(value)


def _digest(module: Any, value: Any) -> str:
    return getattr(module, f"{_public_name()}_digest")(value)


def _validate(module: Any, value: Any) -> dict[str, Any]:
    return getattr(module, f"validate_{_public_name()}_public_payload")(value)


def _walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(_walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(_walk_values(item))
        return tuple(nested)
    return (value,)


def _unsigned_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def test_builds_pass_watch_and_block_rows_with_private_refs_redacted() -> None:
    module = _module()
    report = _build(
        module,
        (
            _input(
                module,
                "candidate-alpha/market-slug?token=hidden&wallet=private",
                memory_match_score=d("0.950000"),
                source_rank_score=d("0.900000"),
                independent_source_count=d("4.000000"),
                contradiction_risk_score=d("0.100000"),
                reason_codes=("memory_snapshot_ready",),
            ),
            _input(
                module,
                "queue-item-watch",
                memory_match_score=d("0.700000"),
                source_rank_score=d("0.650000"),
                independent_source_count=d("2.000000"),
                contradiction_risk_score=d("0.350000"),
                reason_codes=("manual_review_requested",),
            ),
            _input(
                module,
                "queue-item-block",
                memory_match_score=d("0.450000"),
                source_rank_score=d("0.400000"),
                independent_source_count=d("1.000000"),
                contradiction_risk_score=d("0.700000"),
                reason_codes=("manual_review_requested", "missing_memory_evidence"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
        public_notes=(
            module.ResearchStrategyMemoryAuthorityQuorumPublicNote(
                key="review_scope",
                value="memory quorum scorecard review only",
            ),
        ),
    )

    assert is_dataclass(report)
    assert type(report) is module.ResearchStrategyMemoryAuthorityQuorumScorecardReport
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.status == "block"
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_score == d("0.666667")
    assert report.min_score == d("0.385833")
    assert report.max_contradiction_risk_score == d("0.700000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")

    blocked = report.rows[0]
    assert blocked.item_digest.startswith("sha256:")
    assert blocked.memory_gap_score == d("0.550000")
    assert blocked.source_rank_gap_score == d("0.600000")
    assert blocked.quorum_score == d("0.333333")
    assert blocked.contradiction_safety_score == d("0.300000")
    assert blocked.score == d("0.385833")
    assert blocked.reason_codes == (
        "manual_review_requested",
        "missing_memory_evidence",
        "memory_match_block",
        "source_rank_block",
        "quorum_block",
        "contradiction_risk_block",
        "aggregate_score_block",
    )

    watched = report.rows[1]
    assert watched.score == d("0.671667")
    assert watched.reason_codes == (
        "manual_review_requested",
        "memory_match_watch",
        "source_rank_watch",
        "quorum_watch",
        "contradiction_risk_watch",
        "aggregate_score_watch",
    )

    passed = report.rows[2]
    assert passed.status == "pass"
    assert passed.score == d("0.942500")
    assert passed.reason_codes == ("memory_snapshot_ready", "memory_quorum_pass")

    payload = _payload(module, report)
    encoded_payload = json.dumps(payload, sort_keys=True)
    assert "candidate-alpha" not in encoded_payload
    assert "market-slug" not in encoded_payload
    assert "token=hidden" not in encoded_payload
    assert "wallet=private" not in encoded_payload
    assert payload["rows"][0]["item_digest"].startswith("sha256:")
    assert payload["public_notes"] == [
        {
            "key": "review_scope",
            "value": "memory quorum scorecard review only",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        }
    ]


def test_public_payload_digest_is_deterministic_decimal_stringed_and_validated() -> None:
    module = _module()
    first = _build(
        module,
        (
            _input(module, "raw-b", memory_match_score=d("0.720000")),
            _input(module, "raw-a", memory_match_score=d("0.940000")),
        ),
    )
    second = _build(
        module,
        (
            _input(module, "raw-a", memory_match_score=d("0.940000")),
            _input(module, "raw-b", memory_match_score=d("0.720000")),
        ),
    )

    first_payload = _payload(module, first)
    second_payload = _payload(module, second)

    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert first.derived_validation_digest == _digest(module, first)
    assert first_payload["derived_validation_digest"] == _unsigned_digest(first_payload)
    assert len(first.derived_validation_digest) == 64
    int(first.derived_validation_digest, 16)
    assert first_payload["row_count"] == "2.000000"
    assert first_payload["rows"][0]["score"] == "0.862000"
    assert first_payload["rows"][0]["observed_at"] == "2026-07-09T13:30:00+00:00"
    assert not any(type(value) in (int, float) for value in _walk_values(first_payload))

    tampered_digest = dict(first_payload)
    tampered_digest["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        _validate(module, tampered_digest)

    tampered_score = json.loads(json.dumps(first_payload))
    tampered_score["rows"][0]["score"] = "0.010000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        _validate(module, tampered_score)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)


def test_public_payload_rejects_raw_private_fields_values_and_flag_downgrades() -> None:
    module = _module()
    report = _build(module, (_input(module),))
    payload = _payload(module, report)

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        _validate(module, missing_digest)

    bad_flag = json.loads(json.dumps(payload))
    bad_flag["rows"][0]["readonly"] = False
    bad_flag["derived_validation_digest"] = _unsigned_digest(bad_flag)
    with pytest.raises(ValueError, match="readonly"):
        _validate(module, bad_flag)

    with pytest.raises(ValueError, match="unsafe"):
        _validate(
            module,
            {
                "candidate_id": "private-alpha",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "derived_validation_digest": "0" * 64,
            },
        )

    with pytest.raises(ValueError, match="unsafe"):
        _validate(
            module,
            {
                "summary": "source url and raw text must stay private",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "derived_validation_digest": "0" * 64,
            },
        )


def test_dataclasses_are_frozen_decimal_only_and_status_limited() -> None:
    module = _module()

    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type) and exported_name.startswith("ResearchStrategy"):
            assert is_dataclass(exported)

    report = _build(module, (_input(module),))
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="memory_match_score"):
        _input(module, memory_match_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_rank_score"):
        _input(module, source_rank_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="observed_at"):
        _input(module, observed_at=_DatetimeSubclass(2026, 7, 9, 13, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="item_ref"):
        _input(module, item_ref=_StringSubclass("subclassed"))
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="clear")
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)

    for value in (report, *report.rows):
        for field in fields(value):
            item = getattr(value, field.name)
            if isinstance(item, Decimal):
                assert type(item) is Decimal


def test_report_only_scope_has_no_forbidden_runtime_surface_terms() -> None:
    module = _module()
    source = MODULE_PATH.read_text()
    lowered = source.lower()

    for forbidden in (
        "db",
        "database",
        "network",
        "wallet",
        "order",
        "live",
        "trading",
        "sizing",
        "recommendation",
    ):
        assert forbidden not in lowered

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_MEMORY_AUTHORITY_QUORUM_SCORECARD_CONFIG_VERSION",
        "ResearchStrategyMemoryAuthorityQuorumScorecardConfig",
        "ResearchStrategyMemoryAuthorityQuorumInput",
        "ResearchStrategyMemoryAuthorityQuorumPublicNote",
        "ResearchStrategyMemoryAuthorityQuorumScorecardRow",
        "ResearchStrategyMemoryAuthorityQuorumScorecardReport",
        "build_research_strategy_memory_authority_quorum_scorecard_report",
        "research_strategy_memory_authority_quorum_scorecard_report_public_payload",
        "research_strategy_memory_authority_quorum_scorecard_report_digest",
        "validate_research_strategy_memory_authority_quorum_scorecard_report_public_payload",
    )
