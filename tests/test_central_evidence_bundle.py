from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.central_evidence_bundle import (
    EvidenceBundle,
    EvidenceItemAvailability,
    EvidenceItemRequirement,
    ZeroWeightPlaceholder,
    typed_value_equality,
)


AS_OF = datetime(2026, 9, 5, 12, 0, 0, tzinfo=UTC)


def test_placeholder_and_bundle_contracts_fail_closed() -> None:
    with pytest.raises(ValueError):
        ZeroWeightPlaceholder(
            item_name="x",
            availability=EvidenceItemAvailability.READY,
            reason_codes=("never",),
        )
    placeholder = ZeroWeightPlaceholder(
        item_name="x",
        availability=EvidenceItemAvailability.MISSING,
        reason_codes=("item_missing",),
    )
    assert placeholder.weight == Decimal("0")
    with pytest.raises(ValueError):
        ZeroWeightPlaceholder(
            item_name="x",
            availability=EvidenceItemAvailability.MISSING,
            reason_codes=("a", "a"),
        )
    with pytest.raises(ValueError):
        EvidenceBundle(
            team_id="crypto_btc",
            market_reference=" bad reference ",
            as_of=AS_OF,
            items={"a": placeholder},
        )


def test_typed_value_equality_contract() -> None:
    assert typed_value_equality(Decimal("1.0"), Decimal("1.00")) is True
    assert typed_value_equality(Decimal("1.0"), Decimal("1.1")) is False
    assert typed_value_equality(Decimal("1"), "1") is None
    assert typed_value_equality(
        {"a": Decimal("1"), "b": [Decimal("1"), Decimal("2")]},
        {"b": [Decimal("1"), Decimal("2")], "a": Decimal("1.0")},
    ) is True
    assert typed_value_equality({"a": Decimal("1")}, {"a": Decimal("1"), "b": Decimal("2")}) is False
    assert typed_value_equality([Decimal("1"), Decimal("2")], [Decimal("1")]) is False
    # Values outside the decoded envelope domain stay incomparable, never equal.
    assert typed_value_equality({"a": 1}, {"a": 1}) is None
    assert typed_value_equality(None, None) is True
    assert typed_value_equality(True, True) is True
    assert typed_value_equality(True, 1) is None
    assert typed_value_equality(AS_OF, AS_OF) is True


