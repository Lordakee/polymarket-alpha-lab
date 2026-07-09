from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_source_authority_revision_conflict_queue_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_authority_revision_conflict_queue_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedRevisionConflictShape:
    public_case_key: str
    authority_bucket: str
    private_candidate_reference: str
    private_market_reference: str
    private_source_reference: str
    revision_observed_at: datetime
    authority_revision_observed_at: datetime
    authority_score: Decimal
    revision_conflict_score: Decimal
    corroborating_authority_count: Decimal
    required_authority_count: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "revision_watch_age_seconds": d("3600.000000"),
        "revision_block_age_seconds": d("21600.000000"),
        "authority_score_watch_threshold": d("0.700000"),
        "authority_score_block_threshold": d("0.300000"),
        "revision_conflict_watch_threshold": d("0.300000"),
        "revision_conflict_block_threshold": d("0.700000"),
        "corroboration_gap_watch_threshold": d("0.500000"),
        "corroboration_gap_block_threshold": d("0.800000"),
        "watch_queue_pressure_score": d("0.250000"),
        "block_queue_pressure_score": d("0.700000"),
        "revision_age_weight": d("0.300000"),
        "authority_gap_weight": d("0.250000"),
        "revision_conflict_weight": d("0.300000"),
        "authority_corroboration_gap_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.ResearchSourceAuthorityRevisionConflictQueueConfig(**values)


def item(
    index: int,
    *,
    public_case_key: str | None = None,
    authority_bucket: str | None = None,
    revision_observed_at: datetime | None = None,
    authority_revision_observed_at: datetime | None = None,
    authority_score: Decimal = d("0.950000"),
    revision_conflict_score: Decimal = d("0.050000"),
    corroborating_authority_count: Decimal = d("2.000000"),
    required_authority_count: Decimal = d("2.000000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceAuthorityRevisionConflictQueueInput(
        public_case_key=public_case_key or f"case-{index:03d}",
        authority_bucket=authority_bucket or f"authority-{index:03d}",
        private_candidate_reference=(
            f"raw_candidate_id=CAND-{index:03d}; token=secret-{index}"
        ),
        private_market_reference=(
            f"market_id=0xMARKET{index:03d}; market_slug=will-alpha-{index}; "
            f"question=Will Alpha resolve {index}?"
        ),
        private_source_reference=(
            "https://authority.example.test/private?"
            f"dsn=postgres://user:pass@host/db&table=authority_table_{index}; "
            f"wallet=0xabc; order={index}; trade={index}; live feed; source text"
        ),
        revision_observed_at=revision_observed_at
        if revision_observed_at is not None
        else GENERATED_AT - timedelta(minutes=20),
        authority_revision_observed_at=authority_revision_observed_at
        if authority_revision_observed_at is not None
        else GENERATED_AT - timedelta(minutes=20),
        authority_score=authority_score,
        revision_conflict_score=revision_conflict_score,
        corroborating_authority_count=corroborating_authority_count,
        required_authority_count=required_authority_count,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_source_authority_revision_conflict_queue_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at.astimezone(timezone(timedelta(hours=-4))),
    )


def test_empty_input_returns_report_only_pass_with_digest_surface() -> None:
    module = api()
    conflict_report = report(())

    assert module.STATUSES == ("pass", "watch", "block")
    assert type(conflict_report) is module.ResearchSourceAuthorityRevisionConflictQueueReport
    assert is_dataclass(conflict_report)
    assert conflict_report.generated_at == GENERATED_AT
    assert conflict_report.row_count == d("0.000000")
    assert conflict_report.stale_revision_count == d("0.000000")
    assert conflict_report.low_authority_count == d("0.000000")
    assert conflict_report.conflict_count == d("0.000000")
    assert conflict_report.corroboration_gap_count == d("0.000000")
    assert conflict_report.pass_count == d("0.000000")
    assert conflict_report.watch_count == d("0.000000")
    assert conflict_report.block_count == d("0.000000")
    assert conflict_report.average_conflict_queue_pressure_score == d("0.000000")
    assert conflict_report.max_conflict_queue_pressure_score == d("0.000000")
    assert conflict_report.status == "pass"
    assert conflict_report.rows == ()
    assert conflict_report.reason_codes == ("authority_revision_conflict_queue_empty",)
    assert conflict_report.reason_code_counts == (
        module.ResearchSourceAuthorityRevisionConflictQueueReasonCodeCount(
            reason_code="authority_revision_conflict_queue_empty",
            count=d("1.000000"),
        ),
    )
    assert len(conflict_report.derived_validation_digest) == 64
    int(conflict_report.derived_validation_digest, 16)
    assert conflict_report.paper_only is True
    assert conflict_report.report_only is True
    assert conflict_report.readonly is True


def test_prioritizes_revision_conflict_queue_with_decimal_scores() -> None:
    module = api()
    conflict_report = report(
        (
            item(
                1,
                public_case_key="alpha-pass",
                authority_bucket="authority-pass",
            ),
            item(
                2,
                public_case_key="beta-watch",
                authority_bucket="authority-watch",
                revision_observed_at=GENERATED_AT - timedelta(hours=3),
                authority_revision_observed_at=GENERATED_AT - timedelta(hours=2),
                authority_score=d("0.650000"),
                revision_conflict_score=d("0.400000"),
                corroborating_authority_count=d("1.000000"),
                required_authority_count=d("3.000000"),
                reason_codes=("manual_revision_review",),
            ),
            item(
                3,
                public_case_key="gamma-block",
                authority_bucket="authority-block",
                revision_observed_at=GENERATED_AT - timedelta(hours=8),
                authority_revision_observed_at=GENERATED_AT - timedelta(hours=7),
                authority_score=d("0.250000"),
                revision_conflict_score=d("0.800000"),
                corroborating_authority_count=d("0.000000"),
                required_authority_count=d("3.000000"),
                reason_codes=("primary_authority_changed",),
            ),
        ),
    )

    assert conflict_report.status == "block"
    assert conflict_report.row_count == d("3.000000")
    assert conflict_report.stale_revision_count == d("2.000000")
    assert conflict_report.low_authority_count == d("2.000000")
    assert conflict_report.conflict_count == d("2.000000")
    assert conflict_report.corroboration_gap_count == d("2.000000")
    assert conflict_report.pass_count == d("1.000000")
    assert conflict_report.watch_count == d("1.000000")
    assert conflict_report.block_count == d("1.000000")
    assert conflict_report.average_conflict_queue_pressure_score == d("0.459722")
    assert conflict_report.max_conflict_queue_pressure_score == d("0.877500")

    block_row, watch_row, pass_row = conflict_report.rows
    assert type(block_row) is module.ResearchSourceAuthorityRevisionConflictQueueRow
    assert block_row.public_case_key == "gamma-block"
    assert block_row.revision_age_seconds == d("28800.000000")
    assert block_row.authority_revision_age_seconds == d("25200.000000")
    assert block_row.revision_age_pressure == d("1.000000")
    assert block_row.revision_age_band == "stale"
    assert block_row.authority_gap_score == d("0.750000")
    assert block_row.authority_corroboration_gap_score == d("1.000000")
    assert block_row.conflict_queue_pressure_score == d("0.877500")
    assert block_row.status == "block"
    assert block_row.reason_codes == (
        "authority_corroboration_block",
        "authority_gap_block",
        "authority_revision_conflict_queue_block",
        "input_primary_authority_changed",
        "revision_age_block",
        "revision_conflict_block",
    )

    assert watch_row.public_case_key == "beta-watch"
    assert watch_row.status == "watch"
    assert watch_row.revision_age_seconds == d("10800.000000")
    assert watch_row.authority_revision_age_seconds == d("7200.000000")
    assert watch_row.revision_age_pressure == d("0.500000")
    assert watch_row.revision_age_band == "late"
    assert watch_row.authority_gap_score == d("0.350000")
    assert watch_row.authority_corroboration_gap_score == d("0.666667")
    assert watch_row.conflict_queue_pressure_score == d("0.457500")
    assert "input_manual_revision_review" in watch_row.reason_codes

    assert pass_row.public_case_key == "alpha-pass"
    assert pass_row.status == "pass"
    assert pass_row.revision_age_pressure == d("0.055556")
    assert pass_row.revision_age_band == "fresh"
    assert pass_row.conflict_queue_pressure_score == d("0.044167")
    assert pass_row.reason_codes == (
        "authority_corroboration_clear",
        "authority_gap_clear",
        "authority_revision_conflict_queue_pass",
        "revision_age_fresh",
        "revision_conflict_clear",
    )


def test_custom_config_weights_are_used_to_validate_pressure_scores() -> None:
    module = api()
    custom_cfg = config(
        revision_age_weight=d("0.100000"),
        authority_gap_weight=d("0.700000"),
        revision_conflict_weight=d("0.100000"),
        authority_corroboration_gap_weight=d("0.100000"),
    )

    conflict_report = report(
        (
            item(
                1,
                public_case_key="custom-weight-case",
                authority_bucket="authority-weighted",
            ),
        ),
        cfg=custom_cfg,
    )
    payload = module.research_source_authority_revision_conflict_queue_report_payload(
        conflict_report,
    )

    row = conflict_report.rows[0]
    assert row.revision_age_pressure == d("0.055556")
    assert row.authority_gap_score == d("0.050000")
    assert row.revision_conflict_score == d("0.050000")
    assert row.authority_corroboration_gap_score == d("0.000000")
    assert row.conflict_queue_pressure_score == d("0.045556")
    assert row.conflict_queue_pressure_score != d("0.044167")
    assert payload["rows"][0]["conflict_queue_pressure_score"] == "0.045556"


def test_payload_and_digest_are_deterministic_public_safe_and_decimal_strings() -> None:
    module = api()
    rows = (
        SuppliedRevisionConflictShape(
            public_case_key="beta-watch",
            authority_bucket="authority-watch",
            private_candidate_reference="raw_candidate_id=CAND-002; token=secret",
            private_market_reference=(
                "market_id=0xMARKET002; market_slug=will-alpha; "
                "question=Will Alpha resolve?"
            ),
            private_source_reference=(
                "https://authority.example.test/source?dsn=postgres://host/db&"
                "table=authority_table&wallet=0xabc&order=1&trade=1; source text"
            ),
            revision_observed_at=GENERATED_AT - timedelta(hours=3),
            authority_revision_observed_at=GENERATED_AT - timedelta(hours=2),
            authority_score=d("0.650000"),
            revision_conflict_score=d("0.400000"),
            corroborating_authority_count=d("1.000000"),
            required_authority_count=d("3.000000"),
            reason_codes=("manual_revision_review",),
        ),
        item(1, public_case_key="alpha-pass", authority_bucket="authority-pass"),
    )
    first_report = report(rows)
    second_report = report(tuple(reversed(rows)))
    first_payload = module.research_source_authority_revision_conflict_queue_report_payload(
        first_report,
    )
    second_payload = module.research_source_authority_revision_conflict_queue_report_payload(
        second_report,
    )
    unsigned_payload = dict(first_payload)
    digest = unsigned_payload.pop("derived_validation_digest")
    canonical = json.dumps(
        unsigned_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    encoded = json.dumps(first_payload, sort_keys=True).lower()

    assert first_payload == second_payload
    assert first_report.derived_validation_digest == second_report.derived_validation_digest
    assert first_payload["derived_validation_digest"] == first_report.derived_validation_digest
    assert digest == hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    assert first_payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert first_payload["rows"][0]["conflict_queue_pressure_score"] == "0.457500"
    assert first_payload["rows"][1]["revision_age_seconds"] == "1200.000000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert not any(type(value) is int for value in _walk_payload_values(first_payload))
    assert all(not isinstance(value, Decimal) for value in _walk_payload_values(first_payload))
    for forbidden in (
        "raw_candidate_id",
        "cand-002",
        "market_id",
        "market_slug",
        "question",
        "will alpha resolve",
        "https://authority.example.test",
        "dsn=postgres",
        "authority_table",
        "token=secret",
        "wallet=0xabc",
        "order=1",
        "trade=1",
        "source text",
        "private_candidate_reference",
        "private_market_reference",
        "private_source_reference",
    ):
        assert forbidden not in encoded

    tampered_payload = dict(first_payload)
    tampered_payload["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_source_authority_revision_conflict_queue_report_payload(
            tampered_payload,
        )


def test_mapping_inputs_are_coerced_without_private_reference_leakage() -> None:
    module = api()
    mapping_input = {
        "public_case_key": "mapped-watch",
        "authority_bucket": "authority-mapped",
        "private_candidate_reference": "raw_candidate_id=CAND-MAP; token=secret",
        "private_market_reference": (
            "market_id=0xMAPPED; market_slug=mapped-market; "
            "question=Will mapped inputs work?"
        ),
        "private_source_reference": (
            "https://authority.example.test/private?dsn=postgres://host/db&"
            "table=authority_table&wallet=0xabc&order=1&trade=1; source text"
        ),
        "revision_observed_at": GENERATED_AT - timedelta(hours=2),
        "authority_revision_observed_at": GENERATED_AT - timedelta(hours=2),
        "authority_score": d("0.650000"),
        "revision_conflict_score": d("0.400000"),
        "corroborating_authority_count": d("1.000000"),
        "required_authority_count": d("3.000000"),
        "reason_codes": ("manual_revision_review",),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }

    conflict_report = report((mapping_input,))
    payload = module.research_source_authority_revision_conflict_queue_report_payload(
        conflict_report,
    )
    encoded = json.dumps(payload, sort_keys=True).lower()

    assert conflict_report.rows[0].public_case_key == "mapped-watch"
    assert conflict_report.rows[0].status == "watch"
    assert "input_manual_revision_review" in conflict_report.rows[0].reason_codes
    for forbidden in (
        "raw_candidate_id",
        "cand-map",
        "market_id",
        "market_slug",
        "mapped-market",
        "will mapped inputs work",
        "https://authority.example.test",
        "dsn=postgres",
        "authority_table",
        "token=secret",
        "wallet=0xabc",
        "order=1",
        "trade=1",
        "source text",
        "private_candidate_reference",
        "private_market_reference",
        "private_source_reference",
    ):
        assert forbidden not in encoded


def test_validation_rejects_bad_types_thresholds_flags_and_unsafe_public_values() -> None:
    module = api()
    with pytest.raises(ValueError, match="revision_age_weight"):
        config(revision_age_weight=d("0.100000"))
    with pytest.raises(ValueError, match="block_queue_pressure_score"):
        config(block_queue_pressure_score=d("0.200000"))
    with pytest.raises(ValueError, match="revision_watch_age_seconds"):
        config(revision_watch_age_seconds=d("21600.000000"))
    with pytest.raises(ValueError, match="authority_score_block_threshold"):
        config(authority_score_block_threshold=d("0.800000"))
    with pytest.raises(ValueError, match="revision_block_age_seconds"):
        config(revision_block_age_seconds=21600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="authority_gap_weight"):
        config(authority_gap_weight=DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_source_authority_revision_conflict_queue_report(
            (item(1),),
            config=config(),
            generated_at=datetime(2026, 7, 9, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_source_authority_revision_conflict_queue_report(
            (item(1),),
            config=config(),
            generated_at=DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="public_case_key"):
        item(1, public_case_key="case url")
    with pytest.raises(ValueError, match="public_case_key"):
        item(1, public_case_key="market-alpha")
    with pytest.raises(ValueError, match="revision_observed_at"):
        report((item(1, revision_observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="authority_revision_observed_at"):
        report(
            (
                item(
                    1,
                    authority_revision_observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )
    with pytest.raises(ValueError, match="authority_score"):
        item(1, authority_score=d("1.100000"))
    with pytest.raises(ValueError, match="revision_conflict_score"):
        item(1, revision_conflict_score=DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="corroborating_authority_count"):
        item(
            1,
            corroborating_authority_count=d("3.000000"),
            required_authority_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        item(1, reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(item(1), paper_only=False)
    with pytest.raises(ValueError, match="duplicate public_case_key and authority_bucket"):
        report(
            (
                item(1, public_case_key="case-a", authority_bucket="authority-a"),
                item(2, public_case_key="case-a", authority_bucket="authority-a"),
            ),
        )


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    module = api()
    conflict_report = report((item(1),))
    payload = module.research_source_authority_revision_conflict_queue_report_payload(
        conflict_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    with pytest.raises(FrozenInstanceError):
        conflict_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        conflict_report.rows[0].conflict_queue_pressure_score = d("1.000000")  # type: ignore[misc]
    with pytest.raises(TypeError):
        type("BadConfig", (module.ResearchSourceAuthorityRevisionConflictQueueConfig,), {})
    with pytest.raises(ValueError, match="status"):
        replace(conflict_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="conflict_queue_pressure_score"):
        replace(conflict_report.rows[0], conflict_queue_pressure_score=d("0.750000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(conflict_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="row_count"):
        replace(conflict_report, row_count=d("2.000000"))
    for field_name in (
        "stale_revision_count",
        "low_authority_count",
        "conflict_count",
        "corroboration_gap_count",
    ):
        with pytest.raises(ValueError, match=field_name):
            replace(conflict_report, **{field_name: d("9.000000")})

    unsafe_payload = dict(payload)
    unsafe_payload["market_slug"] = "unsafe"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_source_authority_revision_conflict_queue_report_payload(
            unsafe_payload,
        )


def test_owned_module_has_no_db_network_execution_or_advice_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "psycopg",
        "sqlalchemy",
        "sqlite",
        "supabase",
        ".write(",
        "db_",
        "source_url",
        "source_text",
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "dsn",
        "wallet",
        "order",
        "trade",
        "live execution",
        "execute(",
        "recommendation",
        "sizing",
    )

    assert all(term not in source for term in forbidden_terms)


def test_public_api_is_exactly_the_report_only_surface() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_AUTHORITY_REVISION_CONFLICT_QUEUE_REPORT_CONFIG_VERSION",
        "ResearchSourceAuthorityRevisionConflictQueueConfig",
        "ResearchSourceAuthorityRevisionConflictQueueInput",
        "ResearchSourceAuthorityRevisionConflictQueueReasonCodeCount",
        "ResearchSourceAuthorityRevisionConflictQueueReport",
        "ResearchSourceAuthorityRevisionConflictQueueRow",
        "STATUSES",
        "build_research_source_authority_revision_conflict_queue_report",
        "research_source_authority_revision_conflict_queue_report_payload",
    )


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
