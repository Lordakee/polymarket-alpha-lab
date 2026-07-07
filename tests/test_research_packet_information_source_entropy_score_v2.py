from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from json import dumps
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_packet_information_source_entropy_score_v2"


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "packet_id": "packet-information-source-entropy-v2",
        "source_id": "source-alpha",
        "source_family": "official",
        "claim_id": "claim-alpha",
        "official_source": True,
        "stale_source": False,
        "contradiction_group_id": None,
    }
    values.update(overrides)
    return module.ResearchPacketInformationSourceEntropyObservation(**values)


def balanced_observations() -> tuple[object, ...]:
    return (
        observation(
            source_id="source-official-a",
            source_family="official",
            claim_id="claim-alpha",
            official_source=True,
            stale_source=False,
        ),
        observation(
            source_id="source-official-b",
            source_family="official",
            claim_id="claim-beta",
            official_source=True,
            stale_source=False,
        ),
        observation(
            source_id="source-expert-a",
            source_family="expert",
            claim_id="claim-alpha",
            official_source=False,
            stale_source=False,
        ),
        observation(
            source_id="source-expert-b",
            source_family="expert",
            claim_id="claim-gamma",
            official_source=False,
            stale_source=True,
        ),
        observation(
            source_id="source-market-a",
            source_family="market",
            claim_id="claim-delta",
            official_source=False,
            stale_source=False,
            contradiction_group_id="cluster-alpha",
        ),
        observation(
            source_id="source-market-b",
            source_family="market",
            claim_id="claim-epsilon",
            official_source=False,
            stale_source=False,
        ),
    )


def concentrated_observations() -> tuple[object, ...]:
    return (
        observation(
            source_id="source-official-a",
            source_family="official",
            claim_id="claim-alpha",
            official_source=True,
            stale_source=True,
            contradiction_group_id="cluster-alpha",
        ),
        observation(
            source_id="source-official-b",
            source_family="official",
            claim_id="claim-alpha",
            official_source=True,
            stale_source=True,
            contradiction_group_id="cluster-alpha",
        ),
        observation(
            source_id="source-official-c",
            source_family="official",
            claim_id="claim-alpha",
            official_source=True,
            stale_source=False,
            contradiction_group_id="cluster-alpha",
        ),
        observation(
            source_id="source-official-d",
            source_family="official",
            claim_id="claim-alpha",
            official_source=True,
            stale_source=False,
        ),
    )


def score_input(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "packet_id": "packet-information-source-entropy-v2",
        "source_observations": balanced_observations(),
        "reason_codes": ("research_packet_present",),
    }
    values.update(overrides)
    return module.ResearchPacketInformationSourceEntropyScoreV2Input(**values)


def score(subject: object | None = None):
    module = api()
    return module.score_research_packet_information_source_entropy_score_v2(
        score_input() if subject is None else subject,
    )


def public_field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_no_float_or_int_values(value: Any) -> None:
    if type(value) is float:
        raise AssertionError(f"unexpected float value {value!r}")
    if type(value) is int:
        raise AssertionError(f"unexpected int value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def assert_public_numbers_are_decimal_only(value: object) -> None:
    if type(value) in (bool, str) or value is None:
        return
    if isinstance(value, Decimal):
        assert type(value) is Decimal
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numbers_are_decimal_only(getattr(value, field.name))
        return
    if isinstance(value, tuple):
        for item in value:
            assert_public_numbers_are_decimal_only(item)
        return
    assert type(value) is not float
    assert type(value) is not int


def test_balanced_source_family_distribution_scores_high_entropy() -> None:
    module = api()

    result = score()

    assert result.source_count == d("6.000000")
    assert result.source_family_count == d("3.000000")
    assert result.source_family_distribution == (
        module.ResearchPacketInformationSourceFamilyDistributionBucket(
            source_family="expert",
            source_count=d("2.000000"),
            source_share=d("0.333333"),
        ),
        module.ResearchPacketInformationSourceFamilyDistributionBucket(
            source_family="market",
            source_count=d("2.000000"),
            source_share=d("0.333333"),
        ),
        module.ResearchPacketInformationSourceFamilyDistributionBucket(
            source_family="official",
            source_count=d("2.000000"),
            source_share=d("0.333333"),
        ),
    )
    assert result.official_source_count == d("2.000000")
    assert result.official_source_share == d("0.333333")
    assert result.duplicate_claim_count == d("1.000000")
    assert result.duplicate_claim_ratio == d("0.166667")
    assert result.stale_source_count == d("1.000000")
    assert result.stale_share == d("0.166667")
    assert result.contradiction_group_count == d("1.000000")
    assert result.contradiction_concentration == d("0.166667")
    assert result.source_family_entropy_score == d("1.000000")
    assert result.source_entropy_score == d("0.875000")
    assert result.entropy_band == "high"
    assert result.reason_codes == (
        "research_packet_present",
        "research_packet_information_source_entropy_score_v2",
        "entropy_band_high",
        "source_family_distribution_balanced",
        "official_source_share_present",
        "duplicate_claim_ratio_within_limit",
        "stale_share_within_limit",
        "contradiction_concentration_within_limit",
    )
    assert len(result.derived_validation_digest) == 64
    assert type(result.source_entropy_score) is Decimal
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_concentrated_duplicate_stale_contradictory_sources_score_low_entropy() -> None:
    result = score(
        score_input(
            source_observations=concentrated_observations(),
            reason_codes=(),
        ),
    )

    assert result.source_count == d("4.000000")
    assert result.source_family_count == d("1.000000")
    assert result.source_family_distribution[0].source_share == d("1.000000")
    assert result.official_source_share == d("1.000000")
    assert result.duplicate_claim_count == d("3.000000")
    assert result.duplicate_claim_ratio == d("0.750000")
    assert result.stale_source_count == d("2.000000")
    assert result.stale_share == d("0.500000")
    assert result.contradiction_group_count == d("1.000000")
    assert result.contradiction_concentration == d("0.750000")
    assert result.source_family_entropy_score == d("0.000000")
    assert result.source_entropy_score == d("0.000000")
    assert result.entropy_band == "low"
    assert result.reason_codes == (
        "research_packet_information_source_entropy_score_v2",
        "entropy_band_low",
        "source_family_distribution_concentrated",
        "official_source_share_high",
        "duplicate_claim_ratio_elevated",
        "stale_share_elevated",
        "contradiction_concentration_elevated",
    )


def test_empty_packet_has_empty_entropy_band_and_zero_decimal_metrics() -> None:
    result = score(score_input(source_observations=(), reason_codes=()))

    assert result.source_count == d("0.000000")
    assert result.source_family_count == d("0.000000")
    assert result.source_family_distribution == ()
    assert result.official_source_share == d("0.000000")
    assert result.duplicate_claim_ratio == d("0.000000")
    assert result.stale_share == d("0.000000")
    assert result.contradiction_concentration == d("0.000000")
    assert result.source_family_entropy_score == d("0.000000")
    assert result.source_entropy_score == d("0.000000")
    assert result.entropy_band == "empty"
    assert result.reason_codes == (
        "research_packet_information_source_entropy_score_v2",
        "entropy_band_empty",
        "source_family_distribution_empty",
        "official_source_share_absent",
        "duplicate_claim_ratio_within_limit",
        "stale_share_within_limit",
        "contradiction_concentration_within_limit",
    )


def test_payload_serializes_decimals_as_strings_and_revalidates_digest() -> None:
    module = api()
    result = score()
    payload = module.research_packet_information_source_entropy_score_v2_payload(result)

    dumps(payload, sort_keys=True)
    assert payload == result.payload
    assert payload["source_count"] == "6.000000"
    assert payload["source_entropy_score"] == "0.875000"
    assert payload["entropy_band"] == "high"
    assert payload["source_family_distribution"][0] == {
        "source_family": "expert",
        "source_count": "2.000000",
        "source_share": "0.333333",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    reversed_result = score(
        score_input(source_observations=tuple(reversed(balanced_observations()))),
    )
    assert reversed_result == result
    assert reversed_result.derived_validation_digest == result.derived_validation_digest

    object.__setattr__(result, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_packet_information_source_entropy_score_v2_payload(result)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    subject = score_input()
    result = score(subject)

    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert is_dataclass(result.source_family_distribution[0])
    assert (
        module.ResearchPacketInformationSourceEntropyObservation.__dataclass_params__.frozen
    )
    assert (
        module.ResearchPacketInformationSourceFamilyDistributionBucket
        .__dataclass_params__
        .frozen
    )
    assert (
        module.ResearchPacketInformationSourceEntropyScoreV2Input
        .__dataclass_params__
        .frozen
    )
    assert (
        module.ResearchPacketInformationSourceEntropyScoreV2Result
        .__dataclass_params__
        .frozen
    )

    with pytest.raises(FrozenInstanceError):
        subject.packet_id = "other-packet"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.entropy_band = "medium"  # type: ignore[misc]

    assert_public_numbers_are_decimal_only(subject)
    assert_public_numbers_are_decimal_only(result)

    decimal_fields = {
        "ResearchPacketInformationSourceFamilyDistributionBucket": {
            "source_count",
            "source_share",
        },
        "ResearchPacketInformationSourceEntropyScoreV2Input": {
            "high_entropy_threshold",
            "medium_entropy_threshold",
            "metric_watch_threshold",
            "official_overreliance_threshold",
        },
        "ResearchPacketInformationSourceEntropyScoreV2Result": {
            "source_count",
            "source_family_count",
            "official_source_count",
            "official_source_share",
            "duplicate_claim_count",
            "duplicate_claim_ratio",
            "stale_source_count",
            "stale_share",
            "contradiction_group_count",
            "contradiction_concentration",
            "source_family_entropy_score",
            "source_entropy_score",
        },
    }
    for class_name, field_names in decimal_fields.items():
        annotations = getattr(module, class_name).__annotations__
        for field_name in field_names:
            assert annotations[field_name] == "Decimal"

    with pytest.raises(ValueError, match="source_id must be a public identifier"):
        observation(source_id=" source-alpha")
    with pytest.raises(ValueError, match="official_source must be a bool"):
        observation(official_source=1)
    with pytest.raises(ValueError, match="source_observations must be a tuple"):
        score_input(source_observations=[observation()])
    with pytest.raises(ValueError, match="packet_id must match"):
        score_input(source_observations=(observation(packet_id="other-packet"),))
    with pytest.raises(ValueError, match="source_id values must be unique"):
        score_input(source_observations=(observation(), observation()))
    with pytest.raises(ValueError, match="high_entropy_threshold must be a Decimal"):
        score_input(high_entropy_threshold=DecimalSubclass("0.750000"))
    with pytest.raises(ValueError, match="medium_entropy_threshold must be between"):
        score_input(medium_entropy_threshold=d("1.000001"))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        score_input(reason_codes=["research_packet_present"])
    with pytest.raises(ValueError, match="paper_only must be True"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        score_input(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="score_input"):
        score(object())

    rebuilt = module.ResearchPacketInformationSourceEntropyScoreV2Result(
        **public_field_values(result),
    )
    assert rebuilt == result


def test_manual_result_rebuilds_validate_derived_fields_and_digest() -> None:
    result = score()

    with pytest.raises(ValueError, match="official_source_share must match"):
        replace(result, official_source_share=d("0.500000"))
    with pytest.raises(ValueError, match="source_family_distribution must match"):
        replace(result, source_family_distribution=())
    with pytest.raises(ValueError, match="source_entropy_score must match"):
        replace(result, source_entropy_score=d("0.900000"))
    with pytest.raises(ValueError, match="entropy_band must match"):
        replace(result, entropy_band="medium")
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(result, reason_codes=("entropy_band_high",))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)


def test_rejects_digest_tampering_and_unsafe_public_payload_keys_and_values() -> None:
    module = api()
    result = score()

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.ResearchPacketInformationSourceEntropyScoreV2Result(
            **{
                **public_field_values(result),
                "derived_validation_digest": "0" * 64,
            },
        )

    unsafe_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )
    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe"):
            observation(source_id=f"{term}-source")
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_research_packet_information_source_entropy_score_v2_unsafe_payload(
                "unsafe-test",
                {f"{term}_field": "paper_report"},
            )
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_research_packet_information_source_entropy_score_v2_unsafe_payload(
                "unsafe-test",
                {"safe_field": f"{term}_value"},
            )


def test_module_has_no_unsafe_runtime_surface_or_float_literals() -> None:
    module = api()
    source = Path(
        "src/polymarket_alpha_lab/research_packet_information_source_entropy_score_v2.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()

    forbidden_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "private_key",
        "submit_order",
        "cancel_order",
        "place_order",
        "create_order",
        "db_write",
        "open(",
        "Path(",
        ".read",
        ".write",
        "commit(",
        "connect(",
        "execute(",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source

    unsafe_surface_terms = (
        "live",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "wallet",
        " auth",
        "order",
        "buy",
        "sell",
        "trade",
        "trading",
    )
    for term in unsafe_surface_terms:
        assert term not in lowered

    tree = ast.parse(source)
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}

    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
    assert module.__all__ == (
        "ENTROPY_BANDS",
        "ResearchPacketInformationSourceEntropyObservation",
        "ResearchPacketInformationSourceFamilyDistributionBucket",
        "ResearchPacketInformationSourceEntropyScoreV2Input",
        "ResearchPacketInformationSourceEntropyScoreV2Result",
        "score_research_packet_information_source_entropy_score_v2",
        "research_packet_information_source_entropy_score_v2_payload",
        "reject_research_packet_information_source_entropy_score_v2_unsafe_payload",
    )
    root = importlib.import_module("polymarket_alpha_lab")
    assert "research_packet_information_source_entropy_score_v2" not in getattr(
        root,
        "__all__",
        (),
    )
