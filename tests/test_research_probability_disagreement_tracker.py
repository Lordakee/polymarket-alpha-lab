from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_probability_disagreement_tracker import (
    DEFAULT_RESEARCH_PROBABILITY_DISAGREEMENT_TRACKER_CONFIG_VERSION,
    ResearchProbabilityDisagreementConfig,
    ResearchProbabilityDisagreementInput,
    ResearchProbabilityDisagreementReport,
    build_research_probability_disagreement_report,
    research_probability_disagreement_report_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_probability_disagreement_tracker.py"
)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchProbabilityDisagreementConfig:
    values: dict[str, object] = {
        "config_version": "research-probability-disagreement-test-v0",
        "watch_disagreement_threshold": d("0.050000"),
        "block_disagreement_threshold": d("0.150000"),
    }
    values.update(overrides)
    return ResearchProbabilityDisagreementConfig(**values)


def input_row(
    market_slug: str,
    *,
    model: str,
    team: str,
    market: str,
    observed_at: datetime = GENERATED_AT,
    public_notes: str = "public research probability comparison",
) -> ResearchProbabilityDisagreementInput:
    return ResearchProbabilityDisagreementInput(
        market_slug=market_slug,
        model_probability=d(model),
        team_probability=d(team),
        market_implied_probability=d(market),
        observed_at=observed_at,
        public_notes=public_notes,
    )


def report(
    *rows: ResearchProbabilityDisagreementInput,
    cfg: ResearchProbabilityDisagreementConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchProbabilityDisagreementReport:
    return build_research_probability_disagreement_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_probability_disagreement_report_tracks_pairwise_gaps_and_status_counts() -> None:
    disagreement_report = report(
        input_row(
            "pass-market",
            model="0.520000",
            team="0.530000",
            market="0.510000",
        ),
        input_row(
            "block-market",
            model="0.900000",
            team="0.650000",
            market="0.600000",
        ),
        input_row(
            "watch-market",
            model="0.700000",
            team="0.620000",
            market="0.680000",
        ),
    )

    assert disagreement_report.config_version == "research-probability-disagreement-test-v0"
    assert disagreement_report.status == "block"
    assert tuple(row.market_slug for row in disagreement_report.rows) == (
        "block-market",
        "watch-market",
        "pass-market",
    )
    assert disagreement_report.market_count == d("3.000000")
    assert disagreement_report.pass_count == d("1.000000")
    assert disagreement_report.watch_count == d("1.000000")
    assert disagreement_report.block_count == d("1.000000")
    assert disagreement_report.largest_abs_disagreement == d("0.300000")
    assert disagreement_report.average_max_abs_disagreement == d("0.133333")

    block_row = disagreement_report.rows[0]
    assert block_row.status == "block"
    assert block_row.model_team_abs_disagreement == d("0.250000")
    assert block_row.model_market_abs_disagreement == d("0.300000")
    assert block_row.team_market_abs_disagreement == d("0.050000")
    assert block_row.average_abs_disagreement == d("0.200000")
    assert block_row.reason_codes == (
        "probability_disagreement_block",
        "probability_disagreement_model_market",
        "probability_disagreement_model_team",
        "probability_disagreement_team_market",
    )
    assert disagreement_report.reason_code_counts == (
        ("probability_disagreement_block", d("1.000000")),
        ("probability_disagreement_model_market", d("1.000000")),
        ("probability_disagreement_model_team", d("2.000000")),
        ("probability_disagreement_pass", d("1.000000")),
        ("probability_disagreement_team_market", d("2.000000")),
        ("probability_disagreement_watch", d("1.000000")),
    )
    assert disagreement_report.reason_codes == (
        "probability_disagreement_block",
        "probability_disagreement_model_market",
        "probability_disagreement_model_team",
        "probability_disagreement_pass",
        "probability_disagreement_team_market",
        "probability_disagreement_watch",
    )
    assert all(
        type(value) is Decimal
        for value in (
            disagreement_report.market_count,
            disagreement_report.pass_count,
            disagreement_report.watch_count,
            disagreement_report.block_count,
            disagreement_report.largest_abs_disagreement,
            disagreement_report.average_max_abs_disagreement,
            block_row.model_team_abs_disagreement,
            block_row.model_market_abs_disagreement,
            block_row.team_market_abs_disagreement,
            block_row.max_abs_disagreement,
            block_row.average_abs_disagreement,
        )
    )
    assert all(
        value.as_tuple().exponent == -6
        for value in (
            disagreement_report.market_count,
            disagreement_report.largest_abs_disagreement,
            disagreement_report.average_max_abs_disagreement,
            block_row.model_team_abs_disagreement,
            block_row.average_abs_disagreement,
        )
    )
    assert disagreement_report.paper_only is True
    assert disagreement_report.report_only is True
    assert disagreement_report.readonly is True


def test_probability_disagreement_report_passes_when_all_gaps_are_below_watch_threshold() -> None:
    disagreement_report = report(
        input_row(
            "aligned-market",
            model="0.520000",
            team="0.530000",
            market="0.510000",
        ),
    )

    assert disagreement_report.status == "pass"
    assert disagreement_report.pass_count == d("1.000000")
    assert disagreement_report.watch_count == d("0.000000")
    assert disagreement_report.block_count == d("0.000000")
    assert disagreement_report.reason_codes == ("probability_disagreement_pass",)


def test_probability_disagreement_empty_report_blocks_as_missing_research_inputs() -> None:
    disagreement_report = report()

    assert disagreement_report.status == "block"
    assert disagreement_report.market_count == d("0.000000")
    assert disagreement_report.largest_abs_disagreement == d("0.000000")
    assert disagreement_report.average_max_abs_disagreement == d("0.000000")
    assert disagreement_report.rows == ()
    assert disagreement_report.reason_codes == ("probability_disagreement_missing_inputs",)
    assert disagreement_report.reason_code_counts == (
        ("probability_disagreement_missing_inputs", d("1.000000")),
    )


def test_probability_disagreement_payload_is_public_json_ready_and_decimal_string_only() -> None:
    disagreement_report = report(
        input_row(
            "utc-market",
            model="0.700000",
            team="0.620000",
            market="0.680000",
            observed_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=2))),
    )

    payload = research_probability_disagreement_report_payload(disagreement_report)

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["market_count"] == "1.000000"
    assert payload["average_max_abs_disagreement"] == "0.080000"
    assert payload["rows"][0]["observed_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["rows"][0]["model_probability"] == "0.700000"
    assert payload["rows"][0]["model_team_abs_disagreement"] == "0.080000"
    assert payload["reason_code_counts"][0][1] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, (float, Decimal)) for value in walk_values(payload))


def test_probability_disagreement_dataclasses_are_frozen_and_normalize_utc() -> None:
    row = input_row(
        "frozen-market",
        model="0.700000",
        team="0.620000",
        market="0.680000",
        observed_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
    )

    assert row.observed_at == GENERATED_AT
    with pytest.raises(FrozenInstanceError):
        row.paper_only = False  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("model_probability", 1),
        ("model_probability", 0.5),
        ("team_probability", "0.500000"),
        ("market_implied_probability", None),
    ),
)
def test_probability_disagreement_inputs_require_decimal_public_probabilities(
    field_name: str,
    value: object,
) -> None:
    values: dict[str, object] = {
        "market_slug": "strict-market",
        "model_probability": d("0.500000"),
        "team_probability": d("0.510000"),
        "market_implied_probability": d("0.520000"),
        "observed_at": GENERATED_AT,
        "public_notes": "public probability comparison",
    }
    values[field_name] = value

    with pytest.raises(ValueError, match=field_name):
        ResearchProbabilityDisagreementInput(**values)


def test_probability_disagreement_validation_rejects_bad_thresholds_datetimes_and_flags() -> None:
    with pytest.raises(ValueError, match="model_probability"):
        input_row("bad-probability", model="1.100000", team="0.500000", market="0.500000")
    with pytest.raises(ValueError, match="observed_at"):
        input_row(
            "bad-time",
            model="0.500000",
            team="0.500000",
            market="0.500000",
            observed_at=datetime(2026, 7, 7, 12, 0),
        )
    with pytest.raises(ValueError, match="block_disagreement_threshold"):
        config(
            watch_disagreement_threshold=d("0.150000"),
            block_disagreement_threshold=d("0.050000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        ResearchProbabilityDisagreementConfig(paper_only=False)
    with pytest.raises(ValueError, match="rows"):
        build_research_probability_disagreement_report(
            (object(),),
            config=config(),
            generated_at=GENERATED_AT,
        )


def test_probability_disagreement_public_payload_rejects_sensitive_or_advice_text() -> None:
    with pytest.raises(ValueError, match="public_notes"):
        input_row(
            "unsafe-public-market",
            model="0.500000",
            team="0.510000",
            market="0.520000",
            public_notes="contains private token detail",
        )
    with pytest.raises(ValueError, match="public_notes"):
        input_row(
            "advice-public-market",
            model="0.500000",
            team="0.510000",
            market="0.520000",
            public_notes="buy yes for this outcome",
        )


def test_probability_disagreement_report_consistency_validation() -> None:
    disagreement_report = report(
        input_row("alpha", model="0.900000", team="0.650000", market="0.600000"),
        input_row("beta", model="0.520000", team="0.530000", market="0.510000"),
    )

    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            disagreement_report,
            reason_code_counts=tuple(reversed(disagreement_report.reason_code_counts)),
        )
    with pytest.raises(ValueError, match="rows"):
        replace(disagreement_report, rows=tuple(reversed(disagreement_report.rows)))
    with pytest.raises(ValueError, match="report"):
        research_probability_disagreement_report_payload(object())  # type: ignore[arg-type]


def test_probability_disagreement_module_is_report_only_and_has_no_io_surfaces() -> None:
    module = importlib.import_module("polymarket_alpha_lab.research_probability_disagreement_tracker")
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    disagreement_report = report(
        input_row("safe-market", model="0.520000", team="0.530000", market="0.510000"),
    )
    serialized_report = repr(research_probability_disagreement_report_payload(disagreement_report)).lower()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_PROBABILITY_DISAGREEMENT_TRACKER_CONFIG_VERSION",
        "ResearchProbabilityDisagreementConfig",
        "ResearchProbabilityDisagreementInput",
        "ResearchProbabilityDisagreementReport",
        "ResearchProbabilityDisagreementRow",
        "build_research_probability_disagreement_report",
        "research_probability_disagreement_report_payload",
    )
    forbidden_public_tokens = (
        "auth",
        "key",
        "private",
        "secret",
        "token",
        "wallet",
    )
    assert not any(token in serialized_report for token in forbidden_public_tokens)

    imported_modules: set[str] = set()
    call_names: list[str] = []
    attribute_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    forbidden_import_fragments = (
        "http",
        "psycopg",
        "requests",
        "socket",
        "sqlite",
        "supabase",
        "urllib",
    )
    forbidden_call_or_attribute_names = {
        "cancel",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "getenv",
        "open",
        "rollback",
        "send",
        "submit",
        "write",
    }

    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    assert not (set(call_names) & forbidden_call_or_attribute_names)
    assert not (set(attribute_names) & forbidden_call_or_attribute_names)
    assert all(not hasattr(module, name) for name in forbidden_call_or_attribute_names)


def test_probability_disagreement_public_numeric_fields_are_decimals() -> None:
    disagreement_report = report(
        input_row("numeric-market", model="0.700000", team="0.620000", market="0.680000"),
    )

    for value in (
        ResearchProbabilityDisagreementConfig(),
        disagreement_report.rows[0],
        disagreement_report,
    ):
        for field in fields(value):
            field_value = getattr(value, field.name)
            if (
                field.name.endswith("_probability")
                or field.name.endswith("_threshold")
                or field.name.endswith("_count")
                or field.name.endswith("_disagreement")
            ):
                assert type(field_value) is Decimal, field.name


def test_probability_disagreement_default_config_version_is_stable() -> None:
    assert DEFAULT_RESEARCH_PROBABILITY_DISAGREEMENT_TRACKER_CONFIG_VERSION == (
        "research-probability-disagreement-tracker-v0"
    )


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in walk_values(nested))
    return (value,)
