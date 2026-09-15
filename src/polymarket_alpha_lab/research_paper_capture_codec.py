"""Closed, canonical paper inputs. Raw bytes survive invalid-JSON rejection.

This codec is not an input-file loader, provider client or trade authorization.
"""
from __future__ import annotations

import base64
from dataclasses import asdict, replace
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
import json

from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventCostAssumptions, PaperCostAwareEventStrategyConfig,
)
from polymarket_alpha_lab.research_paper_inputs import (
    ResearchPaperBook, ResearchPaperScenario, copy_scenarios, json_value,
)
from polymarket_alpha_lab.team_research_agent_types import strict_json
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot

VERSION = 'research-paper-input-v1'
MAX_PAYLOAD_BYTES = 4194304
MAX_RESULT_BYTES = 1048576


def dump(value) -> str:
    return json.dumps(json_value(value), ensure_ascii=True, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)


def checksum(payload: str) -> str:
    return sha256(payload.encode('utf-8')).hexdigest()


def encode_paper_scenario(scenario: ResearchPaperScenario) -> str:
    """Bind every input, including capture times, exact raw bytes and all costs."""
    s = copy_scenarios((scenario,))[0]
    data = dict(schema_version=VERSION, record_id=s.record_id,
        record_sha256=s.record_sha256, decision_at=s.decision_at,
        market=dict(market_slug=s.market.market_slug, fetched_at=s.market.fetched_at,
                    raw_base64=base64.b64encode(s.market.raw_json).decode('ascii')),
        yes_book=dict(captured_at=s.yes_book.captured_at,
                      raw_base64=base64.b64encode(s.yes_book.raw_json).decode('ascii')),
        no_book=dict(captured_at=s.no_book.captured_at,
                     raw_base64=base64.b64encode(s.no_book.raw_json).decode('ascii')),
        requested_size=s.requested_size, costs=asdict(s.costs), gates=asdict(s.gates),
        resolution_risk=s.resolution_risk, assumptions_id=s.assumptions_id,
        max_age_seconds=s.max_age_seconds, paper_only=True, report_only=True, readonly=True)
    payload = dump(data)
    if len(payload.encode('utf-8')) > MAX_PAYLOAD_BYTES:
        raise ValueError('paper_capture_input_limit')
    return payload


def decode_paper_scenario(payload: str, expected_sha256: str) -> ResearchPaperScenario:
    """Re-encoding rejects extra/defaulted fields and noncanonical representations."""
    try:
        if (type(payload) is not str or not 1 <= len(payload.encode('utf-8')) <= MAX_PAYLOAD_BYTES
                or checksum(payload) != expected_sha256):
            raise ValueError
        v = strict_json(payload)
        if type(v) is not dict or v.pop('schema_version') != VERSION:
            raise ValueError
        for name in ('market', 'yes_book', 'no_book'):
            value = dict(v[name])
            raw = base64.b64decode(value.pop('raw_base64'), validate=True)
            clock = 'fetched_at' if name == 'market' else 'captured_at'
            value[clock] = datetime.fromisoformat(value[clock])
            cls = GammaMarketSnapshot if name == 'market' else ResearchPaperBook
            v[name] = cls(raw_json=raw, **value)
        for name in ('requested_size', 'resolution_risk'):
            if type(v[name]) is not str:
                raise ValueError
            v[name] = Decimal(v[name])
        for name, cls in (('costs', PaperCostAwareEventCostAssumptions),
                          ('gates', PaperCostAwareEventStrategyConfig)):
            value = v[name]
            if type(value) is not dict or any(type(x) is not str for x in value.values()):
                raise ValueError
            v[name] = cls(**{k: x if k == 'config_version' else Decimal(x) for k, x in value.items()})
        v['decision_at'] = datetime.fromisoformat(v['decision_at'])
        s = ResearchPaperScenario(**v)
        if encode_paper_scenario(s) != payload:
            raise ValueError
        return s
    except Exception:
        raise ValueError('paper_capture_input_invalid') from None


__all__ = ('encode_paper_scenario', 'decode_paper_scenario')
