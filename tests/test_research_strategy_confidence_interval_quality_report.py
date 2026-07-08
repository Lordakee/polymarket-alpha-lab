from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from json import dumps

import pytest

from polymarket_alpha_lab.research_strategy_confidence_interval_quality_report import (
    DEFAULT_RESEARCH_STRATEGY_CONFIDENCE_INTERVAL_QUALITY_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_CONFIDENCE_INTERVAL_QUALITY_STATUSES,
    ResearchStrategyConfidenceIntervalQualityConfig,
    ResearchStrategyConfidenceIntervalQualityInput,
    ResearchStrategyConfidenceIntervalQualityReport,
    ResearchStrategyConfidenceIntervalQualityRow,
    build_research_strategy_confidence_interval_quality_report,
    research_strategy_confidence_interval_quality_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyConfidenceIntervalQualityConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_CONFIDENCE_INTERVAL_QUALITY_REPORT_CONFIG_VERSION
        ),
        "interval_width_watch_threshold": d("0.200000"),
        "interval_width_block_threshold": d("0.400000"),
        "calibration_support_watch_floor": d("0.700000"),
        "calibration_support_block_floor": d("0.400000"),
        "stale_evidence_watch_age_seconds": d("3600"),
        "stale_evidence_block_age_seconds": d("21600"),
        "source_confidence_watch_floor": d("0.800000"),
        "source_confidence_block_floor": d("0.500000"),
        "recheck_urgency_watch_threshold": d("0.500000"),
        "recheck_urgency_block_threshold": d("0.850000"),
    }
    values.update(overrides)
    return ResearchStrategyConfidenceIntervalQualityConfig(**values)


def ci_input(**overrides: object) -> ResearchStrategyConfidenceIntervalQualityInput:
    values = {
        "confidence_case_ref": "case_alpha",
        "strategy_ref": "strategy_alpha",
        "market_slug": "market-alpha",
        "observed_at": datetime(2026, 7, 8, 11, 50, tzinfo=UTC),
        "forecast_probability": d("0.500000"),
        "lower_bound_probability": d("0.450000"),
        "upper_bound_probability": d("0.550000"),
        "calibration_support_score": d("0.900000"),
        "source_confidence_score": d("0.920000"),
    }
    values.update(overrides)
    return ResearchStrategyConfidenceIntervalQualityInput(**values)


def report(
    *rows: ResearchStrategyConfidenceIntervalQualityInput,
    cfg: ResearchStrategyConfidenceIntervalQualityConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyConfidenceIntervalQualityReport:
    return build_research_strategy_confidence_interval_quality_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def resign_payload(payload: dict[str, object]) -> dict[str, object]:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    payload["derived_validation_digest"] = sha256(encoded).hexdigest()
    return payload


def test_report_scores_aggregate_interval_quality_for_manual_review() -> None:
    summary = report(
        ci_input(),
        ci_input(
            confidence_case_ref="case_beta",
            strategy_ref="strategy_beta",
            market_slug="market-beta",
            observed_at=datetime(2026, 7, 8, 10, 0, tzinfo=UTC),
            forecast_probability=d("0.420000"),
            lower_bound_probability=d("0.300000"),
            upper_bound_probability=d("0.550000"),
            calibration_support_score=d("0.650000"),
            source_confidence_score=d("0.720000"),
        ),
        ci_input(
            confidence_case_ref="case_gamma",
            strategy_ref="strategy_gamma",
            market_slug="market-gamma",
            observed_at=datetime(2026, 7, 7, 11, 0, tzinfo=UTC),
            forecast_probability=d("0.400000"),
            lower_bound_probability=d("0.100000"),
            upper_bound_probability=d("0.700000"),
            calibration_support_score=d("0.300000"),
            source_confidence_score=d("0.300000"),
        ),
    )

    assert summary.generated_at == GENERATED_AT
    assert (
        summary.config_version
        == DEFAULT_RESEARCH_STRATEGY_CONFIDENCE_INTERVAL_QUALITY_REPORT_CONFIG_VERSION
    )
    assert summary.source_row_count == d("3")
    assert summary.pass_count == d("1")
    assert summary.watch_count == d("1")
    assert summary.block_count == d("1")
    assert summary.mean_interval_width_probability == d("0.316667")
    assert summary.mean_calibration_support_score == d("0.616667")
    assert summary.mean_stale_evidence_pressure == d("0.400000")
    assert summary.mean_source_confidence_score == d("0.646667")
    assert summary.mean_recheck_urgency_score == d("0.625000")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "calibration_support_review",
        "confidence_interval_quality_block",
        "interval_width_review",
        "recheck_urgency_review",
        "source_confidence_review",
        "stale_evidence_review",
    )
    assert tuple(row.confidence_case_ref for row in summary.rows) == (
        "case_gamma",
        "case_beta",
        "case_alpha",
    )

    blocked = summary.rows[0]
    assert isinstance(blocked, ResearchStrategyConfidenceIntervalQualityRow)
    assert blocked.interval_width_probability == d("0.600000")
    assert blocked.stale_evidence_age_seconds == d("90000")
    assert blocked.stale_evidence_pressure == d("1.000000")
    assert blocked.recheck_urgency_score == d("1.000000")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "calibration_support_block",
        "interval_width_block",
        "recheck_urgency_block",
        "source_confidence_block",
        "stale_evidence_block",
    )

    watched = summary.rows[1]
    assert watched.interval_width_probability == d("0.250000")
    assert watched.stale_evidence_age_seconds == d("7200")
    assert watched.stale_evidence_pressure == d("0.200000")
    assert watched.recheck_urgency_score == d("0.625000")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "calibration_support_watch",
        "interval_width_watch",
        "recheck_urgency_watch",
        "source_confidence_watch",
        "stale_evidence_watch",
    )

    passed = summary.rows[2]
    assert passed.interval_width_probability == d("0.100000")
    assert passed.stale_evidence_pressure == d("0.000000")
    assert passed.recheck_urgency_score == d("0.250000")
    assert passed.status == "pass"
    assert passed.reason_codes == ("confidence_interval_quality_pass",)
    assert passed.paper_only is True
    assert passed.report_only is True
    assert passed.readonly is True
    assert len(passed.derived_validation_digest) == 64


def test_payload_is_deterministic_decimal_stringed_and_digest_guarded() -> None:
    generated_at = datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    first_payload = research_strategy_confidence_interval_quality_report_payload(
        report(ci_input(), generated_at=generated_at),
    )
    second_payload = research_strategy_confidence_interval_quality_report_payload(
        report(ci_input(), generated_at=generated_at),
    )

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["source_row_count"] == "1.000000"
    assert first_payload["rows"][0]["interval_width_probability"] == "0.100000"
    assert first_payload["rows"][0]["recheck_urgency_score"] == "0.250000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    encoded_public_payload = dumps(first_payload, sort_keys=True)
    assert "market_slug" not in encoded_public_payload
    assert "market-alpha" not in encoded_public_payload

    tampered_payload = research_strategy_confidence_interval_quality_report_payload(
        report(ci_input()),
    )
    tampered_payload["rows"][0]["interval_width_probability"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_confidence_interval_quality_report_payload(tampered_payload)

    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_confidence_interval_quality_report_payload(
            {
                "credential_ref": "redacted",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )

    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_confidence_interval_quality_report_payload(
            {
                "note": "secret phrase",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )

    for unsafe_field in (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
    ):
        unsafe_payload = resign_payload(
            {
                **first_payload,
                unsafe_field: "redacted",
            },
        )
        with pytest.raises(ValueError, match="unsafe"):
            research_strategy_confidence_interval_quality_report_payload(unsafe_payload)

    invalid_status_payload = resign_payload({**first_payload, "status": "review"})
    with pytest.raises(ValueError, match="status"):
        research_strategy_confidence_interval_quality_report_payload(
            invalid_status_payload,
        )


def test_validation_rejects_non_decimal_bounds_flags_times_and_duplicates() -> None:
    with pytest.raises(ValueError, match="forecast_probability"):
        ci_input(forecast_probability=0.62)
    with pytest.raises(ValueError, match="forecast_probability"):
        ci_input(forecast_probability=d("1.200000"))
    with pytest.raises(ValueError, match="lower_bound_probability"):
        ci_input(lower_bound_probability=d("0.560000"))
    with pytest.raises(ValueError, match="forecast_probability"):
        ci_input(forecast_probability=d("0.900000"))
    with pytest.raises(ValueError, match="observed_at"):
        ci_input(observed_at=datetime(2026, 7, 8, 11, 50))
    with pytest.raises(ValueError, match="generated_at"):
        report(ci_input(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(ci_input(observed_at=datetime(2026, 7, 8, 12, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="duplicate"):
        report(
            ci_input(confidence_case_ref="same_case"),
            ci_input(confidence_case_ref="same_case", strategy_ref="strategy_beta"),
        )
    with pytest.raises(ValueError, match="threshold"):
        config(interval_width_watch_threshold=d("0.500000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)


def test_dataclasses_are_frozen_decimal_only_and_reject_tampering() -> None:
    summary = report(ci_input())
    row = summary.rows[0]

    assert is_dataclass(row)
    assert RESEARCH_STRATEGY_CONFIDENCE_INTERVAL_QUALITY_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            row,
            interval_width_probability=d("0.200000"),
            derived_validation_digest=row.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary,
            source_row_count=d("0"),
            derived_validation_digest=summary.derived_validation_digest,
        )


def test_module_scope_is_pure_report_reducer_with_local_exports_only() -> None:
    import polymarket_alpha_lab.research_strategy_confidence_interval_quality_report as module

    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_CONFIDENCE_INTERVAL_QUALITY_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_CONFIDENCE_INTERVAL_QUALITY_STATUSES",
        "ResearchStrategyConfidenceIntervalQualityConfig",
        "ResearchStrategyConfidenceIntervalQualityInput",
        "ResearchStrategyConfidenceIntervalQualityRow",
        "ResearchStrategyConfidenceIntervalQualityReport",
        "build_research_strategy_confidence_interval_quality_report",
        "research_strategy_confidence_interval_quality_report_payload",
    )
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }

    forbidden_source_terms = (
        "reco" + "mmendation",
        "siz" + "ing",
        "b" + "uy",
        "se" + "ll",
        "wal" + "let",
        "or" + "der",
        "li" + "ve",
        "trad" + "ing",
        "data" + "base",
        "net" + "work",
        "request",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
    )
    assert all(term not in source.lower() for term in forbidden_source_terms)

    forbidden_call_names = {
        "__import__",
        "connect",
        "execute",
        "float",
        "open",
        "request",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names
