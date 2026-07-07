from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.research_cross_domain_correlation_alert as api
from polymarket_alpha_lab.research_cross_domain_correlation_alert import (
    ResearchCrossDomainCorrelationAlertConfig,
    ResearchCrossDomainCorrelationAlertObservation,
    ResearchCrossDomainCorrelationAlertReport,
    ResearchCrossDomainCorrelationAlertRow,
    build_research_cross_domain_correlation_alert_report,
    research_cross_domain_correlation_alert_payload,
)


NOW = datetime(2026, 2, 3, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_cross_domain_correlation_alert.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    *,
    left_domain: str = "politics",
    right_domain: str = "btc",
    observed_at: datetime = NOW,
    signed_correlation: Decimal = d("0.300000"),
    co_move_intensity: Decimal = d("0.250000"),
    catalyst_overlap: Decimal = d("0.200000"),
    lag_alignment: Decimal = d("0.200000"),
    confidence: Decimal = d("0.800000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchCrossDomainCorrelationAlertObservation:
    return ResearchCrossDomainCorrelationAlertObservation(
        left_domain=left_domain,
        right_domain=right_domain,
        observed_at=observed_at,
        signed_correlation=signed_correlation,
        co_move_intensity=co_move_intensity,
        catalyst_overlap=catalyst_overlap,
        lag_alignment=lag_alignment,
        confidence=confidence,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[ResearchCrossDomainCorrelationAlertObservation, ...],
    *,
    config: ResearchCrossDomainCorrelationAlertConfig | None = None,
    generated_at: datetime = NOW,
) -> ResearchCrossDomainCorrelationAlertReport:
    return build_research_cross_domain_correlation_alert_report(
        rows,
        generated_at=generated_at,
        config=config,
    )


def walk_payload(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(walk_payload(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(walk_payload(item))
        return tuple(nested)
    return (value,)


def bad_public_fragments() -> tuple[str, ...]:
    return (
        "raw",
        "".join(("candi", "date")),
        "".join(("mar", "ket")),
        "".join(("so", "urce")),
        "".join(("ur", "l")),
        "".join(("d", "sn")),
        "".join(("ta", "ble")),
        "".join(("to", "ken")),
        "".join(("b", "uy")),
        "".join(("se", "ll")),
        "".join(("pos", "ition")),
        "".join(("recom", "mend")),
        "".join(("li", "ve")),
        "".join(("au", "th")),
        "".join(("wal", "let")),
        "".join(("or", "der")),
        "".join(("muta", "tion")),
    )


def test_cross_domain_alert_reduces_pairs_and_sorts_by_risk() -> None:
    summary = report(
        (
            observation(
                left_domain="soccer",
                right_domain="basketball",
                signed_correlation=d("0.680000"),
                co_move_intensity=d("0.550000"),
                catalyst_overlap=d("0.480000"),
                lag_alignment=d("0.500000"),
                confidence=d("0.820000"),
            ),
            observation(),
            observation(
                left_domain="gold",
                right_domain="equity_index",
                signed_correlation=d("-0.850000"),
                co_move_intensity=d("0.780000"),
                catalyst_overlap=d("0.760000"),
                lag_alignment=d("0.640000"),
                confidence=d("0.900000"),
            ),
        ),
    )

    assert summary.alert_status == "block"
    assert summary.observed_pair_count == d("3.000000")
    assert summary.covered_domain_count == d("6.000000")
    assert summary.pass_pair_count == d("1.000000")
    assert summary.watch_pair_count == d("1.000000")
    assert summary.block_pair_count == d("1.000000")
    assert summary.average_correlation_risk_score == d("0.515833")
    assert summary.max_correlation_risk_score == d("0.757500")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.alert_status, row.pair_key) for row in summary.rows) == (
        ("block", "equity_index__gold"),
        ("watch", "soccer__basketball"),
        ("pass", "politics__btc"),
    )

    blocked = summary.rows[0]
    assert blocked.absolute_correlation == d("0.850000")
    assert blocked.correlation_risk_score == d("0.757500")
    assert blocked.confidence_adjusted_risk_score == d("0.681750")
    assert blocked.reason_codes == (
        "cross_domain_correlation_block",
        "absolute_correlation_block",
        "co_move_intensity_block",
        "catalyst_overlap_block",
        "lag_alignment_watch",
        "correlation_risk_score_block",
    )

    watch = summary.rows[1]
    assert watch.correlation_risk_score == d("0.552500")
    assert watch.confidence_adjusted_risk_score == d("0.453050")
    assert watch.reason_codes == (
        "cross_domain_correlation_watch",
        "absolute_correlation_watch",
        "co_move_intensity_watch",
        "lag_alignment_watch",
        "correlation_risk_score_watch",
    )

    ready = summary.rows[2]
    assert ready.alert_status == "pass"
    assert ready.correlation_risk_score == d("0.237500")
    assert ready.confidence_adjusted_risk_score == d("0.190000")
    assert ready.reason_codes == ("cross_domain_correlation_pass",)


def test_empty_cross_domain_alert_is_pass_and_report_only() -> None:
    summary = report(())

    assert summary.alert_status == "pass"
    assert summary.observed_pair_count == d("0.000000")
    assert summary.covered_domain_count == d("0.000000")
    assert summary.pass_pair_count == d("0.000000")
    assert summary.watch_pair_count == d("0.000000")
    assert summary.block_pair_count == d("0.000000")
    assert summary.average_correlation_risk_score == d("0.000000")
    assert summary.max_correlation_risk_score == d("0.000000")
    assert summary.rows == ()
    assert summary.reason_codes == ("cross_domain_correlation_pass",)
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_cross_domain_payload_is_deterministic_decimal_string_only_and_public() -> None:
    rows = (
        observation(left_domain="soccer", right_domain="basketball"),
        observation(left_domain="btc", right_domain="politics"),
    )

    first = report(rows)
    second = report(tuple(reversed(rows)))
    payload = research_cross_domain_correlation_alert_payload(first)
    encoded = json.dumps(payload, sort_keys=True)

    assert first.payload == second.payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload["observed_pair_count"] == "2.000000"
    assert payload["rows"][0]["correlation_risk_score"] == "0.237500"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert not any(isinstance(value, Decimal) for value in walk_payload(payload))
    assert not any(isinstance(value, float) for value in walk_payload(payload))
    for value in bad_public_fragments():
        assert value not in encoded.lower()


def test_frozen_exact_types_and_strict_validation() -> None:
    summary = report((observation(),))

    with pytest.raises(FrozenInstanceError):
        summary.alert_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].correlation_risk_score = d("0.900000")  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadObservation(ResearchCrossDomainCorrelationAlertObservation):
            pass

    with pytest.raises(TypeError):

        class BadRow(ResearchCrossDomainCorrelationAlertRow):
            pass

    with pytest.raises(ValueError, match="left_domain"):
        observation(left_domain=_StringSubclass("politics"))
    with pytest.raises(ValueError, match="right_domain"):
        observation(right_domain="baseball")
    with pytest.raises(ValueError, match="distinct"):
        observation(left_domain="btc", right_domain="btc")
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=_DateTimeSubclass(2026, 2, 3, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="signed_correlation"):
        observation(signed_correlation=_DecimalSubclass("0.300000"))
    with pytest.raises(ValueError, match="co_move_intensity"):
        observation(co_move_intensity=d("0.5000001"))
    with pytest.raises(ValueError, match="catalyst_overlap"):
        observation(catalyst_overlap=0.2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="lag_alignment"):
        observation(lag_alignment=d("1.000001"))
    with pytest.raises(ValueError, match="confidence"):
        observation(confidence=d("-0.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="generated_at"):
        build_research_cross_domain_correlation_alert_report(
            (observation(),),
            generated_at=_DateTimeSubclass(2026, 2, 3, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        report((replace(observation(), observed_at=datetime(2026, 2, 4, tzinfo=UTC)),))
    with pytest.raises(ValueError, match="unique"):
        report((observation(), observation(left_domain="btc", right_domain="politics")))


def test_report_digest_and_consistency_reject_manual_drift() -> None:
    summary = report(
        (
            observation(),
            observation(left_domain="soccer", right_domain="basketball"),
        ),
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(summary, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="observed_pair_count"):
        replace(summary, observed_pair_count=d("3.000000"))
    with pytest.raises(ValueError, match="alert_status"):
        replace(summary, alert_status="block")
    with pytest.raises(ValueError, match="rows"):
        replace(summary, rows=tuple(reversed(summary.rows)))


def test_module_has_no_io_store_or_execution_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_roots = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write",
        "write_bytes",
        "write_text",
        "float",
        "__import__",
    }

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(value in lowered for value in bad_public_fragments())
    for cls in (
        ResearchCrossDomainCorrelationAlertConfig,
        ResearchCrossDomainCorrelationAlertObservation,
        ResearchCrossDomainCorrelationAlertRow,
        ResearchCrossDomainCorrelationAlertReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(value in lowered for value in bad_public_fragments())

    for module_name in imported_modules:
        assert module_name.split(".", 1)[0] not in forbidden_import_roots
    for call_name in call_names:
        assert call_name not in forbidden_calls
    for attr_name in attribute_names:
        assert attr_name not in forbidden_calls
