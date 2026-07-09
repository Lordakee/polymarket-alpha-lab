from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal, ROUND_DOWN, localcontext
import hashlib
import json
from pathlib import Path

import pytest

import polymarket_alpha_lab.research_source_authority_evidence_decay_router_report as api
from polymarket_alpha_lab.research_source_authority_evidence_decay_router_report import (
    ResearchSourceAuthorityEvidenceDecayRouterConfig,
    ResearchSourceAuthorityEvidenceDecayRouterInput,
    ResearchSourceAuthorityEvidenceDecayRouterPublicPayloadItem,
    ResearchSourceAuthorityEvidenceDecayRouterReport,
    ResearchSourceAuthorityEvidenceDecayRouterRow,
    build_research_source_authority_evidence_decay_router_report,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def canonical_digest(payload: dict[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def input_row(
    *,
    raw_candidate_id: str = "candidate-private-123",
    raw_market_id: str = "market-private-456",
    raw_market_slug: str = "will-private-market-resolve",
    raw_market_question: str = "Will the private market resolve yes?",
    raw_source_reference: str = "https://authority.example/path?token=secret",
    raw_source_text: str | None = "raw source text with private token",
    authority_score: Decimal = Decimal("0.900000"),
    evidence_support_score: Decimal = Decimal("0.900000"),
    evidence_observed_at: datetime = GENERATED_AT - timedelta(hours=1),
    independence_score: Decimal = Decimal("0.800000"),
    conflict_score: Decimal = Decimal("0.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchSourceAuthorityEvidenceDecayRouterInput:
    return ResearchSourceAuthorityEvidenceDecayRouterInput(
        raw_candidate_id=raw_candidate_id,
        raw_market_id=raw_market_id,
        raw_market_slug=raw_market_slug,
        raw_market_question=raw_market_question,
        raw_source_reference=raw_source_reference,
        raw_source_text=raw_source_text,
        authority_score=authority_score,
        evidence_support_score=evidence_support_score,
        evidence_observed_at=evidence_observed_at,
        independence_score=independence_score,
        conflict_score=conflict_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    rows: tuple[ResearchSourceAuthorityEvidenceDecayRouterInput, ...],
    *,
    public_payload: tuple[
        ResearchSourceAuthorityEvidenceDecayRouterPublicPayloadItem,
        ...,
    ] = (),
) -> ResearchSourceAuthorityEvidenceDecayRouterReport:
    return build_research_source_authority_evidence_decay_router_report(
        rows,
        generated_at=GENERATED_AT,
        public_payload=public_payload,
    )


def test_router_status_counts_cover_pass_watch_and_block() -> None:
    report = build_report(
        (
            input_row(raw_candidate_id="pass-candidate"),
            input_row(
                raw_candidate_id="watch-candidate",
                authority_score=Decimal("0.600000"),
            ),
            input_row(
                raw_candidate_id="block-candidate",
                evidence_observed_at=GENERATED_AT - timedelta(days=8),
            ),
        ),
    )

    assert report.router_status == "block"
    assert report.evidence_count == Decimal("3.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.block_count == Decimal("1.000000")
    assert report.average_authority_score == Decimal("0.800000")
    assert report.oldest_evidence_age_seconds == Decimal("691200.000000")
    assert {row.router_status for row in report.rows} == {"pass", "watch", "block"}
    assert set(report.reason_codes) >= {"router_pass", "router_watch", "router_block"}
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in report.rows)


def test_empty_report_blocks_with_digest_and_decimal_string_payload() -> None:
    report = build_report(())
    payload = report.payload

    assert report.router_status == "block"
    assert report.evidence_count == Decimal("0.000000")
    assert report.reason_codes == ("no_evidence", "router_block")
    assert payload["evidence_count"] == "0.000000"
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert api.research_source_authority_evidence_decay_router_report_digest(report) == (
        payload["derived_validation_digest"]
    )
    json.dumps(payload, sort_keys=True)
    _assert_no_decimal_objects(payload)


def test_payload_is_deterministic_redacted_and_digest_validated() -> None:
    first = input_row(
        raw_candidate_id="candidate-alpha-raw",
        raw_market_id="market-alpha-raw",
        raw_market_slug="private-alpha-market-slug",
        raw_market_question="Will private alpha leak?",
        raw_source_reference="https://alpha.example/source?token=alpha-secret",
        raw_source_text="alpha private source text",
    )
    second = input_row(
        raw_candidate_id="candidate-beta-raw",
        raw_market_id="market-beta-raw",
        raw_market_slug="private-beta-market-slug",
        raw_market_question="Will private beta leak?",
        raw_source_reference="vendor://beta/private/source",
        raw_source_text="beta private source text",
        authority_score=Decimal("0.500000"),
        evidence_support_score=Decimal("0.700000"),
    )
    public_payload = (
        ResearchSourceAuthorityEvidenceDecayRouterPublicPayloadItem(
            "safe_summary",
            "authority and evidence decay buckets only",
        ),
    )

    first_report = build_report((first, second), public_payload=public_payload)
    second_report = build_report((second, first), public_payload=public_payload)
    payload = first_report.payload

    assert payload == second_report.payload
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["derived_validation_digest"] == first_report.derived_validation_digest
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(first_report.derived_validation_digest) == 64
    int(first_report.derived_validation_digest, 16)
    assert all(str(row["evidence_ref"]).startswith("sha256:") for row in payload["rows"])  # type: ignore[index]
    _assert_no_non_decimal_public_numbers(first_report)

    public_blob = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "candidate-alpha-raw",
        "candidate-beta-raw",
        "market-alpha-raw",
        "market-beta-raw",
        "private-alpha-market-slug",
        "private-beta-market-slug",
        "will private alpha leak",
        "will private beta leak",
        "https://alpha.example",
        "vendor://beta",
        "alpha private source text",
        "beta private source text",
        "token",
        "secret",
        "source_url",
        "source_text",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
    ):
        assert forbidden not in public_blob


def test_evidence_ref_binds_all_routing_relevant_inputs() -> None:
    low_conflict = input_row(
        raw_candidate_id="same-private-candidate",
        raw_market_id="same-private-market",
        raw_market_slug="same-private-slug",
        raw_market_question="Will same private market resolve?",
        raw_source_reference="https://same.example/source",
        raw_source_text="same private source text",
        conflict_score=Decimal("0.000000"),
    )
    high_conflict = input_row(
        raw_candidate_id="same-private-candidate",
        raw_market_id="same-private-market",
        raw_market_slug="same-private-slug",
        raw_market_question="Will same private market resolve?",
        raw_source_reference="https://same.example/source",
        raw_source_text="same private source text",
        conflict_score=Decimal("0.700000"),
    )

    report = build_report((low_conflict, high_conflict))

    assert len({row.evidence_ref for row in report.rows}) == 2


def test_digest_public_payload_and_status_validation_reject_tampering() -> None:
    report = build_report((input_row(),))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            report,
            public_payload=(
                ResearchSourceAuthorityEvidenceDecayRouterPublicPayloadItem(
                    "safe_summary",
                    "changed authority decay bucket",
                ),
            ),
        )

    downgraded_payload = dict(report.payload)
    downgraded_payload["readonly"] = False
    downgraded_payload["derived_validation_digest"] = canonical_digest(downgraded_payload)
    with pytest.raises(ValueError, match="readonly"):
        api.validate_research_source_authority_evidence_decay_router_public_payload(
            downgraded_payload,
        )

    bad_status_payload = dict(report.payload)
    bad_status_payload["router_status"] = "hold"
    bad_status_payload["derived_validation_digest"] = canonical_digest(bad_status_payload)
    with pytest.raises(ValueError, match="router_status"):
        api.validate_research_source_authority_evidence_decay_router_public_payload(
            bad_status_payload,
        )


def test_public_payload_validation_requires_exact_canonical_schema() -> None:
    report = build_report(
        (input_row(),),
        public_payload=(
            ResearchSourceAuthorityEvidenceDecayRouterPublicPayloadItem(
                "safe_summary",
                "authority decay buckets only",
            ),
        ),
    )

    extra_top_level = deepcopy(report.payload)
    extra_top_level["safe_extra"] = "unexpected"
    extra_top_level["derived_validation_digest"] = canonical_digest(extra_top_level)
    with pytest.raises(ValueError, match="public payload fields"):
        api.validate_research_source_authority_evidence_decay_router_public_payload(
            extra_top_level,
        )

    missing_rows = deepcopy(report.payload)
    missing_rows.pop("rows")
    missing_rows["derived_validation_digest"] = canonical_digest(missing_rows)
    with pytest.raises(ValueError, match="public payload fields"):
        api.validate_research_source_authority_evidence_decay_router_public_payload(
            missing_rows,
        )

    tuple_rows = deepcopy(report.payload)
    tuple_rows["rows"] = tuple(tuple_rows["rows"])  # type: ignore[arg-type]
    tuple_rows["derived_validation_digest"] = canonical_digest(tuple_rows)
    with pytest.raises(ValueError, match="rows must be a list"):
        api.validate_research_source_authority_evidence_decay_router_public_payload(
            tuple_rows,
        )

    extra_row_field = deepcopy(report.payload)
    extra_row_field["rows"][0]["safe_extra"] = "unexpected"  # type: ignore[index]
    extra_row_field["derived_validation_digest"] = canonical_digest(extra_row_field)
    with pytest.raises(ValueError, match="row fields"):
        api.validate_research_source_authority_evidence_decay_router_public_payload(
            extra_row_field,
        )

    nested_false_flag = deepcopy(report.payload)
    nested_false_flag["rows"][0]["readonly"] = False  # type: ignore[index]
    nested_false_flag["derived_validation_digest"] = canonical_digest(nested_false_flag)
    with pytest.raises(ValueError, match="readonly"):
        api.validate_research_source_authority_evidence_decay_router_public_payload(
            nested_false_flag,
        )

    extra_public_item_field = deepcopy(report.payload)
    extra_public_item_field["public_payload"][0]["safe_extra"] = "unexpected"  # type: ignore[index]
    extra_public_item_field["derived_validation_digest"] = canonical_digest(
        extra_public_item_field,
    )
    with pytest.raises(ValueError, match="public payload item fields"):
        api.validate_research_source_authority_evidence_decay_router_public_payload(
            extra_public_item_field,
        )


def test_public_payload_validation_rejects_noncanonical_and_inconsistent_values() -> None:
    report = build_report((input_row(),))

    noncanonical_count = deepcopy(report.payload)
    noncanonical_count["evidence_count"] = "1"
    noncanonical_count["derived_validation_digest"] = canonical_digest(
        noncanonical_count,
    )
    with pytest.raises(ValueError, match="evidence_count.*canonical Decimal string"):
        api.validate_research_source_authority_evidence_decay_router_public_payload(
            noncanonical_count,
        )

    inconsistent_count = deepcopy(report.payload)
    inconsistent_count["pass_count"] = "0.000000"
    inconsistent_count["derived_validation_digest"] = canonical_digest(
        inconsistent_count,
    )
    with pytest.raises(ValueError, match="pass_count must match rows"):
        api.validate_research_source_authority_evidence_decay_router_public_payload(
            inconsistent_count,
        )

    inconsistent_router_score = deepcopy(report.payload)
    inconsistent_router_score["rows"][0]["router_score"] = "0.000000"  # type: ignore[index]
    inconsistent_router_score["derived_validation_digest"] = canonical_digest(
        inconsistent_router_score,
    )
    with pytest.raises(ValueError, match="router_score must match row components"):
        api.validate_research_source_authority_evidence_decay_router_public_payload(
            inconsistent_router_score,
        )

    forged_pass_row = deepcopy(report.payload)
    forged_pass_row["rows"][0]["authority_score"] = "0.100000"  # type: ignore[index]
    forged_pass_row["rows"][0]["router_score"] = "0.570000"  # type: ignore[index]
    forged_pass_row["average_authority_score"] = "0.100000"
    forged_pass_row["derived_validation_digest"] = canonical_digest(forged_pass_row)
    with pytest.raises(ValueError, match="router_status must match row components"):
        api.validate_research_source_authority_evidence_decay_router_public_payload(
            forged_pass_row,
        )

    oversized_count = deepcopy(report.payload)
    oversized_count["evidence_count"] = f"{'9' * 80}.000000"
    oversized_count["derived_validation_digest"] = canonical_digest(oversized_count)
    with pytest.raises(ValueError, match="evidence_count.*canonical Decimal string"):
        api.validate_research_source_authority_evidence_decay_router_public_payload(
            oversized_count,
        )


def test_duplicate_inputs_and_public_payload_keys_are_rejected() -> None:
    duplicate_input = input_row()
    with pytest.raises(ValueError, match="inputs must be unique"):
        build_report((duplicate_input, duplicate_input))

    duplicate_public_item = ResearchSourceAuthorityEvidenceDecayRouterPublicPayloadItem(
        "safe_summary",
        "authority decay buckets only",
    )
    with pytest.raises(ValueError, match="public_payload keys must be unique"):
        build_report(
            (input_row(),),
            public_payload=(duplicate_public_item, duplicate_public_item),
        )


def test_payload_serializer_requires_typed_report() -> None:
    report = build_report((input_row(),))

    with pytest.raises(
        ValueError,
        match="report must be a ResearchSourceAuthorityEvidenceDecayRouterReport",
    ):
        api.research_source_authority_evidence_decay_router_report_payload(
            report.payload,
        )


def test_row_rejects_router_score_inconsistent_with_components() -> None:
    row = build_report((input_row(),)).rows[0]

    with pytest.raises(ValueError, match="router_score must match row components"):
        replace(row, router_score=Decimal("0.000000"))


def test_decimal_math_is_independent_of_caller_context() -> None:
    row = input_row(
        authority_score=Decimal("0.876543"),
        evidence_support_score=Decimal("0.765432"),
        evidence_observed_at=GENERATED_AT
        - timedelta(days=2, seconds=34567, microseconds=890123),
        independence_score=Decimal("0.654321"),
        conflict_score=Decimal("0.123456"),
    )
    expected = build_report((row,)).payload

    with localcontext() as context:
        context.prec = 7
        context.rounding = ROUND_DOWN
        actual = build_report((row,)).payload

    assert actual == expected


def test_public_payload_rejects_sensitive_keys_and_values() -> None:
    for unsafe_key in (
        "candidate",
        "candidate_id",
        "market",
        "market_id",
        "slug",
        "market_slug",
        "question",
        "market_question",
        "source",
        "url",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "auth_token",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchSourceAuthorityEvidenceDecayRouterPublicPayloadItem(
                unsafe_key,
                "safe value",
            )

    for unsafe_value in (
        "https://example.test/source",
        "candidate_id=candidate-private-123",
        "market_slug=private-slug",
        "source_text=raw source text",
        "dsn=postgres://secret",
        "wallet surface",
        "order surface",
        "trade surface",
        "sizing surface",
        "recommendation surface",
        "auth token",
        "www.example.test/source",
        "research table snapshot",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchSourceAuthorityEvidenceDecayRouterPublicPayloadItem(
                "safe_key",
                unsafe_value,
            )


def test_dataclasses_are_frozen_decimal_strict_and_flags_are_hard() -> None:
    report = build_report((input_row(),))

    with pytest.raises(FrozenInstanceError):
        report.router_status = "watch"  # type: ignore[misc]
    with pytest.raises(TypeError):

        class BadRow(ResearchSourceAuthorityEvidenceDecayRouterRow):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        ResearchSourceAuthorityEvidenceDecayRouterConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(input_row(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="authority_score"):
        input_row(authority_score=Decimal("0.900000") + Decimal("0"))  # accepted
        input_row(authority_score=0.9)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="authority_score"):
        input_row(authority_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="evidence_observed_at"):
        input_row(evidence_observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="evidence_observed_at"):
        input_row(
            evidence_observed_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="evidence_observed_at"):
        build_research_source_authority_evidence_decay_router_report(
            (input_row(evidence_observed_at=GENERATED_AT + timedelta(seconds=1)),),
            generated_at=GENERATED_AT,
        )


def test_public_api_and_module_scope_are_report_only_without_live_surfaces() -> None:
    unsafe_surface_terms = (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "live",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_surface_terms)

    for cls in (
        ResearchSourceAuthorityEvidenceDecayRouterConfig,
        ResearchSourceAuthorityEvidenceDecayRouterPublicPayloadItem,
        ResearchSourceAuthorityEvidenceDecayRouterRow,
        ResearchSourceAuthorityEvidenceDecayRouterReport,
    ):
        for field in fields(cls):
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            lowered = field.name.lower()
            assert not any(term in lowered for term in unsafe_surface_terms)

    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_authority_evidence_decay_router_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_imports_or_calls = (
        "requests",
        "httpx",
        "urllib",
        "aiohttp",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
        "subprocess",
        "open(",
        "connect(",
    )
    assert all(term not in source for term in forbidden_imports_or_calls)


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


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
