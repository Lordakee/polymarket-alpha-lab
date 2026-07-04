from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _MissingOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_recommendation_conflict_resolution_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            "strategy-recommendation-conflict-resolution-digest-v0"
        ),
        "stale_acknowledgement_age_seconds": d("7200.000000"),
    }
    values.update(overrides)
    return module.StrategyRecommendationConflictResolutionDigestConfig(**values)


def conflict(
    recommendation_id: str,
    *,
    candidate_id: str = "candidate-alpha",
    forecast_recommendation: str = "recommend",
    market_context_recommendation: str = "recommend",
    forecast_reason_codes: tuple[str, ...] = ("positive_edge",),
    market_reason_codes: tuple[str, ...] = ("market_context_supportive",),
    source_conflict_status: str = "resolved",
    conflict_acknowledged_at: datetime | None = GENERATED_AT - timedelta(minutes=30),
    reviewer_resolution: str | None = "approve",
    reviewer_id: str | None = "reviewer-alpha",
    observed_at: datetime = GENERATED_AT - timedelta(hours=1),
    source_config_version: str = "recommendation-conflict-feed-v0",
):
    module = api()
    return module.StrategyRecommendationConflictResolutionInput(
        recommendation_id=recommendation_id,
        candidate_id=candidate_id,
        forecast_recommendation=forecast_recommendation,
        market_context_recommendation=market_context_recommendation,
        forecast_reason_codes=forecast_reason_codes,
        market_reason_codes=market_reason_codes,
        source_conflict_status=source_conflict_status,
        conflict_acknowledged_at=conflict_acknowledged_at,
        reviewer_resolution=reviewer_resolution,
        reviewer_id=reviewer_id,
        observed_at=observed_at,
        source_config_version=source_config_version,
    )


def report(*rows: object, generated_at: datetime = GENERATED_AT, cfg: object | None = None):
    module = api()
    return module.build_strategy_recommendation_conflict_resolution_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_clear_readonly_decimal_report() -> None:
    digest = report()

    assert is_dataclass(digest)
    assert digest.generated_at == GENERATED_AT
    assert (
        digest.config_version
        == "strategy-recommendation-conflict-resolution-digest-v0"
    )
    assert digest.status == "clear"
    assert digest.reason_codes == ("conflict_resolution_digest_clear",)
    assert digest.input_count == d("0")
    assert digest.row_count == d("0")
    assert digest.clear_count == d("0")
    assert digest.watch_count == d("0")
    assert digest.blocked_count == d("0")
    assert digest.contradictory_reason_code_count == d("0")
    assert digest.forecast_market_disagreement_count == d("0")
    assert digest.unresolved_source_conflict_count == d("0")
    assert digest.stale_acknowledgement_count == d("0")
    assert digest.missing_reviewer_resolution_count == d("0")
    assert digest.blocked_ratio == d("0.000000")
    assert digest.rows == ()
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True


def test_clear_watch_and_blocked_rows_are_reduced_with_counts() -> None:
    digest = report(
        conflict("rec-clear", candidate_id="candidate-clear"),
        conflict(
            "rec-watch",
            candidate_id="candidate-watch",
            conflict_acknowledged_at=GENERATED_AT - timedelta(hours=3),
        ),
        conflict(
            "rec-blocked",
            candidate_id="candidate-blocked",
            forecast_recommendation="recommend",
            market_context_recommendation="avoid",
            source_conflict_status="unresolved",
            reviewer_resolution=None,
            reviewer_id=None,
        ),
    )

    assert digest.status == "blocked"
    assert digest.input_count == d("3")
    assert digest.row_count == d("3")
    assert digest.clear_count == d("1")
    assert digest.watch_count == d("1")
    assert digest.blocked_count == d("1")
    assert digest.forecast_market_disagreement_count == d("1")
    assert digest.unresolved_source_conflict_count == d("1")
    assert digest.stale_acknowledgement_count == d("1")
    assert digest.missing_reviewer_resolution_count == d("1")
    assert digest.blocked_ratio == d("0.333333")
    assert digest.reason_codes == (
        "forecast_market_context_disagreement",
        "unresolved_source_conflict",
        "stale_conflict_acknowledgement",
        "missing_reviewer_resolution",
    )

    assert tuple(row.recommendation_id for row in digest.rows) == (
        "rec-blocked",
        "rec-watch",
        "rec-clear",
    )
    assert tuple(row.status for row in digest.rows) == ("blocked", "watch", "clear")
    assert digest.rows[0].reason_codes == (
        "forecast_market_context_disagreement",
        "unresolved_source_conflict",
        "missing_reviewer_resolution",
    )
    assert digest.rows[1].reason_codes == ("stale_conflict_acknowledgement",)
    assert digest.rows[2].reason_codes == ("conflict_resolution_clear",)


def test_contradictory_reason_codes_block_and_aggregate_stably() -> None:
    digest = report(
        conflict(
            "rec-contradictory",
            forecast_reason_codes=("negative_edge", "positive_edge"),
            market_reason_codes=(
                "market_context_supportive",
                "market_context_adverse",
            ),
        ),
    )

    assert digest.status == "blocked"
    assert digest.contradictory_reason_code_count == d("1")
    assert digest.reason_code_counts == (
        ("contradictory_reason_codes", d("1")),
    )
    row = digest.rows[0]
    assert row.status == "blocked"
    assert row.contradictory_reason_code_count == d("2")
    assert row.reason_codes == ("contradictory_reason_codes",)


def test_stale_acknowledgement_and_missing_reviewer_resolution_are_separate() -> None:
    digest = report(
        conflict(
            "rec-stale",
            conflict_acknowledged_at=GENERATED_AT - timedelta(hours=3),
        ),
        conflict(
            "rec-missing-review",
            conflict_acknowledged_at=None,
            reviewer_resolution=None,
        ),
    )

    assert digest.status == "blocked"
    assert digest.watch_count == d("1")
    assert digest.blocked_count == d("1")
    assert digest.stale_acknowledgement_count == d("1")
    assert digest.missing_reviewer_resolution_count == d("1")
    assert digest.rows[0].reason_codes == ("missing_reviewer_resolution",)
    assert digest.rows[1].reason_codes == ("stale_conflict_acknowledgement",)


def test_rows_sort_by_severity_reason_count_age_and_identifiers() -> None:
    digest = report(
        conflict("rec-clear-z", candidate_id="candidate-z"),
        conflict(
            "rec-watch-a",
            candidate_id="candidate-a",
            conflict_acknowledged_at=GENERATED_AT - timedelta(hours=3),
        ),
        conflict(
            "rec-blocked-b",
            candidate_id="candidate-b",
            forecast_recommendation="recommend",
            market_context_recommendation="avoid",
            observed_at=GENERATED_AT - timedelta(hours=1),
        ),
        conflict(
            "rec-blocked-a",
            candidate_id="candidate-a",
            forecast_recommendation="avoid",
            market_context_recommendation="recommend",
            source_conflict_status="unresolved",
            reviewer_resolution=None,
            observed_at=GENERATED_AT - timedelta(hours=2),
        ),
    )

    assert tuple(row.recommendation_id for row in digest.rows) == (
        "rec-blocked-a",
        "rec-blocked-b",
        "rec-watch-a",
        "rec-clear-z",
    )
    assert digest.reason_codes == (
        "forecast_market_context_disagreement",
        "unresolved_source_conflict",
        "stale_conflict_acknowledgement",
        "missing_reviewer_resolution",
    )
    assert digest.reason_code_counts == (
        ("forecast_market_context_disagreement", d("2")),
        ("unresolved_source_conflict", d("1")),
        ("stale_conflict_acknowledgement", d("1")),
        ("missing_reviewer_resolution", d("1")),
    )


def test_input_reason_codes_are_canonicalized_for_deterministic_rows() -> None:
    row = conflict(
        "rec-reason-seq",
        forecast_reason_codes=("positive_edge", "negative_edge"),
        market_reason_codes=("market_context_supportive", "market_context_adverse"),
    )

    assert row.forecast_reason_codes == ("negative_edge", "positive_edge")
    assert row.market_reason_codes == (
        "market_context_adverse",
        "market_context_supportive",
    )


def test_payload_helper_uses_decimal_strings_no_floats_and_no_unsafe_keys() -> None:
    module = api()
    payload = module.strategy_recommendation_conflict_resolution_digest_payload(
        report(
            conflict(
                "rec-payload",
                forecast_recommendation="recommend",
                market_context_recommendation="avoid",
                observed_at=GENERATED_AT - timedelta(minutes=15),
            ),
        ),
    )

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["input_count"] == "1"
    assert payload["blocked_ratio"] == "1.000000"
    assert payload["reason_code_counts"] == [
        ["forecast_market_context_disagreement", "1"],
    ]
    assert payload["rows"][0]["observed_age_seconds"] == "900.000000"
    assert payload["rows"][0]["paper_only"] is True

    def walk(value: object) -> tuple[object, ...]:
        if isinstance(value, dict):
            items: list[object] = []
            for child in value.values():
                items.extend(walk(child))
            return tuple(items)
        if isinstance(value, list):
            items = []
            for child in value:
                items.extend(walk(child))
            return tuple(items)
        return (value,)

    assert not any(isinstance(value, float) for value in walk(payload))
    with pytest.raises(ValueError, match="report must be"):
        module.strategy_recommendation_conflict_resolution_digest_payload(object())


def test_rejects_sensitive_public_text_values_without_leaking_them() -> None:
    sensitive_candidate_id = "candidate-" + "sec" + "ret" + "-tok" + "en"

    with pytest.raises(ValueError, match="candidate_id") as exc_info:
        conflict("rec-sensitive", candidate_id=sensitive_candidate_id)

    assert sensitive_candidate_id not in str(exc_info.value)


def test_validation_errors_for_inputs_config_and_report_consistency() -> None:
    module = api()

    with pytest.raises(ValueError, match="stale_acknowledgement_age_seconds"):
        config(stale_acknowledgement_age_seconds=d("0.000000"))
    with pytest.raises(ValueError, match="stale_acknowledgement_age_seconds"):
        config(stale_acknowledgement_age_seconds=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=" strategy-recommendation-conflict-resolution-digest-v0")
    with pytest.raises(ValueError, match="recommendation_id"):
        conflict(" rec-bad")
    with pytest.raises(ValueError, match="forecast_recommendation"):
        conflict("rec-bad-forecast", forecast_recommendation="buy")
    with pytest.raises(ValueError, match="forecast_reason_codes"):
        conflict("rec-empty-reasons", forecast_reason_codes=())
    with pytest.raises(ValueError, match="observed_at"):
        conflict(
            "rec-subclass-datetime",
            observed_at=_DatetimeSubclass(2026, 7, 2, 11, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        conflict(
            "rec-missing-offset",
            observed_at=datetime(2026, 7, 2, 11, 0, tzinfo=_MissingOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(conflict("rec-naive-generated"), generated_at=datetime(2026, 7, 2, 12, 0))
    with pytest.raises(ValueError, match="future"):
        report(
            conflict(
                "rec-future",
                observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="duplicate"):
        report(conflict("rec-duplicate"), conflict("rec-duplicate"))
    with pytest.raises(ValueError, match="config"):
        module.build_strategy_recommendation_conflict_resolution_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    digest = report(conflict("rec-consistency"))
    with pytest.raises(ValueError, match="row_count"):
        replace(digest, row_count=d("2"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(digest, reason_codes=("missing_reviewer_resolution",))


def test_datetime_normalization_flags_and_frozen_dataclasses() -> None:
    row = conflict(
        "rec-timezone",
        observed_at=datetime(2026, 7, 2, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
        conflict_acknowledged_at=datetime(
            2026,
            7,
            2,
            4,
            30,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )
    assert row.observed_at == GENERATED_AT
    assert row.observed_at.tzinfo is UTC
    assert row.conflict_acknowledged_at == GENERATED_AT - timedelta(minutes=30)
    assert row.conflict_acknowledged_at.tzinfo is UTC

    digest = report(conflict("rec-frozen"))
    with pytest.raises(FrozenInstanceError):
        digest.rows[0].status = "clear"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.candidate_id = "candidate-beta"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(row, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(digest, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(digest.rows[0], readonly=False)


def test_static_forbidden_surface_terms_are_absent_from_owned_module() -> None:
    module = api()
    source_path = Path(module.__file__)
    source = source_path.read_text(encoding="utf-8").lower()
    public_names = tuple(module.__all__)

    for name in public_names:
        assert hasattr(module, name), name

    assert ".total_seconds(" not in source
    assert "float(" not in source
    assert "httpx" not in source
    assert "requests" not in source
    for banned in (
        "live",
        "auth",
        "wallet",
        "broker",
        "order",
        "submit",
        "cancel",
        "signing",
        "private_key",
        "advice",
    ):
        assert banned not in source
        assert all(banned not in name.lower() for name in public_names)

    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imports = (
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    )
    imported_roots: set[str] = set()
    for node in imports:
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        else:
            if node.module:
                imported_roots.add(node.module.split(".", 1)[0])
    assert not imported_roots & {
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    assert "open(" not in source
    assert "pathlib" not in source
    assert "inspect" not in source
    assert inspect.getsource(module).count("@dataclass(frozen=True)") == 4
