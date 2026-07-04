from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_adp_employment_surprise_digest import (
    DEFAULT_MARKET_RESEARCH_ADP_EMPLOYMENT_SURPRISE_DIGEST_CONFIG_VERSION,
    MarketResearchAdpEmploymentSurpriseDigestConfig,
    MarketResearchAdpEmploymentSurpriseDigestObservation,
    MarketResearchAdpEmploymentSurpriseDigestReasonCodeCount,
    MarketResearchAdpEmploymentSurpriseDigestReport,
    build_market_research_adp_employment_surprise_digest,
    market_research_adp_employment_surprise_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 13, 0, tzinfo=UTC)
SOURCE_TZ = timezone(timedelta(hours=-4))
SOURCE_OBSERVED_AT = datetime(2026, 7, 3, 8, 30, tzinfo=SOURCE_TZ)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchAdpEmploymentSurpriseDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_ADP_EMPLOYMENT_SURPRISE_DIGEST_CONFIG_VERSION
        ),
        "material_surprise_threshold": d("0.150000"),
        "max_observation_age_seconds": d("7200.000000"),
    }
    values.update(overrides)
    return MarketResearchAdpEmploymentSurpriseDigestConfig(**values)


def observation(
    release_id: str,
    *,
    actual: str,
    consensus: str,
    previous: str,
    market_slug: str | None = None,
    observed_at: datetime = SOURCE_OBSERVED_AT,
    source_name: str = "adp_release",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchAdpEmploymentSurpriseDigestObservation:
    return MarketResearchAdpEmploymentSurpriseDigestObservation(
        release_id=release_id,
        market_slug=market_slug or f"us-adp-employment-{release_id}",
        observed_at=observed_at,
        actual_jobs_change=d(actual),
        consensus_jobs_change=d(consensus),
        previous_jobs_change=d(previous),
        source_name=source_name,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketResearchAdpEmploymentSurpriseDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchAdpEmploymentSurpriseDigestReport:
    return build_market_research_adp_employment_surprise_digest(
        rows,
        generated_at=generated_at,
        config=cfg or config(),
    )


def test_adp_employment_surprise_digest_reduces_inputs_deterministically() -> None:
    summary = report(
        (
            observation(
                "2026-06",
                actual="150.000000",
                consensus="100.000000",
                previous="120.000000",
                observed_at=GENERATED_AT - timedelta(hours=3),
            ),
            observation(
                "2026-05",
                actual="80.000000",
                consensus="100.000000",
                previous="95.000000",
                observed_at=GENERATED_AT - timedelta(hours=3),
            ),
            observation(
                "2026-04",
                actual="101.000000",
                consensus="100.000000",
                previous="98.000000",
                observed_at=GENERATED_AT.astimezone(SOURCE_TZ),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(SOURCE_TZ),
    )

    assert isinstance(summary, MarketResearchAdpEmploymentSurpriseDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_ADP_EMPLOYMENT_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "watch"
    assert summary.recommended_next_step == "review_adp_employment_surprise"
    assert tuple(row.release_id for row in summary.observations) == (
        "2026-04",
        "2026-05",
        "2026-06",
    )
    assert all(row.observed_at.tzinfo is UTC for row in summary.observations)
    assert summary.observation_count == d("3.000000")
    assert summary.material_surprise_count == d("2.000000")
    assert summary.positive_surprise_count == d("1.000000")
    assert summary.negative_surprise_count == d("1.000000")
    assert summary.stale_observation_count == d("2.000000")
    assert summary.missing_consensus_count == ZERO
    assert summary.largest_abs_surprise_ratio == d("0.500000")
    assert summary.average_surprise_ratio == d("0.103333")
    assert summary.reason_codes == (
        "market_research_adp_employment_surprise_digest_material_positive_surprise",
        "market_research_adp_employment_surprise_digest_material_negative_surprise",
        "market_research_adp_employment_surprise_digest_stale_observation",
        "market_research_adp_employment_surprise_digest_watch",
    )
    assert summary.reason_code_counts == (
        MarketResearchAdpEmploymentSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_adp_employment_surprise_digest_"
                "material_positive_surprise"
            ),
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        MarketResearchAdpEmploymentSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_adp_employment_surprise_digest_"
                "material_negative_surprise"
            ),
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        MarketResearchAdpEmploymentSurpriseDigestReasonCodeCount(
            reason_code="market_research_adp_employment_surprise_digest_stale_observation",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        MarketResearchAdpEmploymentSurpriseDigestReasonCodeCount(
            reason_code="market_research_adp_employment_surprise_digest_watch",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_adp_employment_surprise_digest_passes_when_surprises_are_immaterial() -> None:
    summary = report(
        (
            observation(
                "2026-06",
                actual="103.000000",
                consensus="100.000000",
                previous="99.000000",
                observed_at=GENERATED_AT,
            ),
        ),
    )

    assert summary.digest_status == "pass"
    assert summary.recommended_next_step == "continue_monitoring_adp_employment_surprise"
    assert summary.reason_codes == (
        "market_research_adp_employment_surprise_digest_no_material_surprise",
    )
    assert summary.reason_code_counts == (
        MarketResearchAdpEmploymentSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_adp_employment_surprise_digest_"
                "no_material_surprise"
            ),
            count=d("1.000000"),
            observation_ratio=d("1.000000"),
        ),
    )


def test_adp_employment_surprise_digest_blocks_on_missing_consensus() -> None:
    summary = report(
        (
            observation(
                "2026-06",
                actual="95.000000",
                consensus="0.000000",
                previous="110.000000",
            ),
        ),
    )

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == "repair_adp_employment_consensus_inputs"
    assert summary.observation_count == d("1.000000")
    assert summary.material_surprise_count == ZERO
    assert summary.missing_consensus_count == d("1.000000")
    assert summary.largest_abs_surprise_ratio == ZERO
    assert summary.average_surprise_ratio == ZERO
    assert summary.reason_codes == (
        "market_research_adp_employment_surprise_digest_missing_consensus",
        "market_research_adp_employment_surprise_digest_no_material_surprise",
    )


def test_empty_adp_employment_surprise_digest_is_watch_and_decimal_only() -> None:
    summary = report(())

    assert summary.digest_status == "watch"
    assert summary.recommended_next_step == "review_adp_employment_surprise"
    assert summary.observation_count == ZERO
    assert summary.material_surprise_count == ZERO
    assert summary.positive_surprise_count == ZERO
    assert summary.negative_surprise_count == ZERO
    assert summary.stale_observation_count == ZERO
    assert summary.missing_consensus_count == ZERO
    assert summary.largest_abs_surprise_ratio == ZERO
    assert summary.average_surprise_ratio == ZERO
    assert summary.observations == ()
    assert summary.reason_codes == (
        "market_research_adp_employment_surprise_digest_no_inputs",
    )
    assert summary.reason_code_counts == (
        MarketResearchAdpEmploymentSurpriseDigestReasonCodeCount(
            reason_code="market_research_adp_employment_surprise_digest_no_inputs",
            count=ZERO,
            observation_ratio=ZERO,
        ),
    )

    public_values = asdict(summary)
    numeric_or_countish = (
        "count",
        "ratio",
        "change",
        "threshold",
        "seconds",
    )
    for name, value in public_values.items():
        if any(fragment in name for fragment in numeric_or_countish):
            if isinstance(value, (dict, list, tuple)):
                continue
            assert isinstance(value, Decimal), (name, value)


def test_adp_employment_surprise_dataclasses_are_frozen_and_validate_surface() -> None:
    obs = observation("2026-06", actual="150.000000", consensus="100.000000", previous="120.000000")
    summary = report((obs,))

    assert obs.observed_at == datetime(2026, 7, 3, 12, 30, tzinfo=UTC)
    with pytest.raises(FrozenInstanceError):
        obs.release_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.digest_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].count = d("2.000000")  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclassing"):
        type(
            "BadObservation",
            (MarketResearchAdpEmploymentSurpriseDigestObservation,),
            {},
        )
    with pytest.raises(ValueError, match="Decimal"):
        MarketResearchAdpEmploymentSurpriseDigestObservation(
            release_id="2026-06",
            market_slug="us-adp-employment-2026-06",
            observed_at=SOURCE_OBSERVED_AT,
            actual_jobs_change=_DecimalSubclass("150.000000"),
            consensus_jobs_change=d("100.000000"),
            previous_jobs_change=d("120.000000"),
            source_name="adp_release",
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("actual_jobs_change", 150),
        ("actual_jobs_change", "150.000000"),
        ("consensus_jobs_change", 100.0),
        ("previous_jobs_change", _DecimalSubclass("120.000000")),
    ),
)
def test_adp_employment_surprise_observation_requires_exact_decimal_numbers(
    field_name: str,
    value: object,
) -> None:
    values = {
        "release_id": "2026-06",
        "market_slug": "us-adp-employment-2026-06",
        "observed_at": SOURCE_OBSERVED_AT,
        "actual_jobs_change": d("150.000000"),
        "consensus_jobs_change": d("100.000000"),
        "previous_jobs_change": d("120.000000"),
        "source_name": "adp_release",
    }
    values[field_name] = value

    with pytest.raises(ValueError, match=field_name):
        MarketResearchAdpEmploymentSurpriseDigestObservation(**values)


def test_adp_employment_surprise_rejects_unsafe_inputs_and_false_flags() -> None:
    with pytest.raises(ValueError, match="observed_at"):
        observation(
            "2026-06",
            actual="150.000000",
            consensus="100.000000",
            previous="120.000000",
            observed_at=datetime(2026, 7, 3, 12, 30),
        )
    with pytest.raises(ValueError, match="observed_at"):
        observation(
            "2026-06",
            actual="150.000000",
            consensus="100.000000",
            previous="120.000000",
            observed_at=_DatetimeSubclass(2026, 7, 3, 12, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        observation(
            "2026-06",
            actual="150.000000",
            consensus="100.000000",
            previous="120.000000",
            observed_at=datetime(2026, 7, 3, 12, 30, tzinfo=_NoneOffsetTz()),
        )
    with pytest.raises(ValueError, match="public string"):
        observation(
            _StringSubclass("2026-06"),  # type: ignore[arg-type]
            actual="150.000000",
            consensus="100.000000",
            previous="120.000000",
        )
    with pytest.raises(ValueError, match="source_name"):
        observation(
            "2026-06",
            actual="150.000000",
            consensus="100.000000",
            previous="120.000000",
            source_name="vendor_token_secret",
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(config(), readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(
            observation(
                "2026-06",
                actual="150.000000",
                consensus="100.000000",
                previous="120.000000",
            ),
            paper_only=False,
        )


def test_adp_employment_surprise_payload_is_report_only_and_literal_safe() -> None:
    summary = report(
        (
            observation(
                "2026-06",
                actual="150.000000",
                consensus="100.000000",
                previous="120.000000",
            ),
        ),
    )
    payload = market_research_adp_employment_surprise_digest_payload(summary)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["observation_count"] == "1.000000"
    assert payload["largest_abs_surprise_ratio"] == "0.500000"
    assert payload["observations"][0]["actual_jobs_change"] == "150.000000"
    assert payload["reason_code_counts"][0]["paper_only"] is True

    src = Path(
        "src/polymarket_alpha_lab/"
        "market_research_adp_employment_surprise_digest.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(src)
    banned = (
        "requests",
        "urllib",
        "httpx",
        "socket",
        "sqlite3",
        "psycopg",
        "supabase",
        "web3",
        "wallet",
        "order",
        "trade",
        "auth",
    )
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imported = tuple(alias.name for alias in node.names)
            module = getattr(node, "module", "") or ""
            assert not any(name.startswith(banned) for name in imported)
            assert not any(module.startswith(name) for name in banned)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in {"open", "exec", "eval", "compile"}
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {
                    "connect",
                    "request",
                    "post",
                    "put",
                    "delete",
                    "send",
                    "cancel",
                    "replace",
                }

    public_numeric_names = {
        field.name
        for cls in (
            MarketResearchAdpEmploymentSurpriseDigestConfig,
            MarketResearchAdpEmploymentSurpriseDigestObservation,
            MarketResearchAdpEmploymentSurpriseDigestReport,
            MarketResearchAdpEmploymentSurpriseDigestReasonCodeCount,
        )
        for field in fields(cls)
        if any(
            fragment in field.name
            for fragment in ("count", "ratio", "change", "threshold", "seconds")
        )
        and field.name not in {"observations", "reason_code_counts"}
    }
    assert public_numeric_names
    for name in public_numeric_names:
        value = getattr(
            summary,
            name,
            getattr(summary.observations[0], name, getattr(config(), name, None)),
        )
        if value is not None:
            assert type(value) is Decimal
