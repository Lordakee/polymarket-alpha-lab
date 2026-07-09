from __future__ import annotations

import ast
import importlib
import importlib.util
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any, get_args, get_type_hints

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_event_cluster_review_priority_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_event_cluster_review_priority_report.py",
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def _module() -> Any:
    spec = importlib.util.find_spec(MODULE_NAME)
    assert spec is not None, "review priority report module is missing"
    return importlib.import_module(MODULE_NAME)


def _at(**kwargs: int) -> datetime:
    return GENERATED_AT - timedelta(**kwargs)


def _input_row(
    module: Any,
    *,
    cluster_ref: str,
    raw_candidate_id: str,
    raw_market_id: str,
    raw_market_slug: str,
    raw_market_question: str,
    raw_source_url: str,
    raw_source_text: str,
    signal_divergence_score: Decimal,
    evidence_observed_at: datetime,
    source_consensus_score: Decimal,
    cost_pressure_score: Decimal,
    resolution_ambiguity_score: Decimal,
    team_capacity_score: Decimal,
) -> Any:
    return module.ResearchStrategyEventClusterReviewPriorityInputRow(
        cluster_ref=cluster_ref,
        raw_candidate_id=raw_candidate_id,
        raw_market_id=raw_market_id,
        raw_market_slug=raw_market_slug,
        raw_market_question=raw_market_question,
        raw_source_url=raw_source_url,
        raw_source_text=raw_source_text,
        signal_divergence_score=signal_divergence_score,
        evidence_observed_at=evidence_observed_at,
        source_consensus_score=source_consensus_score,
        cost_pressure_score=cost_pressure_score,
        resolution_ambiguity_score=resolution_ambiguity_score,
        team_capacity_score=team_capacity_score,
    )


def _sample_rows(module: Any) -> tuple[Any, ...]:
    return (
        _input_row(
            module,
            cluster_ref="cluster-alpha-private-ref",
            raw_candidate_id="candidate-alpha-raw-001",
            raw_market_id="market-alpha-raw-001",
            raw_market_slug="fed-path-alpha",
            raw_market_question="Will policy guidance shift this week?",
            raw_source_url="https://private.example/fed-path-alpha",
            raw_source_text="private source note with token and wallet references",
            signal_divergence_score=d("0.900000"),
            evidence_observed_at=_at(hours=8),
            source_consensus_score=d("0.200000"),
            cost_pressure_score=d("0.900000"),
            resolution_ambiguity_score=d("0.900000"),
            team_capacity_score=d("0.100000"),
        ),
        _input_row(
            module,
            cluster_ref="cluster-beta-private-ref",
            raw_candidate_id="candidate-beta-raw-001",
            raw_market_id="market-beta-raw-001",
            raw_market_slug="inflation-print-beta",
            raw_market_question="Will CPI exceed consensus?",
            raw_source_url="https://private.example/inflation-print-beta",
            raw_source_text="private source note",
            signal_divergence_score=d("0.300000"),
            evidence_observed_at=_at(hours=4),
            source_consensus_score=d("0.550000"),
            cost_pressure_score=d("0.600000"),
            resolution_ambiguity_score=d("0.550000"),
            team_capacity_score=d("0.350000"),
        ),
        _input_row(
            module,
            cluster_ref="cluster-gamma-private-ref",
            raw_candidate_id="candidate-gamma-raw-001",
            raw_market_id="market-gamma-raw-001",
            raw_market_slug="earnings-gamma",
            raw_market_question="Will earnings beat consensus?",
            raw_source_url="https://private.example/earnings-gamma",
            raw_source_text="private source note",
            signal_divergence_score=d("0.100000"),
            evidence_observed_at=_at(minutes=30),
            source_consensus_score=d("0.900000"),
            cost_pressure_score=d("0.100000"),
            resolution_ambiguity_score=d("0.100000"),
            team_capacity_score=d("0.900000"),
        ),
    )


def _report(module: Any, rows: tuple[Any, ...]) -> Any:
    return module.build_research_strategy_event_cluster_review_priority_report(
        rows,
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def test_module_import_surface_exists() -> None:
    assert importlib.util.find_spec(MODULE_NAME) is not None


def test_build_report_prioritizes_event_clusters_for_review() -> None:
    module = _module()

    report = _report(module, _sample_rows(module))

    assert is_dataclass(report)
    assert type(report) is module.ResearchStrategyEventClusterReviewPriorityReport
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        module.DEFAULT_RESEARCH_STRATEGY_EVENT_CLUSTER_REVIEW_PRIORITY_REPORT_CONFIG_VERSION
    )
    assert report.status == "block"
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_review_priority_score == d("0.502500")
    assert report.max_review_priority_score == d("0.895000")
    assert report.max_evidence_age_seconds == d("28800.000000")
    assert report.min_source_consensus_score == d("0.200000")
    assert report.max_cost_pressure_score == d("0.900000")
    assert report.max_resolution_ambiguity_score == d("0.900000")
    assert report.min_team_capacity_score == d("0.100000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.cluster_row_number for row in report.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert all(row.cluster_digest.startswith("sha256:") for row in report.rows)
    assert len({row.cluster_digest for row in report.rows}) == 3

    blocked = report.rows[0]
    assert blocked.signal_divergence_score == d("0.900000")
    assert blocked.evidence_age_seconds == d("28800.000000")
    assert blocked.evidence_freshness_pressure_score == d("1.000000")
    assert blocked.source_consensus_gap_score == d("0.800000")
    assert blocked.team_capacity_pressure_score == d("0.900000")
    assert blocked.review_priority_score == d("0.895000")
    assert blocked.reason_codes == (
        "signal_divergence_block",
        "evidence_freshness_block",
        "source_consensus_block",
        "cost_pressure_block",
        "resolution_ambiguity_block",
        "team_capacity_block",
        "review_priority_score_block",
    )

    watched = report.rows[1]
    assert watched.evidence_age_seconds == d("14400.000000")
    assert watched.evidence_freshness_pressure_score == d("0.666667")
    assert watched.source_consensus_gap_score == d("0.450000")
    assert watched.team_capacity_pressure_score == d("0.650000")
    assert watched.review_priority_score == d("0.515000")
    assert watched.reason_codes == (
        "signal_divergence_watch",
        "evidence_freshness_watch",
        "source_consensus_watch",
        "cost_pressure_watch",
        "resolution_ambiguity_watch",
        "team_capacity_watch",
        "review_priority_score_watch",
    )

    passed = report.rows[2]
    assert passed.evidence_age_seconds == d("1800.000000")
    assert passed.review_priority_score == d("0.097500")
    assert passed.reason_codes == ("event_cluster_review_priority_pass",)

    assert report.reason_codes == (
        "signal_divergence_block",
        "evidence_freshness_block",
        "source_consensus_block",
        "cost_pressure_block",
        "resolution_ambiguity_block",
        "team_capacity_block",
        "review_priority_score_block",
        "signal_divergence_watch",
        "evidence_freshness_watch",
        "source_consensus_watch",
        "cost_pressure_watch",
        "resolution_ambiguity_watch",
        "team_capacity_watch",
        "review_priority_score_watch",
        "event_cluster_review_priority_pass",
    )
    assert report.reason_code_counts[0] == (
        module.ResearchStrategyEventClusterReviewPriorityReasonCodeCount(
            reason_code="signal_divergence_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        )
    )


def test_payload_is_public_safe_deterministic_and_digest_validated() -> None:
    module = _module()

    payload = module.research_strategy_event_cluster_review_priority_report_payload(
        _report(module, tuple(reversed(_sample_rows(module)))),
    )

    json.dumps(payload, sort_keys=True)
    assert _float_paths(payload) == ()
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["row_count"] == "3.000000"
    assert len(str(payload["derived_validation_digest"])) == 64
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert tuple(row["cluster_row_number"] for row in payload["rows"]) == (
        "1.000000",
        "2.000000",
        "3.000000",
    )
    assert tuple(row["status"] for row in payload["rows"]) == ("block", "watch", "pass")

    repeat_payload = module.research_strategy_event_cluster_review_priority_report_payload(
        _report(module, _sample_rows(module)),
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
        "fed-path-alpha",
        "inflation-print-beta",
        "earnings-gamma",
        "Will policy guidance shift this week?",
        "Will CPI exceed consensus?",
        "cluster-alpha-private-ref",
        "cluster-beta-private-ref",
        "cluster-gamma-private-ref",
        "https://private.example/fed-path-alpha",
        "private source note with token and wallet references",
    ):
        assert raw_value not in payload_text
    for forbidden_public_key in (
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "private_token",
        "wallet",
    ):
        assert forbidden_public_key not in payload_text

    tampered = dict(payload)
    tampered["row_count"] = "999.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_event_cluster_review_priority_report_payload(tampered)

    redigested_extra_field = dict(payload)
    redigested_extra_field["public_note"] = "candidate-alpha-raw-001"
    redigested_extra_field["derived_validation_digest"] = _payload_digest(
        redigested_extra_field,
    )
    with pytest.raises(ValueError, match="unexpected public payload key"):
        module.research_strategy_event_cluster_review_priority_report_payload(
            redigested_extra_field,
        )

    redigested_missing_flag = dict(payload)
    redigested_missing_flag.pop("readonly")
    redigested_missing_flag["derived_validation_digest"] = _payload_digest(
        redigested_missing_flag,
    )
    with pytest.raises(ValueError, match="readonly"):
        module.research_strategy_event_cluster_review_priority_report_payload(
            redigested_missing_flag,
        )

    unsafe = dict(payload)
    unsafe["source_url"] = "https://private.example/leak"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_strategy_event_cluster_review_priority_report_payload(unsafe)

    with pytest.raises(ValueError, match="value must be"):
        module.research_strategy_event_cluster_review_priority_report_payload(object())


def test_empty_report_is_report_only_block_and_digest_stable() -> None:
    module = _module()

    report = _report(module, ())
    payload = module.research_strategy_event_cluster_review_priority_report_payload(report)

    assert report.status == "block"
    assert report.row_count == ZERO
    assert report.pass_count == ZERO
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.average_review_priority_score == ZERO
    assert report.max_review_priority_score == ZERO
    assert report.rows == ()
    assert report.reason_codes == ("empty_input",)
    assert report.reason_code_counts == (
        module.ResearchStrategyEventClusterReviewPriorityReasonCodeCount(
            reason_code="empty_input",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )
    assert payload["derived_validation_digest"] == report.derived_validation_digest


def test_public_dataclasses_are_frozen_decimal_only_and_validate_inputs() -> None:
    module = _module()
    contract_classes = (
        module.ResearchStrategyEventClusterReviewPriorityConfig,
        module.ResearchStrategyEventClusterReviewPriorityInputRow,
        module.ResearchStrategyEventClusterReviewPriorityReportRow,
        module.ResearchStrategyEventClusterReviewPriorityReasonCodeCount,
        module.ResearchStrategyEventClusterReviewPriorityReport,
    )

    assert module.REPORT_STATUSES == ("pass", "watch", "block")
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

    row = _sample_rows(module)[0]
    with pytest.raises(FrozenInstanceError):
        row.signal_divergence_score = d("0.1")  # type: ignore[attr-defined,misc]

    with pytest.raises(ValueError, match="signal_divergence_score"):
        _input_row(
            module,
            cluster_ref="cluster-bad-decimal",
            raw_candidate_id="candidate-bad",
            raw_market_id="market-bad",
            raw_market_slug="slug-bad",
            raw_market_question="Question?",
            raw_source_url="https://private.example/bad",
            raw_source_text="private",
            signal_divergence_score=0.5,  # type: ignore[arg-type]
            evidence_observed_at=_at(minutes=1),
            source_consensus_score=d("0.900000"),
            cost_pressure_score=d("0.100000"),
            resolution_ambiguity_score=d("0.100000"),
            team_capacity_score=d("0.900000"),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        _input_row(
            module,
            cluster_ref="cluster-naive",
            raw_candidate_id="candidate-naive",
            raw_market_id="market-naive",
            raw_market_slug="slug-naive",
            raw_market_question="Question?",
            raw_source_url="https://private.example/naive",
            raw_source_text="private",
            signal_divergence_score=d("0.100000"),
            evidence_observed_at=datetime(2026, 7, 8, 12, 0),
            source_consensus_score=d("0.900000"),
            cost_pressure_score=d("0.100000"),
            resolution_ambiguity_score=d("0.100000"),
            team_capacity_score=d("0.900000"),
        )
    with pytest.raises(ValueError, match="concrete UTC offset"):
        _input_row(
            module,
            cluster_ref="cluster-none-offset",
            raw_candidate_id="candidate-none-offset",
            raw_market_id="market-none-offset",
            raw_market_slug="slug-none-offset",
            raw_market_question="Question?",
            raw_source_url="https://private.example/none-offset",
            raw_source_text="private",
            signal_divergence_score=d("0.100000"),
            evidence_observed_at=datetime(
                2026,
                7,
                8,
                12,
                0,
                tzinfo=_NoneOffsetTimezone(),
            ),
            source_consensus_score=d("0.900000"),
            cost_pressure_score=d("0.100000"),
            resolution_ambiguity_score=d("0.100000"),
            team_capacity_score=d("0.900000"),
        )
    with pytest.raises(ValueError, match="evidence_observed_at"):
        _report(
            module,
            (
                _input_row(
                    module,
                    cluster_ref="cluster-future",
                    raw_candidate_id="candidate-future",
                    raw_market_id="market-future",
                    raw_market_slug="slug-future",
                    raw_market_question="Question?",
                    raw_source_url="https://private.example/future",
                    raw_source_text="private",
                    signal_divergence_score=d("0.100000"),
                    evidence_observed_at=GENERATED_AT + timedelta(seconds=1),
                    source_consensus_score=d("0.900000"),
                    cost_pressure_score=d("0.100000"),
                    resolution_ambiguity_score=d("0.100000"),
                    team_capacity_score=d("0.900000"),
                ),
            ),
        )
    with pytest.raises(ValueError, match="weights"):
        module.ResearchStrategyEventClusterReviewPriorityConfig(
            signal_divergence_weight=d("0.300000"),
        )
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)


def test_module_is_pure_in_memory_report_only_surface() -> None:
    module = _module()
    public_names = tuple(module.__all__)
    source = inspect.getsource(module).lower()
    tree = ast.parse(source)

    assert MODULE_PATH.exists()
    assert ".total_seconds(" not in source
    assert "float(" not in source
    for banned in (
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("tr", "ading"),
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


def _payload_digest(payload: dict[str, object]) -> str:
    payload_without_digest = dict(payload)
    payload_without_digest.pop("derived_validation_digest", None)
    canonical = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _type_uses_float(value: object) -> bool:
    if value is float:
        return True
    return any(_type_uses_float(item) for item in get_args(value))


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, value: datetime | None) -> None:
        return None

    def dst(self, value: datetime | None) -> None:
        return None
