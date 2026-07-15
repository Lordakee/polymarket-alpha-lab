from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_source_cross_check_retrieval_gap_report as api
from polymarket_alpha_lab.research_source_cross_check_retrieval_gap_report import (
    DEFAULT_RESEARCH_SOURCE_CROSS_CHECK_RETRIEVAL_GAP_REPORT_CONFIG_VERSION,
    ResearchSourceCrossCheckRetrievalGapConfig,
    ResearchSourceCrossCheckRetrievalGapInputRow,
    ResearchSourceCrossCheckRetrievalGapReport,
    build_research_source_cross_check_retrieval_gap_report,
    research_source_cross_check_retrieval_gap_report_payload,
)


NOW = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _NaiveTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def _input_row(
    review_bucket: str,
    source_class: str,
    *,
    retrieved_at: datetime = NOW - timedelta(minutes=5),
    parse_success_count: Decimal = d("1.000000"),
    parse_failure_count: Decimal = d("0.000000"),
    contradiction_count: Decimal = d("0.000000"),
    retry_backlog_count: Decimal = d("0.000000"),
    manual_review_due_at: datetime | None = None,
) -> ResearchSourceCrossCheckRetrievalGapInputRow:
    return ResearchSourceCrossCheckRetrievalGapInputRow(
        review_bucket=review_bucket,
        source_class=source_class,
        retrieved_at=retrieved_at,
        parse_success_count=parse_success_count,
        parse_failure_count=parse_failure_count,
        contradiction_count=contradiction_count,
        retry_backlog_count=retry_backlog_count,
        manual_review_due_at=manual_review_due_at,
    )


def _config(**overrides: object) -> ResearchSourceCrossCheckRetrievalGapConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_SOURCE_CROSS_CHECK_RETRIEVAL_GAP_REPORT_CONFIG_VERSION
        ),
        "required_source_classes": ("official", "primary", "secondary"),
        "freshness_watch_age_seconds": d("3600.000000"),
        "freshness_block_age_seconds": d("7200.000000"),
        "min_watch_parse_reliability_score": d("0.750000"),
        "min_pass_parse_reliability_score": d("0.900000"),
        "contradiction_watch_threshold": d("0.250000"),
        "contradiction_block_threshold": d("0.500000"),
        "retry_backlog_watch_threshold": d("0.250000"),
        "retry_backlog_block_threshold": d("0.500000"),
        "manual_review_watch_horizon_seconds": d("1800.000000"),
    }
    values.update(overrides)
    return ResearchSourceCrossCheckRetrievalGapConfig(**values)


def _sample_rows() -> tuple[ResearchSourceCrossCheckRetrievalGapInputRow, ...]:
    return (
        _input_row("retrieval_pass", "official"),
        _input_row("retrieval_pass", "primary"),
        _input_row("retrieval_pass", "secondary"),
        _input_row(
            "retrieval_watch",
            "official",
            retrieved_at=NOW - timedelta(seconds=4000),
        ),
        _input_row("retrieval_watch", "primary"),
        _input_row(
            "retrieval_block",
            "official",
            retrieved_at=NOW - timedelta(seconds=9000),
            parse_success_count=d("1.000000"),
            parse_failure_count=d("3.000000"),
            contradiction_count=d("2.000000"),
            retry_backlog_count=d("2.000000"),
            manual_review_due_at=NOW - timedelta(minutes=1),
        ),
    )


def _build_report(
    rows: tuple[ResearchSourceCrossCheckRetrievalGapInputRow, ...],
) -> ResearchSourceCrossCheckRetrievalGapReport:
    return build_research_source_cross_check_retrieval_gap_report(
        rows,
        generated_at=NOW,
        config=_config(),
    )


def test_aggregates_retrieval_gaps_and_sorts_statuses_deterministically() -> None:
    report = _build_report(tuple(reversed(_sample_rows())))

    assert report == ResearchSourceCrossCheckRetrievalGapReport(
        generated_at=NOW,
        config_version=(
            DEFAULT_RESEARCH_SOURCE_CROSS_CHECK_RETRIEVAL_GAP_REPORT_CONFIG_VERSION
        ),
        report_status="block",
        review_action="pause_cross_check_until_retrieval_gaps_clear",
        review_bucket_count=d("3.000000"),
        pass_count=d("1.000000"),
        watch_count=d("1.000000"),
        block_count=d("1.000000"),
        source_observation_count=d("6.000000"),
        missing_corroborating_source_class_count=d("3.000000"),
        max_retrieval_age_seconds=d("9000.000000"),
        average_parse_reliability_score=d("0.750000"),
        max_contradiction_pressure_score=d("1.000000"),
        retry_backlog_count=d("2.000000"),
        max_manual_review_urgency_score=d("1.000000"),
        rows=report.rows,
        reason_codes=(
            "missing_corroborating_source_class_watch",
            "missing_corroborating_source_class_block",
            "retrieval_freshness_watch",
            "retrieval_freshness_block",
            "parse_reliability_block",
            "contradiction_pressure_block",
            "retry_backlog_block",
            "manual_review_urgency_block",
            "source_cross_check_retrieval_gap_pass",
        ),
        derived_validation_digest=report.derived_validation_digest,
    )
    assert tuple(row.review_bucket for row in report.rows) == (
        "retrieval_block",
        "retrieval_watch",
        "retrieval_pass",
    )

    block_row = report.rows[0]
    assert block_row.gap_status == "block"
    assert block_row.required_source_class_count == d("3.000000")
    assert block_row.observed_source_class_count == d("1.000000")
    assert block_row.missing_corroborating_source_class_count == d("2.000000")
    assert block_row.retrieval_age_seconds == d("9000.000000")
    assert block_row.retrieval_freshness_score == d("1.000000")
    assert block_row.parse_attempt_count == d("4.000000")
    assert block_row.parse_reliability_score == d("0.250000")
    assert block_row.contradiction_pressure_score == d("1.000000")
    assert block_row.retry_backlog_pressure_score == d("0.666667")
    assert block_row.manual_review_urgency_score == d("1.000000")
    assert block_row.reason_codes == (
        "missing_corroborating_source_class_block",
        "retrieval_freshness_block",
        "parse_reliability_block",
        "contradiction_pressure_block",
        "retry_backlog_block",
        "manual_review_urgency_block",
    )

    watch_row = report.rows[1]
    assert watch_row.gap_status == "watch"
    assert watch_row.missing_corroborating_source_class_count == d("1.000000")
    assert watch_row.retrieval_age_seconds == d("4000.000000")
    assert watch_row.retrieval_freshness_score == d("0.555556")
    assert watch_row.parse_reliability_score == d("1.000000")
    assert watch_row.reason_codes == (
        "missing_corroborating_source_class_watch",
        "retrieval_freshness_watch",
    )

    pass_row = report.rows[2]
    assert pass_row.gap_status == "pass"
    assert pass_row.reason_codes == ("source_cross_check_retrieval_gap_pass",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_is_deterministic_json_ready_redacted_and_digest_validates() -> None:
    report = _build_report(_sample_rows())
    reversed_report = _build_report(tuple(reversed(_sample_rows())))

    payload = research_source_cross_check_retrieval_gap_report_payload(report)
    reversed_payload = research_source_cross_check_retrieval_gap_report_payload(
        reversed_report,
    )

    json.dumps(payload, sort_keys=True)
    assert payload == reversed_payload
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["review_bucket_count"] == "3.000000"
    assert payload["max_retrieval_age_seconds"] == "9000.000000"
    assert payload["average_parse_reliability_score"] == "0.750000"
    assert payload["rows"][0]["review_bucket"] == "retrieval_block"
    assert payload["rows"][0]["retry_backlog_pressure_score"] == "0.666667"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert report.payload == payload
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(report)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    tampered = dict(payload)
    tampered["retry_backlog_count"] = "0.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_source_cross_check_retrieval_gap_report_payload(tampered)

    public_text = json.dumps(payload, sort_keys=True).lower()
    forbidden_fragments = (
        "http://",
        "https://",
        "raw_url",
        "raw_text",
        "market_id",
        "market_slug",
        "candidate_id",
        "dsn",
        "table_name",
        "private_token",
    )
    assert not any(fragment in public_text for fragment in forbidden_fragments)


def test_dataclasses_are_frozen_reject_subclassing_and_use_decimal_metrics() -> None:
    report = _build_report(_sample_rows())

    with pytest.raises(FrozenInstanceError):
        report.rows[0].gap_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchSourceCrossCheckRetrievalGapConfig):
            pass

    for value in _walk_public_values(report):
        if isinstance(value, Decimal):
            assert type(value) is Decimal
        if type(value) is int or isinstance(value, float):
            raise AssertionError(f"public numeric value is not Decimal: {value!r}")


def test_rejects_unsafe_inputs_bad_decimals_times_duplicates_and_flags() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        ResearchSourceCrossCheckRetrievalGapConfig(paper_only=False)
    with pytest.raises(ValueError, match="freshness"):
        ResearchSourceCrossCheckRetrievalGapConfig(
            freshness_watch_age_seconds=d("7200.000000"),
            freshness_block_age_seconds=d("3600.000000"),
        )
    with pytest.raises(ValueError, match="required_source_classes"):
        ResearchSourceCrossCheckRetrievalGapConfig(required_source_classes=())
    with pytest.raises(ValueError, match="parse_success_count"):
        _input_row("bad_decimal", "official", parse_success_count=1)
    with pytest.raises(ValueError, match="parse_success_count"):
        _input_row(
            "bad_decimal_subclass",
            "official",
            parse_success_count=_DecimalSubclass("1.000000"),
        )
    with pytest.raises(ValueError, match="review_bucket"):
        _input_row(_join_parts("market", "_", "id"), "official")
    with pytest.raises(ValueError, match="source_class"):
        _input_row("unsafe_source", _join_parts("private", "_", "token"))
    with pytest.raises(ValueError, match="timezone-aware"):
        _input_row(
            "naive_time",
            "official",
            retrieved_at=datetime(2026, 7, 8),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        _input_row(
            "naive_like_tzinfo",
            "official",
            retrieved_at=datetime(2026, 7, 8, tzinfo=_NaiveTz()),
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(_input_row("not_readonly", "official"), readonly=False)
    with pytest.raises(ValueError, match="future"):
        build_research_source_cross_check_retrieval_gap_report(
            (
                _input_row(
                    "future_retrieval",
                    "official",
                    retrieved_at=NOW + timedelta(seconds=1),
                ),
            ),
            generated_at=NOW,
            config=_config(),
        )
    with pytest.raises(ValueError, match="duplicate"):
        build_research_source_cross_check_retrieval_gap_report(
            (
                _input_row("duplicate_class", "official"),
                _input_row("duplicate_class", "official"),
            ),
            generated_at=NOW,
            config=_config(),
        )


def test_empty_input_and_zero_denominators_are_canonical() -> None:
    empty_report = _build_report(())

    assert empty_report.report_status == "pass"
    assert empty_report.review_bucket_count == d("0.000000")
    assert empty_report.pass_count == d("0.000000")
    assert empty_report.watch_count == d("0.000000")
    assert empty_report.block_count == d("0.000000")
    assert empty_report.source_observation_count == d("0.000000")
    assert empty_report.missing_corroborating_source_class_count == d("0.000000")
    assert empty_report.max_retrieval_age_seconds == d("0.000000")
    assert empty_report.average_parse_reliability_score == d("0.000000")
    assert empty_report.max_contradiction_pressure_score == d("0.000000")
    assert empty_report.retry_backlog_count == d("0.000000")
    assert empty_report.max_manual_review_urgency_score == d("0.000000")
    assert empty_report.rows == ()
    assert empty_report.reason_codes == (
        "source_cross_check_retrieval_gap_pass",
    )

    zero_attempt_report = _build_report(
        tuple(
            _input_row(
                "zero_attempts",
                source_class,
                parse_success_count=d("0.000000"),
                parse_failure_count=d("0.000000"),
            )
            for source_class in ("official", "primary", "secondary")
        ),
    )
    zero_attempt_row = zero_attempt_report.rows[0]

    assert zero_attempt_row.parse_attempt_count == d("0.000000")
    assert zero_attempt_row.parse_reliability_score == d("0.000000")
    assert zero_attempt_row.contradiction_pressure_score == d("0.000000")
    assert zero_attempt_row.retry_backlog_pressure_score == d("0.000000")
    assert zero_attempt_row.gap_status == "block"
    assert zero_attempt_row.reason_codes == ("parse_reliability_block",)


def test_rejects_nonfinite_values_bad_collections_and_derived_tampering() -> None:
    with pytest.raises(ValueError, match="parse_failure_count"):
        _input_row(
            "nan_count",
            "official",
            parse_failure_count=d("NaN"),
        )
    with pytest.raises(ValueError, match="retry_backlog_count"):
        _input_row(
            "infinite_count",
            "official",
            retry_backlog_count=d("Infinity"),
        )
    with pytest.raises(ValueError, match="required_source_classes"):
        _config(required_source_classes=("official", "official"))
    with pytest.raises(ValueError, match="parse_reliability"):
        _config(
            min_watch_parse_reliability_score=d("0.900000"),
            min_pass_parse_reliability_score=d("0.750000"),
        )
    with pytest.raises(ValueError, match="contradiction"):
        _config(
            contradiction_watch_threshold=d("0.500000"),
            contradiction_block_threshold=d("0.250000"),
        )
    with pytest.raises(ValueError, match="retry_backlog"):
        _config(
            retry_backlog_watch_threshold=d("0.500000"),
            retry_backlog_block_threshold=d("0.250000"),
        )
    with pytest.raises(ValueError, match="manual_review_watch_horizon_seconds"):
        _config(manual_review_watch_horizon_seconds=d("0.000000"))
    with pytest.raises(ValueError, match="timezone-aware"):
        _input_row(
            "naive_review_due",
            "official",
            manual_review_due_at=datetime(2026, 7, 8),
        )
    with pytest.raises(ValueError, match="input_rows"):
        build_research_source_cross_check_retrieval_gap_report(
            "not rows",
            generated_at=NOW,
            config=_config(),
        )
    with pytest.raises(ValueError, match="input_rows"):
        build_research_source_cross_check_retrieval_gap_report(
            (object(),),
            generated_at=NOW,
            config=_config(),
        )

    report = _build_report(_sample_rows())
    payload = research_source_cross_check_retrieval_gap_report_payload(report)
    assert research_source_cross_check_retrieval_gap_report_payload(payload) == payload
    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=d("9.000000"))


def test_module_has_no_db_network_or_action_surfaces() -> None:
    source = inspect.getsource(api).lower()
    tree = ast.parse(source)

    assert "float(" not in source
    assert ".total_seconds(" not in source

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
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
                "delete",
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

    unsafe_terms = (
        "auth",
        "wallet",
        "account",
        "broker",
        "order",
        "trade",
        "trading",
        "sizing",
        "recommend",
        "market_id",
        "market_slug",
        "candidate_id",
        "candidate_identifier",
        "dsn",
        "table_name",
        "private_token",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(token in lowered for token in unsafe_terms)
    for cls in (
        ResearchSourceCrossCheckRetrievalGapConfig,
        ResearchSourceCrossCheckRetrievalGapInputRow,
        ResearchSourceCrossCheckRetrievalGapReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(token in lowered for token in unsafe_terms)


def _walk_public_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            values.extend(_walk_public_values(getattr(value, field.name)))
        return tuple(values)
    if isinstance(value, tuple):
        for item in value:
            values.extend(_walk_public_values(item))
        return tuple(values)
    values.append(value)
    return tuple(values)


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    for item in _walk_public_values(value):
        if isinstance(item, Decimal):
            continue
        if type(item) is bool or item is None or isinstance(item, (str, datetime)):
            continue
        if type(item) is int or isinstance(item, float):
            raise AssertionError(f"public numeric value is not Decimal: {item!r}")
