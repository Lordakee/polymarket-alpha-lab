from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timezone, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 2, 14, 30, tzinfo=timezone(timedelta(hours=-4)))


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_event_dependency_cluster_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def market(
    market_id: str,
    *,
    event_key: str,
    category_id: str,
    source_families: tuple[str, ...],
    resolution_dependencies: tuple[str, ...] = (),
    paper_exposure: str = "0",
    reference: str = "https://polymarket.example/redacted",
    reason_codes: tuple[str, ...] = ("market_dependency_candidate",),
):
    digest = api()
    return digest.MarketEventDependencyInput(
        market_id=market_id,
        event_key=event_key,
        category_id=category_id,
        source_families=source_families,
        resolution_dependencies=resolution_dependencies,
        paper_exposure=d(paper_exposure),
        sensitive_reference=reference,
        reason_codes=reason_codes,
    )


def report(*rows):
    digest = api()
    return digest.build_market_event_dependency_cluster_digest(
        rows,
        config=digest.MarketEventDependencyClusterDigestConfig(
            max_cluster_exposure_share=d("0.500000"),
        ),
        generated_at=GENERATED_AT,
    )


def test_digest_clusters_shared_event_category_source_dependency_and_exposure() -> None:
    digest_report = report(
        market(
            "alpha",
            event_key="fed-cut-2026",
            category_id="macro",
            source_families=("official", "newswire"),
            resolution_dependencies=("fed-resolution",),
            paper_exposure="75",
        ),
        market(
            "beta",
            event_key="fed-cut-2026",
            category_id="macro",
            source_families=("official", "macro-data"),
            resolution_dependencies=("fed-resolution",),
            paper_exposure="25",
        ),
        market(
            "gamma",
            event_key="btc-etf-2026",
            category_id="crypto",
            source_families=("official", "newswire"),
            paper_exposure="10",
        ),
    )

    assert is_dataclass(digest_report)
    assert digest_report.generated_at == datetime(2026, 7, 2, 18, 30, tzinfo=UTC)
    assert digest_report.market_count == d("3")
    assert digest_report.cluster_count == d("2")
    assert digest_report.dependency_cluster_count == d("1")
    assert digest_report.total_paper_exposure == d("110")
    assert digest_report.max_cluster_exposure_share == d("0.909091")
    assert digest_report.status == "blocked"
    assert digest_report.reason_codes == (
        "dependency_clusters_blocked",
        "exposure_concentration_high",
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True

    assert tuple(row.cluster_key for row in digest_report.cluster_rows) == (
        "event:fed-cut-2026",
        "event:btc-etf-2026",
    )
    primary = digest_report.cluster_rows[0]
    assert primary.market_count == d("2")
    assert primary.category_overlap_count == d("1")
    assert primary.source_family_overlap_count == d("1")
    assert primary.resolution_dependency_count == d("1")
    assert primary.paper_exposure == d("100")
    assert primary.exposure_share == d("0.909091")
    assert primary.status == "blocked"
    assert primary.reason_codes == (
        "category_overlap",
        "exposure_concentration_high",
        "resolution_dependency_overlap",
        "shared_event_key",
        "source_family_overlap",
    )
    assert primary.redacted_market_ids == (
        "redacted:market:000001",
        "redacted:market:000002",
    )
    assert primary.redacted_references == (
        "redacted:reference",
        "redacted:reference",
    )


def test_empty_digest_is_readonly_pass_with_decimal_zeroes() -> None:
    digest_report = report()

    assert digest_report.market_count == d("0")
    assert digest_report.cluster_count == d("0")
    assert digest_report.dependency_cluster_count == d("0")
    assert digest_report.total_paper_exposure == d("0")
    assert digest_report.max_cluster_exposure_share == d("0.000000")
    assert digest_report.status == "pass"
    assert digest_report.reason_codes == ("dependency_clusters_clear",)
    assert digest_report.cluster_rows == ()


def test_digest_rejects_floats_nonfinite_values_flags_and_mutation() -> None:
    digest = api()

    with pytest.raises(ValueError, match="paper_exposure must be a Decimal"):
        digest.MarketEventDependencyInput(
            market_id="alpha",
            event_key="fed-cut-2026",
            category_id="macro",
            source_families=("official",),
            resolution_dependencies=(),
            paper_exposure=1.0,
            reason_codes=("market_dependency_candidate",),
        )

    with pytest.raises(ValueError, match="paper_exposure must be finite"):
        market(
            "alpha",
            event_key="fed-cut-2026",
            category_id="macro",
            source_families=("official",),
            paper_exposure="Infinity",
        )

    row = market(
        "alpha",
        event_key="fed-cut-2026",
        category_id="macro",
        source_families=("official",),
    )
    with pytest.raises(FrozenInstanceError):
        row.paper_exposure = d("9")  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        digest.MarketEventDependencyClusterDigestConfig(readonly=False)


def test_digest_rejects_invalid_generated_at_datetimes() -> None:
    digest = api()

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        digest.build_market_event_dependency_cluster_digest(
            (),
            config=digest.MarketEventDependencyClusterDigestConfig(),
            generated_at=datetime(2026, 7, 2, 14, 30),
        )

    class NoneOffsetTimezone(tzinfo):
        def utcoffset(self, dt: datetime | None) -> None:
            return None

        def dst(self, dt: datetime | None) -> None:
            return None

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        digest.build_market_event_dependency_cluster_digest(
            (),
            config=digest.MarketEventDependencyClusterDigestConfig(),
            generated_at=datetime(2026, 7, 2, 14, 30, tzinfo=NoneOffsetTimezone()),
        )

    class DatetimeSubclass(datetime):
        pass

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        digest.build_market_event_dependency_cluster_digest(
            (),
            config=digest.MarketEventDependencyClusterDigestConfig(),
            generated_at=DatetimeSubclass(2026, 7, 2, 14, 30, tzinfo=UTC),
        )


def test_digest_validates_determinism_duplicates_and_report_consistency() -> None:
    digest = api()
    row = market(
        "alpha",
        event_key="fed-cut-2026",
        category_id="macro",
        source_families=("newswire", "official"),
    )

    assert row.source_families == ("newswire", "official")

    with pytest.raises(ValueError, match="source_families must be unique"):
        market(
            "alpha",
            event_key="fed-cut-2026",
            category_id="macro",
            source_families=("official", "official"),
        )

    with pytest.raises(ValueError, match="inputs must not contain duplicate market_id"):
        report(row, row)

    valid_report = report(
        market(
            "beta",
            event_key="btc-etf-2026",
            category_id="crypto",
            source_families=("official",),
            paper_exposure="1",
        ),
        market(
            "gamma",
            event_key="fed-cut-2026",
            category_id="macro",
            source_families=("official",),
            paper_exposure="2",
        ),
    )
    with pytest.raises(ValueError, match="cluster_count must match cluster_rows"):
        replace(valid_report, cluster_count=d("3"))

    with pytest.raises(ValueError, match="cluster_rows must use deterministic sequence"):
        digest.MarketEventDependencyClusterDigestReport(
            generated_at=valid_report.generated_at,
            config_version=valid_report.config_version,
            market_count=valid_report.market_count,
            cluster_count=valid_report.cluster_count,
            dependency_cluster_count=valid_report.dependency_cluster_count,
            total_paper_exposure=valid_report.total_paper_exposure,
            max_cluster_exposure_share=valid_report.max_cluster_exposure_share,
            status=valid_report.status,
            reason_codes=valid_report.reason_codes,
            cluster_rows=tuple(reversed(valid_report.cluster_rows)),
        )


def test_digest_payload_is_json_ready_and_redacts_sensitive_references() -> None:
    payload = api().market_event_dependency_cluster_digest_payload(
        report(
            market(
                "secret-market-123",
                event_key="fed-cut-2026",
                category_id="macro",
                source_families=("official", "newswire"),
                resolution_dependencies=("fed-resolution",),
                paper_exposure="20",
                reference="https://internal.example/token=secret",
            ),
            market(
                "secret-market-456",
                event_key="fed-cut-2026",
                category_id="macro",
                source_families=("official",),
                paper_exposure="5",
                reference="private://wallet/reference",
            ),
        ),
    )

    payload_text = repr(payload).lower()
    assert "secret-market" not in payload_text
    assert "internal.example" not in payload_text
    assert "token=secret" not in payload_text
    assert "private://" not in payload_text
    assert "recommend" not in payload_text
    assert "wallet" not in payload_text
    assert "auth" not in payload_text
    assert payload["total_paper_exposure"] == "25"
    assert payload["cluster_rows"][0]["redacted_market_ids"] == [
        "redacted:market:000001",
        "redacted:market:000002",
    ]
    assert payload["cluster_rows"][0]["redacted_references"] == [
        "redacted:reference",
        "redacted:reference",
    ]


def test_module_scope_has_no_live_network_storage_or_sensitive_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/market_event_dependency_cluster_digest.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "httpx",
        "requests",
        "socket",
        "psycopg",
        "supabase",
        "sqlite",
        "sqlalchemy",
        "open(",
        "auth",
        "wallet",
        "account",
        "private_key",
        "secret",
        "advice",
        "trade",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
