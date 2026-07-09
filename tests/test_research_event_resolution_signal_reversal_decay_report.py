from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(hours=6)
RESOLVED_AT = GENERATED_AT - timedelta(hours=3)
PRIVATE_EVENT_REFERENCE = (
    "candidate-alpha-market-id-123-slug-question-https://example.invalid/source?token=x"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_event_resolution_signal_reversal_decay_report.py",
)
FORBIDDEN_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "http://",
    "https://",
    "source_url",
    "source_text",
    "postgres://",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_event_resolution_signal_reversal_decay_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def observation(
    private_event_reference: str = PRIVATE_EVENT_REFERENCE,
    *,
    observed_at: datetime = OBSERVED_AT,
    resolved_at: datetime = RESOLVED_AT,
    pre_resolution_signal_score: Decimal = d("0.620000"),
    post_resolution_signal_score: Decimal = d("0.580000"),
    evidence_confidence_score: Decimal = d("0.900000"),
    authority_conflict_score: Decimal = d("0.050000"),
    corroboration_count: Decimal = d("4"),
    expected_corroboration_count: Decimal = d("4"),
    **overrides: object,
):
    values = {
        "private_event_reference": private_event_reference,
        "observed_at": observed_at,
        "resolved_at": resolved_at,
        "pre_resolution_signal_score": pre_resolution_signal_score,
        "post_resolution_signal_score": post_resolution_signal_score,
        "evidence_confidence_score": evidence_confidence_score,
        "authority_conflict_score": authority_conflict_score,
        "corroboration_count": corroboration_count,
        "expected_corroboration_count": expected_corroboration_count,
    }
    values.update(overrides)
    return api().ResearchEventResolutionSignalReversalDecayObservation(**values)


def build_report(*items, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_event_resolution_signal_reversal_decay_report(
        items,
        config=(
            module.ResearchEventResolutionSignalReversalDecayConfig()
            if cfg is None
            else cfg
        ),
        generated_at=generated_at,
    )


def test_empty_report_is_report_only_pass_with_stable_payload() -> None:
    report = build_report()

    assert report.status == "pass"
    assert report.report_action == "paper_event_resolution_signal_reversal_decay_monitor"
    assert report.event_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.average_reversal_decay_score == d("0.000000")
    assert report.max_reversal_decay_score == d("0.000000")
    assert report.max_signal_reversal_magnitude == d("0.000000")
    assert report.max_post_resolution_age_hours == d("0.000000")
    assert report.reason_codes == (
        "event_resolution_signal_reversal_decay_report_pass",
    )
    assert report.reason_code_counts == ()
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.payload["derived_validation_digest"] == canonical_digest(report.payload)


def test_signal_reversal_decay_scores_rows_and_ranks_deterministically() -> None:
    passing = observation("private-pass")
    watching = observation(
        "private-watch",
        observed_at=GENERATED_AT - timedelta(hours=24),
        resolved_at=GENERATED_AT - timedelta(hours=9),
        pre_resolution_signal_score=d("0.300000"),
        post_resolution_signal_score=d("0.700000"),
        evidence_confidence_score=d("0.700000"),
        authority_conflict_score=d("0.250000"),
        corroboration_count=d("2"),
        expected_corroboration_count=d("4"),
    )
    blocking = observation(
        "private-block",
        observed_at=GENERATED_AT - timedelta(hours=48),
        resolved_at=GENERATED_AT - timedelta(hours=18),
        pre_resolution_signal_score=d("0.050000"),
        post_resolution_signal_score=d("0.950000"),
        evidence_confidence_score=d("0.200000"),
        authority_conflict_score=d("0.900000"),
        corroboration_count=d("0"),
        expected_corroboration_count=d("4"),
    )

    report = build_report(
        passing,
        watching,
        blocking,
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )
    reversed_report = build_report(blocking, watching, passing)

    assert api().EVENT_RESOLUTION_SIGNAL_REVERSAL_DECAY_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.report_action == "paper_event_resolution_signal_reversal_decay_block"
    assert report.event_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_reversal_decay_score == d("0.444222")
    assert report.max_reversal_decay_score == d("0.900000")
    assert report.max_signal_reversal_magnitude == d("0.900000")
    assert report.max_post_resolution_age_hours == d("18.000000")

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert report.rows == reversed_report.rows

    block_row, watch_row, pass_row = report.rows
    assert block_row.event_digest == hashlib.sha256(
        "private-block".encode("utf-8"),
    ).hexdigest()
    assert block_row.observation_age_hours == d("48.000000")
    assert block_row.post_resolution_age_hours == d("18.000000")
    assert block_row.signal_reversal_magnitude == d("0.900000")
    assert block_row.evidence_confidence_decay_score == d("0.800000")
    assert block_row.post_resolution_decay_score == d("1.000000")
    assert block_row.corroboration_gap_score == d("1.000000")
    assert block_row.reversal_decay_score == d("0.900000")
    assert block_row.reason_codes == (
        "authority_conflict_pressure",
        "corroboration_gap",
        "evidence_confidence_decay",
        "post_resolution_decay",
        "signal_reversal_high",
        "event_resolution_signal_reversal_decay_block",
    )
    assert watch_row.reversal_decay_score == d("0.370000")
    assert watch_row.status == "watch"
    assert pass_row.reversal_decay_score == d("0.062667")
    assert pass_row.reason_codes == (
        "event_resolution_signal_reversal_decay_pass",
    )

    payload = api().research_event_resolution_signal_reversal_decay_report_payload(report)
    reversed_payload = api().research_event_resolution_signal_reversal_decay_report_payload(
        reversed_report,
    )
    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert api().research_event_resolution_signal_reversal_decay_report_digest(
        report,
    ) == payload["derived_validation_digest"]
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["event_count"] == "3.000000"
    assert payload["rows"][0]["reversal_decay_score"] == "0.900000"
    assert PRIVATE_EVENT_REFERENCE not in json.dumps(payload, sort_keys=True)
    assert _float_paths(payload) == ()
    assert _int_paths(payload) == ()
    assert _unsafe_public_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_payload_rejects_tampering_and_unsafe_public_surfaces() -> None:
    module = api()
    report = build_report(observation())
    payload = module.research_event_resolution_signal_reversal_decay_report_payload(report)

    leaked = dict(payload)
    leaked["candidate_id"] = "candidate-alpha"
    leaked["derived_validation_digest"] = canonical_digest(leaked)
    with pytest.raises(ValueError, match="unsafe"):
        module.research_event_resolution_signal_reversal_decay_report_payload(leaked)

    bad_status = dict(payload)
    bad_status["status"] = "blocked"
    bad_status["derived_validation_digest"] = canonical_digest(bad_status)
    with pytest.raises(ValueError, match="status"):
        module.research_event_resolution_signal_reversal_decay_report_payload(bad_status)

    numeric = dict(payload)
    numeric["event_count"] = 1
    numeric["derived_validation_digest"] = canonical_digest(numeric)
    with pytest.raises(ValueError, match="Decimal"):
        module.research_event_resolution_signal_reversal_decay_report_payload(numeric)

    numeric_string = dict(payload)
    numeric_string["event_count"] = "one"
    numeric_string["derived_validation_digest"] = canonical_digest(numeric_string)
    with pytest.raises(ValueError, match="Decimal"):
        module.research_event_resolution_signal_reversal_decay_report_payload(
            numeric_string,
        )

    nested_flag = json.loads(json.dumps(payload))
    nested_flag["rows"][0]["readonly"] = False
    nested_flag["derived_validation_digest"] = canonical_digest(nested_flag)
    with pytest.raises(ValueError, match="readonly"):
        module.research_event_resolution_signal_reversal_decay_report_payload(nested_flag)

    recommendation_surface = dict(payload)
    recommendation_surface["recommendation"] = "hold"
    recommendation_surface["derived_validation_digest"] = canonical_digest(
        recommendation_surface,
    )
    with pytest.raises(ValueError, match="unsafe|schema"):
        module.research_event_resolution_signal_reversal_decay_report_payload(
            recommendation_surface,
        )

    fake_minimal_report = {
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    fake_minimal_report["derived_validation_digest"] = canonical_digest(
        fake_minimal_report,
    )
    with pytest.raises(ValueError, match="schema"):
        module.research_event_resolution_signal_reversal_decay_report_payload(
            fake_minimal_report,
        )

    changed = dict(payload)
    changed["event_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_event_resolution_signal_reversal_decay_report_payload(changed)


def test_validation_rejects_bad_types_flags_duplicates_and_manual_drift() -> None:
    module = api()

    with pytest.raises(ValueError, match="generated_at"):
        build_report(generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 8, 10, 0))
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=_DateTimeSubclass(2026, 7, 8, 10, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="pre_resolution_signal_score"):
        observation(pre_resolution_signal_score=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="post_resolution_signal_score"):
        observation(post_resolution_signal_score=_DecimalSubclass("0.5"))
    with pytest.raises(ValueError, match="corroboration_count"):
        observation(corroboration_count=d("1.500000"))
    with pytest.raises(ValueError, match="resolved_at"):
        observation(resolved_at=OBSERVED_AT - timedelta(seconds=1))
    with pytest.raises(ValueError, match="resolved_at"):
        build_report(observation(resolved_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="unique"):
        build_report(observation("private-dupe"), observation("private-dupe"))
    with pytest.raises(ValueError, match="paper_only"):
        module.ResearchEventResolutionSignalReversalDecayConfig(paper_only=False)
    with pytest.raises(ValueError, match="weights"):
        module.ResearchEventResolutionSignalReversalDecayConfig(
            corroboration_gap_weight=d("0.200000"),
        )

    report = build_report(observation())
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="status"):
        replace(report, status="blocked")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_public_dataclasses_are_frozen_decimal_only_and_exported() -> None:
    module = api()
    report = build_report(observation())

    assert module.__all__ == (
        "DEFAULT_RESEARCH_EVENT_RESOLUTION_SIGNAL_REVERSAL_DECAY_REPORT_CONFIG_VERSION",
        "EVENT_RESOLUTION_SIGNAL_REVERSAL_DECAY_STATUSES",
        "ResearchEventResolutionSignalReversalDecayConfig",
        "ResearchEventResolutionSignalReversalDecayObservation",
        "ResearchEventResolutionSignalReversalDecayReasonCodeCount",
        "ResearchEventResolutionSignalReversalDecayReport",
        "ResearchEventResolutionSignalReversalDecayRow",
        "build_research_event_resolution_signal_reversal_decay_report",
        "research_event_resolution_signal_reversal_decay_report_digest",
        "research_event_resolution_signal_reversal_decay_report_payload",
    )

    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    for value in (
        module.ResearchEventResolutionSignalReversalDecayConfig(),
        observation("private-exact"),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    ):
        for flag_name in ("paper_only", "report_only", "readonly"):
            assert getattr(value, flag_name) is True
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        for field in fields(value):
            public_value = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if field.name.endswith(
                (
                    "_count",
                    "_score",
                    "_threshold",
                    "_weight",
                    "_hours",
                    "_magnitude",
                    "_ratio",
                ),
            ):
                assert type(public_value) is Decimal

    with pytest.raises(TypeError):

        class BadObservation(module.ResearchEventResolutionSignalReversalDecayObservation):
            pass


def test_module_imports_no_db_network_wallet_order_or_live_trading_dependencies() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    forbidden_roots = {
        "bs4",
        "httpx",
        "playwright",
        "psycopg",
        "requests",
        "scrapy",
        "selenium",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "urllib",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_roots
        elif isinstance(node, ast.ImportFrom):
            assert node.module is not None
            assert node.module.split(".", 1)[0] not in forbidden_roots


def _float_paths(value: object, path: str = "payload") -> tuple[str, ...]:
    if isinstance(value, float):
        return (path,)
    if isinstance(value, dict):
        return tuple(
            item
            for key, child in value.items()
            for item in _float_paths(child, f"{path}.{key}")
        )
    if isinstance(value, list):
        return tuple(
            item
            for index, child in enumerate(value)
            for item in _float_paths(child, f"{path}[{index}]")
        )
    return ()


def _int_paths(value: object, path: str = "payload") -> tuple[str, ...]:
    if type(value) is int:
        return (path,)
    if isinstance(value, dict):
        return tuple(
            item
            for key, child in value.items()
            for item in _int_paths(child, f"{path}.{key}")
        )
    if isinstance(value, list):
        return tuple(
            item
            for index, child in enumerate(value)
            for item in _int_paths(child, f"{path}[{index}]")
        )
    return ()


def _unsafe_public_paths(value: object, path: str = "payload") -> tuple[str, ...]:
    if isinstance(value, str):
        normalized = value.lower()
        if any(fragment in normalized for fragment in FORBIDDEN_PUBLIC_FRAGMENTS):
            return (path,)
        return ()
    if isinstance(value, dict):
        paths: list[str] = []
        for key, child in value.items():
            normalized_key = key.lower()
            if any(fragment in normalized_key for fragment in FORBIDDEN_PUBLIC_FRAGMENTS):
                paths.append(f"{path}.{key}")
            paths.extend(_unsafe_public_paths(child, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        return tuple(
            item
            for index, child in enumerate(value)
            for item in _unsafe_public_paths(child, f"{path}[{index}]")
        )
    return ()
