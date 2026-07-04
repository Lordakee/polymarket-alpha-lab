from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_recommendation_source_coverage_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-source-coverage-v0",
        "min_source_count": d("3"),
        "min_source_family_count": d("2"),
        "max_source_age_hours": d("24"),
        "require_resolution_source_evidence": True,
    }
    values.update(overrides)
    return module.StrategyRecommendationSourceCoverageDigestConfig(**values)


def evidence(
    candidate_id: str,
    source_id: str,
    source_family: str,
    *,
    observed_at: datetime = GENERATED_AT - timedelta(hours=2),
    resolution_source_evidence: bool = False,
    reason_codes: tuple[str, ...] = ("source_coverage_input",),
):
    module = api()
    return module.StrategyRecommendationSourceCoverageDigestInput(
        candidate_id=candidate_id,
        source_id=source_id,
        source_family=source_family,
        observed_at=observed_at,
        resolution_source_evidence=resolution_source_evidence,
        reason_codes=reason_codes,
    )


def report(*rows, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_strategy_recommendation_source_coverage_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def passing_candidate(candidate_id: str = "candidate-alpha"):
    return (
        evidence(candidate_id, "official-1", "official", resolution_source_evidence=True),
        evidence(candidate_id, "news-1", "news"),
        evidence(candidate_id, "news-2", "news"),
    )


def test_empty_input_returns_clear_readonly_decimal_report() -> None:
    digest = report()

    assert is_dataclass(digest)
    assert digest.generated_at == GENERATED_AT
    assert digest.config_version == "strategy-source-coverage-v0"
    assert digest.input_count == d("0")
    assert digest.candidate_count == d("0")
    assert digest.sufficient_candidate_count == d("0")
    assert digest.watch_candidate_count == d("0")
    assert digest.blocked_candidate_count == d("0")
    assert digest.stale_candidate_count == d("0")
    assert digest.missing_resolution_candidate_count == d("0")
    assert digest.low_source_family_candidate_count == d("0")
    assert digest.status == "pass"
    assert digest.reason_codes == ("source_coverage_digest_clear",)
    assert digest.rows == ()
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True


def test_sufficient_coverage_across_families_recency_and_resolution_evidence() -> None:
    digest = report(*passing_candidate())

    assert digest.status == "pass"
    assert digest.reason_codes == ("source_coverage_digest_sufficient",)
    assert digest.input_count == d("3")
    assert digest.candidate_count == d("1")
    assert digest.sufficient_candidate_count == d("1")
    assert digest.watch_candidate_count == d("0")
    assert digest.blocked_candidate_count == d("0")

    row = digest.rows[0]
    assert row.candidate_id == "candidate-alpha"
    assert row.coverage_status == "sufficient"
    assert row.source_count == d("3")
    assert row.fresh_source_count == d("3")
    assert row.stale_source_count == d("0")
    assert row.source_family_count == d("2")
    assert row.fresh_source_family_count == d("2")
    assert row.resolution_source_evidence_count == d("1")
    assert row.source_coverage_ratio == d("1.000000")
    assert row.source_family_coverage_ratio == d("1.000000")
    assert row.reason_codes == ("source_coverage_sufficient",)


def test_stale_sources_watch_when_fresh_coverage_is_still_sufficient() -> None:
    digest = report(
        *passing_candidate("candidate-stale"),
        evidence(
            "candidate-stale",
            "old-1",
            "official",
            observed_at=GENERATED_AT - timedelta(hours=25),
            resolution_source_evidence=True,
        ),
    )

    assert digest.status == "watch"
    assert digest.sufficient_candidate_count == d("0")
    assert digest.watch_candidate_count == d("1")
    assert digest.stale_candidate_count == d("1")
    assert digest.reason_codes == ("source_coverage_stale_sources_present",)
    assert digest.rows[0].coverage_status == "watch"
    assert digest.rows[0].fresh_source_count == d("3")
    assert digest.rows[0].stale_source_count == d("1")
    assert digest.rows[0].reason_codes == ("source_coverage_sources_stale",)


def test_missing_resolution_source_evidence_blocks_candidate() -> None:
    digest = report(
        evidence("candidate-missing-resolution", "news-1", "news"),
        evidence("candidate-missing-resolution", "news-2", "news"),
        evidence("candidate-missing-resolution", "data-1", "data"),
    )

    assert digest.status == "blocked"
    assert digest.blocked_candidate_count == d("1")
    assert digest.missing_resolution_candidate_count == d("1")
    assert digest.reason_codes == ("source_coverage_resolution_evidence_missing",)
    assert digest.rows[0].coverage_status == "blocked"
    assert digest.rows[0].resolution_source_evidence_count == d("0")
    assert digest.rows[0].reason_codes == (
        "source_coverage_resolution_evidence_missing",
    )


def test_low_source_family_diversity_blocks_candidate() -> None:
    digest = report(
        evidence(
            "candidate-low-family",
            "official-1",
            "official",
            resolution_source_evidence=True,
        ),
        evidence("candidate-low-family", "official-2", "official"),
        evidence("candidate-low-family", "official-3", "official"),
    )

    assert digest.status == "blocked"
    assert digest.low_source_family_candidate_count == d("1")
    assert digest.reason_codes == ("source_coverage_family_diversity_low",)
    assert digest.rows[0].fresh_source_family_count == d("1")
    assert digest.rows[0].source_family_coverage_ratio == d("0.500000")
    assert digest.rows[0].reason_codes == (
        "source_coverage_family_diversity_below_minimum",
    )


def test_rows_and_rollup_reason_codes_are_sorted_deterministically() -> None:
    digest = report(
        evidence("candidate-zeta", "official-1", "official", resolution_source_evidence=True),
        evidence("candidate-alpha", "official-1", "official", resolution_source_evidence=True),
        evidence("candidate-alpha", "news-1", "news"),
        evidence("candidate-alpha", "news-2", "news"),
        evidence("candidate-mu", "official-1", "official", resolution_source_evidence=True),
        evidence("candidate-mu", "news-1", "news"),
        evidence("candidate-mu", "news-2", "news"),
        evidence(
            "candidate-mu",
            "old-1",
            "official",
            observed_at=GENERATED_AT - timedelta(days=2),
            resolution_source_evidence=True,
        ),
    )

    assert tuple(row.candidate_id for row in digest.rows) == (
        "candidate-zeta",
        "candidate-mu",
        "candidate-alpha",
    )
    assert tuple(row.coverage_status for row in digest.rows) == (
        "blocked",
        "watch",
        "sufficient",
    )
    assert digest.reason_codes == (
        "source_coverage_sources_below_minimum",
        "source_coverage_family_diversity_low",
        "source_coverage_stale_sources_present",
    )


def test_payload_helper_uses_decimal_strings_and_no_floats() -> None:
    payload = api().strategy_recommendation_source_coverage_digest_payload(
        report(*passing_candidate()),
    )

    assert payload["input_count"] == "3"
    assert payload["rows"][0]["source_coverage_ratio"] == "1.000000"
    assert payload["rows"][0]["observed_source_families"] == ["news", "official"]

    def assert_no_float(value: object) -> None:
        if isinstance(value, float):
            raise AssertionError("payload contains a float")
        if isinstance(value, dict):
            for item in value.values():
                assert_no_float(item)
        if isinstance(value, list):
            for item in value:
                assert_no_float(item)

    assert_no_float(payload)


def test_payload_helper_requires_report_hard_flags() -> None:
    module = api()
    digest = report(*passing_candidate())

    with pytest.raises(ValueError, match="paper_only"):
        module.strategy_recommendation_source_coverage_digest_payload(
            replace(digest, paper_only=False),
        )
    with pytest.raises(ValueError, match="report_only"):
        module.strategy_recommendation_source_coverage_digest_payload(
            replace(digest, report_only=False),
        )
    with pytest.raises(ValueError, match="readonly"):
        module.strategy_recommendation_source_coverage_digest_payload(
            replace(digest, readonly=False),
        )


def test_validation_errors_for_inputs_config_and_report_consistency() -> None:
    module = api()

    with pytest.raises(ValueError, match="min_source_count"):
        config(min_source_count=d("0"))
    with pytest.raises(ValueError, match="min_source_count"):
        config(min_source_count=_DecimalSubclass("3"))
    with pytest.raises(ValueError, match="max_source_age_hours"):
        config(max_source_age_hours=_DecimalSubclass("24"))
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=" strategy-source-coverage-v0")
    with pytest.raises(ValueError, match="source_family"):
        evidence("candidate-alpha", "source-1", " official")
    with pytest.raises(ValueError, match="reason_codes"):
        evidence("candidate-alpha", "source-1", "official", reason_codes=())
    with pytest.raises(ValueError, match="observed_at"):
        evidence(
            "candidate-alpha",
            "source-1",
            "official",
            observed_at=_DatetimeSubclass(2026, 7, 2, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        evidence(
            "candidate-alpha",
            "source-1",
            "official",
            observed_at=datetime(
                2026,
                7,
                2,
                8,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(
            evidence("candidate-alpha", "source-1", "official"),
            generated_at=datetime(2026, 7, 2),
        )
    with pytest.raises(ValueError, match="duplicate"):
        report(
            evidence("candidate-alpha", "source-1", "official"),
            evidence("candidate-alpha", "source-1", "news"),
        )
    with pytest.raises(ValueError, match="observed_at"):
        report(
            evidence(
                "candidate-alpha",
                "source-1",
                "official",
                observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="config"):
        module.build_strategy_recommendation_source_coverage_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    digest = report(*passing_candidate())
    with pytest.raises(ValueError, match="candidate_count"):
        replace(digest, candidate_count=d("2"))


def test_rejects_unsafe_live_surface_text_values() -> None:
    with pytest.raises(ValueError, match="unsafe surface text"):
        evidence("wallet-candidate", "source-1", "official")
    with pytest.raises(ValueError, match="unsafe surface text"):
        evidence("candidate-alpha", "order-source", "official")
    with pytest.raises(ValueError, match="unsafe surface text"):
        evidence("candidate-alpha", "source-1", "auth-source")


def test_rows_sort_deterministically_by_candidate_id_when_risk_keys_match() -> None:
    digest = report(
        evidence("candidate-zeta", "official-1", "official", resolution_source_evidence=True),
        evidence("candidate-zeta", "news-1", "news"),
        evidence("candidate-zeta", "news-2", "news"),
        evidence("candidate-alpha", "official-1", "official", resolution_source_evidence=True),
        evidence("candidate-alpha", "news-1", "news"),
        evidence("candidate-alpha", "news-2", "news"),
    )

    assert tuple(row.candidate_id for row in digest.rows) == (
        "candidate-alpha",
        "candidate-zeta",
    )


def test_datetime_requires_exact_utc_and_dataclasses_are_frozen() -> None:
    module = api()
    row = evidence(
        "candidate-alpha",
        "source-1",
        "official",
        observed_at=GENERATED_AT,
        resolution_source_evidence=True,
    )
    assert row.observed_at == GENERATED_AT
    assert row.observed_at.tzinfo is UTC

    digest = report(*passing_candidate(), generated_at=GENERATED_AT)
    cfg = config()
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True
    for value in (cfg, digest, digest.rows[0]):
        for field in fields(value):
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.startswith(("min_", "max_"))
            ):
                assert field.type == "Decimal"
                assert type(getattr(value, field.name)) is Decimal

    with pytest.raises(FrozenInstanceError):
        digest.rows[0].source_count = d("9")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.source_family = "news"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        cfg.min_source_count = d("4")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(row, paper_only=False)


def test_module_has_no_static_forbidden_surface_terms() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_recommendation_source_coverage_digest.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "broker",
        "advice",
        "network",
        "live trading",
        "order",
        "cancel",
        "replace",
        "signing",
        "api_key",
        "private_key",
        "payload_json",
        "sqlite",
        "psycopg",
        "supabase",
        "requests",
        "httpx",
        "socket",
        "subprocess",
        "open(",
        "read(",
        "write(",
        "float(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in {"__import__", "open", "read", "write", "float"}
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {
                    "connect",
                    "execute",
                    "open",
                    "read",
                    "read_text",
                    "request",
                    "write",
                    "write_text",
                }
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in {
                    "httpx",
                    "os",
                    "pathlib",
                    "psycopg",
                    "requests",
                    "socket",
                    "sqlite3",
                    "subprocess",
                    "supabase",
                }
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in {
                "httpx",
                "os",
                "pathlib",
                "psycopg",
                "requests",
                "socket",
                "sqlite3",
                "subprocess",
                "supabase",
            }
