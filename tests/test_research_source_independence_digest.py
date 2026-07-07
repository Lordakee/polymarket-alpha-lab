from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

import polymarket_alpha_lab.research_source_independence_digest as api
from polymarket_alpha_lab.research_source_independence_digest import (
    ResearchSourceGroupFact,
    ResearchSourceIndependenceDigestConfig,
    ResearchSourceIndependenceDigestReport,
    ResearchSourceIndependenceDigestRow,
    ResearchSourceIndependencePublicPayloadItem,
    build_research_source_independence_digest,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(char: str) -> str:
    return char * 64


def fact(
    index: int,
    *,
    correlation_group_ref: str | None = None,
    weight: Decimal = d("0.250000"),
    source_role: str = "secondary",
    stance: str = "corroborating",
    freshness_quality: Decimal = d("0.800000"),
) -> ResearchSourceGroupFact:
    suffix = f"{index:08x}"
    return ResearchSourceGroupFact(
        source_group_ref=f"sg_{suffix}",
        source_group_digest=digest(format(index, "x")),
        correlation_group_ref=correlation_group_ref or f"cg_{suffix}",
        weight=weight,
        source_role=source_role,
        stance=stance,
        freshness_quality=freshness_quality,
    )


def report(
    facts: tuple[ResearchSourceGroupFact, ...],
    *,
    config: ResearchSourceIndependenceDigestConfig | None = None,
    public_payload: tuple[ResearchSourceIndependencePublicPayloadItem, ...] = (),
    generated_at: datetime = GENERATED_AT,
) -> ResearchSourceIndependenceDigestReport:
    return build_research_source_independence_digest(
        facts,
        generated_at=generated_at,
        config=config,
        public_payload=public_payload,
    )


def test_independence_digest_passes_with_weighted_independent_coverage() -> None:
    digest_report = report(
        (
            fact(
                4,
                correlation_group_ref="cg_00000003",
                weight=d("0.100000"),
                freshness_quality=d("0.400000"),
            ),
            fact(
                1,
                weight=d("0.400000"),
                source_role="official",
                freshness_quality=d("1.000000"),
            ),
            fact(
                3,
                correlation_group_ref="cg_00000003",
                weight=d("0.200000"),
                stance="contradicting",
                freshness_quality=d("0.600000"),
            ),
            fact(
                2,
                weight=d("0.300000"),
                source_role="primary",
                stance="contradicting",
                freshness_quality=d("0.800000"),
            ),
        ),
    )

    assert type(digest_report) is ResearchSourceIndependenceDigestReport
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.status == "pass"
    assert digest_report.source_group_count == d("4.000000")
    assert digest_report.correlation_group_count == d("3.000000")
    assert digest_report.total_weight == d("1.000000")
    assert digest_report.independent_weight == d("0.700000")
    assert digest_report.independent_source_coverage == d("0.700000")
    assert digest_report.correlated_source_concentration == d("0.400000")
    assert digest_report.official_primary_source_presence == d("0.700000")
    assert digest_report.contradiction_diversity == d("0.666667")
    assert digest_report.freshness_quality == d("0.800000")
    assert digest_report.reason_codes == (
        "independent_source_coverage_pass",
        "correlated_source_concentration_pass",
        "official_or_primary_source_present",
        "contradiction_diversity_present",
        "freshness_quality_pass",
        "research_source_independence_pass",
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True

    assert tuple(row.source_group_ref for row in digest_report.rows) == (
        "sg_00000001",
        "sg_00000002",
        "sg_00000003",
        "sg_00000004",
    )
    assert all(type(row) is ResearchSourceIndependenceDigestRow for row in digest_report.rows)
    assert digest_report.rows[0].independent_weight == d("0.400000")
    assert digest_report.rows[0].correlated_weight_share == d("0.400000")
    assert digest_report.rows[2].independent_weight == d("0.000000")
    assert digest_report.rows[2].correlated_weight_share == d("0.300000")
    assert digest_report.rows[2].reason_codes == (
        "source_group_correlated",
        "source_group_secondary",
        "source_group_contradicting",
        "source_group_freshness_watch",
    )


def test_watch_and_blocked_statuses_have_deterministic_reason_codes() -> None:
    watch_report = report(
        (
            fact(1, weight=d("0.340000"), source_role="official"),
            fact(2, weight=d("0.330000"), source_role="primary"),
            fact(3, weight=d("0.330000")),
        ),
    )
    blocked_report = report(
        (
            fact(
                1,
                correlation_group_ref="cg_0000000a",
                weight=d("0.600000"),
                freshness_quality=d("0.100000"),
            ),
            fact(
                2,
                correlation_group_ref="cg_0000000a",
                weight=d("0.400000"),
                freshness_quality=d("0.200000"),
            ),
        ),
    )
    empty_report = report(())

    assert watch_report.status == "watch"
    assert watch_report.independent_source_coverage == d("1.000000")
    assert watch_report.correlated_source_concentration == d("0.340000")
    assert watch_report.contradiction_diversity == d("0.000000")
    assert watch_report.reason_codes == (
        "independent_source_coverage_pass",
        "correlated_source_concentration_pass",
        "official_or_primary_source_present",
        "contradiction_diversity_missing",
        "freshness_quality_pass",
        "research_source_independence_watch",
    )

    assert blocked_report.status == "blocked"
    assert blocked_report.independent_source_coverage == d("0.000000")
    assert blocked_report.correlated_source_concentration == d("1.000000")
    assert blocked_report.official_primary_source_presence == d("0.000000")
    assert blocked_report.freshness_quality == d("0.140000")
    assert blocked_report.reason_codes == (
        "independent_source_coverage_blocked",
        "correlated_source_concentration_blocked",
        "official_or_primary_source_missing",
        "contradiction_diversity_missing",
        "freshness_quality_blocked",
        "research_source_independence_blocked",
    )

    assert empty_report.status == "blocked"
    assert empty_report.total_weight == d("0.000000")
    assert empty_report.reason_codes == (
        "empty_source_group_facts",
        "research_source_independence_blocked",
    )


def test_payload_serializes_decimal_values_as_strings_and_rejects_tampering() -> None:
    digest_report = report(
        (
            fact(1, weight=d("0.500000"), source_role="official"),
            fact(2, weight=d("0.500000"), source_role="primary", stance="contradicting"),
        ),
        public_payload=(
            ResearchSourceIndependencePublicPayloadItem("safe_ref", digest("a")),
        ),
    )

    payload = digest_report.payload
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["total_weight"] == "1.000000"
    assert payload["rows"][0]["weight"] == "0.500000"
    assert payload["public_payload"][0]["value_digest"] == digest("a")
    assert payload["derived_validation_digest"] == digest_report.derived_validation_digest
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    assert ": 0." not in encoded
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(payload))
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    _assert_no_non_decimal_public_numbers(digest_report)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(digest_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            digest_report,
            public_payload=(
                ResearchSourceIndependencePublicPayloadItem("safe_ref", digest("b")),
            ),
        )


def test_validation_rejects_raw_source_surfaces_bad_types_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="source_group_ref"):
        replace(fact(1), source_group_ref="nytimes")
    with pytest.raises(ValueError, match="source_group_digest"):
        replace(fact(1), source_group_digest="not-a-digest")
    with pytest.raises(ValueError, match="correlation_group_ref"):
        replace(fact(1), correlation_group_ref="cg_market_slug")
    with pytest.raises(ValueError, match="weight"):
        replace(fact(1), weight=d("0.000000"))
    with pytest.raises(ValueError, match="weight"):
        replace(fact(1), weight=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="weight"):
        replace(fact(1), weight=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="source_role"):
        replace(fact(1), source_role="blog")
    with pytest.raises(ValueError, match="stance"):
        replace(fact(1), stance="unknown")
    with pytest.raises(ValueError, match="freshness_quality"):
        replace(fact(1), freshness_quality=d("1.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((fact(1),), generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((fact(1),), generated_at=_DatetimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="paper_only"):
        replace(fact(1), paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        ResearchSourceIndependenceDigestConfig(readonly=False)
    with pytest.raises(ValueError, match="unsafe public"):
        ResearchSourceIndependencePublicPayloadItem("market_slug", digest("a"))
    with pytest.raises(ValueError, match="unsafe public"):
        ResearchSourceIndependencePublicPayloadItem("raw_url", digest("a"))
    for unsafe_key in (
        "account_ref",
        "credential_ref",
        "http_ref",
        "link_ref",
        "secret_ref",
        "token_ref",
        "trading_ref",
        "www_ref",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchSourceIndependencePublicPayloadItem(unsafe_key, digest("a"))
    with pytest.raises(ValueError, match="value_digest"):
        ResearchSourceIndependencePublicPayloadItem("safe_ref", "not-a-digest")
    with pytest.raises(ValueError, match="duplicate source_group_ref"):
        report((fact(1), fact(1)))
    with pytest.raises(ValueError, match="duplicate public_payload key"):
        report(
            (fact(1),),
            public_payload=(
                ResearchSourceIndependencePublicPayloadItem("safe_ref", digest("a")),
                ResearchSourceIndependencePublicPayloadItem("safe_ref", digest("b")),
            ),
        )


def test_report_dataclass_rejects_inconsistent_reason_code_surfaces() -> None:
    digest_report = report(
        (
            fact(1, source_role="official"),
            fact(2, source_role="primary", stance="contradicting"),
        ),
    )

    bad_row = replace(
        digest_report.rows[0],
        reason_codes=(
            "source_group_correlated",
            "source_group_official_or_primary",
            "source_group_freshness_pass",
        ),
    )
    bad_row_values = _report_values_without_digest(digest_report)
    bad_row_values["rows"] = (bad_row, digest_report.rows[1])
    with pytest.raises(ValueError, match="row reason_codes"):
        ResearchSourceIndependenceDigestReport(
            **bad_row_values,
            derived_validation_digest=api._report_digest_from_values(bad_row_values),
        )

    bad_report_values = _report_values_without_digest(digest_report)
    bad_report_values["status"] = "blocked"
    bad_report_values["reason_codes"] = (
        "empty_source_group_facts",
        "research_source_independence_blocked",
    )
    with pytest.raises(ValueError, match="empty_source_group_facts"):
        ResearchSourceIndependenceDigestReport(
            **bad_report_values,
            derived_validation_digest=api._report_digest_from_values(bad_report_values),
        )


def test_public_dataclasses_are_frozen_and_reject_subclassing() -> None:
    digest_report = report((fact(1), fact(2, stance="contradicting", source_role="official")))

    with pytest.raises(FrozenInstanceError):
        digest_report.status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        digest_report.rows[0].weight = d("0.100000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(digest_report, status="blocked")

    with pytest.raises(TypeError):

        class BadFact(ResearchSourceGroupFact):
            pass


def test_owned_module_exposes_no_raw_or_trading_surfaces() -> None:
    raw_terms = ("market", "question", "url", "uri", "raw", "name", "slug")
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in raw_terms)

    for cls in (
        ResearchSourceGroupFact,
        ResearchSourceIndependenceDigestConfig,
        ResearchSourceIndependenceDigestRow,
        ResearchSourceIndependenceDigestReport,
        ResearchSourceIndependencePublicPayloadItem,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in raw_terms)
            assert "_id" not in lowered
            assert not lowered.endswith("id")

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    ):
        assert not hasattr(api, forbidden_name)

    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_independence_digest.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_source_terms = (
        "requests",
        "httpx",
        "urllib",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
        "os.environ",
        "getenv",
        "supabase",
        "postgres",
    )

    assert all(term not in source for term in forbidden_source_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))


def _report_values_without_digest(
    digest_report: ResearchSourceIndependenceDigestReport,
) -> dict[str, object]:
    return {
        field.name: getattr(digest_report, field.name)
        for field in fields(digest_report)
        if field.name != "derived_validation_digest"
    }
