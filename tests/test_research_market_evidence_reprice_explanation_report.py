from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_market_evidence_reprice_explanation_report"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "evidence_age_watch_seconds": d("3600.000000"),
        "evidence_age_block_seconds": d("7200.000000"),
        "source_class_quorum_watch_ratio": d("0.750000"),
        "source_class_quorum_block_ratio": d("0.500000"),
        "unexplained_book_movement_watch_bps": d("100.000000"),
        "unexplained_book_movement_block_bps": d("250.000000"),
        "contradiction_pressure_watch_ratio": d("0.250000"),
        "contradiction_pressure_block_ratio": d("0.500000"),
        "manual_review_urgency_watch_ratio": d("0.750000"),
        "manual_review_urgency_block_ratio": d("1.000000"),
    }
    values.update(overrides)
    return module.ResearchMarketEvidenceRepriceExplanationConfig(**values)


def input_row(
    aggregate_row_number: Decimal,
    *,
    evidence_age_seconds: Decimal = d("600.000000"),
    source_class_quorum_count: Decimal = d("3.000000"),
    required_source_class_quorum_count: Decimal = d("3.000000"),
    total_book_movement_bps: Decimal = d("80.000000"),
    explained_book_movement_bps: Decimal = d("80.000000"),
    contradiction_count: Decimal = d("0.000000"),
    evidence_claim_count: Decimal = d("4.000000"),
    manual_review_age_seconds: Decimal = d("60.000000"),
    manual_review_sla_seconds: Decimal = d("3600.000000"),
) -> Any:
    module = api()
    return module.ResearchMarketEvidenceRepriceExplanationInput(
        aggregate_row_number=aggregate_row_number,
        evidence_age_seconds=evidence_age_seconds,
        source_class_quorum_count=source_class_quorum_count,
        required_source_class_quorum_count=required_source_class_quorum_count,
        total_book_movement_bps=total_book_movement_bps,
        explained_book_movement_bps=explained_book_movement_bps,
        contradiction_count=contradiction_count,
        evidence_claim_count=evidence_claim_count,
        manual_review_age_seconds=manual_review_age_seconds,
        manual_review_sla_seconds=manual_review_sla_seconds,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_market_evidence_reprice_explanation_report(
        rows,
        config=config() if cfg is None else cfg,
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(
        unsigned,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def assert_no_float_or_int_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, int) and not isinstance(value, bool):
        raise AssertionError(f"unexpected int value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def test_empty_report_is_pass_readonly_and_digest_validated() -> None:
    module = api()
    report = build_report()
    payload = module.research_market_evidence_reprice_explanation_report_payload(report)

    assert report.status == "pass"
    assert report.row_count == d("0.000000")
    assert report.pass_row_count == d("0.000000")
    assert report.watch_row_count == d("0.000000")
    assert report.block_row_count == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("evidence_reprice_explanation_no_rows",)
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_report_classifies_evidence_explainability_and_sorts_rows() -> None:
    report = build_report(
        input_row(d("2.000000")),
        input_row(
            d("3.000000"),
            evidence_age_seconds=d("4000.000000"),
            source_class_quorum_count=d("2.000000"),
            required_source_class_quorum_count=d("3.000000"),
            total_book_movement_bps=d("200.000000"),
            explained_book_movement_bps=d("80.000000"),
            contradiction_count=d("1.000000"),
            evidence_claim_count=d("5.000000"),
            manual_review_age_seconds=d("2800.000000"),
            manual_review_sla_seconds=d("3600.000000"),
        ),
        input_row(
            d("1.000000"),
            evidence_age_seconds=d("8000.000000"),
            source_class_quorum_count=d("1.000000"),
            required_source_class_quorum_count=d("3.000000"),
            total_book_movement_bps=d("500.000000"),
            explained_book_movement_bps=d("100.000000"),
            contradiction_count=d("3.000000"),
            evidence_claim_count=d("4.000000"),
            manual_review_age_seconds=d("4000.000000"),
            manual_review_sla_seconds=d("3600.000000"),
        ),
    )

    assert tuple(row.aggregate_row_number for row in report.rows) == (
        d("1.000000"),
        d("3.000000"),
        d("2.000000"),
    )
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.unexplained_book_movement_bps for row in report.rows) == (
        d("400.000000"),
        d("120.000000"),
        d("0.000000"),
    )
    assert tuple(row.source_class_quorum_ratio for row in report.rows) == (
        d("0.333333"),
        d("0.666667"),
        d("1.000000"),
    )
    assert report.status == "block"
    assert report.row_count == d("3.000000")
    assert report.pass_row_count == d("1.000000")
    assert report.watch_row_count == d("1.000000")
    assert report.block_row_count == d("1.000000")
    assert report.max_unexplained_book_movement_bps == d("400.000000")
    assert report.max_contradiction_pressure_ratio == d("0.750000")
    assert report.max_manual_review_urgency_ratio == d("1.111111")
    assert report.reason_codes == (
        "evidence_reprice_explanation_stale_evidence",
        "evidence_reprice_explanation_source_class_quorum_gap",
        "evidence_reprice_explanation_unexplained_book_movement",
        "evidence_reprice_explanation_contradiction_pressure",
        "evidence_reprice_explanation_manual_review_urgent",
    )


def test_payload_is_deterministic_digest_checked_and_public_only() -> None:
    module = api()
    first = build_report(input_row(d("1.000000")))
    second = build_report(input_row(d("1.000000")))

    first_payload = first.payload
    second_payload = second.payload
    assert first_payload == second_payload
    assert json.dumps(first_payload, allow_nan=False, sort_keys=True) == json.dumps(
        second_payload,
        allow_nan=False,
        sort_keys=True,
    )
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert len(first.derived_validation_digest) == 64
    int(first.derived_validation_digest, 16)
    assert_no_float_or_int_values(first_payload)

    payload_text = json.dumps(first_payload, sort_keys=True).lower()
    for forbidden in (
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "private_token",
        "token",
    ):
        assert forbidden not in payload_text
        with pytest.raises(ValueError, match="unsafe public payload"):
            module.reject_research_market_evidence_reprice_explanation_unsafe_public_payload(
                "unsafe payload",
                {forbidden: "redacted"},
            )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)


def test_validation_frozen_dataclasses_decimal_only_flags_and_scope() -> None:
    module = api()
    cfg = config()
    subject = input_row(d("1.000000"))
    report = build_report(subject)

    assert module.STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "DEFAULT_RESEARCH_MARKET_EVIDENCE_REPRICE_EXPLANATION_CONFIG_VERSION",
        "STATUSES",
        "ResearchMarketEvidenceRepriceExplanationConfig",
        "ResearchMarketEvidenceRepriceExplanationInput",
        "ResearchMarketEvidenceRepriceExplanationReport",
        "ResearchMarketEvidenceRepriceExplanationRow",
        "build_research_market_evidence_reprice_explanation_report",
        "reject_research_market_evidence_reprice_explanation_unsafe_public_payload",
        "research_market_evidence_reprice_explanation_report_payload",
    )
    for instance in (cfg, subject, report, report.rows[0]):
        assert is_dataclass(instance)
        assert instance.__dataclass_params__.frozen
        assert instance.paper_only is True
        assert instance.report_only is True
        assert instance.readonly is True

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        cfg.evidence_age_watch_seconds = d("1.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="aggregate_row_number must be a Decimal"):
        input_row(1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="aggregate_row_number must be a Decimal"):
        input_row(DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="aggregate_row_number must be integral"):
        input_row(d("1.500000"))
    with pytest.raises(ValueError, match="evidence_age_seconds must be nonnegative"):
        input_row(d("1.000000"), evidence_age_seconds=d("-1.000000"))
    with pytest.raises(ValueError, match="explained_book_movement_bps"):
        input_row(
            d("1.000000"),
            total_book_movement_bps=d("10.000000"),
            explained_book_movement_bps=d("20.000000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(subject, readonly=False)
    with pytest.raises(ValueError, match="config"):
        module.build_research_market_evidence_reprice_explanation_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
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
