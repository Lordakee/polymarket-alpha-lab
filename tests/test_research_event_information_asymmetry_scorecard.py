from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_event_information_asymmetry_scorecard import (
    DEFAULT_RESEARCH_EVENT_INFORMATION_ASYMMETRY_SCORECARD_CONFIG_VERSION,
    ResearchEventInformationAsymmetryInput,
    ResearchEventInformationAsymmetryPublicNote,
    ResearchEventInformationAsymmetryReasonCodeCount,
    ResearchEventInformationAsymmetryReport,
    ResearchEventInformationAsymmetryRow,
    ResearchEventInformationAsymmetryScorecardConfig,
    build_research_event_information_asymmetry_scorecard,
    research_event_information_asymmetry_scorecard_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path("src/polymarket_alpha_lab/research_event_information_asymmetry_scorecard.py")


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object) -> ResearchEventInformationAsymmetryScorecardConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_EVENT_INFORMATION_ASYMMETRY_SCORECARD_CONFIG_VERSION,
        "min_source_diversity_score": d("0.600000"),
        "pass_source_diversity_score": d("0.800000"),
        "watch_freshness_age_hours": d("24.000000"),
        "block_freshness_age_hours": d("72.000000"),
        "watch_contradiction_score": d("0.300000"),
        "block_contradiction_score": d("0.650000"),
        "min_resolution_clarity_score": d("0.550000"),
        "pass_resolution_clarity_score": d("0.800000"),
        "min_team_expertise_score": d("0.500000"),
        "pass_team_expertise_score": d("0.750000"),
        "watch_asymmetry_score": d("0.500000"),
        "block_asymmetry_score": d("0.750000"),
        "source_diversity_weight": d("0.250000"),
        "freshness_weight": d("0.200000"),
        "contradiction_weight": d("0.200000"),
        "resolution_clarity_weight": d("0.200000"),
        "team_expertise_weight": d("0.150000"),
    }
    values.update(overrides)
    return ResearchEventInformationAsymmetryScorecardConfig(**values)


def _input(
    domain_key: str = "event-domain-alpha",
    **overrides: object,
) -> ResearchEventInformationAsymmetryInput:
    values = {
        "domain_key": domain_key,
        "source_diversity_score": d("0.900000"),
        "freshness_age_hours": d("6.000000"),
        "contradiction_score": d("0.100000"),
        "resolution_clarity_score": d("0.900000"),
        "team_expertise_score": d("0.850000"),
    }
    values.update(overrides)
    return ResearchEventInformationAsymmetryInput(**values)


def _report(
    rows: tuple[ResearchEventInformationAsymmetryInput, ...],
    *,
    cfg: ResearchEventInformationAsymmetryScorecardConfig | None = None,
    generated_at: datetime = GENERATED_AT,
    public_notes: tuple[ResearchEventInformationAsymmetryPublicNote, ...] = (),
) -> ResearchEventInformationAsymmetryReport:
    return build_research_event_information_asymmetry_scorecard(
        rows,
        generated_at=generated_at,
        config=cfg or _config(),
        public_notes=public_notes,
    )


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


def _assert_decimal_numeric_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {"paper_only", "report_only", "readonly"}:
            continue
        item = getattr(value, field.name)
        if item is None:
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if field.name.endswith(("_count", "_score", "_hours", "_ratio")):
            assert type(item) is Decimal


def test_scorecard_builds_pass_watch_and_block_public_report() -> None:
    report = _report(
        (
            _input("raw-candidate-alpha?market=hidden&token=secret"),
            _input(
                "event-domain-watch",
                source_diversity_score=d("0.700000"),
                freshness_age_hours=d("30.000000"),
                contradiction_score=d("0.350000"),
                resolution_clarity_score=d("0.700000"),
                team_expertise_score=d("0.650000"),
            ),
            _input(
                "event-domain-block",
                source_diversity_score=d("0.500000"),
                freshness_age_hours=d("80.000000"),
                contradiction_score=d("0.700000"),
                resolution_clarity_score=d("0.400000"),
                team_expertise_score=d("0.350000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
        public_notes=(
            ResearchEventInformationAsymmetryPublicNote(
                key="review_scope",
                value="public information quality review only",
            ),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == DEFAULT_RESEARCH_EVENT_INFORMATION_ASYMMETRY_SCORECARD_CONFIG_VERSION
    assert report.public_status == "block"
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_asymmetry_score == d("0.375833")
    assert report.max_asymmetry_score == d("0.682500")
    assert report.min_source_diversity_score == d("0.500000")
    assert report.max_freshness_age_hours == d("80.000000")
    assert report.max_contradiction_score == d("0.700000")
    assert report.min_resolution_clarity_score == d("0.400000")
    assert report.min_team_expertise_score == d("0.350000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.public_status for row in report.rows) == ("block", "watch", "pass")

    blocked = report.rows[0]
    assert type(blocked) is ResearchEventInformationAsymmetryRow
    assert blocked.source_diversity_gap_score == d("0.500000")
    assert blocked.freshness_gap_score == d("1.000000")
    assert blocked.contradiction_score == d("0.700000")
    assert blocked.resolution_clarity_gap_score == d("0.600000")
    assert blocked.team_expertise_gap_score == d("0.650000")
    assert blocked.asymmetry_score == d("0.682500")
    assert blocked.reason_codes == (
        "source_diversity_block",
        "freshness_block",
        "contradiction_block",
        "resolution_clarity_block",
        "team_expertise_block",
        "asymmetry_score_watch",
    )

    watched = report.rows[1]
    assert watched.freshness_gap_score == d("0.416667")
    assert watched.asymmetry_score == d("0.340833")
    assert watched.reason_codes == (
        "source_diversity_watch",
        "freshness_watch",
        "contradiction_watch",
        "resolution_clarity_watch",
        "team_expertise_watch",
    )

    passed = report.rows[2]
    assert passed.asymmetry_score == d("0.104167")
    assert passed.reason_codes == ("information_quality_pass",)


def test_empty_scorecard_is_report_only_block() -> None:
    report = _report(())

    assert report.public_status == "block"
    assert report.row_count == ZERO
    assert report.pass_count == ZERO
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.average_asymmetry_score == ZERO
    assert report.max_asymmetry_score == ZERO
    assert report.min_source_diversity_score == ZERO
    assert report.max_freshness_age_hours == ZERO
    assert report.max_contradiction_score == ZERO
    assert report.min_resolution_clarity_score == ZERO
    assert report.min_team_expertise_score == ZERO
    assert report.rows == ()
    assert report.reason_code_counts == (
        ResearchEventInformationAsymmetryReasonCodeCount(
            reason_code="empty_input",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )
    assert report.reason_codes == ("empty_input",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_redacts_private_domain_keys_and_serializes_decimal_strings() -> None:
    report = _report(
        (
            _input("raw-candidate-id/market-slug?token=hidden&wallet=private"),
        ),
    )

    payload = research_event_information_asymmetry_scorecard_payload(report)
    rendered = repr(payload).casefold()
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == report.payload
    assert payload["row_count"] == "1.000000"
    assert payload["rows"][0]["asymmetry_score"] == "0.104167"
    assert payload["rows"][0]["domain_digest"].startswith("sha256:")
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert ": 1.0" not in encoded
    for leaked in (
        "raw-candidate-id",
        "market-slug",
        "token",
        "hidden",
        "wallet",
        "private",
    ):
        assert leaked not in rendered
        assert leaked not in repr(asdict(report)).casefold()


def test_decimal_type_rejection_and_frozen_public_dataclasses() -> None:
    assert is_dataclass(ResearchEventInformationAsymmetryScorecardConfig)
    assert is_dataclass(ResearchEventInformationAsymmetryInput)
    assert is_dataclass(ResearchEventInformationAsymmetryPublicNote)
    assert is_dataclass(ResearchEventInformationAsymmetryReasonCodeCount)
    assert is_dataclass(ResearchEventInformationAsymmetryRow)
    assert is_dataclass(ResearchEventInformationAsymmetryReport)

    cfg = _config()
    row = _input()
    report = _report((row,), cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.contradiction_score = d("0.200000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].asymmetry_score = ZERO  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.public_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass(DEFAULT_RESEARCH_EVENT_INFORMATION_ASYMMETRY_SCORECARD_CONFIG_VERSION))
    with pytest.raises(ValueError, match="min_source_diversity_score"):
        _config(min_source_diversity_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_contradiction_score"):
        _config(watch_contradiction_score=_DecimalSubclass("0.300000"))
    with pytest.raises(ValueError, match="block_freshness_age_hours"):
        _config(block_freshness_age_hours=d("12.000000"))
    with pytest.raises(ValueError, match="watch_contradiction_score"):
        _config(watch_contradiction_score=d("0.800000"))
    with pytest.raises(ValueError, match="min_resolution_clarity_score"):
        _config(min_resolution_clarity_score=d("0.900000"))
    with pytest.raises(ValueError, match="min_team_expertise_score"):
        _config(min_team_expertise_score=d("0.800000"))
    with pytest.raises(ValueError, match="watch_asymmetry_score"):
        _config(watch_asymmetry_score=d("0.800000"))
    with pytest.raises(ValueError, match="asymmetry score weights"):
        _config(source_diversity_weight=d("0.300000"))
    with pytest.raises(ValueError, match="domain_key"):
        _input(_StringSubclass("event-domain-alpha"))
    with pytest.raises(ValueError, match="domain_key"):
        _input(" event-domain-alpha")
    with pytest.raises(ValueError, match="source_diversity_score"):
        _input(source_diversity_score="0.900000")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="freshness_age_hours"):
        _input(freshness_age_hours=6)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="contradiction_score"):
        _input(contradiction_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="generated_at"):
        build_research_event_information_asymmetry_scorecard(
            (),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
            config=_config(),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_event_information_asymmetry_scorecard(
            (),
            generated_at=datetime(2026, 7, 8, 12, 0),
            config=_config(),
        )
    with pytest.raises(ValueError, match="config"):
        build_research_event_information_asymmetry_scorecard(
            (),
            generated_at=GENERATED_AT,
            config=object(),  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="inputs"):
        _report((object(),))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    (
        ("key", "source_ref"),
        ("key", "wallet"),
        ("value", "https://example.test/source"),
        ("value", "raw source text copied here"),
        ("value", "buy or sell recommendation"),
        ("value", "wallet auth token"),
        ("value", "order trade position"),
        ("value", "private key copied"),
    ),
)
def test_public_leak_rejection_for_notes(field_name: str, field_value: str) -> None:
    values = {"key": "review_scope", "value": "public review only"}
    values[field_name] = field_value
    with pytest.raises(ValueError, match="unsafe public|contains unsafe public"):
        ResearchEventInformationAsymmetryPublicNote(**values)


def test_public_payload_rejects_forbidden_fields_values_and_statuses() -> None:
    report = _report((_input(),))
    payload = research_event_information_asymmetry_scorecard_payload(report)
    rendered = repr(payload).casefold()

    for token in (
        "candidate",
        "market",
        "slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
        "private key",
        "blocked",
    ):
        assert token not in rendered

    tampered_status = dict(payload)
    tampered_status["public_status"] = "blocked"
    with pytest.raises(ValueError, match="pass, watch, or block"):
        research_event_information_asymmetry_scorecard_payload(tampered_status)

    tampered_field = dict(payload)
    tampered_field["market_slug"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public field"):
        research_event_information_asymmetry_scorecard_payload(tampered_field)

    tampered_value = dict(payload)
    tampered_value["public_notes"] = [
        {
            "key": "review_scope",
            "value": "source text copied here",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    with pytest.raises(ValueError, match="unsafe public value"):
        research_event_information_asymmetry_scorecard_payload(tampered_value)


def test_hard_flags_are_enforced() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        _config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        _config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        _config(readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        _input(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        ResearchEventInformationAsymmetryPublicNote(
            key="review_scope",
            value="public review only",
            report_only=False,
        )

    report = _report((_input(),))
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report.rows[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report.reason_code_counts[0], readonly=False)


def test_manual_report_and_row_drift_rejected() -> None:
    report = _report((_input(),))
    passed = report.rows[0]

    with pytest.raises(ValueError, match="public_status"):
        replace(passed, public_status="block")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            passed,
            reason_codes=("information_quality_pass", "source_diversity_watch"),
        )
    with pytest.raises(ValueError, match="asymmetry_score"):
        replace(passed, asymmetry_score=ZERO, validation_config=_config())
    with pytest.raises(ValueError, match="domain_digest"):
        replace(passed, domain_digest="raw-candidate-market")

    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        unordered = _report((
            _input("event-domain-z", contradiction_score=d("0.700000")),
            _input("event-domain-a"),
        ))
        replace(unordered, rows=tuple(reversed(unordered.rows)))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_deterministic_payload_and_digest_independent_of_input_order() -> None:
    rows = (
        _input("event-domain-c", contradiction_score=d("0.700000")),
        _input("event-domain-a"),
        _input("event-domain-b", source_diversity_score=d("0.700000")),
    )
    notes = (
        ResearchEventInformationAsymmetryPublicNote(
            key="review_scope",
            value="public review only",
        ),
    )

    report_a = _report(rows, public_notes=notes)
    report_b = _report(tuple(reversed(rows)), public_notes=notes)

    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert research_event_information_asymmetry_scorecard_payload(
        report_a,
    ) == research_event_information_asymmetry_scorecard_payload(report_b)
    assert tuple(row.public_status for row in report_a.rows) == ("block", "watch", "pass")

    tampered = research_event_information_asymmetry_scorecard_payload(report_a)
    tampered["row_count"] = "4.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_event_information_asymmetry_scorecard_payload(tampered)


def test_public_numeric_fields_are_decimals() -> None:
    source_row = _input()
    report = _report((source_row,))

    _assert_decimal_numeric_fields(source_row)
    _assert_decimal_numeric_fields(report)
    _assert_decimal_numeric_fields(report.rows[0])
    _assert_decimal_numeric_fields(report.reason_code_counts[0])


def test_module_scope_is_read_only_report_only_and_public_api_is_narrow() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.research_event_information_asymmetry_scorecard",
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_EVENT_INFORMATION_ASYMMETRY_SCORECARD_CONFIG_VERSION",
        "ResearchEventInformationAsymmetryInput",
        "ResearchEventInformationAsymmetryPublicNote",
        "ResearchEventInformationAsymmetryReasonCodeCount",
        "ResearchEventInformationAsymmetryReport",
        "ResearchEventInformationAsymmetryRow",
        "ResearchEventInformationAsymmetryScorecardConfig",
        "build_research_event_information_asymmetry_scorecard",
        "research_event_information_asymmetry_scorecard_payload",
    )

    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    call_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_roots = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
        "float",
        "__import__",
    }

    for module_name in imported_modules:
        assert module_name.split(".", 1)[0] not in forbidden_import_roots
    for call_name in call_names:
        assert call_name not in forbidden_calls
