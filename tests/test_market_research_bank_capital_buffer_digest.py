from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.market_research_bank_capital_buffer_digest"
GENERATED_AT = datetime(2026, 7, 4, 15, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


@dataclass(frozen=True)
class _UnknownPublicPayloadObject:
    public_value: str = "public-value"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


class _NoneOffsetTzinfo(tzinfo):
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
        "config_version": (
            module.DEFAULT_MARKET_RESEARCH_BANK_CAPITAL_BUFFER_DIGEST_CONFIG_VERSION
        ),
        "fresh_observation_max_age_seconds": d("7200.000000"),
        "minimum_capital_buffer_ratio": d("0.025000"),
        "min_source_count": d("2.000000"),
        "probability_repricing_threshold": d("0.050000"),
    }
    values.update(overrides)
    return module.MarketResearchBankCapitalBufferDigestConfig(**values)


def signal(
    research_key: str = "research.bank_capital.ready",
    *,
    condition_id: str = "condition.bank.capital.ready",
    bank_key: str = "regional_ready",
    capital_source_reference: str = "public-capital-note",
    observed_at: datetime | None = None,
    source_count: Decimal = d("3.000000"),
    cet1_capital_ratio: Decimal = d("0.115000"),
    minimum_capital_ratio: Decimal = d("0.080000"),
    stress_loss_ratio: Decimal = d("0.010000"),
    market_probability_before: Decimal = d("0.410000"),
    market_probability_after: Decimal = d("0.430000"),
) -> Any:
    module = api()
    return module.MarketResearchBankCapitalBufferDigestSignal(
        research_key=research_key,
        condition_id=condition_id,
        bank_key=bank_key,
        capital_source_reference=capital_source_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        source_count=source_count,
        cet1_capital_ratio=cet1_capital_ratio,
        minimum_capital_ratio=minimum_capital_ratio,
        stress_loss_ratio=stress_loss_ratio,
        market_probability_before=market_probability_before,
        market_probability_after=market_probability_after,
    )


def digest(
    *signals: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_market_research_bank_capital_buffer_digest(
        signals,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in walk_values(nested))
    return (value,)


def test_capital_buffer_digest_reduces_and_sorts_deterministically() -> None:
    module = api()
    report = digest(
        signal(),
        signal(
            "research.bank_capital.watch",
            condition_id="condition.bank.capital.watch",
            bank_key="money_center_watch",
            cet1_capital_ratio=d("0.101000"),
            minimum_capital_ratio=d("0.080000"),
            stress_loss_ratio=d("0.015000"),
            market_probability_before=d("0.300000"),
            market_probability_after=d("0.360000"),
        ),
        signal(
            "research.bank_capital.blocked",
            condition_id="condition.bank.capital.blocked",
            bank_key="regional_blocked",
            capital_source_reference="https://capital.example/bank?token=secret-123",
            observed_at=GENERATED_AT - timedelta(hours=3),
            source_count=d("1.000000"),
            cet1_capital_ratio=d("0.070000"),
            minimum_capital_ratio=d("0.080000"),
            stress_loss_ratio=d("0.030000"),
            market_probability_before=d("0.200000"),
            market_probability_after=d("0.280000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(report, module.MarketResearchBankCapitalBufferDigestReport)
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        module.DEFAULT_MARKET_RESEARCH_BANK_CAPITAL_BUFFER_DIGEST_CONFIG_VERSION
    )
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_bank_capital_buffer_digest"
    )
    assert report.observation_count == d("3.000000")
    assert report.ready_observation_count == d("1.000000")
    assert report.watch_observation_count == d("1.000000")
    assert report.blocked_observation_count == d("1.000000")
    assert report.capital_buffer_breach_count == d("1.000000")
    assert report.capital_buffer_thin_count == d("2.000000")
    assert report.stress_loss_buffer_gap_count == d("1.000000")
    assert report.stale_observation_count == d("1.000000")
    assert report.thin_source_count == d("1.000000")
    assert report.probability_repricing_count == d("2.000000")
    assert report.average_capital_buffer_ratio == d("0.015333")
    assert report.min_capital_buffer_ratio == d("-0.010000")
    assert report.max_stress_loss_buffer_gap_ratio == d("0.040000")
    assert report.max_observation_age_seconds == d("10800.000000")
    assert tuple(row.bank_key for row in report.rows) == (
        "regional_blocked",
        "money_center_watch",
        "regional_ready",
    )

    blocked = report.rows[0]
    assert blocked.capital_status == "blocked"
    assert blocked.capital_buffer_ratio == d("-0.010000")
    assert blocked.stress_loss_buffer_gap_ratio == d("0.040000")
    assert blocked.probability_delta == d("0.080000")
    assert blocked.redacted_capital_source_reference == "sha256:4f85c358c151"
    assert blocked.reason_codes == (
        "market_research_bank_capital_buffer_digest_capital_buffer_breach",
        "market_research_bank_capital_buffer_digest_capital_buffer_thin",
        "market_research_bank_capital_buffer_digest_stress_loss_buffer_gap",
        "market_research_bank_capital_buffer_digest_stale_observation",
        "market_research_bank_capital_buffer_digest_probability_repricing",
        "market_research_bank_capital_buffer_digest_thin_source",
    )
    assert report.reason_codes == (
        "market_research_bank_capital_buffer_digest_capital_buffer_breach",
        "market_research_bank_capital_buffer_digest_capital_buffer_thin",
        "market_research_bank_capital_buffer_digest_stress_loss_buffer_gap",
        "market_research_bank_capital_buffer_digest_stale_observation",
        "market_research_bank_capital_buffer_digest_probability_repricing",
        "market_research_bank_capital_buffer_digest_thin_source",
        "market_research_bank_capital_buffer_digest_ready",
    )
    assert all(row.paper_only and row.report_only and row.readonly for row in report.rows)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    public = repr(asdict(report)).lower()
    for token in ("https://", "token=", "secret", "capital.example"):
        assert token not in public


def test_empty_digest_and_payload_are_decimal_string_only() -> None:
    module = api()
    report = digest()

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_bank_capital_buffer_digest"
    )
    assert report.observation_count == ZERO
    assert report.rows == ()
    assert report.reason_codes == (
        "market_research_bank_capital_buffer_digest_no_inputs",
    )
    assert report.reason_code_counts == (
        module.MarketResearchBankCapitalBufferDigestReasonCodeCount(
            reason_code="market_research_bank_capital_buffer_digest_no_inputs",
            count=d("1.000000"),
            observation_ratio=ZERO,
        ),
    )
    with pytest.raises(ValueError, match="count must be positive"):
        module.MarketResearchBankCapitalBufferDigestReasonCodeCount(
            reason_code="market_research_bank_capital_buffer_digest_no_inputs",
            count=ZERO,
            observation_ratio=ZERO,
        )

    payload = module.market_research_bank_capital_buffer_digest_payload(
        digest(signal()),
    )

    json.dumps(payload, sort_keys=True)
    assert payload == module.market_research_bank_capital_buffer_digest_payload(
        digest(signal()),
    )
    assert payload["generated_at"] == "2026-07-04T15:00:00+00:00"
    assert payload["observation_count"] == "1.000000"
    assert payload["average_capital_buffer_ratio"] == "0.035000"
    assert payload["rows"][0]["capital_buffer_ratio"] == "0.035000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert not any(isinstance(value, Decimal) for value in walk_values(payload))

    for raw_payload in (
        payload,
        [payload],
        {"payload"},
        _UnknownPublicPayloadObject(),
    ):
        with pytest.raises(
            ValueError,
            match="MarketResearchBankCapitalBufferDigestReport",
        ):
            module.market_research_bank_capital_buffer_digest_payload(raw_payload)

    tampered_report = digest(signal())
    object.__setattr__(tampered_report, "observation_count", d("1"))
    with pytest.raises(ValueError, match="six-decimal"):
        module.market_research_bank_capital_buffer_digest_payload(tampered_report)


def test_payload_rejects_common_secret_surface_values() -> None:
    module = api()

    for unsafe_value in (
        "api_key",
        "bearer-header",
        "credential-label",
        "password-hint",
    ):
        tampered_report = digest(signal())
        object.__setattr__(tampered_report, "recommended_next_step", unsafe_value)
        with pytest.raises(ValueError, match="unsafe|secret|redacted"):
            module.market_research_bank_capital_buffer_digest_payload(
                tampered_report,
            )


def test_payload_revalidates_tampered_report_and_nested_payloads() -> None:
    module = api()

    tampered_report = digest(signal())
    object.__setattr__(tampered_report, "observation_count", d("2.000000"))
    with pytest.raises(ValueError, match="observation_count"):
        module.market_research_bank_capital_buffer_digest_payload(tampered_report)

    nested_tampered_report = digest(signal())
    object.__setattr__(
        nested_tampered_report,
        "rows",
        (asdict(nested_tampered_report.rows[0]),),
    )
    with pytest.raises(ValueError, match="rows must contain"):
        module.market_research_bank_capital_buffer_digest_payload(nested_tampered_report)

    zero_count_report = digest(signal())
    object.__setattr__(
        zero_count_report.reason_code_counts[0],
        "count",
        ZERO,
    )
    with pytest.raises(ValueError, match="count"):
        module.market_research_bank_capital_buffer_digest_payload(
            zero_count_report,
        )

    false_flag_report = digest(signal())
    object.__setattr__(false_flag_report.rows[0], "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        module.market_research_bank_capital_buffer_digest_payload(
            false_flag_report,
        )

    unknown_nested_report = digest(signal())
    object.__setattr__(
        unknown_nested_report,
        "rows",
        (_UnknownPublicPayloadObject(),),
    )
    with pytest.raises(ValueError, match="supported public dataclass"):
        module.market_research_bank_capital_buffer_digest_payload(
            unknown_nested_report,
        )


def test_dataclasses_are_frozen_hard_flagged_and_decimal_only() -> None:
    module = api()
    cfg = config()
    source = signal()
    report = digest(source, cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        source.source_count = d("4.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].capital_buffer_ratio = d("0.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.observation_count = d("2.000000")  # type: ignore[misc]

    for public_type in (
        module.MarketResearchBankCapitalBufferDigestConfig,
        module.MarketResearchBankCapitalBufferDigestSignal,
        module.MarketResearchBankCapitalBufferDigestRow,
        module.MarketResearchBankCapitalBufferDigestReasonCodeCount,
        module.MarketResearchBankCapitalBufferDigestReport,
    ):
        assert is_dataclass(public_type)
        assert all("float" not in str(field.type) for field in fields(public_type))
        assert all("int" not in str(field.type) and field.type is not int for field in fields(public_type))

    numeric_public_fragments = {
        "seconds",
        "ratio",
        "count",
        "probability",
    }
    for item in (cfg, source, report, report.rows[0], report.reason_code_counts[0]):
        for field_name, value in asdict(item).items():
            if field_name in {"reason_code_counts", "reason_codes", "rows"}:
                continue
            if any(fragment in field_name for fragment in numeric_public_fragments):
                assert type(value) is Decimal, (field_name, type(value))
                assert value.as_tuple().exponent == -6

    with pytest.raises(ValueError, match="paper_only"):
        module.MarketResearchBankCapitalBufferDigestSignal(
            **{**asdict(source), "paper_only": False},
        )
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report.rows[0], paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report.reason_code_counts[0], report_only=False)


@pytest.mark.parametrize(
    ("factory", "message"),
    (
        (lambda: config(minimum_capital_buffer_ratio=_DecimalSubclass("0.010000")), "Decimal"),
        (lambda: config(min_source_count=2), "Decimal"),
        (lambda: signal(cet1_capital_ratio=d("1.500000")), "cet1_capital_ratio"),
        (lambda: signal(minimum_capital_ratio=Decimal("-0.010000")), "minimum_capital_ratio"),
        (lambda: signal(stress_loss_ratio=50), "stress_loss_ratio"),
        (lambda: signal(bank_key=_StringSubclass("regional")), "bank_key"),
        (lambda: signal(observed_at=_DatetimeSubclass(2026, 7, 4, tzinfo=UTC)), "observed_at"),
        (
            lambda: signal(observed_at=datetime(2026, 7, 4, tzinfo=_NoneOffsetTzinfo())),
            "timezone-aware",
        ),
        (lambda: signal(research_key="research.wallet.capital"), "research_key"),
    ),
)
def test_validates_inputs(factory: object, message: str) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        factory()


def test_rejects_subclasses_duplicates_future_rows_and_inconsistent_reports() -> None:
    module = api()

    with pytest.raises(TypeError, match="subclassing"):
        type("ConfigSubclass", (module.MarketResearchBankCapitalBufferDigestConfig,), {})
    with pytest.raises(TypeError, match="subclassing"):
        type("SignalSubclass", (module.MarketResearchBankCapitalBufferDigestSignal,), {})
    with pytest.raises(TypeError, match="subclassing"):
        type("RowSubclass", (module.MarketResearchBankCapitalBufferDigestRow,), {})
    with pytest.raises(TypeError, match="subclassing"):
        type(
            "ReasonCodeCountSubclass",
            (module.MarketResearchBankCapitalBufferDigestReasonCodeCount,),
            {},
        )
    with pytest.raises(TypeError, match="subclassing"):
        type("ReportSubclass", (module.MarketResearchBankCapitalBufferDigestReport,), {})

    with pytest.raises(ValueError, match="timezone-aware"):
        digest(signal(), generated_at=datetime(2026, 7, 4, 15, 0))
    with pytest.raises(ValueError, match="timezone-aware"):
        digest(
            signal(),
            generated_at=datetime(2026, 7, 4, 15, 0, tzinfo=_NoneOffsetTzinfo()),
        )
    with pytest.raises(ValueError, match="after generated_at"):
        digest(signal(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="unique research condition bank keys"):
        digest(signal(), signal())

    good = digest(signal())
    with pytest.raises(ValueError, match="reason_codes"):
        replace(good, reason_codes=("unexpected",))
    with pytest.raises(ValueError, match="observation_count"):
        replace(good, observation_count=d("99.000000"))

    ready_signal = signal("research.bank_capital.ready")
    watch_signal = signal(
        "research.bank_capital.watch",
        condition_id="condition.bank.capital.watch",
        bank_key="money_center_watch",
        cet1_capital_ratio=d("0.101000"),
        minimum_capital_ratio=d("0.080000"),
        market_probability_before=d("0.300000"),
        market_probability_after=d("0.360000"),
    )
    blocked_signal = signal(
        "research.bank_capital.blocked",
        condition_id="condition.bank.capital.blocked",
        bank_key="regional_blocked",
        source_count=d("1.000000"),
        cet1_capital_ratio=d("0.070000"),
        minimum_capital_ratio=d("0.080000"),
        stress_loss_ratio=d("0.030000"),
    )
    mixed = digest(ready_signal, watch_signal, blocked_signal)
    assert mixed == digest(blocked_signal, watch_signal, ready_signal)

    with pytest.raises(ValueError, match="rows must be ranked"):
        replace(mixed, rows=tuple(reversed(mixed.rows)))
    with pytest.raises(ValueError, match="reason_code_counts must be ranked"):
        replace(mixed, reason_code_counts=tuple(reversed(mixed.reason_code_counts)))
    with pytest.raises(ValueError, match="reason_codes must be ranked"):
        replace(mixed, reason_codes=tuple(reversed(mixed.reason_codes)))
    with pytest.raises(ValueError, match="reason_codes must be ranked"):
        replace(mixed.rows[0], reason_codes=tuple(reversed(mixed.rows[0].reason_codes)))


def test_module_scope_is_pure_report_only_and_has_no_forbidden_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/market_research_bank_capital_buffer_digest.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "order",
        "cancel",
        "replace",
        "exchange mutation",
        "private_key",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite",
        "database",
        "durable",
        "store",
        "open(",
        "live trading",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_dataclass_helpers = {"asdict"}
    forbidden_import_roots = {
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "supabase",
        "web3",
        "pathlib",
    }
    forbidden_call_names = {
        "open",
        "connect",
        "request",
        "urlopen",
        "create_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "place_order",
        "float",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
            assert all(
                alias.name not in forbidden_dataclass_helpers
                for alias in node.names
            )
        elif isinstance(node, ast.Call):
            call = node.func
            if isinstance(call, ast.Name):
                assert call.id not in {*forbidden_call_names, *forbidden_dataclass_helpers}
            elif isinstance(call, ast.Attribute):
                assert call.attr not in forbidden_call_names
