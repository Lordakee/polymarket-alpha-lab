"""Bounded in-memory inputs for research-to-paper scenario assembly.

No I/O, durable queue, authenticated fee feed or implicit trading permission.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
import json

from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventCostAssumptions, PaperCostAwareEventStrategyConfig,
)
from polymarket_alpha_lab.research_resolution import digest, utc
from polymarket_alpha_lab.team_research_agent_types import hard_flags, identifier
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot

MAX_BOOK_BYTES = 131072
MAX_SCENARIOS = 100
MAX_INPUT_BYTES = 8388608


def bounded_decimal(value: Decimal, *, positive: bool = False, maximum=Decimal('1000000')) -> Decimal:
    if (type(value) is not Decimal or not value.is_finite()
            or len(value.as_tuple().digits) > 18 or not -9 <= value.as_tuple().exponent <= 0
            or value < 0 or value > maximum or (positive and value == 0)):
        raise ValueError('research_paper_decimal_invalid')
    return value


def json_value(value):
    if type(value) is datetime: return value.isoformat()
    if type(value) is Decimal: return format(value, 'f')
    if type(value) in (tuple, list): return [json_value(x) for x in value]
    if type(value) is dict: return {k: json_value(v) for k, v in value.items()}
    if value is None or type(value) in (str, bool, int): return value
    raise ValueError('research_paper_serialization_invalid')


def content_hash(value) -> str:
    return sha256(json.dumps(json_value(value), sort_keys=True, ensure_ascii=True,
                             separators=(',', ':'), allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class ResearchPaperBook:
    captured_at: datetime
    raw_json: bytes = field(repr=False)

    def __post_init__(self):
        object.__setattr__(self, 'captured_at', utc('captured_at', self.captured_at))
        if type(self.raw_json) is not bytes or not 1 <= len(self.raw_json) <= MAX_BOOK_BYTES:
            raise ValueError('research_paper_book_size_invalid')

    @property
    def content_sha256(self):
        return sha256(self.raw_json).hexdigest()


@dataclass(frozen=True, slots=True)
class ResearchPaperScenario:
    """Explicit hypothetical inputs, not a prospective trade or persisted intent.

    Fees use the existing quadratic per-share SCENARIO model. All six costs and
    risk thresholds must be supplied; no market tariff/defaults are inferred.
    """
    record_id: str
    record_sha256: str
    decision_at: datetime
    market: GammaMarketSnapshot = field(repr=False)
    yes_book: ResearchPaperBook = field(repr=False)
    no_book: ResearchPaperBook = field(repr=False)
    requested_size: Decimal
    costs: PaperCostAwareEventCostAssumptions
    gates: PaperCostAwareEventStrategyConfig
    resolution_risk: Decimal
    assumptions_id: str
    max_age_seconds: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self):
        hard_flags(self)
        identifier('record_id', self.record_id)
        identifier('assumptions_id', self.assumptions_id)
        digest(self.record_sha256)
        object.__setattr__(self, 'decision_at', utc('decision_at', self.decision_at))
        for name, expected in (('market', GammaMarketSnapshot), ('yes_book', ResearchPaperBook),
                ('no_book', ResearchPaperBook), ('costs', PaperCostAwareEventCostAssumptions),
                ('gates', PaperCostAwareEventStrategyConfig)):
            value = getattr(self, name)
            if type(value) is not expected:
                raise ValueError('research_paper_input_type_invalid')
            copied = replace(value)
            if name == 'market': copied = replace(copied, fetched_at=utc('fetched_at', copied.fetched_at))
            object.__setattr__(self, name, copied)
        bounded_decimal(self.requested_size, positive=True)
        bounded_decimal(self.resolution_risk, maximum=Decimal(1))
        for name, value in asdict(self.costs).items():
            bounded_decimal(value, maximum=Decimal(1))
        identifier('config_version', self.gates.config_version)
        for name, value in asdict(self.gates).items():
            if name != 'config_version': bounded_decimal(value)
        if type(self.max_age_seconds) is not int or not 1 <= self.max_age_seconds <= 300:
            raise ValueError('research_paper_age_invalid')

    def binding(self):
        s = replace(self)
        return dict(record_id=s.record_id, record_sha256=s.record_sha256,
            decision_at=s.decision_at, market_sha256=s.market.content_sha256,
            market_fetched_at=s.market.fetched_at,
            yes_book_sha256=s.yes_book.content_sha256, yes_book_captured_at=s.yes_book.captured_at,
            no_book_sha256=s.no_book.content_sha256, no_book_captured_at=s.no_book.captured_at,
            requested_size=s.requested_size, costs=asdict(s.costs), gates=asdict(s.gates),
            resolution_risk=s.resolution_risk, assumptions_id=s.assumptions_id,
            max_age_seconds=s.max_age_seconds, fee_model='quadratic_per_share_scenario',
            execution_price_basis='worst_consumed_ask_upper_bound', full_size_required=True)


def copy_scenarios(values):
    if type(values) is not tuple or len(values) > MAX_SCENARIOS:
        raise ValueError('research_paper_scenarios_invalid')
    if any(type(row) is not ResearchPaperScenario for row in values):
        raise ValueError('research_paper_scenarios_invalid')
    rows = tuple(replace(row) for row in values)
    if len({row.record_id for row in rows}) != len(rows):
        raise ValueError('research_paper_duplicate_record')
    if sum(len(s.market.raw_json) + len(s.yes_book.raw_json) + len(s.no_book.raw_json) for s in rows) > MAX_INPUT_BYTES:
        raise ValueError('research_paper_input_limit')
    return rows


__all__ = ('ResearchPaperBook', 'ResearchPaperScenario')
