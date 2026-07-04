from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.market_research_policy_judicial_stay_expiration_digest"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_policy_judicial_stay_expiration_digest.py",
)
GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
_UNSET = object()


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def test_policy_judicial_stay_expiration_digest_public_api_exists() -> None:
    assert importlib.util.find_spec(MODULE_NAME) is not None


def test_policy_judicial_stay_expiration_digest_reduces_rows_deterministically() -> None:
    digest = digest_module()

    summary = report(
        digest,
        (
            input_row(
                digest,
                "research.stay-expiration.scotus-election",
                condition_id="condition_scotus_election",
                court_key="scotus",
                jurisdiction_key="us",
                docket_key="24a-election",
                case_title="election-procedure-challenge",
                policy_domain="elections",
                public_expiration_reference=(
                    "https://court.example/stay-expiration?case=sealed-123"
                ),
                stay_expires_at=GENERATED_AT + timedelta(hours=6),
                last_checked_at=GENERATED_AT - timedelta(hours=4),
                acknowledged_at=None,
                source_count=d("1.000000"),
                policy_impact_score=d("0.880000"),
                extension_probability_score=d("0.720000"),
                market_relevance_score=d("0.760000"),
                expiration_config_version="judicial-stay-expiration-v1",
            ),
            input_row(
                digest,
                "research.stay-expiration.ca5-energy",
                condition_id="condition_ca5_energy",
                court_key="ca5",
                jurisdiction_key="us",
                docket_key="25-1001",
                case_title="energy-rule-appeal",
                policy_domain="energy",
                public_expiration_reference="sealed-stay-expiration-feed",
                stay_expires_at=GENERATED_AT + timedelta(hours=30),
                last_checked_at=GENERATED_AT - timedelta(hours=3),
                acknowledged_at=GENERATED_AT - timedelta(hours=1),
                source_count=d("2.000000"),
                policy_impact_score=d("0.620000"),
                extension_probability_score=d("0.580000"),
                market_relevance_score=d("0.610000"),
                expiration_config_version="judicial-stay-expiration-v1",
            ),
            input_row(
                digest,
                "research.stay-expiration.state-tax",
                condition_id="condition_state_tax",
                court_key="ny-court-appeals",
                jurisdiction_key="ny",
                docket_key="tax-2026-07",
                case_title="state-tax-guidance",
                policy_domain="tax",
                public_expiration_reference="public-state-court-stay-expiration",
                stay_expires_at=GENERATED_AT + timedelta(days=4),
                last_checked_at=GENERATED_AT - timedelta(minutes=30),
                acknowledged_at=GENERATED_AT - timedelta(minutes=15),
                source_count=d("3.000000"),
                policy_impact_score=d("0.200000"),
                extension_probability_score=d("0.300000"),
                market_relevance_score=d("0.210000"),
                expiration_config_version="judicial-stay-expiration-v0",
            ),
            input_row(
                digest,
                "research.stay-expiration.old-health",
                condition_id="condition_health",
                court_key="dc-circuit",
                jurisdiction_key="us",
                docket_key="health-2026",
                case_title="health-rule-remand",
                policy_domain="health",
                public_expiration_reference="public-dc-circuit-stay-expiration",
                stay_expires_at=GENERATED_AT - timedelta(hours=2),
                last_checked_at=GENERATED_AT - timedelta(hours=28),
                acknowledged_at=GENERATED_AT - timedelta(hours=5),
                source_count=d("2.000000"),
                policy_impact_score=d("0.100000"),
                extension_probability_score=d("0.700000"),
                market_relevance_score=d("0.180000"),
                expiration_config_version="judicial-stay-expiration-v2",
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        digest.DEFAULT_MARKET_RESEARCH_POLICY_JUDICIAL_STAY_EXPIRATION_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_policy_judicial_stay_expiration_digest"
    )
    assert summary.expiration_count == d("4.000000")
    assert summary.ready_expiration_count == d("1.000000")
    assert summary.watch_expiration_count == d("1.000000")
    assert summary.blocked_expiration_count == d("2.000000")
    assert summary.high_policy_impact_count == d("2.000000")
    assert summary.high_extension_probability_count == d("2.000000")
    assert summary.high_market_relevance_count == d("2.000000")
    assert summary.near_term_expiration_count == d("2.000000")
    assert summary.stale_status_check_count == d("1.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.missing_acknowledgement_count == d("1.000000")
    assert summary.expired_stay_count == d("1.000000")
    assert summary.average_policy_impact_score == d("0.450000")
    assert summary.average_extension_probability_score == d("0.575000")
    assert summary.average_market_relevance_score == d("0.440000")
    assert summary.average_source_count == d("2.000000")
    assert summary.minimum_seconds_until_expiration == d("-7200.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.court_key, row.research_key) for row in summary.rows) == (
        ("scotus", "research.stay-expiration.scotus-election"),
        ("dc-circuit", "research.stay-expiration.old-health"),
        ("ca5", "research.stay-expiration.ca5-energy"),
        ("ny-court-appeals", "research.stay-expiration.state-tax"),
    )

    scotus = summary.rows[0]
    assert scotus.expiration_status == "blocked"
    assert scotus.seconds_until_expiration == d("21600.000000")
    assert scotus.status_check_age_seconds == d("14400.000000")
    assert scotus.acknowledgement_lag_seconds is None
    assert scotus.redacted_public_expiration_reference == redacted(
        "https://court.example/stay-expiration?case=sealed-123",
    )
    assert scotus.reason_codes == (
        "market_research_policy_judicial_stay_expiration_digest_high_policy_impact",
        "market_research_policy_judicial_stay_expiration_digest_high_extension_probability",
        "market_research_policy_judicial_stay_expiration_digest_high_market_relevance",
        "market_research_policy_judicial_stay_expiration_digest_near_term_expiration",
        "market_research_policy_judicial_stay_expiration_digest_thin_sources",
        "market_research_policy_judicial_stay_expiration_digest_missing_acknowledgement",
    )

    old_health = summary.rows[1]
    assert old_health.expiration_status == "blocked"
    assert old_health.seconds_until_expiration == d("-7200.000000")
    assert old_health.status_check_age_seconds == d("100800.000000")
    assert old_health.acknowledgement_lag_seconds == d("82800.000000")
    assert old_health.reason_codes == (
        "market_research_policy_judicial_stay_expiration_digest_high_extension_probability",
        "market_research_policy_judicial_stay_expiration_digest_stale_status_check",
        "market_research_policy_judicial_stay_expiration_digest_expired_stay",
    )

    ca5 = summary.rows[2]
    assert ca5.expiration_status == "watch"
    assert ca5.seconds_until_expiration == d("108000.000000")
    assert ca5.acknowledgement_lag_seconds == d("7200.000000")
    assert ca5.redacted_public_expiration_reference == redacted(
        "sealed-stay-expiration-feed",
    )
    assert ca5.reason_codes == (
        "market_research_policy_judicial_stay_expiration_digest_high_policy_impact",
        "market_research_policy_judicial_stay_expiration_digest_high_market_relevance",
        "market_research_policy_judicial_stay_expiration_digest_near_term_expiration",
    )

    state_tax = summary.rows[3]
    assert state_tax.expiration_status == "ready"
    assert state_tax.reason_codes == (
        "market_research_policy_judicial_stay_expiration_digest_ready",
    )

    assert summary.reason_code_counts == (
        digest.MarketResearchPolicyJudicialStayExpirationDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_judicial_stay_expiration_digest_high_policy_impact"
            ),
            count=d("2.000000"),
            expiration_ratio=d("0.500000"),
        ),
        digest.MarketResearchPolicyJudicialStayExpirationDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_judicial_stay_expiration_digest_high_extension_probability"
            ),
            count=d("2.000000"),
            expiration_ratio=d("0.500000"),
        ),
        digest.MarketResearchPolicyJudicialStayExpirationDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_judicial_stay_expiration_digest_high_market_relevance"
            ),
            count=d("2.000000"),
            expiration_ratio=d("0.500000"),
        ),
        digest.MarketResearchPolicyJudicialStayExpirationDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_judicial_stay_expiration_digest_near_term_expiration"
            ),
            count=d("2.000000"),
            expiration_ratio=d("0.500000"),
        ),
        digest.MarketResearchPolicyJudicialStayExpirationDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_judicial_stay_expiration_digest_stale_status_check"
            ),
            count=d("1.000000"),
            expiration_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyJudicialStayExpirationDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_judicial_stay_expiration_digest_thin_sources"
            ),
            count=d("1.000000"),
            expiration_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyJudicialStayExpirationDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_judicial_stay_expiration_digest_missing_acknowledgement"
            ),
            count=d("1.000000"),
            expiration_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyJudicialStayExpirationDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_judicial_stay_expiration_digest_expired_stay"
            ),
            count=d("1.000000"),
            expiration_ratio=d("0.250000"),
        ),
        digest.MarketResearchPolicyJudicialStayExpirationDigestReasonCodeCount(
            reason_code="market_research_policy_judicial_stay_expiration_digest_ready",
            count=d("1.000000"),
            expiration_ratio=d("0.250000"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )
    assert summary.expiration_config_versions == (
        ("ca5", "judicial-stay-expiration-v1"),
        ("dc-circuit", "judicial-stay-expiration-v2"),
        ("ny-court-appeals", "judicial-stay-expiration-v0"),
        ("scotus", "judicial-stay-expiration-v1"),
    )

    public = repr(asdict(summary)).lower()
    for token in (
        "sealed-123",
        "court.example",
        "https://",
        "sealed-stay-expiration-feed",
        "auth",
        "wallet",
        "account",
        "network",
        "database",
        "secret",
        "private",
    ):
        assert token not in public


def test_empty_policy_judicial_stay_expiration_digest_is_blocked_and_report_only() -> None:
    digest = digest_module()
    summary = report(digest, ())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_policy_judicial_stay_expiration_digest"
    )
    assert summary.expiration_count == ZERO
    assert summary.ready_expiration_count == ZERO
    assert summary.watch_expiration_count == ZERO
    assert summary.blocked_expiration_count == ZERO
    assert summary.average_policy_impact_score == ZERO
    assert summary.average_extension_probability_score == ZERO
    assert summary.average_market_relevance_score == ZERO
    assert summary.average_source_count == ZERO
    assert summary.minimum_seconds_until_expiration == ZERO
    assert summary.rows == ()
    assert summary.expiration_config_versions == ()
    assert summary.reason_code_counts == (
        digest.MarketResearchPolicyJudicialStayExpirationDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_judicial_stay_expiration_digest_no_inputs"
            ),
            count=d("1.000000"),
            expiration_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_policy_judicial_stay_expiration_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_policy_judicial_stay_expiration_digest_payload_uses_decimal_strings() -> None:
    digest = digest_module()
    summary = report(digest, (input_row(digest),))
    payload = digest.market_research_policy_judicial_stay_expiration_digest_payload(
        summary,
    )
    json.dumps(payload, sort_keys=True)

    assert payload["expiration_count"] == "1.000000"
    assert payload["average_policy_impact_score"] == "0.200000"
    assert payload["rows"][0]["source_count"] == "3.000000"
    assert payload["rows"][0]["seconds_until_expiration"] == "345600.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "'public_expiration_reference':" not in repr(payload)
    assert "private" not in repr(payload).lower()


def test_policy_judicial_stay_expiration_digest_validates_contracts_and_flags() -> None:
    digest = digest_module()

    assert (
        digest.MarketResearchPolicyJudicialStayExpirationDigestConfig
        .__dataclass_params__
        .frozen
    )
    assert (
        digest.MarketResearchPolicyJudicialStayExpirationDigestInputRow
        .__dataclass_params__
        .frozen
    )
    assert (
        digest.MarketResearchPolicyJudicialStayExpirationDigestRow
        .__dataclass_params__
        .frozen
    )
    assert (
        digest.MarketResearchPolicyJudicialStayExpirationDigestReport
        .__dataclass_params__
        .frozen
    )

    summary = report(digest, (input_row(digest),))
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].source_count = d("4.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(digest, config_version=_StringSubclass("judicial-stay-expiration-v0"))
    with pytest.raises(ValueError, match="near_term_expiration_seconds"):
        config(digest, near_term_expiration_seconds=_DecimalSubclass("172800.000000"))
    with pytest.raises(ValueError, match="high_policy_impact_threshold"):
        config(digest, high_policy_impact_threshold=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="research_key"):
        input_row(digest, research_key=" bad")
    with pytest.raises(ValueError, match="case_title"):
        input_row(digest, case_title="private-docket-title")
    with pytest.raises(ValueError, match="stay_expires_at"):
        input_row(digest, stay_expires_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="last_checked_at"):
        input_row(
            digest,
            last_checked_at=_DateTimeSubclass(2026, 7, 4, 11, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="source_count"):
        input_row(digest, source_count=Decimal("1.5"))
    with pytest.raises(ValueError, match="policy_impact_score"):
        input_row(digest, policy_impact_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="extension_probability_score"):
        input_row(digest, extension_probability_score=d("1.000001"))
    with pytest.raises(ValueError, match="market_relevance_score"):
        input_row(digest, market_relevance_score=d("-0.000001"))
    with pytest.raises(ValueError, match="future"):
        report(
            digest,
            (input_row(digest, last_checked_at=GENERATED_AT + timedelta(seconds=1)),),
        )
    with pytest.raises(ValueError, match="paper_only"):
        input_row(digest, paper_only=False)
    with pytest.raises(ValueError, match="config"):
        digest.build_market_research_policy_judicial_stay_expiration_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(TypeError, match="does not support subclassing"):
        type(
            "BadConfig",
            (digest.MarketResearchPolicyJudicialStayExpirationDigestConfig,),
            {},
        )


def test_policy_judicial_stay_expiration_digest_rejects_duplicates_and_bad_consistency() -> None:
    digest = digest_module()

    with pytest.raises(ValueError, match="unique"):
        report(
            digest,
            (
                input_row(digest, court_key="duplicate-court"),
                input_row(
                    digest,
                    "research.stay-expiration.duplicate-2",
                    court_key="duplicate-court",
                ),
            ),
        )

    ready = report(digest, (input_row(digest),)).rows[0]
    with pytest.raises(ValueError, match="reason_codes"):
        row_from(
            digest,
            ready,
            reason_codes=(
                "market_research_policy_judicial_stay_expiration_digest_ready",
                "market_research_policy_judicial_stay_expiration_digest_expired_stay",
            ),
        )
    with pytest.raises(ValueError, match="expiration_status"):
        row_from(digest, ready, expiration_status="blocked")
    with pytest.raises(ValueError, match="redacted_public_expiration_reference"):
        row_from(
            digest,
            ready,
            redacted_public_expiration_reference="https://host?case=sealed",
        )

    summary = report(digest, (input_row(digest),))
    with pytest.raises(ValueError, match="ready_expiration_count"):
        report_from(digest, summary, ready_expiration_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            digest,
            (
                input_row(digest, "research.stay-expiration.z", court_key="z-court"),
                input_row(digest),
            ),
        )
        report_from(digest, unordered, rows=tuple(reversed(unordered.rows)))


def test_public_numeric_count_ratio_score_and_seconds_fields_are_decimals() -> None:
    digest = digest_module()
    summary = report(digest, (input_row(digest),))

    assert_decimal_public_numeric_fields(
        digest.MarketResearchPolicyJudicialStayExpirationDigestConfig(),
    )
    assert_decimal_public_numeric_fields(input_row(digest))
    assert_decimal_public_numeric_fields(summary)
    assert_decimal_public_numeric_fields(summary.rows[0])
    assert_decimal_public_numeric_fields(summary.reason_code_counts[0])


def test_module_has_no_io_durable_store_or_execution_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: set[str] = set()
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    forbidden_import_fragments = (
        "db",
        "env",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "websocket",
        "aiohttp",
        "psycopg",
        "supabase",
        "sqlite",
        "sqlalchemy",
        "pathlib",
        "openai",
        "boto",
        "ccxt",
        "subprocess",
    )
    forbidden_call_or_attribute_names = (
        "connect",
        "execute",
        "fetch",
        "get",
        "post",
        "put",
        "delete",
        "request",
        "open",
        "read",
        "write",
        "mkdir",
        "unlink",
        "rename",
        "submit",
        "cancel",
        "order",
        "trade",
        "wallet",
        "account",
        "sign",
        "auth",
    )

    lowered_imports = tuple(name.lower() for name in imported_modules)
    lowered_surface = tuple(name.lower() for name in (*call_names, *attribute_names))
    assert not any(
        fragment in module_name
        for module_name in lowered_imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in lowered_surface)
    for forbidden in (
        "live trading",
        "wallet",
        "auth",
        "submit_order",
        "cancel_order",
        "replace_order",
        "exchange mutation",
        "account",
        "secret",
    ):
        assert forbidden not in source.lower()


def d(value: str) -> Decimal:
    return Decimal(value)


def redacted(value: str) -> str:
    import hashlib

    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def digest_module() -> Any:
    return importlib.import_module(MODULE_NAME)


def config(digest: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            digest.DEFAULT_MARKET_RESEARCH_POLICY_JUDICIAL_STAY_EXPIRATION_DIGEST_CONFIG_VERSION
        ),
        "near_term_expiration_seconds": d("172800.000000"),
        "stale_status_check_seconds": d("86400.000000"),
        "high_policy_impact_threshold": d("0.600000"),
        "high_extension_probability_threshold": d("0.600000"),
        "high_market_relevance_threshold": d("0.600000"),
        "min_source_count": d("2.000000"),
    }
    values.update(overrides)
    return digest.MarketResearchPolicyJudicialStayExpirationDigestConfig(**values)


def input_row(
    digest: Any,
    research_key: str = "research.stay-expiration.state-tax",
    *,
    condition_id: str = "condition_state_tax",
    court_key: str = "ny-court-appeals",
    jurisdiction_key: str = "ny",
    docket_key: str = "tax-2026-07",
    case_title: str = "state-tax-guidance",
    policy_domain: str = "tax",
    public_expiration_reference: str = "public-state-court-stay-expiration",
    stay_expires_at: datetime | None = None,
    last_checked_at: datetime | None = None,
    acknowledged_at: object = _UNSET,
    source_count: Decimal = d("3.000000"),
    policy_impact_score: Decimal = d("0.200000"),
    extension_probability_score: Decimal = d("0.300000"),
    market_relevance_score: Decimal = d("0.210000"),
    expiration_config_version: str = "judicial-stay-expiration-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return digest.MarketResearchPolicyJudicialStayExpirationDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        court_key=court_key,
        jurisdiction_key=jurisdiction_key,
        docket_key=docket_key,
        case_title=case_title,
        policy_domain=policy_domain,
        public_expiration_reference=public_expiration_reference,
        stay_expires_at=(
            stay_expires_at
            if stay_expires_at is not None
            else GENERATED_AT + timedelta(days=4)
        ),
        last_checked_at=(
            last_checked_at
            if last_checked_at is not None
            else GENERATED_AT - timedelta(minutes=30)
        ),
        acknowledged_at=(
            acknowledged_at
            if acknowledged_at is not _UNSET
            else GENERATED_AT - timedelta(minutes=15)
        ),
        source_count=source_count,
        policy_impact_score=policy_impact_score,
        extension_probability_score=extension_probability_score,
        market_relevance_score=market_relevance_score,
        expiration_config_version=expiration_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    digest: Any,
    rows: tuple[Any, ...],
    *,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return digest.build_market_research_policy_judicial_stay_expiration_digest(
        rows,
        config=config(digest),
        generated_at=generated_at,
    )


def row_from(digest: Any, row: Any, **overrides: object) -> Any:
    values = {
        field.name: getattr(row, field.name)
        for field in fields(row)
        if field.init
    }
    values.update(overrides)
    return digest.MarketResearchPolicyJudicialStayExpirationDigestRow(**values)


def report_from(digest: Any, summary: Any, **overrides: object) -> Any:
    values = {
        field.name: getattr(summary, field.name)
        for field in fields(summary)
        if field.init
    }
    values.update(overrides)
    return digest.MarketResearchPolicyJudicialStayExpirationDigestReport(**values)


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        output: list[Any] = []
        for item in value.values():
            output.extend(walk_values(item))
        return tuple(output)
    if isinstance(value, list):
        output = []
        for item in value:
            output.extend(walk_values(item))
        return tuple(output)
    return (value,)


def assert_decimal_public_numeric_fields(value: Any) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if isinstance(item, bool):
            continue
        is_decimal_public_numeric = (
            field.name == "count"
            or field.name.endswith("_count")
            or field.name.endswith("_ratio")
            or field.name.endswith("_score")
            or "seconds" in field.name
        )
        if is_decimal_public_numeric and not isinstance(item, (tuple, list, dict)):
            assert type(item) is Decimal
        assert not isinstance(item, float)
        assert not isinstance(item, int)
