from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_source_multisource_freshness_gap_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_multisource_freshness_gap_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def observation(
    research_group_id: str,
    *,
    source_family: str,
    seconds_old: int = 1800,
    authority_score: Decimal = d("0.900000"),
    corroboration_score: Decimal = d("0.900000"),
    contradiction_exposure_score: Decimal = d("0.050000"),
    domain_coverage_score: Decimal = d("0.900000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchSourceMultisourceFreshnessObservation(
        research_group_id=research_group_id,
        source_family=source_family,
        observed_at=GENERATED_AT - timedelta(seconds=seconds_old),
        authority_score=authority_score,
        corroboration_score=corroboration_score,
        contradiction_exposure_score=contradiction_exposure_score,
        domain_coverage_score=domain_coverage_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def cfg(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": "research-source-multisource-freshness-gap-report-v0",
        "required_source_families": (
            "official_reporting",
            "domain_specialist",
            "independent_archive",
        ),
        "max_fresh_age_seconds": d("7200.000000"),
        "min_authority_score": d("0.700000"),
        "min_corroboration_score": d("0.650000"),
        "min_domain_coverage_score": d("0.750000"),
        "watch_freshness_gap_score": d("0.350000"),
        "block_freshness_gap_score": d("0.700000"),
        "block_missing_source_family_count": d("2.000000"),
        "update_age_gap_weight": d("0.250000"),
        "authority_gap_weight": d("0.200000"),
        "corroboration_gap_weight": d("0.200000"),
        "contradiction_exposure_weight": d("0.200000"),
        "domain_coverage_gap_weight": d("0.150000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchSourceMultisourceFreshnessGapReportConfig(**values)


def report(*items: object, generated_at: datetime = GENERATED_AT, config: object | None = None):
    module = api()
    return module.build_research_source_multisource_freshness_gap_report(
        items,
        generated_at=generated_at,
        config=config or cfg(),
    )


def assert_no_public_number_payload(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"payload numeric was not serialized as string: {value!r}")
    if isinstance(value, dict):
        for item_value in value.values():
            assert_no_public_number_payload(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_public_number_payload(item_value)


def assert_no_forbidden_public_surface(value: Any) -> None:
    forbidden_key_fragments = (
        "raw",
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "trading",
        "secret",
        "private_key",
        "api_key",
    )
    forbidden_value_fragments = (
        "://",
        "www.",
        "candidate",
        "market_slug",
        "slug",
        "question",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "trading",
        "secret",
        "private_key",
        "api_key",
    )
    if isinstance(value, dict):
        for key, item_value in value.items():
            lowered = key.lower()
            for fragment in forbidden_key_fragments:
                assert fragment not in lowered, key
            assert_no_forbidden_public_surface(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_forbidden_public_surface(item_value)
        return
    if isinstance(value, str):
        lowered = value.lower()
        for fragment in forbidden_value_fragments:
            assert fragment not in lowered, value
        assert " auth" not in lowered, value
        assert "auth " not in lowered, value


def assert_decimal_public_numbers(value: object) -> None:
    for field in fields(value):
        if field.name in {"rows", "reason_code_counts", "public_payload"}:
            continue
        if any(
            marker in field.name
            for marker in (
                "count",
                "score",
                "age",
                "coverage",
                "authority",
                "corroboration",
                "contradiction",
                "weight",
            )
        ):
            assert type(getattr(value, field.name)) is Decimal, field.name


def test_scores_multisource_freshness_gaps_by_group() -> None:
    built = report(
        observation(
            "research-pass",
            source_family="official_reporting",
            seconds_old=1800,
            authority_score=d("0.950000"),
            corroboration_score=d("0.900000"),
            contradiction_exposure_score=d("0.050000"),
            domain_coverage_score=d("0.900000"),
        ),
        observation(
            "research-pass",
            source_family="domain_specialist",
            seconds_old=1200,
            authority_score=d("0.900000"),
            corroboration_score=d("0.880000"),
            contradiction_exposure_score=d("0.100000"),
            domain_coverage_score=d("0.850000"),
        ),
        observation(
            "research-pass",
            source_family="independent_archive",
            seconds_old=600,
            authority_score=d("0.850000"),
            corroboration_score=d("0.920000"),
            contradiction_exposure_score=d("0.080000"),
            domain_coverage_score=d("0.900000"),
        ),
        observation(
            "research-watch",
            source_family="official_reporting",
            seconds_old=3600,
            authority_score=d("0.750000"),
            corroboration_score=d("0.700000"),
            contradiction_exposure_score=d("0.200000"),
            domain_coverage_score=d("0.800000"),
        ),
        observation(
            "research-watch",
            source_family="domain_specialist",
            seconds_old=4000,
            authority_score=d("0.720000"),
            corroboration_score=d("0.680000"),
            contradiction_exposure_score=d("0.150000"),
            domain_coverage_score=d("0.780000"),
        ),
        observation(
            "research-block",
            source_family="official_reporting",
            seconds_old=10800,
            authority_score=d("0.350000"),
            corroboration_score=d("0.200000"),
            contradiction_exposure_score=d("0.950000"),
            domain_coverage_score=d("0.400000"),
        ),
    )

    assert built.status == "block"
    assert built.group_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.max_freshness_gap_score == d("0.820000")
    assert built.average_freshness_gap_score == d("0.428463")
    assert tuple(row.research_group_id for row in built.rows) == (
        "research-block",
        "research-watch",
        "research-pass",
    )

    blocked, watched, passed = built.rows
    assert blocked.status == "block"
    assert blocked.source_count == d("1.000000")
    assert blocked.source_family_count == d("1.000000")
    assert blocked.missing_source_family_count == d("2.000000")
    assert blocked.stale_source_count == d("1.000000")
    assert blocked.low_authority_source_count == d("1.000000")
    assert blocked.low_corroboration_source_count == d("1.000000")
    assert blocked.contradiction_exposed_source_count == d("1.000000")
    assert blocked.domain_coverage_gap_count == d("1.000000")
    assert blocked.max_source_age_seconds == d("10800.000000")
    assert blocked.average_authority_score == d("0.350000")
    assert blocked.average_corroboration_score == d("0.200000")
    assert blocked.max_contradiction_exposure_score == d("0.950000")
    assert blocked.average_domain_coverage_score == d("0.400000")
    assert blocked.freshness_gap_score == d("0.820000")
    assert blocked.reason_codes == (
        "update_age_gap_block",
        "low_authority_block",
        "low_corroboration_block",
        "contradiction_exposure_block",
        "domain_coverage_gap_block",
        "missing_source_family_block",
        "freshness_gap_block",
    )

    assert watched.status == "watch"
    assert watched.source_count == d("2.000000")
    assert watched.source_family_count == d("2.000000")
    assert watched.missing_source_family_count == d("1.000000")
    assert watched.max_source_age_seconds == d("4000.000000")
    assert watched.average_authority_score == d("0.735000")
    assert watched.average_corroboration_score == d("0.690000")
    assert watched.max_contradiction_exposure_score == d("0.200000")
    assert watched.average_domain_coverage_score == d("0.790000")
    assert watched.freshness_gap_score == d("0.325389")
    assert watched.reason_codes == (
        "missing_source_family_watch",
        "freshness_gap_watch",
    )

    assert passed.status == "pass"
    assert passed.source_family_count == d("3.000000")
    assert passed.missing_source_family_count == d("0.000000")
    assert passed.max_source_age_seconds == d("1800.000000")
    assert passed.average_authority_score == d("0.900000")
    assert passed.average_corroboration_score == d("0.900000")
    assert passed.max_contradiction_exposure_score == d("0.100000")
    assert passed.average_domain_coverage_score == d("0.883333")
    assert passed.freshness_gap_score == d("0.140000")
    assert passed.reason_codes == ("source_multisource_freshness_gap_passed",)
    assert passed.paper_only is True
    assert passed.report_only is True
    assert passed.readonly is True


def test_payload_digest_decimal_strings_and_public_surface_are_deterministic() -> None:
    module = api()
    items = (
        observation("research-alpha", source_family="official_reporting"),
        observation("research-alpha", source_family="domain_specialist"),
        observation("research-alpha", source_family="independent_archive"),
        observation(
            "research-beta",
            source_family="official_reporting",
            seconds_old=9000,
            authority_score=d("0.500000"),
            corroboration_score=d("0.400000"),
            contradiction_exposure_score=d("0.700000"),
            domain_coverage_score=d("0.600000"),
        ),
    )
    first = report(*items)
    second = report(*reversed(items))

    payload = module.research_source_multisource_freshness_gap_report_payload(first)
    json.dumps(payload, sort_keys=True)
    assert payload == first.payload
    assert payload["group_count"] == "2.000000"
    assert payload["rows"][0]["research_group_id"] == "research-beta"
    assert payload["rows"][0]["freshness_gap_score"] == "0.700000"
    assert payload["rows"][1]["freshness_gap_score"] == "0.127500"
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert first.derived_validation_digest == second.derived_validation_digest
    assert module.research_source_multisource_freshness_gap_report_digest(first) == (
        first.derived_validation_digest
    )
    assert len(first.derived_validation_digest) == 64
    assert_no_public_number_payload(payload)
    assert_no_forbidden_public_surface(payload)
    assert_decimal_public_numbers(first)


def test_public_exports_and_dataclass_schemas_are_exact() -> None:
    module = api()
    expected_schemas = {
        module.ResearchSourceMultisourceFreshnessGapReportConfig: (
            "config_version",
            "required_source_families",
            "max_fresh_age_seconds",
            "min_authority_score",
            "min_corroboration_score",
            "min_domain_coverage_score",
            "watch_freshness_gap_score",
            "block_freshness_gap_score",
            "block_missing_source_family_count",
            "update_age_gap_weight",
            "authority_gap_weight",
            "corroboration_gap_weight",
            "contradiction_exposure_weight",
            "domain_coverage_gap_weight",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchSourceMultisourceFreshnessObservation: (
            "research_group_id",
            "source_family",
            "observed_at",
            "authority_score",
            "corroboration_score",
            "contradiction_exposure_score",
            "domain_coverage_score",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchSourceMultisourceFreshnessGapPublicPayloadItem: (
            "key",
            "value",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchSourceMultisourceFreshnessGapReasonCodeCount: (
            "reason_code",
            "count",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchSourceMultisourceFreshnessGapRow: (
            "research_group_id",
            "source_count",
            "source_family_count",
            "missing_source_family_count",
            "stale_source_count",
            "low_authority_source_count",
            "low_corroboration_source_count",
            "contradiction_exposed_source_count",
            "domain_coverage_gap_count",
            "max_source_age_seconds",
            "average_authority_score",
            "average_corroboration_score",
            "max_contradiction_exposure_score",
            "average_domain_coverage_score",
            "freshness_gap_score",
            "status",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchSourceMultisourceFreshnessGapReport: (
            "generated_at",
            "config_version",
            "max_fresh_age_seconds",
            "min_authority_score",
            "min_corroboration_score",
            "min_domain_coverage_score",
            "watch_freshness_gap_score",
            "block_freshness_gap_score",
            "block_missing_source_family_count",
            "status",
            "group_count",
            "pass_count",
            "watch_count",
            "block_count",
            "average_freshness_gap_score",
            "max_freshness_gap_score",
            "rows",
            "reason_codes",
            "reason_code_counts",
            "public_payload",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        ),
    }

    for dataclass_type, expected_field_names in expected_schemas.items():
        assert tuple(field.name for field in fields(dataclass_type)) == (
            expected_field_names
        )

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_MULTISOURCE_FRESHNESS_GAP_REPORT_CONFIG_VERSION",
        "ResearchSourceMultisourceFreshnessGapPublicPayloadItem",
        "ResearchSourceMultisourceFreshnessGapReasonCodeCount",
        "ResearchSourceMultisourceFreshnessGapReport",
        "ResearchSourceMultisourceFreshnessGapReportConfig",
        "ResearchSourceMultisourceFreshnessGapRow",
        "ResearchSourceMultisourceFreshnessObservation",
        "build_research_source_multisource_freshness_gap_report",
        "research_source_multisource_freshness_gap_report_digest",
        "research_source_multisource_freshness_gap_report_payload",
    )


def test_public_payload_rejects_raw_surfaces_and_duplicate_keys() -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe"):
        module.ResearchSourceMultisourceFreshnessGapPublicPayloadItem(
            key="raw_summary",
            value="sanitized",
        )

    with pytest.raises(ValueError, match="unsafe"):
        module.ResearchSourceMultisourceFreshnessGapPublicPayloadItem(
            key="summary",
            value="raw_summary",
        )

    duplicate_payload = (
        module.ResearchSourceMultisourceFreshnessGapPublicPayloadItem(
            key="summary",
            value="alpha",
        ),
        module.ResearchSourceMultisourceFreshnessGapPublicPayloadItem(
            key="summary",
            value="beta",
        ),
    )
    with pytest.raises(ValueError, match="duplicate public_payload key"):
        module.build_research_source_multisource_freshness_gap_report(
            (),
            generated_at=GENERATED_AT,
            config=cfg(),
            public_payload=duplicate_payload,
        )


@pytest.mark.parametrize(
    "unsafe_value",
    (
        "recommendation",
        "execution_plan",
        "position_sizing",
        "oauth_credential",
        "local_file_path",
        "supabase_storage",
    ),
)
def test_public_payload_rejects_advice_auth_and_persistence_surfaces(
    unsafe_value: str,
) -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe"):
        module.ResearchSourceMultisourceFreshnessGapPublicPayloadItem(
            key="summary",
            value=unsafe_value,
        )


def test_frozen_flags_subclassing_and_digest_tampering_are_rejected() -> None:
    module = api()
    built = report(
        observation("research-alpha", source_family="official_reporting"),
        observation("research-alpha", source_family="domain_specialist"),
        observation("research-alpha", source_family="independent_archive"),
    )

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(module.ResearchSourceMultisourceFreshnessGapReportConfig):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        replace(built.rows[0], report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(built, readonly=False)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)


def test_public_count_fields_require_whole_decimals() -> None:
    built = report(
        observation("research-alpha", source_family="official_reporting"),
        observation("research-alpha", source_family="domain_specialist"),
        observation("research-alpha", source_family="independent_archive"),
    )

    with pytest.raises(
        ValueError,
        match="block_missing_source_family_count must be a whole Decimal",
    ):
        cfg(block_missing_source_family_count=d("1.500000"))

    with pytest.raises(ValueError, match="source_count must be a whole Decimal"):
        replace(built.rows[0], source_count=d("3.500000"))

    with pytest.raises(ValueError, match="count must be a whole Decimal"):
        replace(built.reason_code_counts[0], count=d("1.500000"))


def test_config_rejects_duplicate_families_and_impossible_missing_threshold() -> None:
    with pytest.raises(ValueError, match="duplicate required_source_families"):
        cfg(
            required_source_families=(
                "official_reporting",
                "official_reporting",
            ),
        )

    with pytest.raises(
        ValueError,
        match="block_missing_source_family_count must not exceed",
    ):
        cfg(block_missing_source_family_count=d("4.000000"))


def test_report_rejects_inconsistent_reason_counts_with_matching_digest() -> None:
    module = api()
    built = report(
        observation("research-alpha", source_family="official_reporting"),
        observation("research-alpha", source_family="domain_specialist"),
        observation("research-alpha", source_family="independent_archive"),
    )
    values = {
        field.name: getattr(built, field.name)
        for field in fields(built)
        if field.name != "derived_validation_digest"
    }
    values["reason_code_counts"] = ()
    matching_digest = module._report_digest_from_values(values)

    with pytest.raises(ValueError, match="reason_code_counts must match rows"):
        replace(
            built,
            reason_code_counts=(),
            derived_validation_digest=matching_digest,
        )


def test_report_rejects_duplicate_group_rows_with_matching_digest() -> None:
    module = api()
    built = report(
        observation("research-alpha", source_family="official_reporting"),
        observation("research-alpha", source_family="domain_specialist"),
        observation("research-alpha", source_family="independent_archive"),
    )
    duplicated_rows = (built.rows[0], built.rows[0])
    doubled_reason_counts = tuple(
        replace(item, count=item.count * d("2.000000"))
        for item in built.reason_code_counts
    )
    values = {
        field.name: getattr(built, field.name)
        for field in fields(built)
        if field.name != "derived_validation_digest"
    }
    values.update(
        {
            "group_count": d("2.000000"),
            "pass_count": d("2.000000"),
            "rows": duplicated_rows,
            "reason_code_counts": doubled_reason_counts,
        },
    )
    matching_digest = module._report_digest_from_values(values)

    with pytest.raises(ValueError, match="duplicate research_group_id"):
        replace(
            built,
            group_count=d("2.000000"),
            pass_count=d("2.000000"),
            rows=duplicated_rows,
            reason_code_counts=doubled_reason_counts,
            derived_validation_digest=matching_digest,
        )


def test_strict_types_unsafe_inputs_and_live_surfaces_are_rejected() -> None:
    with pytest.raises(ValueError, match="authority_score must be a Decimal"):
        observation("research-alpha", source_family="official_reporting", authority_score=0.9)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="corroboration_score must be exactly Decimal"):
        observation(
            "research-alpha",
            source_family="official_reporting",
            corroboration_score=_DecimalSubclass("0.900000"),  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="paper_only must be a bool"):
        observation("research-alpha", source_family="official_reporting", paper_only=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report(generated_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC))

    module = api()
    with pytest.raises(ValueError, match="timezone-aware"):
        module.ResearchSourceMultisourceFreshnessObservation(
            research_group_id="research-alpha",
            source_family="official_reporting",
            observed_at=datetime(2026, 7, 8, 11, 30),
            authority_score=d("0.900000"),
            corroboration_score=d("0.900000"),
            contradiction_exposure_score=d("0.050000"),
            domain_coverage_score=d("0.900000"),
        )

    with pytest.raises(ValueError, match="utcoffset"):
        module.ResearchSourceMultisourceFreshnessObservation(
            research_group_id="research-alpha",
            source_family="official_reporting",
            observed_at=datetime(2026, 7, 8, 11, 30, tzinfo=_NoneOffsetTz()),
            authority_score=d("0.900000"),
            corroboration_score=d("0.900000"),
            contradiction_exposure_score=d("0.050000"),
            domain_coverage_score=d("0.900000"),
        )

    with pytest.raises(ValueError, match="unsafe"):
        observation("candidate_id_123", source_family="official_reporting")

    with pytest.raises(ValueError, match="unsafe"):
        observation("research-alpha", source_family="market_slug_alpha")

    with pytest.raises(ValueError, match="unsafe"):
        observation("research-alpha", source_family="https://example.invalid/source")

    with pytest.raises(ValueError, match="required_source_families must be non-empty"):
        cfg(required_source_families=())

    with pytest.raises(ValueError, match="weights must sum to one"):
        cfg(domain_coverage_gap_weight=d("0.100000"))

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    forbidden_imports = {
        "aiohttp",
        "boto3",
        "os",
        "pathlib",
        "pymongo",
        "psycopg2",
        "redis",
        "requests",
        "httpx",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
        "py_clob_client",
    }
    assert imported_roots.isdisjoint(forbidden_imports)
    forbidden_call_names = {
        "connect",
        "makedirs",
        "mkdir",
        "open",
        "remove",
        "rename",
        "request",
        "rmdir",
        "unlink",
        "urlopen",
        "write",
        "write_bytes",
        "write_text",
    }
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert called_names.isdisjoint(forbidden_call_names)
    assert called_attributes.isdisjoint(forbidden_call_names)
    public_names = set(dir(api()))
    assert "client" not in public_names
    assert "wallet" not in public_names
    assert "order" not in public_names
