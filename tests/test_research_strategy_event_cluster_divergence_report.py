from __future__ import annotations

import ast
import importlib.util
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from importlib import import_module
from typing import Any, get_args, get_type_hints

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_strategy_event_cluster_divergence_report"
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def _api() -> Any:
    return import_module(MODULE_NAME)


def _at(**kwargs: int) -> datetime:
    return GENERATED_AT - timedelta(**kwargs)


def _config(**overrides: object) -> object:
    api = _api()
    values = {
        "config_version": api.DEFAULT_RESEARCH_STRATEGY_EVENT_CLUSTER_DIVERGENCE_REPORT_CONFIG_VERSION,
        "signal_dispersion_watch_threshold": d("0.200000"),
        "signal_dispersion_block_threshold": d("0.350000"),
        "freshness_watch_age_seconds": d("7200.000000"),
        "freshness_block_age_seconds": d("21600.000000"),
        "minimum_source_class_count": d("3.000000"),
        "contradiction_watch_ratio_threshold": d("0.250000"),
        "contradiction_block_ratio_threshold": d("0.600000"),
        "manual_review_watch_urgency_threshold": d("0.500000"),
        "manual_review_block_urgency_threshold": d("0.800000"),
    }
    values.update(overrides)
    return api.ResearchStrategyEventClusterDivergenceReportConfig(**values)


def _input_row(
    *,
    raw_candidate_id: str,
    raw_market_id: str,
    raw_market_slug: str,
    raw_market_question: str,
    cluster_key: str,
    source_class: str,
    signal_score: Decimal,
    evidence_observed_at: datetime,
    unresolved_contradiction_count: Decimal,
    total_evidence_count: Decimal,
) -> object:
    return _api().ResearchStrategyEventClusterDivergenceInputRow(
        raw_candidate_id=raw_candidate_id,
        raw_market_id=raw_market_id,
        raw_market_slug=raw_market_slug,
        raw_market_question=raw_market_question,
        cluster_key=cluster_key,
        source_class=source_class,
        signal_score=signal_score,
        evidence_observed_at=evidence_observed_at,
        unresolved_contradiction_count=unresolved_contradiction_count,
        total_evidence_count=total_evidence_count,
    )


def _sample_rows() -> tuple[object, ...]:
    return (
        _input_row(
            raw_candidate_id="candidate-alpha-raw-001",
            raw_market_id="market-alpha-raw-001",
            raw_market_slug="will-fed-cut-alpha",
            raw_market_question="Will the Fed cut rates before September?",
            cluster_key="cluster-alpha-private",
            source_class="official",
            signal_score=d("0.600000"),
            evidence_observed_at=_at(hours=1),
            unresolved_contradiction_count=d("1.000000"),
            total_evidence_count=d("3.000000"),
        ),
        _input_row(
            raw_candidate_id="candidate-alpha-raw-001",
            raw_market_id="market-alpha-raw-002",
            raw_market_slug="fed-path-alpha",
            raw_market_question="Will policy guidance shift this week?",
            cluster_key="cluster-alpha-private",
            source_class="primary",
            signal_score=d("0.820000"),
            evidence_observed_at=_at(hours=2),
            unresolved_contradiction_count=d("0.000000"),
            total_evidence_count=d("2.000000"),
        ),
        _input_row(
            raw_candidate_id="candidate-alpha-raw-001",
            raw_market_id="market-alpha-raw-003",
            raw_market_slug="rates-alpha",
            raw_market_question="Will rates remain unchanged?",
            cluster_key="cluster-alpha-private",
            source_class="model",
            signal_score=d("0.550000"),
            evidence_observed_at=_at(hours=3),
            unresolved_contradiction_count=d("1.000000"),
            total_evidence_count=d("1.000000"),
        ),
        _input_row(
            raw_candidate_id="candidate-beta-raw-001",
            raw_market_id="market-beta-raw-001",
            raw_market_slug="inflation-print-beta",
            raw_market_question="Will CPI exceed consensus?",
            cluster_key="cluster-beta-private",
            source_class="official",
            signal_score=d("0.100000"),
            evidence_observed_at=_at(hours=8),
            unresolved_contradiction_count=d("3.000000"),
            total_evidence_count=d("4.000000"),
        ),
        _input_row(
            raw_candidate_id="candidate-gamma-raw-001",
            raw_market_id="market-gamma-raw-001",
            raw_market_slug="earnings-gamma",
            raw_market_question="Will earnings beat consensus?",
            cluster_key="cluster-gamma-private",
            source_class="official",
            signal_score=d("0.410000"),
            evidence_observed_at=_at(minutes=20),
            unresolved_contradiction_count=d("0.000000"),
            total_evidence_count=d("5.000000"),
        ),
        _input_row(
            raw_candidate_id="candidate-gamma-raw-001",
            raw_market_id="market-gamma-raw-002",
            raw_market_slug="revenue-gamma",
            raw_market_question="Will revenue beat consensus?",
            cluster_key="cluster-gamma-private",
            source_class="primary",
            signal_score=d("0.410000"),
            evidence_observed_at=_at(minutes=10),
            unresolved_contradiction_count=d("0.000000"),
            total_evidence_count=d("4.000000"),
        ),
        _input_row(
            raw_candidate_id="candidate-gamma-raw-001",
            raw_market_id="market-gamma-raw-003",
            raw_market_slug="guidance-gamma",
            raw_market_question="Will guidance be raised?",
            cluster_key="cluster-gamma-private",
            source_class="model",
            signal_score=d("0.410000"),
            evidence_observed_at=_at(minutes=5),
            unresolved_contradiction_count=d("0.000000"),
            total_evidence_count=d("3.000000"),
        ),
    )


def _report(*rows: object, **config_overrides: object) -> object:
    return _api().build_research_strategy_event_cluster_divergence_report(
        rows,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def test_module_import_surface_exists() -> None:
    assert importlib.util.find_spec(MODULE_NAME) is not None


def test_build_report_aggregates_event_cluster_divergence_pressure() -> None:
    api = _api()

    report = _report(*_sample_rows())

    assert type(report) is api.ResearchStrategyEventClusterDivergenceReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        api.DEFAULT_RESEARCH_STRATEGY_EVENT_CLUSTER_DIVERGENCE_REPORT_CONFIG_VERSION
    )
    assert report.report_status == "block"
    assert report.reason_codes == (
        "cluster_signal_dispersion_watch",
        "evidence_freshness_watch",
        "evidence_freshness_block",
        "source_class_coverage_block",
        "unresolved_contradiction_pressure_watch",
        "unresolved_contradiction_pressure_block",
        "manual_review_urgency_watch",
        "manual_review_urgency_block",
    )
    assert report.input_row_count == d("7.000000")
    assert report.cluster_count == d("3.000000")
    assert report.pass_cluster_count == d("1.000000")
    assert report.watch_cluster_count == d("1.000000")
    assert report.block_cluster_count == d("1.000000")
    assert report.average_signal_dispersion == d("0.090000")
    assert report.average_source_class_coverage_ratio == d("0.777778")
    assert report.average_contradiction_pressure_ratio == d("0.361111")
    assert report.max_evidence_age_seconds == d("28800.000000")
    assert report.max_manual_review_urgency_score == d("1.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.cluster_row_number for row in report.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.review_status for row in report.rows) == (
        "block",
        "watch",
        "pass",
    )
    assert len({row.cluster_hash for row in report.rows}) == 3
    assert all(len(row.cluster_hash) == 64 for row in report.rows)

    blocked = report.rows[0]
    assert blocked.signal_count == d("1.000000")
    assert blocked.candidate_count == d("1.000000")
    assert blocked.market_count == d("1.000000")
    assert blocked.source_class_count == d("1.000000")
    assert blocked.source_class_coverage_ratio == d("0.333333")
    assert blocked.signal_dispersion == d("0.000000")
    assert blocked.max_evidence_age_seconds == d("28800.000000")
    assert blocked.unresolved_contradiction_count == d("3.000000")
    assert blocked.total_evidence_count == d("4.000000")
    assert blocked.contradiction_pressure_ratio == d("0.750000")
    assert blocked.manual_review_urgency_score == d("1.000000")
    assert blocked.reason_codes == (
        "evidence_freshness_block",
        "source_class_coverage_block",
        "unresolved_contradiction_pressure_block",
        "manual_review_urgency_block",
    )

    watched = report.rows[1]
    assert watched.signal_count == d("3.000000")
    assert watched.candidate_count == d("1.000000")
    assert watched.market_count == d("3.000000")
    assert watched.source_class_count == d("3.000000")
    assert watched.source_class_coverage_ratio == d("1.000000")
    assert watched.signal_dispersion == d("0.270000")
    assert watched.max_evidence_age_seconds == d("10800.000000")
    assert watched.contradiction_pressure_ratio == d("0.333333")
    assert watched.manual_review_urgency_score == d("0.771429")
    assert watched.reason_codes == (
        "cluster_signal_dispersion_watch",
        "evidence_freshness_watch",
        "unresolved_contradiction_pressure_watch",
        "manual_review_urgency_watch",
    )

    passed = report.rows[2]
    assert passed.review_status == "pass"
    assert passed.reason_codes == ("event_cluster_divergence_pass",)
    assert passed.signal_dispersion == d("0.000000")
    assert passed.contradiction_pressure_ratio == d("0.000000")


def test_payload_is_public_safe_deterministic_and_digest_validated() -> None:
    api = _api()
    report = _report(*reversed(_sample_rows()))

    payload = api.research_strategy_event_cluster_divergence_report_payload(report)

    json.dumps(payload, sort_keys=True)
    assert _float_paths(payload) == ()
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["input_row_count"] == "7.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert tuple(row["cluster_row_number"] for row in payload["rows"]) == (
        "1.000000",
        "2.000000",
        "3.000000",
    )
    assert tuple(row["review_status"] for row in payload["rows"]) == (
        "block",
        "watch",
        "pass",
    )

    repeat_payload = api.research_strategy_event_cluster_divergence_report_payload(
        _report(*_sample_rows()),
    )
    assert payload == repeat_payload

    payload_text = json.dumps(payload, sort_keys=True)
    for raw_value in (
        "candidate-alpha-raw-001",
        "candidate-beta-raw-001",
        "candidate-gamma-raw-001",
        "market-alpha-raw-001",
        "market-beta-raw-001",
        "market-gamma-raw-001",
        "will-fed-cut-alpha",
        "inflation-print-beta",
        "earnings-gamma",
        "Will the Fed cut rates before September?",
        "Will CPI exceed consensus?",
        "cluster-alpha-private",
        "cluster-beta-private",
        "cluster-gamma-private",
    ):
        assert raw_value not in payload_text
    for forbidden_public_key in (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "private_token",
    ):
        assert forbidden_public_key not in payload_text

    tampered = dict(payload)
    tampered["cluster_count"] = "999.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.research_strategy_event_cluster_divergence_report_payload(tampered)

    with pytest.raises(ValueError, match="report must be"):
        api.research_strategy_event_cluster_divergence_report_payload(object())


def test_empty_report_is_pass_and_digest_stable() -> None:
    api = _api()

    report = _report()
    payload = api.research_strategy_event_cluster_divergence_report_payload(report)

    assert report.report_status == "pass"
    assert report.reason_codes == ("event_cluster_divergence_pass",)
    assert report.input_row_count == d("0.000000")
    assert report.cluster_count == d("0.000000")
    assert report.average_signal_dispersion == d("0.000000")
    assert report.max_manual_review_urgency_score == d("0.000000")
    assert report.rows == ()
    assert payload["derived_validation_digest"] == report.derived_validation_digest


def test_public_dataclasses_are_frozen_decimal_only_and_validate_inputs() -> None:
    api = _api()
    contract_classes = (
        api.ResearchStrategyEventClusterDivergenceReportConfig,
        api.ResearchStrategyEventClusterDivergenceInputRow,
        api.ResearchStrategyEventClusterDivergenceReportRow,
        api.ResearchStrategyEventClusterDivergenceReport,
    )

    assert api.REPORT_STATUSES == ("pass", "watch", "block")
    for contract_class in contract_classes:
        assert is_dataclass(contract_class)
        assert contract_class.__dataclass_params__.frozen is True
        defaults = {field.name: field.default for field in fields(contract_class)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True
        for field_name, hint in get_type_hints(contract_class).items():
            if field_name in {"paper_only", "report_only", "readonly"}:
                continue
            assert not _type_uses_float(hint)

    row = _sample_rows()[0]
    with pytest.raises(FrozenInstanceError):
        row.signal_score = d("0.1")  # type: ignore[attr-defined,misc]

    with pytest.raises(ValueError, match="signal_score"):
        _input_row(
            raw_candidate_id="candidate-bad",
            raw_market_id="market-bad",
            raw_market_slug="slug-bad",
            raw_market_question="Question?",
            cluster_key="cluster-bad",
            source_class="official",
            signal_score=0.5,  # type: ignore[arg-type]
            evidence_observed_at=_at(minutes=1),
            unresolved_contradiction_count=d("0.000000"),
            total_evidence_count=d("1.000000"),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        _input_row(
            raw_candidate_id="candidate-naive",
            raw_market_id="market-naive",
            raw_market_slug="slug-naive",
            raw_market_question="Question?",
            cluster_key="cluster-naive",
            source_class="official",
            signal_score=d("0.500000"),
            evidence_observed_at=datetime(2026, 7, 8, 12, 0),
            unresolved_contradiction_count=d("0.000000"),
            total_evidence_count=d("1.000000"),
        )
    with pytest.raises(ValueError, match="concrete UTC offset"):
        _input_row(
            raw_candidate_id="candidate-none-offset",
            raw_market_id="market-none-offset",
            raw_market_slug="slug-none-offset",
            raw_market_question="Question?",
            cluster_key="cluster-none-offset",
            source_class="official",
            signal_score=d("0.500000"),
            evidence_observed_at=datetime(
                2026,
                7,
                8,
                12,
                0,
                tzinfo=_NoneOffsetTimezone(),
            ),
            unresolved_contradiction_count=d("0.000000"),
            total_evidence_count=d("1.000000"),
        )
    with pytest.raises(ValueError, match="evidence_observed_at"):
        _report(
            _input_row(
                raw_candidate_id="candidate-future",
                raw_market_id="market-future",
                raw_market_slug="slug-future",
                raw_market_question="Question?",
                cluster_key="cluster-future",
                source_class="official",
                signal_score=d("0.500000"),
                evidence_observed_at=GENERATED_AT + timedelta(seconds=1),
                unresolved_contradiction_count=d("0.000000"),
                total_evidence_count=d("1.000000"),
            ),
        )
    with pytest.raises(ValueError, match="source_class"):
        _input_row(
            raw_candidate_id="candidate-source-class",
            raw_market_id="market-source-class",
            raw_market_slug="slug-source-class",
            raw_market_question="Question?",
            cluster_key="cluster-source-class",
            source_class="message-board",
            signal_score=d("0.500000"),
            evidence_observed_at=_at(minutes=1),
            unresolved_contradiction_count=d("0.000000"),
            total_evidence_count=d("1.000000"),
        )
    with pytest.raises(ValueError, match="total_evidence_count"):
        _input_row(
            raw_candidate_id="candidate-count",
            raw_market_id="market-count",
            raw_market_slug="slug-count",
            raw_market_question="Question?",
            cluster_key="cluster-count",
            source_class="official",
            signal_score=d("0.500000"),
            evidence_observed_at=_at(minutes=1),
            unresolved_contradiction_count=d("2.000000"),
            total_evidence_count=d("1.000000"),
        )
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)


def test_module_is_pure_in_memory_report_only_surface() -> None:
    api = _api()
    public_names = tuple(api.__all__)
    source = inspect.getsource(api).lower()
    tree = ast.parse(source)

    assert ".total_seconds(" not in source
    assert "float(" not in source
    for banned in (
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("tra", "ding"),
        _join_parts("siz", "ing"),
        _join_parts("recommend", "ation"),
    ):
        assert banned not in source
        assert all(banned not in name.lower() for name in public_names)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "buy",
                "connect",
                "execute",
                "executemany",
                "open",
                "patch",
                "place",
                "post",
                "put",
                "request",
                "sell",
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


def _float_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if isinstance(value, float):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_float_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_float_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()


def _type_uses_float(value: object) -> bool:
    if value is float:
        return True
    return any(_type_uses_float(item) for item in get_args(value))


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, value: datetime | None) -> None:
        return None

    def dst(self, value: datetime | None) -> None:
        return None
