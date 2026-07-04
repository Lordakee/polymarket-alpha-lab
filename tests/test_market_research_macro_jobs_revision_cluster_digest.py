from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 3, 13, 30, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def digest():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_macro_jobs_revision_cluster_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str = "source-alpha",
    *,
    release_id: str = "nonfarm-payrolls",
    market_slug: str = "us-jobs-report-above-consensus",
    revision_delta_jobs_k: str | Decimal = "42.000000",
    prior_revision_delta_jobs_k: str | Decimal = "18.000000",
    consensus_surprise_jobs_k: str | Decimal = "35.000000",
    revision_window_days: str | Decimal = "28.000000",
    data_timestamp: datetime = datetime(2026, 7, 3, 12, 0, tzinfo=UTC),
    upstream_reason_codes: tuple[str, ...] = ("official_jobs_release",),
):
    module = digest()
    return module.MacroJobsRevisionClusterObservation(
        source_id=source_id,
        release_id=release_id,
        market_slug=market_slug,
        revision_delta_jobs_k=(
            revision_delta_jobs_k
            if isinstance(revision_delta_jobs_k, Decimal)
            else d(revision_delta_jobs_k)
        ),
        prior_revision_delta_jobs_k=(
            prior_revision_delta_jobs_k
            if isinstance(prior_revision_delta_jobs_k, Decimal)
            else d(prior_revision_delta_jobs_k)
        ),
        consensus_surprise_jobs_k=(
            consensus_surprise_jobs_k
            if isinstance(consensus_surprise_jobs_k, Decimal)
            else d(consensus_surprise_jobs_k)
        ),
        revision_window_days=(
            revision_window_days
            if isinstance(revision_window_days, Decimal)
            else d(revision_window_days)
        ),
        data_timestamp=data_timestamp,
        upstream_reason_codes=upstream_reason_codes,
    )


def report(*rows: object, cfg: object | None = None):
    module = digest()
    return module.build_market_research_macro_jobs_revision_cluster_digest(
        rows,
        config=cfg or module.MacroJobsRevisionClusterDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    module = digest()

    digest_report = report()

    assert isinstance(digest_report, module.MacroJobsRevisionClusterDigestReport)
    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-macro-jobs-revision-cluster-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_macro_jobs_revision_cluster_screening"
    )
    assert digest_report.input_count == d("0.000000")
    assert digest_report.row_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.clustered_revision_count == d("0.000000")
    assert digest_report.material_surprise_count == d("0.000000")
    assert digest_report.max_absolute_revision_jobs_k == d("0.000000")
    assert digest_report.average_absolute_revision_jobs_k == d("0.000000")
    assert digest_report.cluster_risk_score == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == ("macro_jobs_revision_cluster_digest_empty",)
    assert digest_report.reason_code_counts == (
        module.MacroJobsRevisionClusterReasonCodeCount(
            reason_code="macro_jobs_revision_cluster_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_high_risk_revision_cluster_blocks_probability_event_screening() -> None:
    module = digest()

    digest_report = report(
        observation(
            "source-payrolls",
            market_slug="headline-payrolls-above-consensus",
            revision_delta_jobs_k="-185.000000",
            prior_revision_delta_jobs_k="96.000000",
            consensus_surprise_jobs_k="-130.000000",
            revision_window_days="21.000000",
        ),
        observation(
            "source-private",
            release_id="adp-employment",
            market_slug="adp-jobs-above-consensus",
            revision_delta_jobs_k="-92.000000",
            prior_revision_delta_jobs_k="-64.000000",
            consensus_surprise_jobs_k="-18.000000",
            revision_window_days="35.000000",
            data_timestamp=datetime(2026, 7, 3, 8, 45, tzinfo=timezone(timedelta(hours=-4))),
        ),
        observation(
            "source-claims",
            release_id="jobless-claims",
            market_slug="initial-claims-below-consensus",
            revision_delta_jobs_k="-12.000000",
            prior_revision_delta_jobs_k="-8.000000",
            consensus_surprise_jobs_k="4.000000",
            revision_window_days="7.000000",
        ),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_macro_jobs_revision_cluster_screening"
    )
    assert digest_report.input_count == d("3.000000")
    assert digest_report.row_count == d("3.000000")
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.clustered_revision_count == d("2.000000")
    assert digest_report.material_surprise_count == d("1.000000")
    assert digest_report.max_absolute_revision_jobs_k == d("185.000000")
    assert digest_report.average_absolute_revision_jobs_k == d("96.333333")
    assert digest_report.cluster_risk_score == d("1.000000")
    assert digest_report.reason_codes == (
        "macro_jobs_revision_cluster_high_abs_revision_present",
        "macro_jobs_revision_clustered_revisions_present",
        "macro_jobs_revision_material_surprise_overlap",
        "macro_jobs_revision_direction_flip_present",
    )
    assert tuple(row.market_slug for row in digest_report.rows) == (
        "headline-payrolls-above-consensus",
        "adp-jobs-above-consensus",
        "initial-claims-below-consensus",
    )

    blocked, watch, passed = digest_report.rows
    assert blocked.revision_status == "blocked"
    assert blocked.absolute_revision_jobs_k == d("185.000000")
    assert blocked.absolute_surprise_jobs_k == d("130.000000")
    assert blocked.data_timestamp == datetime(2026, 7, 3, 12, 0, tzinfo=UTC)
    assert blocked.reason_codes == (
        "macro_jobs_revision_cluster_high_abs_revision",
        "macro_jobs_revision_cluster_window",
        "macro_jobs_revision_direction_flip",
        "macro_jobs_revision_material_surprise",
    )
    assert watch.revision_status == "watch"
    assert watch.reason_codes == (
        "macro_jobs_revision_cluster_watch_abs_revision",
        "macro_jobs_revision_cluster_window",
    )
    assert passed.revision_status == "pass"
    assert passed.reason_codes == ("macro_jobs_revision_cluster_inline",)


def test_rows_and_reason_codes_are_sorted_deterministically() -> None:
    first = observation(
        "source-watch-b",
        market_slug="beta-watch",
        revision_delta_jobs_k="88.000000",
        prior_revision_delta_jobs_k="12.000000",
        consensus_surprise_jobs_k="20.000000",
    )
    second = observation(
        "source-blocked",
        market_slug="alpha-blocked",
        revision_delta_jobs_k="151.000000",
        prior_revision_delta_jobs_k="-10.000000",
        consensus_surprise_jobs_k="105.000000",
    )
    third = observation(
        "source-watch-a",
        market_slug="alpha-watch",
        revision_delta_jobs_k="88.000000",
        prior_revision_delta_jobs_k="10.000000",
        consensus_surprise_jobs_k="10.000000",
    )

    forward = report(first, second, third)
    reverse = report(third, second, first)

    assert forward == reverse
    assert tuple(row.market_slug for row in forward.rows) == (
        "alpha-blocked",
        "alpha-watch",
        "beta-watch",
    )
    for row in forward.rows:
        assert row.reason_codes == tuple(sorted(row.reason_codes))
    assert forward.reason_codes == (
        "macro_jobs_revision_cluster_high_abs_revision_present",
        "macro_jobs_revision_clustered_revisions_present",
        "macro_jobs_revision_material_surprise_overlap",
        "macro_jobs_revision_direction_flip_present",
    )
    assert tuple(item.reason_code for item in forward.reason_code_counts) == (
        "macro_jobs_revision_cluster_high_abs_revision_present",
        "macro_jobs_revision_clustered_revisions_present",
        "macro_jobs_revision_material_surprise_overlap",
        "macro_jobs_revision_direction_flip_present",
    )


def test_non_default_thresholds_can_downgrade_moderate_revision_risk() -> None:
    module = digest()
    cfg = module.MacroJobsRevisionClusterDigestConfig(
        watch_abs_revision_jobs_k=d("120.000000"),
        blocked_abs_revision_jobs_k=d("220.000000"),
        material_surprise_jobs_k=d("160.000000"),
    )

    digest_report = report(
        observation(
            "source-moderate",
            revision_delta_jobs_k="92.000000",
            prior_revision_delta_jobs_k="14.000000",
            consensus_surprise_jobs_k="115.000000",
        ),
        cfg=cfg,
    )

    assert digest_report.digest_status == "pass"
    assert digest_report.recommended_next_step == (
        "allow_report_only_macro_jobs_revision_cluster_screening"
    )
    assert digest_report.rows[0].revision_status == "pass"
    assert digest_report.rows[0].reason_codes == (
        "macro_jobs_revision_cluster_inline",
    )
    assert digest_report.cluster_risk_score == d("0.000000")
    assert digest_report.reason_codes == ("macro_jobs_revision_cluster_digest_clear",)


def test_validation_rejects_bad_inputs_and_inconsistent_public_records() -> None:
    module = digest()

    with pytest.raises(ValueError, match="revision_delta_jobs_k must be a Decimal"):
        observation(revision_delta_jobs_k=_DecimalSubclass("42.000000"))
    with pytest.raises(ValueError, match="revision_window_days must be nonnegative"):
        observation(revision_window_days="-1.000000")
    with pytest.raises(ValueError, match="data_timestamp must be timezone-aware"):
        observation(data_timestamp=datetime(2026, 7, 3, 12, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_macro_jobs_revision_cluster_digest(
            (),
            config=module.MacroJobsRevisionClusterDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 3, 13, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        report("not-an-observation")
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(observation("source-dupe"), observation("source-dupe"))
    with pytest.raises(ValueError, match="watch_abs_revision_jobs_k"):
        module.MacroJobsRevisionClusterDigestConfig(
            watch_abs_revision_jobs_k=d("300.000000"),
            blocked_abs_revision_jobs_k=d("200.000000"),
        )

    valid_row = report(observation("source-valid")).rows[0]
    with pytest.raises(ValueError, match="absolute_revision_jobs_k must match"):
        replace(valid_row, absolute_revision_jobs_k=d("999.000000"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(
            valid_row,
            reason_codes=(
                "macro_jobs_revision_cluster_inline",
                "macro_jobs_revision_cluster_watch_abs_revision",
            ),
        )

    frozen_observation = observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]


def test_hard_flags_are_enforced_on_config_rows_and_report() -> None:
    module = digest()

    digest_report = report(observation("source-hard-flags"))
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in digest_report.rows)

    with pytest.raises(ValueError, match="config paper_only must be True"):
        module.MacroJobsRevisionClusterDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(observation("source-report-only"), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(digest_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(digest_report, paper_only=False)


def test_payload_uses_string_numerics_and_module_has_no_durable_or_live_surfaces() -> None:
    module = digest()
    digest_report = report(observation("source-payload"))

    payload = module.market_research_macro_jobs_revision_cluster_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["revision_delta_jobs_k"] == "42.000000"
    assert payload["rows"][0]["data_timestamp"] == "2026-07-03T12:00:00+00:00"

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                assert "private_key" not in lowered
                assert "wallet" not in lowered
                assert "order" not in lowered
                assert "auth" not in lowered
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))

    walk_payload(payload)

    for public_record in (
        module.MacroJobsRevisionClusterDigestConfig(),
        observation("source-dataclass"),
        digest_report.rows[0],
        digest_report.reason_code_counts[0],
        digest_report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if _is_public_numeric(field_value):
                assert type(field_value) is Decimal, field.name

    source = Path(
        "src/polymarket_alpha_lab/market_research_macro_jobs_revision_cluster_digest.py",
    ).read_text()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "private_key",
        "wallet",
        "urlopen",
        "connect(",
        "execute(",
        "live trading",
        "submit_order",
        "cancel_order",
        "replace_order",
    ):
        assert forbidden not in source.lower()


def _is_public_numeric(value: object) -> bool:
    return isinstance(value, Decimal)
