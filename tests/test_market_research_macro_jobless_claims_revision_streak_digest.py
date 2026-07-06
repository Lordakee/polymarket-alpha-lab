from __future__ import annotations

import ast
from collections.abc import Mapping
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType

import pytest


GENERATED_AT = datetime(2026, 7, 6, 13, 30, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def digest():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_macro_jobless_claims_revision_streak_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def join_text(*parts: str) -> str:
    return "".join(parts)


def observation(
    source_id: str = "source-alpha",
    *,
    release_id: str = "dol-weekly-claims",
    research_topic_key: str = "us.jobless-claims.revision-streak",
    release_week: str = "2026w27",
    initial_claims_revision: str | Decimal = "3000.000000",
    continuing_claims_revision: str | Decimal = "4000.000000",
    revision_streak_weeks: str | Decimal = "1.000000",
    same_direction_revision_weeks: str | Decimal = "1.000000",
    revised_at: datetime = datetime(2026, 7, 6, 12, 30, tzinfo=UTC),
    upstream_reason_codes: tuple[str, ...] = ("official_dol_release",),
):
    module = digest()
    return module.MacroJoblessClaimsRevisionStreakObservation(
        source_id=source_id,
        release_id=release_id,
        research_topic_key=research_topic_key,
        release_week=release_week,
        initial_claims_revision=(
            initial_claims_revision
            if isinstance(initial_claims_revision, Decimal)
            else d(initial_claims_revision)
        ),
        continuing_claims_revision=(
            continuing_claims_revision
            if isinstance(continuing_claims_revision, Decimal)
            else d(continuing_claims_revision)
        ),
        revision_streak_weeks=(
            revision_streak_weeks
            if isinstance(revision_streak_weeks, Decimal)
            else d(revision_streak_weeks)
        ),
        same_direction_revision_weeks=(
            same_direction_revision_weeks
            if isinstance(same_direction_revision_weeks, Decimal)
            else d(same_direction_revision_weeks)
        ),
        revised_at=revised_at,
        upstream_reason_codes=upstream_reason_codes,
    )


def report(*rows: object, cfg: object | None = None, generated_at: datetime = GENERATED_AT):
    module = digest()
    return module.build_market_research_macro_jobless_claims_revision_streak_digest(
        rows,
        config=cfg or module.MacroJoblessClaimsRevisionStreakDigestConfig(),
        generated_at=generated_at.astimezone(timezone(timedelta(hours=-4))),
    )


def test_empty_input_returns_report_only_blocked_digest() -> None:
    module = digest()

    digest_report = report()

    assert isinstance(digest_report, module.MacroJoblessClaimsRevisionStreakDigestReport)
    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-macro-jobless-claims-revision-streak-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_macro_jobless_claims_revision_streak_digest"
    )
    assert digest_report.input_count == d("0.000000")
    assert digest_report.row_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.revision_streak_count == d("0.000000")
    assert digest_report.initial_revision_count == d("0.000000")
    assert digest_report.continuing_revision_count == d("0.000000")
    assert digest_report.same_direction_streak_count == d("0.000000")
    assert digest_report.max_absolute_initial_claims_revision == d("0.000000")
    assert digest_report.average_absolute_initial_claims_revision == d("0.000000")
    assert digest_report.max_revision_streak_weeks == d("0.000000")
    assert digest_report.max_revision_streak_pressure_score == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == ("jobless_claims_revision_streak_digest_empty",)
    assert digest_report.reason_code_counts == (
        module.MacroJoblessClaimsRevisionStreakReasonCodeCount(
            reason_code="jobless_claims_revision_streak_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_revision_streak_rows_reasons_and_counts_are_deterministic() -> None:
    blocked = observation(
        "source-blocked",
        research_topic_key="us.jobless-claims.revision-streak.blocked",
        initial_claims_revision="-18000.000000",
        continuing_claims_revision="-32000.000000",
        revision_streak_weeks="5.000000",
        same_direction_revision_weeks="4.000000",
        upstream_reason_codes=("official_dol_release", "vendor_revision"),
    )
    watched = observation(
        "source-watch",
        research_topic_key="us.jobless-claims.revision-streak.watch",
        initial_claims_revision="7000.000000",
        continuing_claims_revision="12000.000000",
        revision_streak_weeks="3.000000",
        same_direction_revision_weeks="3.000000",
        revised_at=datetime(2026, 7, 6, 8, 30, tzinfo=timezone(timedelta(hours=-4))),
        upstream_reason_codes=(),
    )
    passed = observation(
        "source-pass",
        research_topic_key="us.jobless-claims.revision-streak.inline",
        initial_claims_revision="1000.000000",
        continuing_claims_revision="-2000.000000",
        revision_streak_weeks="1.000000",
        same_direction_revision_weeks="1.000000",
        upstream_reason_codes=(),
    )

    forward = report(watched, passed, blocked)
    reverse = report(blocked, passed, watched)

    assert forward == reverse
    assert forward.digest_status == "blocked"
    assert forward.input_count == d("3.000000")
    assert forward.row_count == d("3.000000")
    assert forward.blocked_count == d("1.000000")
    assert forward.watch_count == d("1.000000")
    assert forward.pass_count == d("1.000000")
    assert forward.revision_streak_count == d("2.000000")
    assert forward.initial_revision_count == d("2.000000")
    assert forward.continuing_revision_count == d("2.000000")
    assert forward.same_direction_streak_count == d("2.000000")
    assert forward.max_absolute_initial_claims_revision == d("18000.000000")
    assert forward.average_absolute_initial_claims_revision == d("8666.666667")
    assert forward.max_revision_streak_weeks == d("5.000000")
    assert forward.max_revision_streak_pressure_score == d("1.000000")
    assert forward.reason_codes == (
        "jobless_claims_revision_streak_blocked_present",
        "jobless_claims_revision_streak_watch_present",
        "jobless_claims_initial_revision_present",
        "jobless_claims_continuing_revision_present",
        "jobless_claims_same_direction_streak_present",
        "jobless_claims_upstream_revision_present",
    )
    assert tuple(row.research_topic_key for row in forward.rows) == (
        "us.jobless-claims.revision-streak.blocked",
        "us.jobless-claims.revision-streak.watch",
        "us.jobless-claims.revision-streak.inline",
    )

    blocked_row, watch_row, pass_row = forward.rows
    assert blocked_row.revision_status == "blocked"
    assert blocked_row.absolute_initial_claims_revision == d("18000.000000")
    assert blocked_row.absolute_continuing_claims_revision == d("32000.000000")
    assert blocked_row.revision_streak_pressure_score == d("1.000000")
    assert blocked_row.reason_codes == (
        "jobless_claims_revision_streak_blocked",
        "jobless_claims_initial_revision_blocked",
        "jobless_claims_continuing_revision_blocked",
        "jobless_claims_same_direction_streak",
        "jobless_claims_upstream_revision_present",
    )
    assert watch_row.revision_status == "watch"
    assert watch_row.revised_at == datetime(2026, 7, 6, 12, 30, tzinfo=UTC)
    assert watch_row.revision_streak_pressure_score == d("0.600000")
    assert watch_row.reason_codes == (
        "jobless_claims_revision_streak_watch",
        "jobless_claims_initial_revision_watch",
        "jobless_claims_continuing_revision_watch",
        "jobless_claims_same_direction_streak",
    )
    assert pass_row.revision_status == "pass"
    assert pass_row.reason_codes == ("jobless_claims_revision_streak_inline",)

    assert tuple(item.reason_code for item in forward.reason_code_counts) == (
        "jobless_claims_revision_streak_blocked_present",
        "jobless_claims_revision_streak_watch_present",
        "jobless_claims_initial_revision_present",
        "jobless_claims_continuing_revision_present",
        "jobless_claims_same_direction_streak_present",
        "jobless_claims_upstream_revision_present",
    )
    assert tuple(item.count for item in forward.reason_code_counts) == (
        d("1.000000"),
        d("1.000000"),
        d("2.000000"),
        d("2.000000"),
        d("2.000000"),
        d("1.000000"),
    )
    assert forward.reason_code_counts[2].row_ratio == d("0.666667")


def test_validation_rejects_subclasses_lists_future_sources_and_noncanonical_values() -> None:
    module = digest()

    public_types = (
        module.MacroJoblessClaimsRevisionStreakDigestConfig,
        module.MacroJoblessClaimsRevisionStreakObservation,
        module.MacroJoblessClaimsRevisionStreakDigestRow,
        module.MacroJoblessClaimsRevisionStreakReasonCodeCount,
        module.MacroJoblessClaimsRevisionStreakDigestReport,
    )
    for public_type in public_types:
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Bad{public_type.__name__}", (public_type,), {})
    with pytest.raises(ValueError, match="initial_claims_revision must be exactly Decimal"):
        observation(initial_claims_revision=_DecimalSubclass("1.000000"))
    with pytest.raises(
        ValueError,
        match="initial_claims_revision must use exactly six decimal places",
    ):
        observation(initial_claims_revision=d("1.00000"))
    with pytest.raises(ValueError, match="revision_streak_weeks must be nonnegative"):
        observation(revision_streak_weeks="-1.000000")
    with pytest.raises(ValueError, match="revised_at must be exactly datetime"):
        observation(revised_at=_DateTimeSubclass(2026, 7, 6, 12, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="revised_at must be timezone-aware"):
        observation(revised_at=datetime(2026, 7, 6, 12, 30))
    with pytest.raises(ValueError, match="upstream_reason_codes must be a tuple"):
        observation(upstream_reason_codes=["vendor_revision"])
    with pytest.raises(ValueError, match="upstream_reason_codes must use canonical sequence"):
        observation(upstream_reason_codes=("vendor_revision", "official_dol_release"))
    with pytest.raises(ValueError, match="observations must be a tuple"):
        module.build_market_research_macro_jobless_claims_revision_streak_digest(
            [observation("source-list")],
            config=module.MacroJoblessClaimsRevisionStreakDigestConfig(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="revised_at must not be after generated_at"):
        report(observation("source-future", revised_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(observation("source-dupe"), observation("source-dupe"))

    tampered_observation = observation("source-tampered")
    object.__setattr__(tampered_observation, "upstream_reason_codes", ["vendor_revision"])
    with pytest.raises(ValueError, match="upstream_reason_codes has unsupported payload value"):
        report(tampered_observation)


def test_public_records_are_frozen_exact_type_decimal_only_tuple_only_and_hard_flagged() -> None:
    module = digest()
    digest_report = report(observation("source-record"))

    public_records = (
        module.MacroJoblessClaimsRevisionStreakDigestConfig(),
        observation("source-dataclass"),
        digest_report.rows[0],
        digest_report.reason_code_counts[0],
        digest_report,
    )
    for public_record in public_records:
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if isinstance(field_value, Decimal):
                assert type(field_value) is Decimal
                assert field_value.as_tuple().exponent == -6
            if isinstance(field_value, tuple):
                assert type(field_value) is tuple

    frozen_observation = observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="config paper_only must be True"):
        module.MacroJoblessClaimsRevisionStreakDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(observation("source-report-only"), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(digest_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(digest_report, paper_only=False)


def test_reason_counts_reject_zero_fractional_and_reconcile_with_rows() -> None:
    module = digest()
    digest_report = report(
        observation(
            "source-reason-blocked",
            initial_claims_revision="-18000.000000",
            continuing_claims_revision="-32000.000000",
            revision_streak_weeks="5.000000",
            same_direction_revision_weeks="4.000000",
        ),
        observation(
            "source-reason-watch",
            research_topic_key="us.jobless-claims.revision-streak.watch",
            initial_claims_revision="7000.000000",
            continuing_claims_revision="12000.000000",
            revision_streak_weeks="3.000000",
            same_direction_revision_weeks="3.000000",
            upstream_reason_codes=(),
        ),
    )

    with pytest.raises(ValueError, match="count must be positive"):
        module.MacroJoblessClaimsRevisionStreakReasonCodeCount(
            reason_code="jobless_claims_revision_streak_blocked_present",
            count=d("0.000000"),
            row_ratio=d("0.000000"),
        )
    with pytest.raises(ValueError, match="count must be a whole count"):
        module.MacroJoblessClaimsRevisionStreakReasonCodeCount(
            reason_code="jobless_claims_revision_streak_blocked_present",
            count=d("1.500000"),
            row_ratio=d("0.500000"),
        )
    with pytest.raises(ValueError, match="reason_codes must use canonical sequence"):
        replace(
            digest_report.rows[0],
            reason_codes=tuple(reversed(digest_report.rows[0].reason_codes)),
        )
    with pytest.raises(ValueError, match="rows must use canonical sequence"):
        replace(digest_report, rows=tuple(reversed(digest_report.rows)))
    with pytest.raises(ValueError, match="reason_code_counts must use canonical sequence"):
        replace(
            digest_report,
            reason_code_counts=tuple(reversed(digest_report.reason_code_counts)),
        )
    with pytest.raises(ValueError, match="reason_code_counts must match"):
        replace(digest_report, reason_code_counts=())
    bad_count = replace(digest_report.reason_code_counts[0], count=d("999.000000"))
    with pytest.raises(ValueError, match="reason_code_counts must match"):
        replace(
            digest_report,
            reason_code_counts=(bad_count, *digest_report.reason_code_counts[1:]),
        )


def test_payload_serializes_public_numerics_and_recursively_revalidates_tampering() -> None:
    module = digest()
    digest_report = report(
        observation(
            "source-payload",
            initial_claims_revision="-18000.000000",
            continuing_claims_revision="-32000.000000",
            revision_streak_weeks="5.000000",
            same_direction_revision_weeks="4.000000",
            revised_at=datetime(2026, 7, 6, 7, 30, tzinfo=timezone(timedelta(hours=-5))),
        ),
    )

    payload = module.market_research_macro_jobless_claims_revision_streak_digest_payload(
        digest_report,
    )

    assert type(payload) is MappingProxyType
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["generated_at"] == "2026-07-06T13:30:00+00:00"
    assert payload["input_count"] == "1.000000"
    assert type(payload["rows"]) is tuple
    assert payload["rows"][0]["revised_at"] == "2026-07-06T12:30:00+00:00"
    assert payload["rows"][0]["initial_claims_revision"] == "-18000.000000"
    assert payload["rows"][0]["revision_streak_pressure_score"] == "1.000000"
    with pytest.raises(TypeError):
        payload["digest_status"] = "pass"  # type: ignore[index]
    with pytest.raises(TypeError):
        payload["rows"][0]["source_id"] = "changed"  # type: ignore[index]

    _assert_payload_has_only_public_json_scalars(payload)

    tampered_time_report = report(observation("source-tampered-time"))
    object.__setattr__(
        tampered_time_report.rows[0],
        "revised_at",
        datetime(2026, 7, 6, 7, 30, tzinfo=timezone(timedelta(hours=-5))),
    )
    with pytest.raises(ValueError, match="revised_at must already be UTC"):
        module.market_research_macro_jobless_claims_revision_streak_digest_payload(
            tampered_time_report,
        )

    tampered_row_report = report(observation("source-tampered-row"))
    object.__setattr__(
        tampered_row_report.rows[0],
        "absolute_initial_claims_revision",
        d("999.000000"),
    )
    with pytest.raises(ValueError, match="absolute_initial_claims_revision must match"):
        module.market_research_macro_jobless_claims_revision_streak_digest_payload(
            tampered_row_report,
        )

    tampered_count_report = report(observation("source-tampered-count"))
    object.__setattr__(tampered_count_report.reason_code_counts[0], "count", d("1.500000"))
    with pytest.raises(ValueError, match="count must be a whole count"):
        module.market_research_macro_jobless_claims_revision_streak_digest_payload(
            tampered_count_report,
        )

    tampered_report = report(observation("source-tampered-report"))
    object.__setattr__(tampered_report, "row_count", d("2.000000"))
    with pytest.raises(ValueError, match="row_count must match rows"):
        module.market_research_macro_jobless_claims_revision_streak_digest_payload(
            tampered_report,
        )
    with pytest.raises(ValueError, match="report must be exactly"):
        module.market_research_macro_jobless_claims_revision_streak_digest_payload(payload)


def test_module_has_no_io_live_surfaces_or_forbidden_payload_helpers() -> None:
    source = Path(
        "src/polymarket_alpha_lab/"
        "market_research_macro_jobless_claims_revision_streak_digest.py",
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
        if isinstance(node, ast.Attribute):
            assert node.attr != "asdict"

    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "sqlite",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "asdict",
        join_text("market", "_slug"),
        "question",
        join_text("payload", "_json"),
        "private_key",
        "api_key",
        "wallet",
        "urlopen",
        "connect(",
        "execute(",
        "live trading",
        "submit_order",
        "cancel_order",
        "replace_order",
        "subprocess",
    ):
        assert forbidden not in source.lower()


def _assert_payload_has_only_public_json_scalars(value: object) -> None:
    if isinstance(value, Mapping):
        for field_name, child in value.items():
            lowered = str(field_name).lower()
            assert "private_key" not in lowered
            assert "wallet" not in lowered
            assert "auth" not in lowered
            assert join_text("market", "_slug") not in lowered
            assert "question" not in lowered
            assert join_text("payload", "_json") not in lowered
            _assert_payload_has_only_public_json_scalars(child)
        return
    if isinstance(value, tuple):
        for child in value:
            _assert_payload_has_only_public_json_scalars(child)
        return
    if type(value) is bool:
        return
    assert not isinstance(value, (Decimal, datetime, float, int))
