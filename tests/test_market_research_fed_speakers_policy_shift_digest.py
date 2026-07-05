from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.market_research_fed_speakers_policy_shift_digest"
GENERATED_AT = datetime(2026, 7, 3, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
_UNSET = object()


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None

    def tzname(self, dt: datetime | None) -> str:
        return "none-offset"


def test_fed_speakers_policy_shift_digest_public_api_exists() -> None:
    assert importlib.util.find_spec(MODULE_NAME) is not None


def test_fed_speakers_policy_shift_digest_reduces_events_deterministically() -> None:
    digest = digest_module()

    summary = report(
        digest,
        (
            input_row(
                digest,
                "research.fed.speaker.powell",
                condition_id="condition_fed_powell",
                speaker_key="fed.speaker.powell",
                speaker_name="jerome-powell",
                policy_topic="rates",
                public_statement_reference="https://fed.example/speech?token=secret-123",
                observed_at=GENERATED_AT - timedelta(hours=3),
                acknowledged_at=None,
                source_count=d("1.000000"),
                hawkish_shift_score=d("0.620000"),
                dovish_shift_score=d("0.100000"),
                market_repricing_score=d("0.120000"),
                statement_consensus_score=d("0.420000"),
                event_config_version="fed-speaker-shift-v1",
            ),
            input_row(
                digest,
                "research.fed.speaker.waller",
                condition_id="condition_fed_waller",
                speaker_key="fed.speaker.waller",
                speaker_name="christopher-waller",
                policy_topic="inflation",
                public_statement_reference="private-fed-speaker-feed",
                observed_at=GENERATED_AT - timedelta(hours=2, minutes=10),
                acknowledged_at=GENERATED_AT - timedelta(minutes=70),
                source_count=d("2.000000"),
                hawkish_shift_score=d("0.200000"),
                dovish_shift_score=d("0.510000"),
                market_repricing_score=d("0.040000"),
                statement_consensus_score=d("0.700000"),
                event_config_version="fed-speaker-shift-v1",
            ),
            input_row(
                digest,
                "research.fed.speaker.bowman",
                condition_id="condition_fed_bowman",
                speaker_key="fed.speaker.bowman",
                speaker_name="michelle-bowman",
                policy_topic="bank-regulation",
                public_statement_reference="fomc-public-speaker-calendar",
                observed_at=GENERATED_AT - timedelta(minutes=30),
                acknowledged_at=GENERATED_AT - timedelta(minutes=20),
                source_count=d("3.000000"),
                hawkish_shift_score=d("0.120000"),
                dovish_shift_score=d("0.100000"),
                market_repricing_score=d("0.010000"),
                statement_consensus_score=d("0.850000"),
                event_config_version="fed-speaker-shift-v0",
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        digest.DEFAULT_MARKET_RESEARCH_FED_SPEAKERS_POLICY_SHIFT_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_fed_speakers_policy_shift_digest"
    )
    assert summary.event_count == d("3.000000")
    assert summary.ready_event_count == d("1.000000")
    assert summary.watch_event_count == d("1.000000")
    assert summary.blocked_event_count == d("1.000000")
    assert summary.material_policy_shift_count == d("2.000000")
    assert summary.hawkish_shift_count == d("1.000000")
    assert summary.dovish_shift_count == d("1.000000")
    assert summary.market_repricing_count == d("1.000000")
    assert summary.low_consensus_count == d("1.000000")
    assert summary.stale_event_count == d("2.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.missing_acknowledgement_count == d("1.000000")
    assert summary.slow_acknowledgement_count == d("1.000000")
    assert summary.average_policy_shift_score == d("0.416667")
    assert summary.average_market_repricing_score == d("0.056667")
    assert summary.average_statement_consensus_score == d("0.656667")
    assert summary.max_event_age_seconds == d("10800.000000")
    assert summary.average_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.speaker_key, row.research_key) for row in summary.rows) == (
        ("fed.speaker.powell", "research.fed.speaker.powell"),
        ("fed.speaker.waller", "research.fed.speaker.waller"),
        ("fed.speaker.bowman", "research.fed.speaker.bowman"),
    )

    powell = summary.rows[0]
    assert powell.policy_shift_status == "blocked"
    assert powell.event_age_seconds == d("10800.000000")
    assert powell.acknowledgement_lag_seconds is None
    assert powell.policy_shift_score == d("0.620000")
    assert powell.policy_shift_direction == "hawkish"
    assert powell.redacted_public_statement_reference == redacted(
        "https://fed.example/speech?token=secret-123",
    )
    assert powell.reason_codes == (
        "market_research_fed_speakers_policy_shift_digest_material_policy_shift",
        "market_research_fed_speakers_policy_shift_digest_hawkish_shift",
        "market_research_fed_speakers_policy_shift_digest_market_repricing",
        "market_research_fed_speakers_policy_shift_digest_low_consensus",
        "market_research_fed_speakers_policy_shift_digest_missing_acknowledgement",
        "market_research_fed_speakers_policy_shift_digest_stale_event",
        "market_research_fed_speakers_policy_shift_digest_thin_sources",
    )

    waller = summary.rows[1]
    assert waller.policy_shift_status == "watch"
    assert waller.event_age_seconds == d("7800.000000")
    assert waller.acknowledgement_lag_seconds == d("3600.000000")
    assert waller.policy_shift_score == d("0.510000")
    assert waller.policy_shift_direction == "dovish"
    assert waller.redacted_public_statement_reference == redacted(
        "private-fed-speaker-feed",
    )
    assert waller.reason_codes == (
        "market_research_fed_speakers_policy_shift_digest_material_policy_shift",
        "market_research_fed_speakers_policy_shift_digest_dovish_shift",
        "market_research_fed_speakers_policy_shift_digest_slow_acknowledgement",
        "market_research_fed_speakers_policy_shift_digest_stale_event",
    )

    bowman = summary.rows[2]
    assert bowman.policy_shift_status == "ready"
    assert bowman.event_age_seconds == d("1800.000000")
    assert bowman.acknowledgement_lag_seconds == d("600.000000")
    assert bowman.policy_shift_score == d("0.120000")
    assert bowman.policy_shift_direction == "neutral"
    assert bowman.redacted_public_statement_reference == "fomc-public-speaker-calendar"
    assert bowman.reason_codes == (
        "market_research_fed_speakers_policy_shift_digest_ready",
    )

    assert summary.reason_code_counts == (
        digest.MarketResearchFedSpeakersPolicyShiftDigestReasonCodeCount(
            reason_code=(
                "market_research_fed_speakers_policy_shift_digest_stale_event"
            ),
            count=d("2.000000"),
            event_ratio=d("0.666667"),
        ),
        digest.MarketResearchFedSpeakersPolicyShiftDigestReasonCodeCount(
            reason_code=(
                "market_research_fed_speakers_policy_shift_digest_material_policy_shift"
            ),
            count=d("2.000000"),
            event_ratio=d("0.666667"),
        ),
        digest.MarketResearchFedSpeakersPolicyShiftDigestReasonCodeCount(
            reason_code=(
                "market_research_fed_speakers_policy_shift_digest_hawkish_shift"
            ),
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        digest.MarketResearchFedSpeakersPolicyShiftDigestReasonCodeCount(
            reason_code=(
                "market_research_fed_speakers_policy_shift_digest_dovish_shift"
            ),
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        digest.MarketResearchFedSpeakersPolicyShiftDigestReasonCodeCount(
            reason_code=(
                "market_research_fed_speakers_policy_shift_digest_market_repricing"
            ),
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        digest.MarketResearchFedSpeakersPolicyShiftDigestReasonCodeCount(
            reason_code=(
                "market_research_fed_speakers_policy_shift_digest_low_consensus"
            ),
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        digest.MarketResearchFedSpeakersPolicyShiftDigestReasonCodeCount(
            reason_code=(
                "market_research_fed_speakers_policy_shift_digest_missing_acknowledgement"
            ),
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        digest.MarketResearchFedSpeakersPolicyShiftDigestReasonCodeCount(
            reason_code=(
                "market_research_fed_speakers_policy_shift_digest_ready"
            ),
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        digest.MarketResearchFedSpeakersPolicyShiftDigestReasonCodeCount(
            reason_code=(
                "market_research_fed_speakers_policy_shift_digest_slow_acknowledgement"
            ),
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        digest.MarketResearchFedSpeakersPolicyShiftDigestReasonCodeCount(
            reason_code=(
                "market_research_fed_speakers_policy_shift_digest_thin_sources"
            ),
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )
    assert summary.event_config_versions == (
        ("fed.speaker.bowman", "fed-speaker-shift-v0"),
        ("fed.speaker.powell", "fed-speaker-shift-v1"),
        ("fed.speaker.waller", "fed-speaker-shift-v1"),
    )

    public = repr(asdict(summary)).lower()
    for token in (
        "secret-123",
        "fed.example",
        "https://",
        "private-fed-speaker-feed",
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
        assert token not in public


def test_empty_fed_speakers_policy_shift_digest_is_blocked_and_report_only() -> None:
    digest = digest_module()
    summary = report(digest, ())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_fed_speakers_policy_shift_digest"
    )
    assert summary.event_count == ZERO
    assert summary.ready_event_count == ZERO
    assert summary.watch_event_count == ZERO
    assert summary.blocked_event_count == ZERO
    assert summary.average_policy_shift_score == ZERO
    assert summary.average_market_repricing_score == ZERO
    assert summary.average_statement_consensus_score == ZERO
    assert summary.max_event_age_seconds == ZERO
    assert summary.average_source_count == ZERO
    assert summary.rows == ()
    assert summary.event_config_versions == ()
    assert summary.reason_code_counts == (
        digest.MarketResearchFedSpeakersPolicyShiftDigestReasonCodeCount(
            reason_code="market_research_fed_speakers_policy_shift_digest_no_inputs",
            count=d("1.000000"),
            event_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_fed_speakers_policy_shift_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_fed_speakers_policy_shift_digest_payload_uses_decimal_strings() -> None:
    digest = digest_module()
    summary = report(digest, (input_row(digest),))
    payload = digest.market_research_fed_speakers_policy_shift_digest_payload(summary)
    json.dumps(payload, sort_keys=True)

    assert payload["event_count"] == "1.000000"
    assert payload["average_policy_shift_score"] == "0.120000"
    assert payload["rows"][0]["source_count"] == "3.000000"
    assert payload["rows"][0]["policy_shift_score"] == "0.120000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "'public_statement_reference':" not in repr(payload)
    assert "private" not in repr(payload).lower()


def test_fed_speakers_policy_shift_digest_validates_contracts_and_flags() -> None:
    digest = digest_module()

    assert digest.MarketResearchFedSpeakersPolicyShiftDigestConfig.__dataclass_params__.frozen
    assert digest.MarketResearchFedSpeakersPolicyShiftDigestInputRow.__dataclass_params__.frozen
    assert digest.MarketResearchFedSpeakersPolicyShiftDigestRow.__dataclass_params__.frozen
    assert digest.MarketResearchFedSpeakersPolicyShiftDigestReport.__dataclass_params__.frozen

    summary = report(digest, (input_row(digest),))
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].source_count = d("4.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        config(digest).config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        input_row(digest).research_key = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].count = d("4.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.digest_status = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(digest, config_version=_StringSubclass("fed-speakers-v0"))
    with pytest.raises(ValueError, match="max_event_age_seconds"):
        config(digest, max_event_age_seconds=_DecimalSubclass("7200.000000"))
    with pytest.raises(ValueError, match="material_policy_shift_threshold"):
        config(digest, material_policy_shift_threshold=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="research_key"):
        input_row(digest, research_key=" bad")
    with pytest.raises(ValueError, match="speaker_name"):
        input_row(digest, speaker_name="private-official")
    with pytest.raises(ValueError, match="observed_at"):
        input_row(digest, observed_at=datetime(2026, 7, 3, 16, 0))
    with pytest.raises(ValueError, match="observed_at"):
        input_row(
            digest,
            observed_at=datetime(2026, 7, 3, 16, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="acknowledged_at"):
        input_row(
            digest,
            acknowledged_at=_DateTimeSubclass(2026, 7, 3, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="acknowledged_at"):
        input_row(
            digest,
            acknowledged_at=datetime(2026, 7, 3, 16, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="source_count"):
        input_row(digest, source_count=Decimal("1.5"))
    with pytest.raises(ValueError, match="hawkish_shift_score"):
        input_row(digest, hawkish_shift_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="dovish_shift_score"):
        input_row(digest, dovish_shift_score=d("1.000001"))
    with pytest.raises(ValueError, match="market_repricing_score"):
        input_row(digest, market_repricing_score=d("-0.000001"))
    with pytest.raises(ValueError, match="future"):
        report(
            digest,
            (input_row(digest, observed_at=GENERATED_AT + timedelta(seconds=1)),),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_row(digest), paper_only=False)
    with pytest.raises(ValueError, match="config"):
        digest.build_market_research_fed_speakers_policy_shift_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(TypeError, match="does not support subclassing"):
        type(
            "BadConfig",
            (digest.MarketResearchFedSpeakersPolicyShiftDigestConfig,),
            {},
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_fed_speakers_policy_shift_digest_rejects_false_hard_flags(
    flag_name: str,
) -> None:
    digest = digest_module()
    false_flag = {flag_name: False}
    summary = report(digest, (input_row(digest),))

    with pytest.raises(ValueError, match=flag_name):
        config(digest, **false_flag)
    with pytest.raises(ValueError, match=flag_name):
        input_row(digest, **false_flag)
    with pytest.raises(ValueError, match=flag_name):
        replace(summary.rows[0], **false_flag)
    with pytest.raises(ValueError, match=flag_name):
        replace(summary.reason_code_counts[0], **false_flag)
    with pytest.raises(ValueError, match=flag_name):
        replace(summary, **false_flag)


def test_fed_speakers_policy_shift_digest_rejects_duplicates_and_bad_consistency() -> None:
    digest = digest_module()

    with pytest.raises(ValueError, match="unique"):
        report(
            digest,
            (
                input_row(digest, speaker_key="fed.speaker.duplicate"),
                input_row(
                    digest,
                    "research.fed.speaker.duplicate-2",
                    speaker_key="fed.speaker.duplicate",
                ),
            ),
        )

    ready = report(digest, (input_row(digest),)).rows[0]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "market_research_fed_speakers_policy_shift_digest_ready",
                "market_research_fed_speakers_policy_shift_digest_stale_event",
            ),
        )
    with pytest.raises(ValueError, match="policy_shift_status"):
        replace(ready, policy_shift_status="blocked")
    with pytest.raises(ValueError, match="policy_shift_score"):
        replace(ready, policy_shift_score=d("0.999999"))
    with pytest.raises(ValueError, match="redacted_public_statement_reference"):
        replace(ready, redacted_public_statement_reference="https://host?token=secret")

    with pytest.raises(ValueError, match="ready_event_count"):
        replace(report(digest, (input_row(digest),)), ready_event_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            digest,
            (
                input_row(digest, "research.fed.speaker.z", speaker_key="fed.speaker.z"),
                input_row(digest),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))


def test_fed_speakers_policy_shift_digest_respects_custom_material_threshold() -> None:
    digest = digest_module()

    summary = report(
        digest,
        (
            input_row(
                digest,
                hawkish_shift_score=d("0.600000"),
                dovish_shift_score=d("0.100000"),
                market_repricing_score=d("0.060000"),
            ),
        ),
        cfg=config(digest, material_policy_shift_threshold=d("0.700000")),
    )

    row = summary.rows[0]
    assert row.policy_shift_score == d("0.600000")
    assert row.policy_shift_direction == "neutral"
    assert row.policy_shift_status == "watch"
    assert row.reason_codes == (
        "market_research_fed_speakers_policy_shift_digest_market_repricing",
    )


def test_fed_speakers_policy_shift_digest_rejects_non_hex_redacted_references() -> None:
    digest = digest_module()
    ready = report(digest, (input_row(digest),)).rows[0]

    with pytest.raises(ValueError, match="redacted_public_statement_reference"):
        replace(ready, redacted_public_statement_reference="sha256:secretsecret")


def test_public_numeric_count_ratio_fields_are_decimals() -> None:
    digest = digest_module()
    summary = report(digest, (input_row(digest),))

    assert_decimal_public_numeric_fields(digest.MarketResearchFedSpeakersPolicyShiftDigestConfig())
    assert_decimal_public_numeric_fields(input_row(digest))
    assert_decimal_public_numeric_fields(summary)
    assert_decimal_public_numeric_fields(summary.rows[0])
    assert_decimal_public_numeric_fields(summary.reason_code_counts[0])


def test_module_has_no_io_durable_store_or_execution_surfaces() -> None:
    module_path = Path(
        "src/polymarket_alpha_lab/market_research_fed_speakers_policy_shift_digest.py",
    )
    source = module_path.read_text(encoding="utf-8")
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
    for forbidden in (
        "live trading",
        "wallet",
        "broker",
        "signing",
        "submit_order",
        "cancel_order",
        "account",
        "advice",
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
            digest.DEFAULT_MARKET_RESEARCH_FED_SPEAKERS_POLICY_SHIFT_DIGEST_CONFIG_VERSION
        ),
        "max_event_age_seconds": d("7200.000000"),
        "material_policy_shift_threshold": d("0.500000"),
        "min_market_repricing_score": d("0.050000"),
        "min_statement_consensus_score": d("0.600000"),
        "min_source_count": d("2.000000"),
        "max_acknowledgement_lag_seconds": d("1800.000000"),
    }
    values.update(overrides)
    return digest.MarketResearchFedSpeakersPolicyShiftDigestConfig(**values)


def input_row(
    digest: Any,
    research_key: str = "research.fed.speaker.bowman",
    *,
    condition_id: str = "condition_fed_bowman",
    speaker_key: str = "fed.speaker.bowman",
    speaker_name: str = "michelle-bowman",
    policy_topic: str = "bank-regulation",
    public_statement_reference: str = "fomc-public-speaker-calendar",
    observed_at: datetime | None = None,
    acknowledged_at: object = _UNSET,
    source_count: Decimal = d("3.000000"),
    hawkish_shift_score: Decimal = d("0.120000"),
    dovish_shift_score: Decimal = d("0.100000"),
    market_repricing_score: Decimal = d("0.010000"),
    statement_consensus_score: Decimal = d("0.850000"),
    event_config_version: str = "fed-speaker-shift-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return digest.MarketResearchFedSpeakersPolicyShiftDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        speaker_key=speaker_key,
        speaker_name=speaker_name,
        policy_topic=policy_topic,
        public_statement_reference=public_statement_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        acknowledged_at=(
            GENERATED_AT - timedelta(minutes=20)
            if acknowledged_at is _UNSET
            else acknowledged_at
        ),
        source_count=source_count,
        hawkish_shift_score=hawkish_shift_score,
        dovish_shift_score=dovish_shift_score,
        market_repricing_score=market_repricing_score,
        statement_consensus_score=statement_consensus_score,
        event_config_version=event_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    digest: Any,
    rows: tuple[object, ...],
    *,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return digest.build_market_research_fed_speakers_policy_shift_digest(
        rows,
        config=cfg or config(digest),
        generated_at=generated_at,
    )


def walk_values(value: object) -> list[object]:
    if isinstance(value, dict):
        return [item for child in value.values() for item in walk_values(child)]
    if isinstance(value, list):
        return [item for child in value for item in walk_values(child)]
    return [value]


def assert_decimal_public_numeric_fields(value: object) -> None:
    assert is_dataclass(value)
    numeric_markers = (
        "age_seconds",
        "average",
        "count",
        "lag_seconds",
        "max_",
        "min_",
        "ratio",
        "score",
        "threshold",
    )
    for field in fields(value):
        field_value = getattr(value, field.name)
        if field.name.endswith(("codes", "counts", "versions")):
            continue
        if any(marker in field.name for marker in numeric_markers):
            if field_value is not None:
                assert type(field_value) is Decimal, field.name
