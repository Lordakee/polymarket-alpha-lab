from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_probability_model_disagreement_report import (
    DEFAULT_RESEARCH_PROBABILITY_MODEL_DISAGREEMENT_REPORT_CONFIG_VERSION,
    ResearchProbabilityModelDisagreementConfig,
    ResearchProbabilityModelDisagreementDigest,
    ResearchProbabilityModelDisagreementInput,
    ResearchProbabilityModelDisagreementReport,
    ResearchProbabilityModelDisagreementRow,
    build_research_probability_model_disagreement_report,
    research_probability_model_disagreement_digest,
    research_probability_model_disagreement_digest_payload,
    research_probability_model_disagreement_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_probability_model_disagreement_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchProbabilityModelDisagreementConfig:
    values: dict[str, object] = {
        "config_version": "research-probability-model-disagreement-test-v0",
        "min_estimate_count": d("2"),
        "watch_probability_range": d("0.100000"),
        "block_probability_range": d("0.250000"),
        "watch_model_team_gap": d("0.080000"),
        "block_model_team_gap": d("0.200000"),
    }
    values.update(overrides)
    return ResearchProbabilityModelDisagreementConfig(**values)


def estimate(
    public_case_key: str,
    participant_label: str,
    *,
    participant_type: str,
    probability: str,
    observed_at: datetime = GENERATED_AT,
    reason_codes: tuple[str, ...] = (),
) -> ResearchProbabilityModelDisagreementInput:
    return ResearchProbabilityModelDisagreementInput(
        public_case_key=public_case_key,
        participant_type=participant_type,
        participant_label=participant_label,
        probability=d(probability),
        observed_at=observed_at,
        reason_codes=reason_codes,
    )


def report(
    *rows: ResearchProbabilityModelDisagreementInput,
    cfg: ResearchProbabilityModelDisagreementConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchProbabilityModelDisagreementReport:
    return build_research_probability_model_disagreement_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_pass_watch_block_statuses_and_human_review_rollup() -> None:
    disagreement_report = report(
        estimate("case-pass", "model-alpha", participant_type="model", probability="0.520000"),
        estimate(
            "case-pass",
            "team-alpha",
            participant_type="research_team",
            probability="0.560000",
        ),
        estimate("case-watch", "model-alpha", participant_type="model", probability="0.400000"),
        estimate(
            "case-watch",
            "team-alpha",
            participant_type="research_team",
            probability="0.530000",
        ),
        estimate("case-block", "model-alpha", participant_type="model", probability="0.200000"),
        estimate(
            "case-block",
            "model-beta",
            participant_type="model",
            probability="0.240000",
        ),
        estimate(
            "case-block",
            "team-alpha",
            participant_type="research_team",
            probability="0.510000",
        ),
    )

    assert disagreement_report.config_version == "research-probability-model-disagreement-test-v0"
    assert disagreement_report.status == "block"
    assert disagreement_report.human_review_status == "block"
    assert tuple(row.public_case_key for row in disagreement_report.rows) == (
        "case-block",
        "case-watch",
        "case-pass",
    )
    assert disagreement_report.case_count == d("3.000000")
    assert disagreement_report.estimate_count == d("7.000000")
    assert disagreement_report.pass_count == d("1.000000")
    assert disagreement_report.watch_count == d("1.000000")
    assert disagreement_report.block_count == d("1.000000")
    assert disagreement_report.max_probability_range == d("0.310000")
    assert disagreement_report.max_model_team_gap == d("0.290000")
    assert disagreement_report.average_probability_range == d("0.160000")

    block_row = disagreement_report.rows[0]
    assert type(block_row) is ResearchProbabilityModelDisagreementRow
    assert block_row.status == "block"
    assert block_row.human_review_status == "block"
    assert block_row.participant_labels == ("model-alpha", "model-beta", "team-alpha")
    assert block_row.estimate_count == d("3.000000")
    assert block_row.model_count == d("2.000000")
    assert block_row.research_team_count == d("1.000000")
    assert block_row.min_probability == d("0.200000")
    assert block_row.max_probability == d("0.510000")
    assert block_row.mean_probability == d("0.316667")
    assert block_row.model_mean_probability == d("0.220000")
    assert block_row.research_team_mean_probability == d("0.510000")
    assert block_row.probability_range == d("0.310000")
    assert block_row.model_team_gap == d("0.290000")
    assert block_row.reason_codes == (
        "model_team_gap_block",
        "probability_model_disagreement_block",
        "probability_range_block",
    )
    assert disagreement_report.reason_codes == (
        "model_team_gap_block",
        "model_team_gap_watch",
        "probability_model_disagreement_block",
        "probability_model_disagreement_pass",
        "probability_model_disagreement_watch",
        "probability_range_block",
        "probability_range_watch",
    )
    assert disagreement_report.reason_code_counts[0].reason_code == "model_team_gap_block"
    assert disagreement_report.reason_code_counts[0].count == d("1.000000")
    assert disagreement_report.paper_only is True
    assert disagreement_report.report_only is True
    assert disagreement_report.readonly is True


def test_missing_family_blocks_for_manual_review_without_trading_language() -> None:
    disagreement_report = report(
        estimate("case-missing-team", "model-alpha", participant_type="model", probability="0.520000"),
    )
    payload = research_probability_model_disagreement_report_payload(disagreement_report)
    encoded = json.dumps(payload, sort_keys=True).lower()

    assert disagreement_report.status == "block"
    assert disagreement_report.rows[0].status == "block"
    assert disagreement_report.rows[0].human_review_status == "block"
    assert "research_team_missing_block" in disagreement_report.rows[0].reason_codes
    assert "estimate_count_below_minimum_block" in disagreement_report.rows[0].reason_codes
    assert "advice" not in encoded
    assert "buy" not in encoded
    assert "sell" not in encoded
    assert "recommend" not in encoded
    assert "position" not in encoded


def test_empty_report_blocks_with_digest_consistency() -> None:
    disagreement_report = report()
    digest = research_probability_model_disagreement_digest(disagreement_report)

    assert type(disagreement_report.digest) is ResearchProbabilityModelDisagreementDigest
    assert disagreement_report.digest == digest
    assert disagreement_report.status == "block"
    assert disagreement_report.human_review_status == "block"
    assert disagreement_report.case_count == d("0.000000")
    assert disagreement_report.estimate_count == d("0.000000")
    assert disagreement_report.reason_codes == ("probability_model_disagreement_missing_inputs",)
    assert disagreement_report.reason_code_counts[0].count == d("1.000000")
    assert disagreement_report.digest.reason_codes == disagreement_report.reason_codes
    assert research_probability_model_disagreement_report_payload(disagreement_report)[
        "digest"
    ] == research_probability_model_disagreement_digest_payload(digest)


def test_decimal_type_rejection_and_frozen_public_dataclasses() -> None:
    valid = estimate(
        "case-type",
        "model-alpha",
        participant_type="model",
        probability="0.520000",
        observed_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
    )
    assert valid.observed_at == GENERATED_AT
    with pytest.raises(FrozenInstanceError):
        valid.probability = d("0.530000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="watch_probability_range"):
        config(watch_probability_range=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="block_model_team_gap"):
        config(block_model_team_gap=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="min_estimate_count"):
        config(min_estimate_count=d("1.5"))
    with pytest.raises(ValueError, match="probability"):
        ResearchProbabilityModelDisagreementInput(
            public_case_key="case-type",
            participant_type="model",
            participant_label="model-alpha",
            probability="0.500000",  # type: ignore[arg-type]
            observed_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="observed_at"):
        estimate(
            "case-type",
            "model-alpha",
            participant_type="model",
            probability="0.520000",
            observed_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(valid, generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("public_case_key", "market_id:123"),
        ("public_case_key", "market-slug-election"),
        ("public_case_key", "raw-candidate-abc"),
        ("public_case_key", "question-will-it-happen"),
        ("participant_label", "source-ref-https-example"),
        ("participant_label", "dsn-table-token"),
        ("participant_label", "wallet-order-field"),
        ("reason_codes", ("buy_yes_recommendation",)),
    ),
)
def test_public_leak_rejection(field_name: str, value: object) -> None:
    values: dict[str, object] = {
        "public_case_key": "case-public",
        "participant_type": "model",
        "participant_label": "model-alpha",
        "probability": d("0.520000"),
        "observed_at": GENERATED_AT,
        "reason_codes": (),
    }
    values[field_name] = value

    with pytest.raises(ValueError, match=field_name):
        ResearchProbabilityModelDisagreementInput(**values)


def test_hard_flags_are_required_for_config_inputs_report_and_digest() -> None:
    valid = estimate("case-flags", "model-alpha", participant_type="model", probability="0.520000")
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(valid, readonly=False)

    disagreement_report = report(
        valid,
        estimate(
            "case-flags",
            "team-alpha",
            participant_type="research_team",
            probability="0.540000",
        ),
    )
    with pytest.raises(ValueError, match="report_only"):
        replace(disagreement_report.digest, report_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(disagreement_report, report_only=False)


def test_deterministic_payload_and_report_digest_consistency() -> None:
    rows = (
        estimate("case-z", "team-z", participant_type="research_team", probability="0.620000"),
        estimate("case-a", "model-a", participant_type="model", probability="0.510000"),
        estimate("case-z", "model-z", participant_type="model", probability="0.350000"),
        estimate("case-a", "team-a", participant_type="research_team", probability="0.540000"),
    )

    first = report(*rows)
    second = report(*tuple(reversed(rows)))
    first_payload = research_probability_model_disagreement_report_payload(first)
    second_payload = research_probability_model_disagreement_report_payload(second)
    digest_payload = research_probability_model_disagreement_digest_payload(
        research_probability_model_disagreement_digest(first),
    )

    assert first == second
    assert first_payload == second_payload
    assert tuple(row.public_case_key for row in first.rows) == ("case-z", "case-a")
    assert first_payload["digest"] == digest_payload
    assert first.digest.status == first.status
    assert first.digest.human_review_status == first.human_review_status
    assert first.digest.max_probability_range == first.max_probability_range
    assert first.digest.max_model_team_gap == first.max_model_team_gap
    assert not any(
        type(value) in (Decimal, float, int) for value in walk_payload_values(first_payload)
    )
    assert json.dumps(first_payload, sort_keys=True) == json.dumps(second_payload, sort_keys=True)

    bad_digest = replace(first.digest, max_probability_range=d("0.000000"))
    with pytest.raises(ValueError, match="digest"):
        replace(first, digest=bad_digest)
    with pytest.raises(ValueError, match="payload"):
        research_probability_model_disagreement_report_payload(object())  # type: ignore[arg-type]


def test_public_payload_contains_no_private_identifiers_or_io_capability_surface() -> None:
    module_source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(module_source)
    disagreement_report = report(
        estimate("case-safe", "model-alpha", participant_type="model", probability="0.520000"),
        estimate(
            "case-safe",
            "team-alpha",
            participant_type="research_team",
            probability="0.540000",
        ),
    )
    encoded = json.dumps(
        research_probability_model_disagreement_report_payload(disagreement_report),
        sort_keys=True,
    ).lower()

    forbidden_payload_terms = (
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    )
    forbidden_imports = {
        "aiohttp",
        "httpx",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlalchemy",
        "subprocess",
        "urllib",
        "web3",
    }
    forbidden_calls = {
        "connect",
        "create_order",
        "execute",
        "open",
        "place_order",
        "post",
        "submit_order",
    }

    assert all(term not in encoded for term in forbidden_payload_terms)
    imported_roots = {
        node.names[0].name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    } | {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert imported_roots.isdisjoint(forbidden_imports)
    assert called_names.isdisjoint(forbidden_calls)
    assert DEFAULT_RESEARCH_PROBABILITY_MODEL_DISAGREEMENT_REPORT_CONFIG_VERSION.endswith(
        "-v0",
    )


def walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
