from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_information_recency_decay_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def item(**overrides: object):
    module = api()
    values = {
        "topic_key": "election_calendar",
        "source_family": "official",
        "information_age_minutes": d("30.000000"),
        "half_life_minutes": d("120.000000"),
        "refresh_window_minutes": d("240.000000"),
        "source_reliability": d("0.900000"),
        "time_sensitivity": d("0.400000"),
        "resolution_urgency": d("0.300000"),
    }
    values.update(overrides)
    return module.ResearchInformationRecencyItem(**values)


def report(*items: object, **overrides: object):
    module = api()
    return module.build_research_information_recency_decay_report(
        items,
        generated_at=overrides.pop("generated_at", NOW),
        **overrides,
    )


def walk(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        children: list[object] = []
        for child in value.values():
            children.extend(walk(child))
        return tuple(children)
    if isinstance(value, list):
        children = []
        for child in value:
            children.extend(walk(child))
        return tuple(children)
    return (value,)


def test_recency_decay_report_outputs_status_counts_and_payload() -> None:
    module = api()
    result = report(
        item(),
        item(
            topic_key="injury_update",
            source_family="team_report",
            information_age_minutes=d("180.000000"),
            half_life_minutes=d("120.000000"),
            refresh_window_minutes=d("240.000000"),
            time_sensitivity=d("0.800000"),
            resolution_urgency=d("0.800000"),
        ),
        item(
            topic_key="court_deadline",
            source_family="filing_calendar",
            information_age_minutes=d("300.000000"),
            half_life_minutes=d("120.000000"),
            refresh_window_minutes=d("240.000000"),
            source_reliability=d("0.700000"),
            time_sensitivity=d("0.900000"),
            resolution_urgency=d("0.900000"),
        ),
    )

    assert result.report_status == "block"
    assert result.item_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.reason_codes == (
        "refresh_window_breached",
        "recency_weight_pass",
        "recency_weight_watch",
        "recency_weight_block",
        "expiry_risk_low",
        "expiry_risk_elevated",
        "expiry_risk_high",
        "time_pressure_high",
        "refresh_priority_critical",
        "refresh_priority_high",
        "refresh_priority_low",
    )

    assert tuple(row.topic_key for row in result.rows) == (
        "court_deadline",
        "injury_update",
        "election_calendar",
    )
    assert tuple(row.recency_status for row in result.rows) == (
        "block",
        "watch",
        "pass",
    )
    assert tuple(row.refresh_priority for row in result.rows) == (
        "critical",
        "high",
        "low",
    )
    assert result.rows[0].refresh_window_remaining_minutes == d("0.000000")
    assert result.rows[0].expiry_risk_score == d("0.876256")
    assert result.rows[1].expiry_risk_score == d("0.681802")
    assert result.rows[2].expiry_risk_score == d("0.243193")

    payload = result.payload
    assert payload == module.research_information_recency_decay_report_payload(result)
    json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert payload["item_count"] == "3.000000"
    assert payload["max_expiry_risk_score"] == "0.876256"
    assert payload["rows"][0]["refresh_priority"] == "critical"
    assert payload["rows"][0]["expiry_risk_score"] == "0.876256"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(type(value) is Decimal for value in walk(payload))
    assert not any(type(value) is float for value in walk(payload))
    assert not any(type(value) is int for value in walk(payload))


def test_empty_report_blocks_with_critical_refresh_priority() -> None:
    result = report()

    assert result.report_status == "block"
    assert result.overall_refresh_priority == "critical"
    assert result.item_count == d("0.000000")
    assert result.reason_codes == ("empty_information", "refresh_priority_critical")
    assert result.rows == ()


def test_validation_requires_frozen_exact_decimal_and_safe_flags() -> None:
    module = api()
    result = report(item())

    with pytest.raises(FrozenInstanceError):
        result.report_status = "pass"  # type: ignore[misc]

    with pytest.raises(ValueError, match="information_age_minutes must be a Decimal"):
        item(information_age_minutes=30)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="source_reliability must be a Decimal"):
        item(source_reliability=0.9)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="source_reliability must be a Decimal"):
        item(source_reliability=_DecimalSubclass("0.900000"))

    with pytest.raises(ValueError, match="information_age_minutes must be finite"):
        item(information_age_minutes=Decimal("NaN"))

    with pytest.raises(ValueError, match="half_life_minutes must be positive"):
        item(half_life_minutes=d("0.000000"))

    with pytest.raises(ValueError, match="source_reliability must be between zero and one"):
        item(source_reliability=d("1.000001"))

    with pytest.raises(ValueError, match="paper_only"):
        item(paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)

    with pytest.raises(ValueError, match="must match rows"):
        replace(result, block_count=d("1.000000"))

    with pytest.raises(ValueError, match="items must be ResearchInformationRecencyItem"):
        report(object())

    with pytest.raises(ValueError, match="config must be"):
        module.build_research_information_recency_decay_report(
            (),
            generated_at=NOW,
            config=object(),
        )


def test_public_payload_excludes_source_url_text_ref_and_market_id_surfaces() -> None:
    module = api()
    result = report(item())
    payload = result.payload
    lowered_keys = tuple(_flatten_keys(payload))
    joined_keys = " ".join(lowered_keys)

    for forbidden in ("source_url", "source_text", "source_ref", "market_id"):
        assert forbidden not in joined_keys

    for unsafe_key in ("market_candidate", "http_feed", "topic?query", "candidate@example"):
        with pytest.raises(ValueError):
            item(topic_key=unsafe_key)

    for cls in (
        module.ResearchInformationRecencyConfig,
        module.ResearchInformationRecencyItem,
        module.ResearchInformationRecencyRow,
        module.ResearchInformationRecencyDecayReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert lowered not in {"source_url", "source_text", "source_ref", "market_id"}
            assert not lowered.endswith("_url")
            assert not lowered.endswith("_ref")


def test_payload_rejects_bad_dicts_and_unknown_fields() -> None:
    module = api()

    with pytest.raises(ValueError, match="payload must be readonly"):
        module.research_information_recency_decay_report_payload(
            {"paper_only": True, "report_only": True, "readonly": False},
        )

    with pytest.raises(ValueError, match="numeric payload values must be Decimal"):
        module.research_information_recency_decay_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "item_count": 1,
            },
        )

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        module.research_information_recency_decay_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "max_expiry_risk_score": 0.5,
            },
        )

    with pytest.raises(ValueError, match="payload field is not supported"):
        module.research_information_recency_decay_report_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "source_url": "x"},
        )

    with pytest.raises(ValueError, match="report must be"):
        module.research_information_recency_decay_report_payload(object())


def test_module_scope_is_report_only_without_side_effect_surfaces() -> None:
    module = api()
    source = Path(
        "src/polymarket_alpha_lab/research_information_recency_decay_report.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
        "order placement",
        "submit_order",
        "cancel_order",
    ):
        assert forbidden not in lowered

    for public_name in module.__all__:
        lowered_name = public_name.lower()
        assert "url" not in lowered_name
        assert "market_id" not in lowered_name

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}


def _flatten_keys(value: object) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, child in value.items():
            keys.append(key.lower())
            keys.extend(_flatten_keys(child))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for child in value:
            keys.extend(_flatten_keys(child))
        return tuple(keys)
    return ()
