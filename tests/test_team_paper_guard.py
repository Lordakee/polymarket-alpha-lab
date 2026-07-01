from dataclasses import dataclass
from decimal import Decimal

import pytest

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


@dataclass(frozen=True)
class SafePacket:
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class UnsafePacket:
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = False


def test_require_paper_only_flags_rejects_false_flags():
    require_paper_only_flags("safe", SafePacket())

    with pytest.raises(ValueError, match="readonly must be True"):
        require_paper_only_flags("unsafe", UnsafePacket())


def test_reject_unsafe_surface_fields_blocks_live_surface_terms():
    safe_payload = {"forecast_probability": Decimal("0.510000")}
    reject_unsafe_surface_fields("payload", safe_payload)

    with pytest.raises(ValueError, match="unsafe live surface field"):
        reject_unsafe_surface_fields("payload", {"order_submission": "never"})

    with pytest.raises(ValueError, match="unsafe live surface field"):
        reject_unsafe_surface_fields("payload", {"wallet": {"address": "0x0"}})


def test_json_ready_no_floats_serializes_decimals_and_rejects_float():
    payload = json_ready_no_floats(
        {
            "probability": Decimal("0.510000"),
            "rows": ({"team_id": "crypto_btc"},),
            "paper_only": True,
        },
    )

    assert payload == {
        "probability": "0.510000",
        "rows": [{"team_id": "crypto_btc"}],
        "paper_only": True,
    }

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        json_ready_no_floats({"probability": 0.51})

