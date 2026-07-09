from __future__ import annotations

import ast
import dataclasses
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
    "polymarket_alpha_lab."
    "research_source_scrapling_resolution_claim_quality_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_scrapling_resolution_claim_quality_report.py"
)
CONFIG_VERSION = "scrapling-resolution-claim-quality-report-v1"
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(minutes=30)
RAW_CASE_REFERENCE = (
    "candidate-42-market-id-slug-question-http://private.example/path?token=secret"
)
RAW_CAPTURE_REFERENCE = (
    "source-url:https://private.example/raw-text/table/wallet/order/trade"
)


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


def cfg(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": CONFIG_VERSION,
        "evidence_quality_weight": d("0.350000"),
        "resolution_alignment_weight": d("0.300000"),
        "authority_coverage_weight": d("0.200000"),
        "contradiction_pressure_weight": d("0.150000"),
        "watch_quality_score": d("0.700000"),
        "block_quality_score": d("0.400000"),
        "watch_staleness_hours": d("24.000000"),
        "block_staleness_hours": d("72.000000"),
        "watch_extraction_error_count": d("1"),
        "block_extraction_error_count": d("3"),
        "watch_missing_resolution_terms_count": d("1"),
        "block_missing_resolution_terms_count": d("2"),
        "watch_contradiction_pressure_score": d("0.350000"),
        "block_contradiction_pressure_score": d("0.700000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchSourceScraplingResolutionClaimQualityConfig(**values)


def sample(
    *,
    case_reference: str = RAW_CASE_REFERENCE,
    capture_reference: str = RAW_CAPTURE_REFERENCE,
    observed_at: datetime = OBSERVED_AT,
    evidence_quality_score: Decimal = d("0.900000"),
    resolution_alignment_score: Decimal = d("0.950000"),
    authority_coverage_score: Decimal = d("0.900000"),
    contradiction_pressure_score: Decimal = d("0.050000"),
    staleness_hours: Decimal = d("1.000000"),
    extraction_error_count: Decimal = d("0"),
    missing_resolution_terms_count: Decimal = d("0"),
    reason_codes: tuple[str, ...] = ("manual_reviewed",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchSourceScraplingResolutionClaimQualityInput(
        case_reference=case_reference,
        capture_reference=capture_reference,
        observed_at=observed_at,
        evidence_quality_score=evidence_quality_score,
        resolution_alignment_score=resolution_alignment_score,
        authority_coverage_score=authority_coverage_score,
        contradiction_pressure_score=contradiction_pressure_score,
        staleness_hours=staleness_hours,
        extraction_error_count=extraction_error_count,
        missing_resolution_terms_count=missing_resolution_terms_count,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, generated_at: datetime = GENERATED_AT, config: object | None = None):
    module = api()
    return module.build_research_source_scrapling_resolution_claim_quality_report(
        items,
        generated_at=generated_at,
        config=config or cfg(),
    )


def test_empty_input_returns_block_report_only_decimal_digest() -> None:
    module = api()
    built = report()

    assert is_dataclass(built)
    assert built.generated_at == GENERATED_AT
    assert built.config_version == CONFIG_VERSION
    assert built.status == "block"
    assert built.item_count == d("0")
    assert built.pass_count == d("0")
    assert built.watch_count == d("0")
    assert built.block_count == d("0")
    assert built.average_quality_score == d("0.000000")
    assert built.lowest_quality_score == d("0.000000")
    assert built.highest_contradiction_pressure_score == d("0.000000")
    assert built.rows == ()
    assert built.reason_codes == ("resolution_claim_quality_no_items",)
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True
    assert_decimal_public_fields(built)

    payload = module.research_source_scrapling_resolution_claim_quality_report_payload(
        built,
    )
    digest_value = (
        module.research_source_scrapling_resolution_claim_quality_report_digest(built)
    )
    assert payload["derived_validation_digest"] == digest_value
    assert len(digest_value) == 64
    int(digest_value, 16)
    assert_no_public_number_payload(payload)
    assert_no_forbidden_public_surface(payload)


def test_report_scores_resolution_claim_quality_and_sorts_deterministically() -> None:
    passed = sample(
        case_reference="pass-case-private-market-question",
        capture_reference="pass-capture-private-url",
        reason_codes=("verified_resolution",),
    )
    watched = sample(
        case_reference="watch-case-private-market-question",
        capture_reference="watch-capture-private-url",
        evidence_quality_score=d("0.700000"),
        resolution_alignment_score=d("0.650000"),
        authority_coverage_score=d("0.600000"),
        contradiction_pressure_score=d("0.200000"),
        staleness_hours=d("26.000000"),
        extraction_error_count=d("1"),
        reason_codes=("needs_review",),
    )
    blocked = sample(
        case_reference="block-case-private-market-question",
        capture_reference="block-capture-private-url",
        evidence_quality_score=d("0.200000"),
        resolution_alignment_score=d("0.300000"),
        authority_coverage_score=d("0.200000"),
        contradiction_pressure_score=d("0.800000"),
        staleness_hours=d("90.000000"),
        extraction_error_count=d("3"),
        missing_resolution_terms_count=d("2"),
        reason_codes=(),
    )

    built = report(passed, watched, blocked)
    reversed_built = report(blocked, watched, passed)

    assert built.status == "block"
    assert built.item_count == d("3")
    assert built.pass_count == d("1")
    assert built.watch_count == d("1")
    assert built.block_count == d("1")
    assert built.average_quality_score == d("0.610833")
    assert built.lowest_quality_score == d("0.230000")
    assert built.highest_contradiction_pressure_score == d("0.800000")
    assert built.rows == reversed_built.rows
    assert built.derived_validation_digest == reversed_built.derived_validation_digest
    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")

    blocked_row, watched_row, passed_row = built.rows
    assert blocked_row.quality_score == d("0.230000")
    assert blocked_row.reason_codes == (
        "authority_coverage_gap",
        "contradiction_pressure_high",
        "extraction_errors_block",
        "quality_score_block",
        "resolution_alignment_gap",
        "resolution_claim_quality_block",
        "resolution_terms_missing_block",
        "stale_capture_block",
    )
    assert watched_row.quality_score == d("0.680000")
    assert watched_row.reason_codes == (
        "extraction_errors_watch",
        "input_needs_review",
        "quality_score_watch",
        "resolution_claim_quality_watch",
        "stale_capture_watch",
    )
    assert passed_row.quality_score == d("0.922500")
    assert passed_row.reason_codes == (
        "input_verified_resolution",
        "resolution_claim_quality_pass",
    )
    assert built.reason_code_counts[0] == (
        "authority_coverage_gap",
        d("1"),
    )


def test_payload_is_public_safe_decimal_string_deterministic_and_digest_checked() -> None:
    module = api()
    built = report(
        sample(case_reference=RAW_CASE_REFERENCE, capture_reference=RAW_CAPTURE_REFERENCE),
        sample(
            case_reference="watch-private-market-slug-question",
            capture_reference="watch-private-url-token",
            evidence_quality_score=d("0.700000"),
            resolution_alignment_score=d("0.650000"),
            authority_coverage_score=d("0.600000"),
            contradiction_pressure_score=d("0.200000"),
            staleness_hours=d("26.000000"),
            extraction_error_count=d("1"),
            reason_codes=("needs_review",),
        ),
    )

    payload = built.payload
    encoded = json.dumps(payload, sort_keys=True)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest")
    expected_digest = hashlib.sha256(
        json.dumps(
            unsigned_payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()

    assert payload["item_count"] == "2.000000"
    assert payload["rows"][0]["status"] == "watch"
    assert payload["rows"][0]["quality_score"] == "0.680000"
    assert payload["rows"][1]["quality_score"] == "0.922500"
    assert payload["derived_validation_digest"] == built.derived_validation_digest
    assert module.research_source_scrapling_resolution_claim_quality_report_digest(
        built,
    ) == expected_digest
    assert RAW_CASE_REFERENCE not in encoded
    assert RAW_CAPTURE_REFERENCE not in encoded
    assert_no_public_number_payload(payload)
    assert_no_forbidden_public_surface(payload)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)

    tampered = dict(payload)
    tampered["item_count"] = "3.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_source_scrapling_resolution_claim_quality_public_payload(
            tampered,
        )

    unsafe_key_payload = dict(payload)
    for unsafe_key in (
        "market_slug",
        "source_text",
        "database_table",
        "authorization_header",
        "execution_file",
    ):
        candidate_payload = dict(unsafe_key_payload)
        candidate_payload[unsafe_key] = "redacted"
        with pytest.raises(ValueError, match="unsafe"):
            module.research_source_scrapling_resolution_claim_quality_report_payload(
                candidate_payload,
            )

    for unsafe_value in (
        "candidate-raw-market",
        "source text from http",
        "database persistence file",
        "wallet order execution",
        "recommendation sizing",
    ):
        unsafe_value_payload = dict(payload)
        unsafe_value_payload["rows"] = [
            dict(payload["rows"][0], case_digest=unsafe_value)
        ]
        with pytest.raises(ValueError, match="unsafe"):
            module.research_source_scrapling_resolution_claim_quality_report_payload(
                unsafe_value_payload,
            )


def test_public_payload_requires_exact_canonical_schema() -> None:
    module = api()
    payload = report(sample()).payload

    def resign(candidate: dict[str, Any]) -> dict[str, Any]:
        unsigned = dict(candidate)
        unsigned.pop("derived_validation_digest", None)
        candidate["derived_validation_digest"] = hashlib.sha256(
            json.dumps(
                unsigned,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8"),
        ).hexdigest()
        return candidate

    extra_top_level = dict(payload)
    extra_top_level["safe_extension"] = "ok"

    missing_top_level = dict(payload)
    missing_top_level.pop("highest_contradiction_pressure_score")

    extra_row = json.loads(json.dumps(payload))
    extra_row["rows"][0]["safe_extension"] = "ok"

    tuple_rows = dict(payload)
    tuple_rows["rows"] = tuple(payload["rows"])

    noncanonical_decimal = dict(payload)
    noncanonical_decimal["item_count"] = "1"

    invalid_datetime = dict(payload)
    invalid_datetime["generated_at"] = "not-a-datetime"

    for candidate in (
        extra_top_level,
        missing_top_level,
        extra_row,
        tuple_rows,
        noncanonical_decimal,
        invalid_datetime,
    ):
        with pytest.raises(ValueError, match="public payload"):
            module.validate_research_source_scrapling_resolution_claim_quality_public_payload(
                resign(candidate),
            )


def test_strict_validation_rejects_bad_types_times_counts_statuses_and_flags() -> None:
    module = api()
    with pytest.raises(ValueError, match="evidence_quality_score must be exactly Decimal"):
        sample(evidence_quality_score=_DecimalSubclass("0.900000"))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="resolution_alignment_score must be a Decimal"):
        sample(resolution_alignment_score=0.9)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        sample(observed_at=datetime(2026, 7, 9, 11, 30))

    with pytest.raises(ValueError, match="observed_at must be exactly datetime"):
        sample(
            observed_at=_DatetimeSubclass(2026, 7, 9, 11, 30, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="utcoffset"):
        sample(observed_at=datetime(2026, 7, 9, 11, 30, tzinfo=_NoneOffsetTz()))

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report(
            sample(),
            generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(sample(observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="extraction_error_count"):
        sample(extraction_error_count=d("1.5"))

    with pytest.raises(ValueError, match="missing_resolution_terms_count"):
        sample(missing_resolution_terms_count=d("-1"))

    with pytest.raises(ValueError, match="quality weights"):
        cfg(contradiction_pressure_weight=d("0.250000"))

    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        sample(report_only=False)

    built = report(sample())
    with pytest.raises(ValueError, match="status"):
        replace(built.rows[0], status="blocked")

    with pytest.raises(ValueError, match="reason_code contains unsafe text"):
        sample(reason_codes=("market_slug",))

    with pytest.raises(ValueError, match="config_version"):
        module.ResearchSourceScraplingResolutionClaimQualityConfig(
            config_version="other",
        )


def test_dataclasses_are_frozen_reject_subclassing_and_export_only_allowed_statuses() -> None:
    module = api()
    config = cfg()
    item = sample()
    built = report(item)

    assert module.RESEARCH_SOURCE_SCRAPLING_RESOLUTION_CLAIM_QUALITY_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert dataclasses.is_dataclass(config)
    assert dataclasses.is_dataclass(item)

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        built.rows[0].quality_score = d("0")  # type: ignore[misc]

    with pytest.raises(TypeError, match="does not support subclassing"):

        class ConfigSubclass(module.ResearchSourceScraplingResolutionClaimQualityConfig):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class InputSubclass(module.ResearchSourceScraplingResolutionClaimQualityInput):
            pass


def test_static_module_has_no_db_network_wallet_order_or_live_surfaces() -> None:
    module = api()
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
        "py_clob_client",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "executemany",
        "open",
        "request",
        "post",
        "put",
        "patch",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports

    for cls in (
        module.ResearchSourceScraplingResolutionClaimQualityRow,
        module.ResearchSourceScraplingResolutionClaimQualityReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert "candidate" not in lowered
            assert "market_id" not in lowered
            assert "slug" not in lowered
            assert "question" not in lowered
            assert "url" not in lowered
            assert "text" not in lowered
            assert "dsn" not in lowered
            assert "table" not in lowered
            assert "token" not in lowered
            assert "wallet" not in lowered
            assert "order" not in lowered
            assert "trade" not in lowered
            assert "sizing" not in lowered
            assert "recommend" not in lowered
            assert "live" not in lowered

    public_names = set(module.__all__)
    forbidden_public_name_fragments = {
        "client",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "recommend",
        "sizing",
        "live",
    }
    for name in public_names:
        lowered = name.lower()
        assert not any(fragment in lowered for fragment in forbidden_public_name_fragments)


def assert_decimal_public_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {"rows", "reason_codes", "reason_code_counts"}:
            continue
        if any(
            marker in field.name
            for marker in (
                "count",
                "score",
                "hours",
                "quality",
                "pressure",
            )
        ):
            assert type(getattr(value, field.name)) is Decimal, field.name


def assert_no_public_number_payload(value: Any) -> None:
    if type(value) in (float, int) or isinstance(value, Decimal):
        raise AssertionError(f"payload numeric was not serialized as string: {value!r}")
    if isinstance(value, dict):
        for item_value in value.values():
            assert_no_public_number_payload(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_public_number_payload(item_value)


def assert_no_forbidden_public_surface(value: Any) -> None:
    forbidden_fragments = (
        "raw",
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "text",
        "url",
        "http",
        "api_key",
        "private_key",
        "credential",
        "secret",
        "auth_",
        "auth-",
        "authorization",
        "dsn",
        "table",
        "token",
        "database",
        "network",
        "persist",
        "persistence",
        "file",
        "wallet",
        "order",
        "trade",
        "live",
        "execute",
        "execution",
        "recommend",
        "recommendation",
        "position",
        "sizing",
    )
    if isinstance(value, dict):
        for key, item_value in value.items():
            lowered_key = key.lower()
            for fragment in forbidden_fragments:
                assert fragment not in lowered_key, key
            assert_no_forbidden_public_surface(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_forbidden_public_surface(item_value)
        return
    if type(value) is str:
        lowered_value = value.lower()
        for fragment in forbidden_fragments:
            assert fragment not in lowered_value, value
