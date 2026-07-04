from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import importlib
import json
from pathlib import Path
import re
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "market_research_policy_supreme_court_shadow_docket_digest"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "market_research_policy_supreme_court_shadow_docket_digest.py"
)
GENERATED_AT = datetime(2026, 7, 4, 16, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _module():
    return importlib.import_module(MODULE_NAME)


def _observation(
    market_slug: str,
    *,
    case_label: str | None = None,
    question: str | None = None,
    observed_at: datetime | None = None,
    market_deadline_at: datetime | None = None,
    court_signal_at: datetime | None = None,
    emergency_application_pending: bool = False,
    administrative_stay_active: bool = False,
    expedited_response_requested: bool = False,
    source_label: str | None = None,
):
    module = _module()
    label = case_label if case_label is not None else f"{market_slug} caption"
    return module.SupremeCourtShadowDocketMarketObservation(
        market_slug=market_slug,
        case_label=label,
        question=question if question is not None else f"Will {label} resolve soon?",
        observed_at=observed_at if observed_at is not None else GENERATED_AT,
        market_deadline_at=(
            market_deadline_at
            if market_deadline_at is not None
            else GENERATED_AT + timedelta(hours=96)
        ),
        court_signal_at=court_signal_at,
        emergency_application_pending=emergency_application_pending,
        administrative_stay_active=administrative_stay_active,
        expedited_response_requested=expedited_response_requested,
        source_label=(
            source_label
            if source_label is not None
            else f"paper:shadow-docket:{market_slug}"
        ),
    )


def _digest(*observations, **kwargs):
    module = _module()
    return module.build_market_research_policy_supreme_court_shadow_docket_digest(
        observations,
        generated_at=GENERATED_AT,
        **kwargs,
    )


def _risk_codes(digest) -> tuple[str, ...]:
    return tuple(row.risk_code for row in digest.market_rows)


def _assert_no_float(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"float found in payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_float(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_float(item)


def test_empty_inventory_returns_report_only_readonly_digest() -> None:
    digest = _digest()

    assert is_dataclass(digest)
    assert digest.generated_at == GENERATED_AT
    assert digest.digest_status == "empty"
    assert digest.market_count == d("0")
    assert digest.high_risk_market_count == d("0")
    assert digest.watch_market_count == d("0")
    assert digest.low_risk_market_count == d("0")
    assert digest.stale_observation_count == d("0")
    assert digest.unresolved_court_signal_count == d("0")
    assert digest.max_timing_risk_score == d("0.000000")
    assert digest.average_timing_risk_score == d("0.000000")
    assert digest.reason_codes == ("shadow_docket_inventory_empty",)
    assert digest.reason_code_counts == (("shadow_docket_inventory_empty", d("1")),)
    assert digest.summary == ("Supreme Court shadow-docket timing inventory is empty",)
    assert digest.market_rows == ()
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True


def test_high_risk_shadow_docket_timing_market_is_screened() -> None:
    digest = _digest(
        _observation(
            "alpha-emergency-application",
            market_deadline_at=GENERATED_AT + timedelta(hours=18),
            court_signal_at=GENERATED_AT + timedelta(hours=10),
            emergency_application_pending=True,
            administrative_stay_active=True,
            expedited_response_requested=True,
        ),
        _observation(
            "beta-response-window",
            market_deadline_at=GENERATED_AT + timedelta(hours=96),
            court_signal_at=GENERATED_AT + timedelta(hours=54),
            expedited_response_requested=True,
        ),
    )

    assert digest.digest_status == "high_risk"
    assert digest.market_count == d("2")
    assert digest.high_risk_market_count == d("1")
    assert digest.watch_market_count == d("1")
    assert digest.low_risk_market_count == d("0")
    assert digest.max_timing_risk_score == d("15.000000")
    assert digest.average_timing_risk_score == d("10.000000")
    assert _risk_codes(digest) == ("high_risk", "watch")

    high_risk = digest.market_rows[0]
    assert high_risk.market_slug == "alpha-emergency-application"
    assert high_risk.hours_until_market_deadline == d("18.000000")
    assert high_risk.court_signal_to_market_deadline_hours == d("8.000000")
    assert high_risk.timing_risk_score == d("15.000000")
    assert high_risk.reason_codes == (
        "shadow_docket_emergency_application_pending",
        "shadow_docket_administrative_stay_active",
        "shadow_docket_expedited_response_requested",
        "shadow_docket_market_deadline_imminent",
        "shadow_docket_court_signal_near_market_deadline",
    )
    assert digest.reason_code_counts == (
        ("shadow_docket_emergency_application_pending", d("1")),
        ("shadow_docket_administrative_stay_active", d("1")),
        ("shadow_docket_expedited_response_requested", d("2")),
        ("shadow_docket_market_deadline_imminent", d("1")),
        ("shadow_docket_court_signal_near_market_deadline", d("2")),
    )


def test_digest_is_deterministic_for_input_sequence_and_reason_codes() -> None:
    alpha = _observation(
        "alpha-watch",
        market_deadline_at=GENERATED_AT + timedelta(hours=80),
        court_signal_at=GENERATED_AT + timedelta(hours=30),
    )
    beta = _observation(
        "beta-low",
        market_deadline_at=GENERATED_AT + timedelta(days=14),
        court_signal_at=GENERATED_AT + timedelta(days=10),
    )
    zeta = _observation(
        "zeta-high",
        market_deadline_at=GENERATED_AT + timedelta(hours=12),
        court_signal_at=GENERATED_AT + timedelta(hours=9),
        emergency_application_pending=True,
        administrative_stay_active=True,
    )

    first = _digest(beta, zeta, alpha)
    second = _digest(alpha, beta, zeta)

    assert first == second
    assert tuple(row.market_slug for row in first.market_rows) == (
        "zeta-high",
        "alpha-watch",
        "beta-low",
    )
    assert first.reason_codes == (
        "shadow_docket_emergency_application_pending",
        "shadow_docket_administrative_stay_active",
        "shadow_docket_market_deadline_imminent",
        "shadow_docket_court_signal_near_market_deadline",
        "shadow_docket_timing_low_risk",
    )


def test_validation_errors_are_explicit_and_utc_aware() -> None:
    module = _module()

    with pytest.raises(ValueError, match="market_slug must be a lowercase market slug"):
        _observation("Bad Slug")

    with pytest.raises(ValueError, match="source_label must start with paper:"):
        _observation("bad-source", source_label="remote:shadow-docket")

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        _observation("naive-observed", observed_at=datetime(2026, 7, 4, 16, 0))

    with pytest.raises(ValueError, match="market_deadline_at must be after observed_at"):
        _observation(
            "past-deadline",
            market_deadline_at=GENERATED_AT - timedelta(hours=1),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_market_research_policy_supreme_court_shadow_docket_digest(
            (),
            generated_at=datetime(2026, 7, 4, 16, 0),
        )

    with pytest.raises(ValueError, match="observations must be a list or tuple"):
        module.build_market_research_policy_supreme_court_shadow_docket_digest(
            "not observations",
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="observations must contain"):
        module.build_market_research_policy_supreme_court_shadow_docket_digest(
            (object(),),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="high_risk_score_threshold must be a Decimal"):
        _digest(high_risk_score_threshold=7)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="watch_risk_score_threshold must be less than"):
        _digest(
            watch_risk_score_threshold=d("9"),
            high_risk_score_threshold=d("7"),
        )


def test_hard_flags_frozen_dataclasses_and_decimal_only_public_numbers() -> None:
    module = _module()
    observation = _observation("alpha-hard-flags")
    digest = _digest(observation)
    row = digest.market_rows[0]

    for public_name in module.__all__:
        public_value = getattr(module, public_name)
        if isinstance(public_value, type):
            assert is_dataclass(public_value)
            assert public_value.__dataclass_params__.frozen is True
            for field in fields(public_value):
                if re.search(
                    r"(count|hours|score|threshold|ratio|window)$",
                    field.name,
                ):
                    assert field.type in (Decimal, "Decimal")

    with pytest.raises(FrozenInstanceError):
        observation.market_slug = "changed"  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        row.risk_code = "changed"  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        digest.digest_status = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(observation, paper_only=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        replace(row, report_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(digest, readonly=False)


def test_non_default_thresholds_change_screening_without_float_math() -> None:
    observation = _observation(
        "alpha-threshold-sensitive",
        market_deadline_at=GENERATED_AT + timedelta(hours=96),
        court_signal_at=GENERATED_AT + timedelta(hours=48),
    )

    default_digest = _digest(observation)
    tight_digest = _digest(
        observation,
        court_signal_high_risk_window_hours=d("24"),
    )

    assert _risk_codes(default_digest) == ("watch",)
    assert default_digest.reason_codes == (
        "shadow_docket_court_signal_near_market_deadline",
    )
    assert _risk_codes(tight_digest) == ("low",)
    assert tight_digest.reason_codes == ("shadow_docket_timing_low_risk",)
    assert tight_digest.court_signal_high_risk_window_hours == d("24.000000")


def test_payload_uses_decimal_strings_utc_datetimes_and_no_sensitive_text() -> None:
    module = _module()
    observation = _observation(
        "alpha-payload",
        observed_at=datetime(
            2026,
            7,
            4,
            9,
            0,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
        market_deadline_at=GENERATED_AT + timedelta(hours=18),
        court_signal_at=GENERATED_AT + timedelta(hours=12),
        emergency_application_pending=True,
    )
    digest = module.build_market_research_policy_supreme_court_shadow_docket_digest(
        (observation,),
        generated_at=datetime(
            2026,
            7,
            4,
            9,
            0,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )

    payload = module.market_research_policy_supreme_court_shadow_docket_digest_payload(
        digest,
    )

    json.dumps(payload, allow_nan=False, sort_keys=True)
    _assert_no_float(payload)
    assert payload["generated_at"] == "2026-07-04T16:00:00Z"
    assert payload["market_count"] == "1"
    assert payload["max_timing_risk_score"] == "10.000000"
    assert payload["market_rows"][0]["observed_at"] == "2026-07-04T16:00:00Z"
    assert payload["market_rows"][0]["hours_until_market_deadline"] == "18.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert "password" not in repr(payload).lower()
    assert "api_key" not in repr(payload).lower()
    assert "bearer" not in repr(payload).lower()

    with pytest.raises(ValueError, match="digest must be"):
        module.market_research_policy_supreme_court_shadow_docket_digest_payload(
            object(),
        )


def test_static_module_has_no_external_io_or_forbidden_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(MODULE_PATH))
    imported_roots: set[str] = set()
    forbidden_calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "open":
                forbidden_calls.append(func.id)
            elif isinstance(func, ast.Attribute) and func.attr in {
                "connect",
                "glob",
                "iterdir",
                "open",
                "read_bytes",
                "read_text",
                "request",
                "write_bytes",
                "write_text",
            }:
                forbidden_calls.append(func.attr)

    assert imported_roots.isdisjoint(
        {
            "httpx",
            "os",
            "pathlib",
            "psycopg",
            "pymongo",
            "redis",
            "requests",
            "socket",
            "sqlite3",
            "subprocess",
            "urllib",
        },
    )
    assert forbidden_calls == []
    assert re.search(
        r"\b(auth|wallet|broker|order|cancel|replace|exchange|mutation|network|private_key)\b",
        source.lower(),
    ) is None
