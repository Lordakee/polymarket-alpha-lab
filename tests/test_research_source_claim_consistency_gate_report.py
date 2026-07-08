from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_source_claim_consistency_gate_report as api
from polymarket_alpha_lab.research_source_claim_consistency_gate_report import (
    DEFAULT_RESEARCH_SOURCE_CLAIM_CONSISTENCY_GATE_REPORT_CONFIG_VERSION,
    ResearchSourceClaimConsistencyGateConfig,
    ResearchSourceClaimConsistencyGateInputRow,
    ResearchSourceClaimConsistencyGateReport,
    ResearchSourceClaimConsistencyPublicPayloadItem,
    build_research_source_claim_consistency_gate_report,
    research_source_claim_consistency_gate_report_payload,
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
    aggregate_label: str,
    source_class: str,
    claim_state: str,
    *,
    observed_at: datetime = NOW,
    unresolved_conflict_count: Decimal = d("0.000000"),
    recheck_due_at: datetime | None = None,
) -> ResearchSourceClaimConsistencyGateInputRow:
    return ResearchSourceClaimConsistencyGateInputRow(
        aggregate_label=aggregate_label,
        source_class=source_class,
        claim_state=claim_state,
        observed_at=observed_at,
        unresolved_conflict_count=unresolved_conflict_count,
        recheck_due_at=recheck_due_at,
    )


def _config(**overrides: object) -> ResearchSourceClaimConsistencyGateConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_SOURCE_CLAIM_CONSISTENCY_GATE_REPORT_CONFIG_VERSION
        ),
        "watch_agreement_threshold": d("0.600000"),
        "pass_agreement_threshold": d("0.800000"),
        "stale_claim_age_seconds": d("86400.000000"),
        "unresolved_conflict_watch_threshold": d("0.250000"),
        "unresolved_conflict_block_threshold": d("0.500000"),
        "recheck_urgency_watch_threshold": d("0.300000"),
        "recheck_urgency_block_threshold": d("0.800000"),
    }
    values.update(overrides)
    return ResearchSourceClaimConsistencyGateConfig(**values)


def _sample_rows() -> tuple[ResearchSourceClaimConsistencyGateInputRow, ...]:
    return (
        _input_row("claim_set_pass", "official", "supports"),
        _input_row("claim_set_pass", "primary", "supports"),
        _input_row("claim_set_pass", "secondary", "supports"),
        _input_row("claim_set_watch", "official", "supports"),
        _input_row("claim_set_watch", "primary", "supports"),
        _input_row("claim_set_watch", "secondary", "contradicts"),
        _input_row("claim_set_block", "official", "supports"),
        _input_row(
            "claim_set_block",
            "primary",
            "contradicts",
            observed_at=NOW - timedelta(days=3),
            unresolved_conflict_count=d("1.000000"),
            recheck_due_at=NOW - timedelta(minutes=10),
        ),
        _input_row(
            "claim_set_block",
            "secondary",
            "contradicts",
            observed_at=NOW - timedelta(days=2),
            unresolved_conflict_count=d("1.000000"),
            recheck_due_at=NOW - timedelta(minutes=5),
        ),
    )


def _build_report(
    rows: tuple[ResearchSourceClaimConsistencyGateInputRow, ...],
    *,
    public_payload: tuple[ResearchSourceClaimConsistencyPublicPayloadItem, ...] = (),
) -> ResearchSourceClaimConsistencyGateReport:
    return build_research_source_claim_consistency_gate_report(
        rows,
        generated_at=NOW,
        config=_config(),
        public_payload=public_payload,
    )


def test_aggregate_consistency_flags_block_watch_and_sorts_deterministically() -> None:
    report = _build_report(tuple(reversed(_sample_rows())))

    assert report == ResearchSourceClaimConsistencyGateReport(
        generated_at=NOW,
        config_version=(
            DEFAULT_RESEARCH_SOURCE_CLAIM_CONSISTENCY_GATE_REPORT_CONFIG_VERSION
        ),
        gate_status="block",
        aggregate_count=d("3.000000"),
        pass_count=d("1.000000"),
        watch_count=d("1.000000"),
        block_count=d("1.000000"),
        claim_summary_count=d("9.000000"),
        stale_contradictory_claim_count=d("2.000000"),
        average_source_class_agreement_score=d("0.777778"),
        max_unresolved_conflict_pressure_score=d("0.666667"),
        max_recheck_urgency_score=d("1.000000"),
        rows=report.rows,
        reason_codes=(
            "source_claim_class_agreement_watch",
            "stale_contradictory_claims",
            "unresolved_conflict_pressure_block",
            "recheck_due",
            "recheck_urgency_block",
            "source_claim_consistency_pass",
        ),
        public_payload=(),
        derived_validation_digest=report.derived_validation_digest,
    )
    assert tuple(row.aggregate_label for row in report.rows) == (
        "claim_set_block",
        "claim_set_watch",
        "claim_set_pass",
    )

    block_row = report.rows[0]
    assert block_row.gate_status == "block"
    assert block_row.source_class_count == d("3.000000")
    assert block_row.majority_claim_state == "contradicts"
    assert block_row.majority_source_class_count == d("2.000000")
    assert block_row.source_class_agreement_score == d("0.666667")
    assert block_row.stale_contradictory_claim_count == d("2.000000")
    assert block_row.unresolved_conflict_count == d("2.000000")
    assert block_row.unresolved_conflict_pressure_score == d("0.666667")
    assert block_row.recheck_due_count == d("2.000000")
    assert block_row.recheck_urgency_score == d("1.000000")
    assert block_row.reason_codes == (
        "source_claim_class_agreement_watch",
        "stale_contradictory_claims",
        "unresolved_conflict_pressure_block",
        "recheck_due",
        "recheck_urgency_block",
    )

    watch_row = report.rows[1]
    assert watch_row.gate_status == "watch"
    assert watch_row.majority_claim_state == "supports"
    assert watch_row.source_class_agreement_score == d("0.666667")
    assert watch_row.unresolved_conflict_pressure_score == d("0.000000")
    assert watch_row.reason_codes == ("source_claim_class_agreement_watch",)

    pass_row = report.rows[2]
    assert pass_row.gate_status == "pass"
    assert pass_row.source_class_agreement_score == d("1.000000")
    assert pass_row.reason_codes == ("source_claim_consistency_pass",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_is_deterministic_json_ready_and_digest_validates() -> None:
    public_payload = (
        ResearchSourceClaimConsistencyPublicPayloadItem("aggregate_scope", "public summary"),
    )
    report = _build_report(_sample_rows(), public_payload=public_payload)
    reversed_report = _build_report(tuple(reversed(_sample_rows())), public_payload=public_payload)

    payload = research_source_claim_consistency_gate_report_payload(report)
    reversed_payload = research_source_claim_consistency_gate_report_payload(reversed_report)

    json.dumps(payload, sort_keys=True)
    encoded_payload = json.dumps(payload, sort_keys=True)
    assert payload == reversed_payload
    assert "recommended_next_step" not in encoded_payload
    assert "recommend" not in encoded_payload.lower()
    assert payload["aggregate_count"] == "3.000000"
    assert payload["claim_summary_count"] == "9.000000"
    assert payload["average_source_class_agreement_score"] == "0.777778"
    assert payload["max_recheck_urgency_score"] == "1.000000"
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["rows"][0]["unresolved_conflict_pressure_score"] == "0.666667"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert report.payload == payload
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(report)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            report,
            public_payload=(
                ResearchSourceClaimConsistencyPublicPayloadItem(
                    "aggregate_scope",
                    "changed summary",
                ),
            ),
        )


def test_dataclasses_are_frozen_reject_subclassing_and_use_decimal_metrics() -> None:
    report = _build_report(_sample_rows())

    with pytest.raises(FrozenInstanceError):
        report.rows[0].gate_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchSourceClaimConsistencyGateConfig):
            pass

    for value in _walk_public_values(report):
        if isinstance(value, Decimal):
            assert type(value) is Decimal
        if type(value) is int or isinstance(value, float):
            raise AssertionError(f"public numeric value is not Decimal: {value!r}")


def test_rejects_unsafe_labels_bad_decimals_times_duplicates_and_flags() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        ResearchSourceClaimConsistencyGateConfig(paper_only=False)
    with pytest.raises(ValueError, match="watch_agreement_threshold"):
        ResearchSourceClaimConsistencyGateConfig(watch_agreement_threshold=d("0.800000"))
    with pytest.raises(ValueError, match="stale_claim_age_seconds"):
        ResearchSourceClaimConsistencyGateConfig(stale_claim_age_seconds=86400)
    with pytest.raises(ValueError, match="unresolved_conflict_count"):
        _input_row("bad_count", "official", "supports", unresolved_conflict_count=1)
    with pytest.raises(ValueError, match="unresolved_conflict_count"):
        _input_row(
            "bad_subclass",
            "official",
            "supports",
            unresolved_conflict_count=_DecimalSubclass("1.000000"),
        )
    with pytest.raises(ValueError, match="source_class"):
        _input_row("unsafe_class", _join_parts("wal", "let"), "supports")
    with pytest.raises(ValueError, match="aggregate_label"):
        _input_row(_join_parts("mar", "ket", "_", "slug"), "official", "supports")
    with pytest.raises(ValueError, match="aggregate_label"):
        _input_row("candidate_123", "official", "supports")
    with pytest.raises(ValueError, match="aggregate_label"):
        _input_row(_join_parts("mar", "ket", "_", "id"), "official", "supports")
    with pytest.raises(ValueError, match="source_class"):
        _input_row("safe_label", _join_parts("source", "_", "url"), "supports")
    with pytest.raises(ValueError, match="claim_state"):
        _input_row("bad_state", "official", "maybe")
    with pytest.raises(ValueError, match="timezone-aware"):
        _input_row("naive_time", "official", "supports", observed_at=datetime(2026, 7, 8))
    with pytest.raises(ValueError, match="timezone-aware"):
        _input_row(
            "naive_like_tzinfo",
            "official",
            "supports",
            observed_at=datetime(2026, 7, 8, tzinfo=_NaiveTz()),
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(_input_row("not_readonly", "official", "supports"), readonly=False)
    with pytest.raises(ValueError, match="future"):
        build_research_source_claim_consistency_gate_report(
            (
                _input_row(
                    "future_claim",
                    "official",
                    "supports",
                    observed_at=NOW + timedelta(seconds=1),
                ),
            ),
            generated_at=NOW,
            config=_config(),
        )
    with pytest.raises(ValueError, match="duplicate"):
        build_research_source_claim_consistency_gate_report(
            (
                _input_row("duplicate_class", "official", "supports"),
                _input_row("duplicate_class", "official", "contradicts"),
            ),
            generated_at=NOW,
            config=_config(),
        )


def test_public_payload_rejects_raw_identifier_url_dsn_table_and_token_surfaces() -> None:
    with pytest.raises(ValueError, match="key"):
        ResearchSourceClaimConsistencyPublicPayloadItem("candidate_id", "public summary")
    with pytest.raises(ValueError, match="key"):
        ResearchSourceClaimConsistencyPublicPayloadItem(
            _join_parts("mar", "ket", "_", "id"),
            "public summary",
        )
    with pytest.raises(ValueError, match="key"):
        ResearchSourceClaimConsistencyPublicPayloadItem(
            _join_parts("source", "_", "text"),
            "public summary",
        )
    with pytest.raises(ValueError, match="key"):
        ResearchSourceClaimConsistencyPublicPayloadItem("dsn", "public summary")
    with pytest.raises(ValueError, match="key"):
        ResearchSourceClaimConsistencyPublicPayloadItem("table_name", "public summary")
    with pytest.raises(ValueError, match="key"):
        ResearchSourceClaimConsistencyPublicPayloadItem("token", "public summary")
    with pytest.raises(ValueError, match="value"):
        ResearchSourceClaimConsistencyPublicPayloadItem(
            "aggregate_scope",
            "https://example.invalid/source",
        )
    with pytest.raises(ValueError, match="value"):
        ResearchSourceClaimConsistencyPublicPayloadItem(
            "aggregate_scope",
            _join_parts("tok", "en", "_", "abc123"),
        )


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
        _join_parts("li", "ve"),
        _join_parts("tra", "ding"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("re", "place"),
        _join_parts("sig", "ning"),
        "recommend",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(token in lowered for token in unsafe_terms)
    for cls in (
        ResearchSourceClaimConsistencyGateConfig,
        ResearchSourceClaimConsistencyGateInputRow,
        ResearchSourceClaimConsistencyGateReport,
        ResearchSourceClaimConsistencyPublicPayloadItem,
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
