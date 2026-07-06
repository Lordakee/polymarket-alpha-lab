from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.market_research_policy_campaign_ad_spend_surge_digest"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "market_research_policy_campaign_ad_spend_surge_digest.py",
)
GENERATED_AT = datetime(2026, 7, 4, 18, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def test_policy_campaign_ad_spend_surge_digest_public_api_exists() -> None:
    assert importlib.util.find_spec(MODULE_NAME) is not None


def test_policy_campaign_ad_spend_surge_digest_reduces_rows_deterministically() -> None:
    digest = digest_module()

    summary = report(
        digest,
        (
            input_row(
                digest,
                "research.ad.ca-senate",
                condition_id="condition_ca_senate_ad",
                race_id="ca-senate-2026",
                campaign_id="campaign-ca-senate",
                jurisdiction_id="ca",
                public_spend_reference="https://ads.example/ca?token=secret-123",
                observed_at=GENERATED_AT - timedelta(hours=6),
                source_count=d("1.000000"),
                spend_surge_score=d("0.820000"),
                ad_volume_score=d("0.720000"),
                message_shift_score=d("0.610000"),
                opposition_response_score=d("0.680000"),
                spend_model_version="campaign-spend-v2",
            ),
            input_row(
                digest,
                "research.ad.tx-house",
                condition_id="condition_tx_house_ad",
                race_id="tx-house-2026",
                campaign_id="campaign-tx-house",
                jurisdiction_id="tx",
                public_spend_reference="private-platform-spend-feed",
                observed_at=GENERATED_AT - timedelta(hours=30),
                source_count=d("2.000000"),
                spend_surge_score=d("0.700000"),
                ad_volume_score=d("0.500000"),
                message_shift_score=d("0.300000"),
                opposition_response_score=d("0.200000"),
                spend_model_version="campaign-spend-v1",
            ),
            input_row(
                digest,
                "research.ad.mn-mayor",
                condition_id="condition_mn_mayor_ad",
                race_id="mn-mayor-2026",
                campaign_id="campaign-mn-mayor",
                jurisdiction_id="mn",
                public_spend_reference="public-municipal-ad-spend",
                observed_at=GENERATED_AT - timedelta(hours=1),
                source_count=d("3.000000"),
                spend_surge_score=d("0.200000"),
                ad_volume_score=d("0.250000"),
                message_shift_score=d("0.220000"),
                opposition_response_score=d("0.180000"),
                spend_model_version="campaign-spend-v0",
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        digest.DEFAULT_MARKET_RESEARCH_POLICY_CAMPAIGN_AD_SPEND_SURGE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_policy_campaign_ad_spend_surge_digest"
    )
    assert summary.campaign_count == d("3.000000")
    assert summary.ready_campaign_count == d("1.000000")
    assert summary.watch_campaign_count == d("1.000000")
    assert summary.blocked_campaign_count == d("1.000000")
    assert summary.high_spend_surge_count == d("2.000000")
    assert summary.high_ad_volume_count == d("1.000000")
    assert summary.high_message_shift_count == d("1.000000")
    assert summary.high_opposition_response_count == d("1.000000")
    assert summary.stale_observation_count == d("1.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.average_spend_surge_score == d("0.573333")
    assert summary.average_ad_volume_score == d("0.490000")
    assert summary.average_message_shift_score == d("0.376667")
    assert summary.average_opposition_response_score == d("0.353333")
    assert summary.average_source_count == d("2.000000")
    assert summary.max_observation_age_seconds == d("108000.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.race_id, row.research_id) for row in summary.rows) == (
        ("ca-senate-2026", "research.ad.ca-senate"),
        ("tx-house-2026", "research.ad.tx-house"),
        ("mn-mayor-2026", "research.ad.mn-mayor"),
    )

    ca_senate = summary.rows[0]
    assert ca_senate.surge_status == "blocked"
    assert ca_senate.observation_age_seconds == d("21600.000000")
    assert ca_senate.redacted_public_spend_reference == redacted(
        "https://ads.example/ca?token=secret-123",
    )
    assert ca_senate.reason_codes == (
        "market_research_policy_campaign_ad_spend_surge_digest_high_spend_surge",
        "market_research_policy_campaign_ad_spend_surge_digest_high_ad_volume",
        "market_research_policy_campaign_ad_spend_surge_digest_high_message_shift",
        "market_research_policy_campaign_ad_spend_surge_digest_high_opposition_response",
        "market_research_policy_campaign_ad_spend_surge_digest_thin_sources",
    )

    tx_house = summary.rows[1]
    assert tx_house.surge_status == "watch"
    assert tx_house.observation_age_seconds == d("108000.000000")
    assert tx_house.redacted_public_spend_reference == redacted(
        "private-platform-spend-feed",
    )
    assert tx_house.reason_codes == (
        "market_research_policy_campaign_ad_spend_surge_digest_high_spend_surge",
        "market_research_policy_campaign_ad_spend_surge_digest_stale_observation",
    )

    mn_mayor = summary.rows[2]
    assert mn_mayor.surge_status == "ready"
    assert mn_mayor.redacted_public_spend_reference == "public-municipal-ad-spend"
    assert mn_mayor.reason_codes == (
        "market_research_policy_campaign_ad_spend_surge_digest_ready",
    )

    assert summary.reason_code_counts == (
        digest.MarketResearchPolicyCampaignAdSpendSurgeDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_campaign_ad_spend_surge_digest_high_spend_surge"
            ),
            count=d("2.000000"),
            campaign_ratio=d("0.666667"),
        ),
        digest.MarketResearchPolicyCampaignAdSpendSurgeDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_campaign_ad_spend_surge_digest_high_ad_volume"
            ),
            count=d("1.000000"),
            campaign_ratio=d("0.333333"),
        ),
        digest.MarketResearchPolicyCampaignAdSpendSurgeDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_campaign_ad_spend_surge_digest_high_message_shift"
            ),
            count=d("1.000000"),
            campaign_ratio=d("0.333333"),
        ),
        digest.MarketResearchPolicyCampaignAdSpendSurgeDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_campaign_ad_spend_surge_digest_high_opposition_response"
            ),
            count=d("1.000000"),
            campaign_ratio=d("0.333333"),
        ),
        digest.MarketResearchPolicyCampaignAdSpendSurgeDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_campaign_ad_spend_surge_digest_stale_observation"
            ),
            count=d("1.000000"),
            campaign_ratio=d("0.333333"),
        ),
        digest.MarketResearchPolicyCampaignAdSpendSurgeDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_campaign_ad_spend_surge_digest_thin_sources"
            ),
            count=d("1.000000"),
            campaign_ratio=d("0.333333"),
        ),
        digest.MarketResearchPolicyCampaignAdSpendSurgeDigestReasonCodeCount(
            reason_code="market_research_policy_campaign_ad_spend_surge_digest_ready",
            count=d("1.000000"),
            campaign_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )
    assert summary.spend_model_versions == (
        ("condition_ca_senate_ad", "campaign-spend-v2"),
        ("condition_mn_mayor_ad", "campaign-spend-v0"),
        ("condition_tx_house_ad", "campaign-spend-v1"),
    )

    public = repr(public_values(summary)).lower()
    for value in (
        "secret-123",
        "ads.example",
        "https://",
        "private-platform-spend-feed",
        "auth",
        "broker",
        "signing",
        "submit",
        "cancel",
        "wallet",
        "account",
        "advice",
        "network",
        "database",
        "token",
        "secret",
        "private",
    ):
        assert value not in public


def test_empty_policy_campaign_ad_spend_surge_digest_is_blocked_and_report_only() -> None:
    digest = digest_module()
    summary = report(digest, ())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_policy_campaign_ad_spend_surge_digest"
    )
    assert summary.campaign_count == ZERO
    assert summary.ready_campaign_count == ZERO
    assert summary.watch_campaign_count == ZERO
    assert summary.blocked_campaign_count == ZERO
    assert summary.average_spend_surge_score == ZERO
    assert summary.average_ad_volume_score == ZERO
    assert summary.average_message_shift_score == ZERO
    assert summary.average_opposition_response_score == ZERO
    assert summary.average_source_count == ZERO
    assert summary.max_observation_age_seconds == ZERO
    assert summary.rows == ()
    assert summary.spend_model_versions == ()
    assert summary.reason_code_counts == (
        digest.MarketResearchPolicyCampaignAdSpendSurgeDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_campaign_ad_spend_surge_digest_no_inputs"
            ),
            count=d("1.000000"),
            campaign_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_policy_campaign_ad_spend_surge_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_policy_campaign_ad_spend_surge_digest_payload_uses_decimal_strings() -> None:
    digest = digest_module()
    summary = report(digest, (input_row(digest),))
    payload = digest.market_research_policy_campaign_ad_spend_surge_digest_payload(
        summary,
    )
    json.dumps(payload, sort_keys=True)

    assert payload["campaign_count"] == "1.000000"
    assert payload["average_spend_surge_score"] == "0.200000"
    assert payload["rows"][0]["source_count"] == "3.000000"
    assert payload["rows"][0]["observation_age_seconds"] == "3600.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, (Decimal, datetime, float)) for value in walk_values(payload))
    assert "'public_spend_reference':" not in repr(payload)
    assert "private" not in repr(payload).lower()


def test_policy_campaign_ad_spend_surge_digest_payload_revalidates_nested_dataclasses() -> None:
    digest = digest_module()

    with pytest.raises(ValueError, match="report"):
        digest.market_research_policy_campaign_ad_spend_surge_digest_payload(object())

    tampered_row_report = report(digest, (input_row(digest),))
    object.__setattr__(tampered_row_report.rows[0], "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        digest.market_research_policy_campaign_ad_spend_surge_digest_payload(
            tampered_row_report,
        )

    tampered_reason_flag_report = report(digest, (input_row(digest),))
    object.__setattr__(
        tampered_reason_flag_report.reason_code_counts[0],
        "readonly",
        False,
    )
    with pytest.raises(ValueError, match="readonly"):
        digest.market_research_policy_campaign_ad_spend_surge_digest_payload(
            tampered_reason_flag_report,
        )

    tampered_reason_type_report = report(digest, (input_row(digest),))
    object.__setattr__(tampered_reason_type_report, "reason_code_counts", (object(),))
    with pytest.raises(ValueError, match="reason_code_counts|reason code"):
        digest.market_research_policy_campaign_ad_spend_surge_digest_payload(
            tampered_reason_type_report,
        )


def test_policy_campaign_ad_spend_surge_digest_validates_contracts_and_flags() -> None:
    digest = digest_module()

    assert digest.MarketResearchPolicyCampaignAdSpendSurgeDigestConfig.__dataclass_params__.frozen
    assert digest.MarketResearchPolicyCampaignAdSpendSurgeDigestInputRow.__dataclass_params__.frozen
    assert digest.MarketResearchPolicyCampaignAdSpendSurgeDigestRow.__dataclass_params__.frozen
    assert digest.MarketResearchPolicyCampaignAdSpendSurgeDigestReport.__dataclass_params__.frozen

    summary = report(digest, (input_row(digest),))
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].source_count = d("4.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(digest, config_version=_StringSubclass("campaign-spend-v0"))
    with pytest.raises(ValueError, match="fresh_observation_max_age_seconds"):
        config(
            digest,
            fresh_observation_max_age_seconds=_DecimalSubclass("86400.000000"),
        )
    with pytest.raises(ValueError, match="high_spend_surge_threshold"):
        config(digest, high_spend_surge_threshold=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="research_id"):
        input_row(digest, research_id=" bad")
    with pytest.raises(ValueError, match="campaign_id"):
        input_row(digest, campaign_id="private-campaign")
    with pytest.raises(ValueError, match="observed_at"):
        input_row(digest, observed_at=datetime(2026, 7, 4, 17, 0))
    with pytest.raises(ValueError, match="observed_at"):
        input_row(
            digest,
            observed_at=_DateTimeSubclass(2026, 7, 4, 17, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="source_count"):
        input_row(digest, source_count=Decimal("1.5"))
    with pytest.raises(ValueError, match="spend_surge_score"):
        input_row(digest, spend_surge_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="ad_volume_score"):
        input_row(digest, ad_volume_score=d("1.000001"))
    with pytest.raises(ValueError, match="message_shift_score"):
        input_row(digest, message_shift_score=d("-0.000001"))
    with pytest.raises(ValueError, match="future"):
        report(
            digest,
            (input_row(digest, observed_at=GENERATED_AT + timedelta(seconds=1)),),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_row(digest), paper_only=False)
    with pytest.raises(ValueError, match="config"):
        digest.build_market_research_policy_campaign_ad_spend_surge_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(TypeError, match="does not support subclassing"):
        type(
            "BadConfig",
            (digest.MarketResearchPolicyCampaignAdSpendSurgeDigestConfig,),
            {},
        )


def test_policy_campaign_ad_spend_surge_digest_rejects_duplicates_and_bad_consistency() -> None:
    digest = digest_module()

    with pytest.raises(ValueError, match="unique"):
        report(
            digest,
            (
                input_row(digest, condition_id="duplicate-condition"),
                input_row(
                    digest,
                    "research.ad.duplicate-2",
                    condition_id="duplicate-condition",
                ),
            ),
        )

    ready = report(digest, (input_row(digest),)).rows[0]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "market_research_policy_campaign_ad_spend_surge_digest_ready",
                "market_research_policy_campaign_ad_spend_surge_digest_thin_sources",
            ),
        )
    with pytest.raises(ValueError, match="surge_status"):
        replace(ready, surge_status="blocked")
    with pytest.raises(ValueError, match="redacted_public_spend_reference"):
        replace(
            ready,
            redacted_public_spend_reference="https://host?token=secret",
        )

    with pytest.raises(ValueError, match="ready_campaign_count"):
        replace(report(digest, (input_row(digest),)), ready_campaign_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            digest,
            (
                input_row(
                    digest,
                    "research.ad.z",
                    condition_id="condition_z",
                    race_id="z-race",
                    spend_surge_score=d("0.700000"),
                ),
                input_row(digest),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))


def test_public_numeric_count_ratio_score_and_seconds_fields_are_decimals() -> None:
    digest = digest_module()
    summary = report(digest, (input_row(digest),))

    assert_decimal_public_numeric_fields(
        digest.MarketResearchPolicyCampaignAdSpendSurgeDigestConfig(),
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
        "asdict",
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
        "broker",
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
    assert "asdict" not in source
    for forbidden in (
        "live trading",
        "wallet",
        "broker",
        "signing",
        "submit_order",
        "cancel_order",
        "account",
        "advice",
        "market_slug",
        "question",
        "payload_json",
    ):
        assert forbidden not in source.lower()

    digest = digest_module()
    public_names = tuple(digest.__all__)
    forbidden_public_fields = ("market_slug", "question", "_".join(("payload", "json")))
    for value in public_names:
        assert value not in forbidden_public_fields
    for class_name in (
        "MarketResearchPolicyCampaignAdSpendSurgeDigestConfig",
        "MarketResearchPolicyCampaignAdSpendSurgeDigestInputRow",
        "MarketResearchPolicyCampaignAdSpendSurgeDigestRow",
        "MarketResearchPolicyCampaignAdSpendSurgeDigestReport",
    ):
        exposed_fields = tuple(field.name for field in fields(getattr(digest, class_name)))
        assert not any(field_name in forbidden_public_fields for field_name in exposed_fields)


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
            digest.DEFAULT_MARKET_RESEARCH_POLICY_CAMPAIGN_AD_SPEND_SURGE_DIGEST_CONFIG_VERSION
        ),
        "fresh_observation_max_age_seconds": d("86400.000000"),
        "high_spend_surge_threshold": d("0.650000"),
        "high_ad_volume_threshold": d("0.600000"),
        "high_message_shift_threshold": d("0.550000"),
        "high_opposition_response_threshold": d("0.500000"),
        "min_source_count": d("2.000000"),
    }
    values.update(overrides)
    return digest.MarketResearchPolicyCampaignAdSpendSurgeDigestConfig(**values)


def input_row(
    digest: Any,
    research_id: str = "research.ad.mn-mayor",
    *,
    condition_id: str = "condition_mn_mayor_ad",
    race_id: str = "mn-mayor-2026",
    campaign_id: str = "campaign-mn-mayor",
    jurisdiction_id: str = "mn",
    public_spend_reference: str = "public-municipal-ad-spend",
    observed_at: datetime | None = None,
    source_count: Decimal = d("3.000000"),
    spend_surge_score: Decimal = d("0.200000"),
    ad_volume_score: Decimal = d("0.250000"),
    message_shift_score: Decimal = d("0.220000"),
    opposition_response_score: Decimal = d("0.180000"),
    spend_model_version: str = "campaign-spend-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return digest.MarketResearchPolicyCampaignAdSpendSurgeDigestInputRow(
        research_id=research_id,
        condition_id=condition_id,
        race_id=race_id,
        campaign_id=campaign_id,
        jurisdiction_id=jurisdiction_id,
        public_spend_reference=public_spend_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(hours=1),
        source_count=source_count,
        spend_surge_score=spend_surge_score,
        ad_volume_score=ad_volume_score,
        message_shift_score=message_shift_score,
        opposition_response_score=opposition_response_score,
        spend_model_version=spend_model_version,
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
    return digest.build_market_research_policy_campaign_ad_spend_surge_digest(
        rows,
        config=config(digest),
        generated_at=generated_at,
    )


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        output: list[Any] = []
        for item in value.values():
            output.extend(walk_values(item))
        return tuple(output)
    if isinstance(value, (list, tuple)):
        output = []
        for item in value:
            output.extend(walk_values(item))
        return tuple(output)
    return (value,)


def public_values(value: Any) -> Any:
    if is_dataclass(value):
        return {
            field.name: public_values(getattr(value, field.name))
            for field in fields(value)
            if field.name != "public_spend_reference"
        }
    if isinstance(value, tuple):
        return tuple(public_values(item) for item in value)
    return value


def assert_decimal_public_numeric_fields(value: Any) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if isinstance(item, bool):
            continue
        if any(
            marker in field.name
            for marker in (
                "count",
                "ratio",
                "score",
                "seconds",
                "threshold",
            )
        ) and not isinstance(item, tuple):
            assert type(item) is Decimal
        assert not isinstance(item, float)
        assert not isinstance(item, int)
