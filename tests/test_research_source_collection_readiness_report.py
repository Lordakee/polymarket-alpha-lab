from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_source_collection_readiness_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "timely_evidence_age_seconds": d("7200.000000"),
        "min_evidence_count": d("3.000000"),
        "min_independent_source_count": d("2.000000"),
        "min_source_type_count": d("2.000000"),
        "pass_readiness_score": d("0.750000"),
        "watch_readiness_score": d("0.500000"),
        "timeliness_weight": d("0.350000"),
        "independence_weight": d("0.350000"),
        "source_type_diversity_weight": d("0.300000"),
    }
    values.update(overrides)
    return module.ResearchSourceCollectionReadinessConfig(**values)


def evidence(
    event_category: str = "politics",
    *,
    source_family: str = "official-election-board",
    source_type: str = "official",
    observed_at: datetime | None = None,
) -> Any:
    module = api()
    return module.ResearchSourceCollectionReadinessEvidence(
        event_category=event_category,
        source_family=source_family,
        source_type=source_type,
        observed_at=(
            observed_at if observed_at is not None else GENERATED_AT - timedelta(minutes=30)
        ),
    )


def build_report(*rows: Any, cfg: Any | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_research_source_collection_readiness_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_empty_collection_readiness_blocks_probability_work() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchSourceCollectionReadinessReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.event_category_count == d("0.000000")
    assert report.evidence_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.min_readiness_score == d("0.000000")
    assert report.average_readiness_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "research_source_collection_readiness_no_evidence",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_readiness_report_scores_timeliness_independence_and_source_type_diversity() -> None:
    report = build_report(
        evidence(
            "politics",
            source_family="official-election-board",
            source_type="official",
            observed_at=GENERATED_AT - timedelta(minutes=30),
        ),
        evidence(
            "politics",
            source_family="independent-wire",
            source_type="news",
            observed_at=GENERATED_AT - timedelta(minutes=45),
        ),
        evidence(
            "politics",
            source_family="polling-aggregator",
            source_type="data",
            observed_at=GENERATED_AT - timedelta(minutes=60),
        ),
        evidence(
            "sports.soccer",
            source_family="league-office",
            source_type="official",
            observed_at=GENERATED_AT - timedelta(minutes=15),
        ),
        evidence(
            "sports.soccer",
            source_family="club-report",
            source_type="official",
            observed_at=GENERATED_AT - timedelta(minutes=20),
        ),
        evidence(
            "finance.crypto",
            source_family="exchange-status",
            source_type="data",
            observed_at=GENERATED_AT - timedelta(hours=4),
        ),
    )

    assert report.status == "block"
    assert report.event_category_count == d("3.000000")
    assert report.evidence_count == d("6.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.min_readiness_score == d("0.325000")
    assert report.average_readiness_score == d("0.725000")
    assert tuple(row.event_category for row in report.rows) == (
        "finance.crypto",
        "sports.soccer",
        "politics",
    )
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")

    blocked, watched, passed = report.rows
    assert blocked.evidence_count == d("1.000000")
    assert blocked.timely_evidence_count == d("0.000000")
    assert blocked.latest_source_age_seconds == d("14400.000000")
    assert blocked.timely_evidence_ratio == d("0.000000")
    assert blocked.independence_ratio == d("0.500000")
    assert blocked.source_type_diversity_ratio == d("0.500000")
    assert blocked.readiness_score == d("0.325000")
    assert blocked.reason_codes == (
        "research_source_collection_readiness_block",
        "research_source_collection_readiness_insufficient_evidence_count",
        "research_source_collection_readiness_insufficient_independent_sources",
        "research_source_collection_readiness_insufficient_source_type_diversity",
        "research_source_collection_readiness_stale_evidence",
    )

    assert watched.evidence_count == d("2.000000")
    assert watched.independent_source_count == d("2.000000")
    assert watched.source_type_count == d("1.000000")
    assert watched.readiness_score == d("0.850000")
    assert watched.reason_codes == (
        "research_source_collection_readiness_insufficient_evidence_count",
        "research_source_collection_readiness_insufficient_source_type_diversity",
        "research_source_collection_readiness_watch",
    )

    assert passed.evidence_count == d("3.000000")
    assert passed.independent_source_count == d("3.000000")
    assert passed.source_type_count == d("3.000000")
    assert passed.readiness_score == d("1.000000")
    assert passed.reason_codes == (
        "research_source_collection_readiness_pass",
        "research_source_collection_readiness_ready",
    )


def test_public_payload_is_deterministic_digest_verified_and_identifier_free() -> None:
    module = api()
    rows = (
        evidence(
            "politics",
            source_family="official-election-board",
            source_type="official",
        ),
        evidence("politics", source_family="independent-wire", source_type="news"),
        evidence("politics", source_family="polling-aggregator", source_type="data"),
        evidence(
            "finance.crypto",
            source_family="raw-source-alpha",
            source_type="data",
            observed_at=GENERATED_AT - timedelta(hours=4),
        ),
    )

    payload = module.research_source_collection_readiness_report_payload(
        build_report(*rows),
    )
    reversed_payload = module.research_source_collection_readiness_report_payload(
        build_report(*reversed(rows)),
    )

    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["rows"][0]["readiness_score"] == "0.325000"
    assert json.dumps(payload, sort_keys=True)
    assert "official-election-board" not in json.dumps(payload, sort_keys=True)
    assert "raw-source-alpha" not in json.dumps(payload, sort_keys=True)

    def assert_public_safe(value: object) -> None:
        forbidden_keys = (
            "candidate_id",
            "market_id",
            "market_slug",
            "market_question",
            "question",
            "source_url",
            "source_text",
            "source_reference",
            "source_id",
            "dsn",
            "table_name",
            "token",
        )
        if isinstance(value, dict):
            for key, item in value.items():
                assert not any(fragment in key.lower() for fragment in forbidden_keys)
                assert_public_safe(item)
        elif isinstance(value, list):
            for item in value:
                assert_public_safe(item)
        else:
            assert type(value) is not float
            assert type(value) is not int
            if isinstance(value, str):
                assert not value.startswith(("http://", "https://"))

    assert_public_safe(payload)


def test_validation_rejects_bad_types_future_times_and_tampered_digests() -> None:
    module = api()
    with pytest.raises(ValueError, match="timely_evidence_age_seconds must be a Decimal"):
        config(timely_evidence_age_seconds=7200)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="pass_readiness_score must be a Decimal"):
        config(pass_readiness_score=_DecimalSubclass("0.750000"))
    with pytest.raises(ValueError, match="source_type"):
        evidence(source_type="social")
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        evidence(observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_report(
            evidence(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        build_report(evidence(observed_at=GENERATED_AT + timedelta(seconds=1)))

    report = build_report(
        evidence("politics", source_family="official-election-board", source_type="official"),
        evidence("politics", source_family="independent-wire", source_type="news"),
        evidence("politics", source_family="polling-aggregator", source_type="data"),
    )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = module.research_source_collection_readiness_report_payload(report)
    payload["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_source_collection_readiness_public_payload(payload)


def test_public_dataclasses_are_frozen_exact_and_hard_flagged() -> None:
    module = api()
    report = build_report(evidence(), evidence(source_family="wire", source_type="news"))

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_COLLECTION_READINESS_CONFIG_VERSION",
        "STATUSES",
        "SOURCE_TYPES",
        "ResearchSourceCollectionReadinessConfig",
        "ResearchSourceCollectionReadinessEvidence",
        "ResearchSourceCollectionReadinessReport",
        "ResearchSourceCollectionReadinessRow",
        "build_research_source_collection_readiness_report",
        "research_source_collection_readiness_report_payload",
        "validate_research_source_collection_readiness_public_payload",
    )
    assert module.STATUSES == ("pass", "watch", "block")
    for value in (config(), evidence(), report.rows[0], report):
        assert is_dataclass(value)
        assert type(value).__dataclass_params__.frozen
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True

    with pytest.raises(FrozenInstanceError):
        report.status = "pass"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "pass"
    with pytest.raises(ValueError, match="paper_only"):
        replace(evidence(), paper_only=False)
    with pytest.raises(TypeError, match="does not support subclassing"):

        class BadReport(module.ResearchSourceCollectionReadinessReport):
            pass


def test_module_scope_is_pure_in_memory_report_only() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        "scrapling",
        "agent_reach",
        "playwright",
        "selenium",
        "recommendation",
        "sizing",
        "private_key",
        "credential",
    ):
        assert forbidden not in lowered

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
        "aiohttp",
        "boto",
        "browser",
        "db",
        "httpx",
        "psycopg",
        "requests",
        "scrapling",
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
