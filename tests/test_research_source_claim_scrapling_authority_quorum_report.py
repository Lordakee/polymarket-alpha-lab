from __future__ import annotations

import ast
import copy
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_source_claim_scrapling_authority_quorum_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_claim_scrapling_authority_quorum_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
COLLECTED_AT = datetime(2026, 7, 9, 11, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "min_authority_quorum_count": d("3.000000"),
        "quorum_pass_ratio": d("1.000000"),
        "quorum_watch_ratio": d("0.750000"),
        "quorum_block_ratio": d("0.333333"),
        "agreement_pass_ratio": d("0.800000"),
        "agreement_watch_ratio": d("0.600000"),
        "agreement_block_ratio": d("0.400000"),
        "parse_confidence_pass_ratio": d("0.850000"),
        "parse_confidence_watch_ratio": d("0.650000"),
        "parse_confidence_block_ratio": d("0.450000"),
        "field_completeness_pass_ratio": d("0.900000"),
        "field_completeness_watch_ratio": d("0.600000"),
        "field_completeness_block_ratio": d("0.400000"),
        "fresh_capture_max_age_seconds": d("3600.000000"),
        "stale_capture_block_age_seconds": d("86400.000000"),
        "min_pass_quorum_score": d("0.800000"),
        "min_watch_quorum_score": d("0.500000"),
        "quorum_weight": d("0.350000"),
        "agreement_weight": d("0.250000"),
        "parse_confidence_weight": d("0.200000"),
        "field_completeness_weight": d("0.100000"),
        "freshness_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchSourceClaimScraplingAuthorityQuorumConfig(**values)


def quorum_input(
    private_claim_ref: str = "private-claim-ref",
    *,
    authority_bucket: str = "official",
    collected_at: datetime = COLLECTED_AT,
    authority_evidence_count: Decimal = d("3"),
    independent_authority_count: Decimal = d("3"),
    agreeing_authority_count: Decimal = d("3"),
    dissenting_authority_count: Decimal = d("0"),
    scrapling_parse_confidence_ratio: Decimal = d("0.950000"),
    scrapling_field_completeness_ratio: Decimal = d("1.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceClaimScraplingAuthorityQuorumInput(
        private_claim_ref=private_claim_ref,
        authority_bucket=authority_bucket,
        collected_at=collected_at,
        authority_evidence_count=authority_evidence_count,
        independent_authority_count=independent_authority_count,
        agreeing_authority_count=agreeing_authority_count,
        dissenting_authority_count=dissenting_authority_count,
        scrapling_parse_confidence_ratio=scrapling_parse_confidence_ratio,
        scrapling_field_completeness_ratio=scrapling_field_completeness_ratio,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: object, cfg: object | None = None) -> Any:
    module = api()
    return module.build_research_source_claim_scrapling_authority_quorum_report(
        items,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def resign_payload(payload: dict[str, Any]) -> None:
    payload["derived_validation_digest"] = canonical_digest(payload)


def walk_public(value: object) -> list[object]:
    values = [value]
    if type(value) is dict:
        for key, item in value.items():
            values.extend(walk_public(key))
            values.extend(walk_public(item))
    elif type(value) is list:
        for item in value:
            values.extend(walk_public(item))
    return values


def assert_payload_has_no_raw_numbers(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"payload leaked raw numeric value {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_payload_has_no_raw_numbers(item)
    elif type(value) is list:
        for item in value:
            assert_payload_has_no_raw_numbers(item)


def assert_payload_has_no_private_surface(payload: dict[str, Any]) -> None:
    rendered = [str(value).casefold() for value in walk_public(payload)]
    forbidden = (
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "raw_url",
        "raw_text",
        "https://",
        "postgres://",
        "dsn",
        "table",
        "token",
        "wallet",
        "private_key",
        "live_trading",
        "sizing",
        "recommendation",
    )
    for fragment in forbidden:
        assert all(fragment not in value for value in rendered), fragment


def assert_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        assert type(value) is Decimal
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric was not Decimal: {value!r}")
    if type(value) is tuple:
        for item in value:
            assert_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            assert_decimal_public_numbers(getattr(value, field.name))


def test_empty_report_blocks_with_report_only_flags_and_digest_payload() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchSourceClaimScraplingAuthorityQuorumReport
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.input_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.attention_count == d("0.000000")
    assert report.average_authority_quorum_score == d("0.000000")
    assert report.lowest_authority_quorum_ratio == d("0.000000")
    assert report.lowest_authority_agreement_ratio == d("0.000000")
    assert report.highest_quorum_risk_score == d("0.000000")
    assert report.max_collection_age_seconds == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("claim_scrapling_authority_quorum_no_inputs",)
    assert report.reason_code_counts == (
        module.ResearchSourceClaimScraplingAuthorityQuorumReasonCodeCount(
            reason_code="claim_scrapling_authority_quorum_no_inputs",
            count=d("1.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert_decimal_public_numbers(report)

    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]

    payload = report.payload
    assert payload["status"] == "block"
    assert payload["rows"] == []
    assert payload["input_count"] == "0.000000"
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert module.research_source_claim_scrapling_authority_quorum_report_digest(
        report,
    ) == payload["derived_validation_digest"]
    assert module.validate_research_source_claim_scrapling_authority_quorum_public_payload(
        payload,
    )
    assert_payload_has_no_raw_numbers(payload)
    assert_payload_has_no_private_surface(payload)


def test_report_scores_pass_watch_and_block_authority_quorum_rows() -> None:
    report = build_report(
        quorum_input("pass-private-claim"),
        quorum_input(
            "watch-private-claim",
            authority_bucket="regional_crosscheck",
            collected_at=GENERATED_AT - timedelta(seconds=7200),
            authority_evidence_count=d("3"),
            independent_authority_count=d("2"),
            agreeing_authority_count=d("2"),
            dissenting_authority_count=d("1"),
            scrapling_parse_confidence_ratio=d("0.700000"),
            scrapling_field_completeness_ratio=d("0.800000"),
        ),
        quorum_input(
            "block-private-claim",
            authority_bucket="thin_scrape",
            collected_at=GENERATED_AT - timedelta(seconds=90000),
            authority_evidence_count=d("0"),
            independent_authority_count=d("0"),
            agreeing_authority_count=d("0"),
            dissenting_authority_count=d("0"),
            scrapling_parse_confidence_ratio=d("0.300000"),
            scrapling_field_completeness_ratio=d("0.200000"),
        ),
    )

    assert report.status == "block"
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.attention_count == d("2.000000")
    assert report.average_authority_quorum_score == d("0.595217")
    assert report.lowest_authority_quorum_ratio == d("0.000000")
    assert report.lowest_authority_agreement_ratio == d("0.000000")
    assert report.highest_quorum_risk_score == d("0.920000")
    assert report.max_collection_age_seconds == d("90000.000000")
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")

    blocked = report.rows[0]
    assert blocked.authority_bucket == "thin_scrape"
    assert blocked.collection_age_seconds == d("90000.000000")
    assert blocked.authority_quorum_ratio == d("0.000000")
    assert blocked.authority_agreement_ratio == d("0.000000")
    assert blocked.freshness_score == d("0.000000")
    assert blocked.authority_quorum_score == d("0.080000")
    assert blocked.quorum_risk_score == d("0.920000")
    assert blocked.reason_codes == (
        "claim_scrapling_authority_quorum_insufficient_authority_block",
        "claim_scrapling_authority_quorum_low_agreement_block",
        "claim_scrapling_authority_quorum_parse_confidence_block",
        "claim_scrapling_authority_quorum_field_completeness_block",
        "claim_scrapling_authority_quorum_stale_capture_block",
        "claim_scrapling_authority_quorum_score_block",
    )

    watched = report.rows[1]
    assert watched.authority_bucket == "regional_crosscheck"
    assert watched.collection_age_seconds == d("7200.000000")
    assert watched.authority_quorum_ratio == d("0.666667")
    assert watched.authority_agreement_ratio == d("0.666667")
    assert watched.freshness_score == d("0.956522")
    assert watched.authority_quorum_score == d("0.715652")
    assert watched.quorum_risk_score == d("0.284348")
    assert watched.reason_codes == (
        "claim_scrapling_authority_quorum_insufficient_authority_watch",
        "claim_scrapling_authority_quorum_low_agreement_watch",
        "claim_scrapling_authority_quorum_parse_confidence_watch",
        "claim_scrapling_authority_quorum_field_completeness_watch",
        "claim_scrapling_authority_quorum_stale_capture_watch",
        "claim_scrapling_authority_quorum_score_watch",
    )

    passed = report.rows[2]
    assert passed.authority_quorum_score == d("0.990000")
    assert passed.quorum_risk_score == d("0.010000")
    assert passed.reason_codes == ("claim_scrapling_authority_quorum_clear",)
    assert report.reason_codes == (
        "claim_scrapling_authority_quorum_insufficient_authority_block",
        "claim_scrapling_authority_quorum_low_agreement_block",
        "claim_scrapling_authority_quorum_parse_confidence_block",
        "claim_scrapling_authority_quorum_field_completeness_block",
        "claim_scrapling_authority_quorum_stale_capture_block",
        "claim_scrapling_authority_quorum_score_block",
        "claim_scrapling_authority_quorum_insufficient_authority_watch",
        "claim_scrapling_authority_quorum_low_agreement_watch",
        "claim_scrapling_authority_quorum_parse_confidence_watch",
        "claim_scrapling_authority_quorum_field_completeness_watch",
        "claim_scrapling_authority_quorum_stale_capture_watch",
        "claim_scrapling_authority_quorum_score_watch",
        "claim_scrapling_authority_quorum_clear",
    )


def test_quorum_ratio_below_pass_threshold_is_watch() -> None:
    report = build_report(
        quorum_input(
            "below-pass-quorum-private-claim",
            authority_evidence_count=d("4"),
            independent_authority_count=d("4"),
            agreeing_authority_count=d("4"),
            dissenting_authority_count=d("0"),
        ),
        cfg=config(min_authority_quorum_count=d("5.000000")),
    )

    assert report.status == "watch"
    assert report.rows[0].authority_quorum_ratio == d("0.800000")
    assert report.rows[0].authority_quorum_score == d("0.920000")
    assert report.rows[0].reason_codes == (
        "claim_scrapling_authority_quorum_insufficient_authority_watch",
    )


def test_public_payload_is_deterministic_redacted_and_digest_validated() -> None:
    module = api()
    raw_private_ref = (
        "https://private.example/raw_candidate?market_id=abc&source_url=secret"
    )
    report_a = build_report(
        quorum_input(raw_private_ref, authority_bucket="official"),
        quorum_input(
            "block-private-claim",
            authority_bucket="thin_scrape",
            collected_at=GENERATED_AT - timedelta(seconds=90000),
            authority_evidence_count=d("0"),
            independent_authority_count=d("0"),
            agreeing_authority_count=d("0"),
            dissenting_authority_count=d("0"),
            scrapling_parse_confidence_ratio=d("0.300000"),
            scrapling_field_completeness_ratio=d("0.200000"),
        ),
    )
    report_b = build_report(
        quorum_input(
            "block-private-claim",
            authority_bucket="thin_scrape",
            collected_at=GENERATED_AT - timedelta(seconds=90000),
            authority_evidence_count=d("0"),
            independent_authority_count=d("0"),
            agreeing_authority_count=d("0"),
            dissenting_authority_count=d("0"),
            scrapling_parse_confidence_ratio=d("0.300000"),
            scrapling_field_completeness_ratio=d("0.200000"),
        ),
        quorum_input(raw_private_ref, authority_bucket="official"),
    )

    payload_a = module.research_source_claim_scrapling_authority_quorum_report_payload(
        report_a,
    )
    payload_b = module.research_source_claim_scrapling_authority_quorum_report_payload(
        report_b,
    )
    digest_a = module.research_source_claim_scrapling_authority_quorum_report_digest(
        report_a,
    )
    digest_b = module.research_source_claim_scrapling_authority_quorum_report_digest(
        report_b,
    )

    assert payload_a == payload_b
    assert digest_a == digest_b
    assert payload_a["derived_validation_digest"] == digest_a
    assert payload_a["derived_validation_digest"] == canonical_digest(payload_a)
    assert len(digest_a) == 64
    int(digest_a, 16)
    assert raw_private_ref not in json.dumps(payload_a, sort_keys=True)
    assert payload_a["rows"][0]["public_claim_ref"].startswith("claim-")
    assert module.validate_research_source_claim_scrapling_authority_quorum_report_digest(
        report_a,
    )
    assert module.validate_research_source_claim_scrapling_authority_quorum_public_payload(
        payload_a,
    )
    assert_payload_has_no_private_surface(payload_a)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, derived_validation_digest="0" * 64)
    tampered = dict(payload_a)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_source_claim_scrapling_authority_quorum_public_payload(
            tampered,
        )


def test_public_payload_rejects_private_identifier_and_secret_surfaces() -> None:
    module = api()
    payload = build_report(quorum_input("private-claim")).payload

    for unsafe_key, unsafe_value in (
        ("source_url", "https://example.test/private"),
        ("source_text", "raw_text: settlement details"),
        ("raw_candidate", "candidate_id=123"),
        ("market_id", "market_slug=abc"),
        ("dsn", "postgres://example"),
        ("table", "private_rows"),
        ("token", "token-secret"),
        ("wallet", "wallet-secret"),
        ("private_key", "secret"),
        ("live_trading", "enabled"),
        ("sizing", "100"),
        ("recommendation", "buy"),
    ):
        tampered = dict(payload)
        tampered[unsafe_key] = unsafe_value
        tampered["derived_validation_digest"] = canonical_digest(tampered)
        with pytest.raises(ValueError, match="unsafe private surface"):
            module.validate_research_source_claim_scrapling_authority_quorum_public_payload(
                tampered,
            )


def test_public_payload_validator_rejects_schema_drift_with_valid_digest() -> None:
    module = api()
    payload = build_report(quorum_input("private-claim")).payload

    extra_top_level = copy.deepcopy(payload)
    extra_top_level["unexpected_safe_key"] = "safe"
    resign_payload(extra_top_level)
    with pytest.raises(ValueError, match="payload schema"):
        module.validate_research_source_claim_scrapling_authority_quorum_public_payload(
            extra_top_level,
        )

    extra_row_field = copy.deepcopy(payload)
    extra_row_field["rows"][0]["unexpected_safe_key"] = "safe"
    resign_payload(extra_row_field)
    with pytest.raises(ValueError, match="row schema"):
        module.validate_research_source_claim_scrapling_authority_quorum_public_payload(
            extra_row_field,
        )

    missing_reason_count = copy.deepcopy(payload)
    del missing_reason_count["reason_code_counts"][0]["count"]
    resign_payload(missing_reason_count)
    with pytest.raises(ValueError, match="reason_code_count schema"):
        module.validate_research_source_claim_scrapling_authority_quorum_public_payload(
            missing_reason_count,
        )

    duplicate_reason_codes = copy.deepcopy(payload)
    duplicate_reason_codes["reason_codes"] = [
        "claim_scrapling_authority_quorum_clear",
        "claim_scrapling_authority_quorum_clear",
    ]
    resign_payload(duplicate_reason_codes)
    with pytest.raises(ValueError, match="reason_codes"):
        module.validate_research_source_claim_scrapling_authority_quorum_public_payload(
            duplicate_reason_codes,
        )


def test_decimal_only_status_flags_and_input_validation() -> None:
    module = api()
    assert module.STATUSES == ("pass", "watch", "block")

    with pytest.raises(ValueError, match="Decimal"):
        quorum_input(authority_evidence_count=3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        quorum_input(scrapling_parse_confidence_ratio=_DecimalSubclass("0.9"))
    with pytest.raises(ValueError, match="whole Decimal"):
        quorum_input(authority_evidence_count=d("1.5"))
    with pytest.raises(ValueError, match="between 0 and 1"):
        quorum_input(scrapling_field_completeness_ratio=d("1.1"))
    with pytest.raises(ValueError, match="must not exceed"):
        quorum_input(
            authority_evidence_count=d("1"),
            independent_authority_count=d("2"),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        quorum_input(collected_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="datetime"):
        quorum_input(
            collected_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        quorum_input(collected_at=datetime(2026, 7, 9, 12, 0, tzinfo=_NoneOffsetTz()))
    with pytest.raises(ValueError, match="paper_only"):
        quorum_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        quorum_input(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        quorum_input(readonly=False)
    with pytest.raises(ValueError, match="public identifier"):
        quorum_input(authority_bucket="https://private.example/source_url")
    with pytest.raises(ValueError, match="after generated_at"):
        build_report(quorum_input(collected_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="one of"):
        replace(build_report(quorum_input()).rows[0], status="blocked")


def test_config_report_consistency_and_hard_flag_validation() -> None:
    module = api()

    with pytest.raises(ValueError, match="weights must sum to 1"):
        config(quorum_weight=d("0.360000"))
    with pytest.raises(ValueError, match="pass >= watch >= block"):
        config(agreement_watch_ratio=d("0.900000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)

    report = build_report(quorum_input())
    with pytest.raises(ValueError, match="input_count"):
        replace(report, input_count=d("2.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report, reason_codes=("claim_scrapling_authority_quorum_no_inputs",))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="watch")

    with pytest.raises(TypeError):
        type(
            "BadConfig",
            (module.ResearchSourceClaimScraplingAuthorityQuorumConfig,),
            {},
        )
    with pytest.raises(TypeError):
        type(
            "BadInput",
            (module.ResearchSourceClaimScraplingAuthorityQuorumInput,),
            {},
        )


def test_module_has_no_external_side_effect_or_execution_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_import_roots = {
        "ccxt",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "supabase",
        "urllib",
        "web3",
    }
    forbidden_call_names = {
        "connect",
        "create_engine",
        "execute",
        "open",
        "place_order",
        "request",
        "send",
        "urlopen",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names

    source = MODULE_PATH.read_text().casefold()
    for forbidden_surface in (
        "wallet",
        "live_trading",
        "position_sizing",
        "trade_recommendation",
        "place_order",
    ):
        assert forbidden_surface not in source
