from __future__ import annotations

import ast
import hashlib
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_source_authority_change_detection_report"
)
GENERATED_AT = datetime(2026, 7, 8, 14, 30, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(minutes=10)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_SOURCE_AUTHORITY_CHANGE_DETECTION_REPORT_CONFIG_VERSION
        ),
        "watch_authority_change_score": d("0.250000"),
        "block_authority_change_score": d("0.600000"),
        "watch_lineage_shift_score": d("0.250000"),
        "block_lineage_shift_score": d("0.600000"),
        "watch_consensus_shift_score": d("0.250000"),
        "block_consensus_shift_score": d("0.600000"),
        "min_pass_verification_coverage": d("1.000000"),
        "min_watch_verification_coverage": d("0.500000"),
        "max_unverified_change_age_seconds": d("86400.000000"),
    }
    values.update(overrides)
    return module.ResearchSourceAuthorityChangeDetectionConfig(**values)


def authority_input(
    source_authority_reference_key: str = "private-source-pass",
    *,
    authority_change_score: Decimal = d("0.050000"),
    lineage_shift_score: Decimal = d("0.020000"),
    consensus_shift_score: Decimal = d("0.030000"),
    verified_source_count: Decimal = d("4"),
    expected_source_count: Decimal = d("4"),
    observed_at: datetime = OBSERVED_AT,
    authority_change_detected: bool = False,
    official_authority_changed: bool = False,
    authority_verification_complete: bool = True,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchSourceAuthorityChangeDetectionInput(
        source_authority_reference_key=source_authority_reference_key,
        authority_change_score=authority_change_score,
        lineage_shift_score=lineage_shift_score,
        consensus_shift_score=consensus_shift_score,
        verified_source_count=verified_source_count,
        expected_source_count=expected_source_count,
        observed_at=observed_at,
        authority_change_detected=authority_change_detected,
        official_authority_changed=official_authority_changed,
        authority_verification_complete=authority_verification_complete,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_research_source_authority_change_detection_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_report_blocks_until_source_authority_inputs_exist() -> None:
    module = api()
    result = report()

    assert module.RESEARCH_SOURCE_AUTHORITY_CHANGE_DETECTION_REPORT_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_AUTHORITY_CHANGE_DETECTION_REPORT_CONFIG_VERSION",
        "RESEARCH_SOURCE_AUTHORITY_CHANGE_DETECTION_REPORT_STATUSES",
        "ResearchSourceAuthorityChangeDetectionConfig",
        "ResearchSourceAuthorityChangeDetectionInput",
        "ResearchSourceAuthorityChangeDetectionReasonCodeCount",
        "ResearchSourceAuthorityChangeDetectionRow",
        "ResearchSourceAuthorityChangeDetectionReport",
        "build_research_source_authority_change_detection_report",
        "research_source_authority_change_detection_report_payload",
        "research_source_authority_change_detection_report_digest",
    )
    assert type(result) is module.ResearchSourceAuthorityChangeDetectionReport
    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == (
        "research-source-authority-change-detection-report-v0"
    )
    assert result.observed_authority_count == ZERO
    assert result.pass_count == ZERO
    assert result.watch_count == ZERO
    assert result.block_count == ZERO
    assert result.changed_authority_count == ZERO
    assert result.review_required_count == ZERO
    assert result.missing_verification_count == ZERO
    assert result.max_authority_change_score == ZERO
    assert result.max_lineage_shift_score == ZERO
    assert result.max_consensus_shift_score == ZERO
    assert result.max_change_age_seconds == ZERO
    assert result.mean_verification_coverage == ZERO
    assert result.status == "block"
    assert result.reason_codes == (
        "source_authority_change_detection_report_empty",
    )
    assert result.reason_code_counts == ()
    assert result.rows == ()
    assert len(result.derived_validation_digest) == 64
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_report_scores_source_authority_change_pass_watch_block() -> None:
    private_block_key = (
        "raw_candidate_id_market_id_market_slug_question_source_url_source_text_"
        "dsn_table_name_token_wallet_order_trade_live_recommendation_sizing"
    )
    result = report(
        authority_input(
            private_block_key,
            authority_change_score=d("0.700000"),
            lineage_shift_score=d("0.800000"),
            consensus_shift_score=d("0.650000"),
            verified_source_count=d("1"),
            expected_source_count=d("4"),
            observed_at=GENERATED_AT - timedelta(days=2),
            authority_change_detected=True,
            official_authority_changed=True,
            authority_verification_complete=False,
        ),
        authority_input(
            "private-source-watch",
            authority_change_score=d("0.300000"),
            lineage_shift_score=d("0.300000"),
            consensus_shift_score=d("0.200000"),
            verified_source_count=d("2"),
            expected_source_count=d("3"),
            observed_at=GENERATED_AT - timedelta(hours=1),
            authority_change_detected=True,
            official_authority_changed=False,
            authority_verification_complete=True,
        ),
        authority_input("private-source-pass"),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
    )

    assert result.generated_at == GENERATED_AT
    assert result.observed_authority_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.changed_authority_count == d("2.000000")
    assert result.review_required_count == d("2.000000")
    assert result.missing_verification_count == d("1.000000")
    assert result.max_authority_change_score == d("0.700000")
    assert result.max_lineage_shift_score == d("0.800000")
    assert result.max_consensus_shift_score == d("0.650000")
    assert result.max_change_age_seconds == d("172800.000000")
    assert result.mean_verification_coverage == d("0.638889")
    assert result.status == "block"
    assert result.reason_codes == (
        "source_authority_change_detection_report_block",
        "authority_change_exception",
        "lineage_shift_exception",
        "consensus_shift_exception",
        "official_authority_change_present",
        "verification_coverage_exception",
        "stale_unverified_change_present",
        "manual_verification_incomplete_present",
    )

    blocked, watched, passed = result.rows
    assert tuple(row.aggregate_row_number for row in result.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")
    assert blocked.source_authority_trace_hash == hashlib.sha256(
        private_block_key.encode("utf-8"),
    ).hexdigest()
    assert blocked.verification_coverage == d("0.250000")
    assert blocked.change_age_seconds == d("172800.000000")
    assert blocked.reason_codes == (
        "source_authority_change_detection_block",
        "authority_change_score_block",
        "lineage_shift_block",
        "consensus_shift_block",
        "official_authority_change_block",
        "verification_coverage_block",
        "stale_unverified_change_block",
        "manual_verification_incomplete_block",
    )
    assert watched.verification_coverage == d("0.666667")
    assert watched.change_age_seconds == d("3600.000000")
    assert watched.reason_codes == (
        "source_authority_change_detection_watch",
        "authority_change_score_watch",
        "lineage_shift_watch",
        "verification_coverage_watch",
        "detected_authority_change_watch",
    )
    assert passed.reason_codes == ("source_authority_change_detection_pass",)

    counts = {item.reason_code: item for item in result.reason_code_counts}
    assert counts["verification_coverage_block"] == (
        api().ResearchSourceAuthorityChangeDetectionReasonCodeCount(
            reason_code="verification_coverage_block",
            count=d("1.000000"),
            observed_authority_ratio=d("0.333333"),
        )
    )


def test_payload_is_deterministic_public_safe_decimal_stringed_and_digest_guarded() -> None:
    module = api()
    first = report(
        authority_input("private-source-z"),
        authority_input("private-source-a"),
    )
    second = report(
        authority_input("private-source-a"),
        authority_input("private-source-z"),
    )

    first_payload = module.research_source_authority_change_detection_report_payload(first)
    second_payload = module.research_source_authority_change_detection_report_payload(second)

    assert first_payload == second_payload
    assert module.research_source_authority_change_detection_report_digest(first) == (
        module.research_source_authority_change_detection_report_digest(second)
    )
    assert len(module.research_source_authority_change_detection_report_digest(first)) == 64
    assert first_payload["generated_at"] == "2026-07-08T14:30:00+00:00"
    assert first_payload["observed_authority_count"] == "2.000000"
    assert first_payload["rows"][0]["aggregate_row_number"] == "1.000000"
    assert len(first_payload["rows"][0]["source_authority_trace_hash"]) == 64
    assert first_payload["rows"][0]["authority_change_score"] == "0.050000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    assert not any(
        type(value) in (int, float, Decimal)
        for value in _walk_payload_values(first_payload)
    )

    rendered = json.dumps(first_payload, sort_keys=True).lower()
    for forbidden in (
        "private-source",
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "http://",
        "https://",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "recommendation",
        "sizing",
    ):
        assert forbidden not in rendered

    tampered_payload = module.research_source_authority_change_detection_report_payload(
        report(authority_input()),
    )
    tampered_payload["rows"][0]["authority_change_score"] = "0.900000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_source_authority_change_detection_report_payload(tampered_payload)

    with pytest.raises(ValueError, match="unsafe"):
        module.research_source_authority_change_detection_report_payload(
            {
                "market_id": "hidden",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


@pytest.mark.parametrize(
    "unsafe_key",
    (
        "database_name",
        "network_route",
        "request_payload",
        "socket_path",
        "subprocess_args",
        "connect_endpoint",
        "execution_surface",
        "trading_surface",
    ),
)
def test_payload_rejects_public_database_network_and_execution_surfaces(
    unsafe_key: str,
) -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe"):
        module.research_source_authority_change_detection_report_payload(
            {
                unsafe_key: "hidden",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_review_required_and_summary_counts_are_derived_from_rows() -> None:
    module = api()
    score_watch = report(
        authority_input(
            "private-score-watch",
            authority_change_score=d("0.300000"),
            authority_change_detected=False,
            authority_verification_complete=True,
        ),
    )
    changed = report(
        authority_input(
            "private-changed-watch",
            authority_change_detected=True,
        ),
    )
    missing = report(
        authority_input(
            "private-missing-block",
            authority_verification_complete=False,
        ),
    )

    assert score_watch.status == "watch"
    assert score_watch.changed_authority_count == ZERO
    assert score_watch.review_required_count == d("1.000000")
    assert score_watch.missing_verification_count == ZERO

    with pytest.raises(ValueError, match="review_required_count"):
        replace(score_watch, review_required_count=ZERO, derived_validation_digest="")
    with pytest.raises(ValueError, match="changed_authority_count"):
        replace(changed, changed_authority_count=ZERO, derived_validation_digest="")
    with pytest.raises(ValueError, match="missing_verification_count"):
        replace(missing, missing_verification_count=ZERO, derived_validation_digest="")


def test_validation_rejects_non_decimal_bad_flags_bad_times_and_duplicates() -> None:
    module = api()
    result = report(authority_input())
    row = result.rows[0]

    for value in (config(), authority_input(), row, result, *result.reason_code_counts):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if (
                item_value is None
                or type(item_value) is bool
                or item.name
                in {
                    "config_version",
                    "derived_validation_digest",
                    "source_authority_reference_key",
                    "source_authority_trace_hash",
                    "observed_at",
                    "generated_at",
                    "paper_only",
                    "readonly",
                    "reason_codes",
                    "reason_code_counts",
                    "report_only",
                    "rows",
                    "status",
                }
            ):
                continue
            if any(
                token in item.name
                for token in ("age", "count", "coverage", "ratio", "score")
            ):
                assert type(item_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        row.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="authority_change_score"):
        authority_input(authority_change_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="lineage_shift_score"):
        authority_input(lineage_shift_score=_DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="verified_source_count"):
        authority_input(verified_source_count=d("5"), expected_source_count=d("4"))
    with pytest.raises(ValueError, match="expected_source_count"):
        authority_input(expected_source_count=d("0"))
    with pytest.raises(ValueError, match="generated_at"):
        report(authority_input(), generated_at=datetime(2026, 7, 8, 14, 30))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            authority_input(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 14, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        report(authority_input(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="duplicate"):
        report(authority_input("same"), authority_input("same"))
    with pytest.raises(ValueError, match="watch_authority_change_score"):
        config(watch_authority_change_score=d("0.700000"))
    with pytest.raises(ValueError, match="paper_only"):
        authority_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            row,
            authority_change_score=d("0.900000"),
            derived_validation_digest=row.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            result,
            observed_authority_count=d("2.000000"),
            derived_validation_digest=result.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="report"):
        module.research_source_authority_change_detection_report_payload(object())


def test_owned_module_has_no_external_execution_or_private_public_surfaces() -> None:
    module = api()
    source = inspect.getsource(module)
    tree = ast.parse(source)

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

    forbidden_terms = (
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "private_token",
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
        "connect(",
    )
    assert all(term not in source.lower() for term in forbidden_terms)

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


def _walk_payload_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item in value.values():
            values.extend(_walk_payload_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(_walk_payload_values(item))
        return tuple(values)
    return (value,)
