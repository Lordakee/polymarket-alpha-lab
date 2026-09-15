"""Compose original research selection, cost/risk decisions and book-walk fills.

Retrospective, in-memory scenarios only. No new score, tariff, portfolio, trade
journal or execution permission. Managed reads keep the original history gate.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime
from decimal import Context, Decimal, DivisionByZero, InvalidOperation, Overflow, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN, localcontext
import re

from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventMarketSnapshot, build_paper_cost_aware_event_strategy_report,
)
from polymarket_alpha_lab.normalize import normalize_order_book
from polymarket_alpha_lab.paper import PaperOrder, simulate_order_book_fill
from polymarket_alpha_lab.research_crypto_launch import CryptoLaunchBlocked, CryptoResearchSpec, market_terms
from polymarket_alpha_lab.research_crypto_observation import assess_crypto_observation_time
from polymarket_alpha_lab.research_execution import CapturedResearchExecution
from polymarket_alpha_lab.research_execution_psycopg import (
    inspect_captured_research_with_psycopg, load_captured_research_evaluation_with_psycopg,
)
from polymarket_alpha_lab.research_paper_inputs import (
    ResearchPaperScenario, bounded_decimal, content_hash, copy_scenarios, json_value,
)
from polymarket_alpha_lab.team_research_agent_types import hard_flags, strict_json
from polymarket_alpha_lab.team_research_evaluation import ResearchEvaluationReport

# Finite input magnitudes/digits/levels keep all additions/products well within
# this private context. Never inherit a caller's low precision or rounding mode.
_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN, Emin=-999999, Emax=999999,
                   traps=[InvalidOperation, DivisionByZero, Overflow])
_ELIGIBLE = ('scored', 'outcome_pending')


class _Blocked(ValueError):
    pass


def _require(condition, reason):
    if not condition: raise _Blocked(reason)


def _decode(value):
    try: return strict_json(value.decode('utf-8') if type(value) is bytes else value)
    except (ValueError, UnicodeError, RecursionError):
        raise _Blocked('malformed_market_or_book') from None


def _number(value, *, maximum=Decimal(1000000)):
    _require(type(value) in (str, int, Decimal), 'market_or_book_number_invalid')
    _require(re.fullmatch(r'(?:0|[1-9][0-9]{0,6})(?:\.[0-9]{1,9})?', str(value)) is not None,
             'market_or_book_number_invalid')
    try: return bounded_decimal(Decimal(value), positive=True, maximum=maximum)
    except ValueError:
        raise _Blocked('market_or_book_number_invalid') from None


def _array(value):
    result = _decode(value) if type(value) is str else value
    _require(type(result) is list, 'market_token_mapping_invalid')
    return result


def _book(evidence, token, condition_id, at, record_at, max_age, tick):
    _require(record_at <= evidence.captured_at <= at and
             (at - evidence.captured_at).total_seconds() <= max_age, 'book_time_invalid')
    raw = _decode(evidence.raw_json)
    _require(type(raw) is dict and raw.get('asset_id') == token and raw.get('market') == condition_id,
             'book_identity_mismatch')
    _require('token_id' not in raw or raw['token_id'] == token, 'book_identity_mismatch')
    timestamp = raw.get('timestamp')
    _require(type(timestamp) is str and re.fullmatch(r'[0-9]{13}', timestamp) is not None,
             'book_timestamp_invalid')
    # Integer timedelta avoids float conversion of Unix milliseconds.
    from datetime import timedelta
    observed = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(milliseconds=int(timestamp))
    _require(observed <= evidence.captured_at and (at-observed).total_seconds() <= max_age,
             'book_timestamp_invalid')
    for side in ('bids', 'asks'):
        levels = raw.get(side)
        _require(type(levels) is list and len(levels) <= 200, 'book_levels_invalid')
        prices = set()
        for level in levels:
            _require(type(level) is dict and set(level) == {'price', 'size'}, 'book_levels_invalid')
            values = []
            for name in ('price', 'size'):
                v = level[name]
                _require(type(v) is str and re.fullmatch(r'(?:0|[1-9][0-9]{0,6})(?:\.[0-9]{1,9})?', v) is not None,
                         'book_levels_invalid')
                d = _number(v, maximum=Decimal(1) if name == 'price' else Decimal(1000000))
                values.append(d)
            _require(values[0] < 1 and values[0] not in prices and values[0] % tick == 0, 'book_levels_invalid')
            prices.add(values[0])
    book = normalize_order_book(raw, captured_at=evidence.captured_at)
    _require(book.best_bid is not None and book.best_ask is not None, 'two_sided_book_required')
    _require(book.best_bid < book.best_ask, 'crossed_or_locked_book')
    return book


def _scenario(execution, s):
    request, record = execution.request, execution.record
    intake, research = record.run.intake, record.run.research
    _require(intake.team_id in ('crypto_btc', 'crypto_eth'), 'unsupported_team')
    _require(record.recorded_at <= s.decision_at < request.forecast_cutoff_at, 'paper_decision_time_invalid')
    _require(record.recorded_at <= s.market.fetched_at <= s.decision_at and
             (s.decision_at-s.market.fetched_at).total_seconds() <= s.max_age_seconds, 'market_time_invalid')
    raw = _decode(s.market.raw_json)
    _require(type(raw) is dict, 'market_invalid')
    _require(raw.get('question') == intake.task.question and
             raw.get('description') == intake.task.resolution_criteria, 'original_terms_changed')
    _require(all(raw.get(k) is v for k,v in (('active', True), ('closed', False),
                 ('acceptingOrders', True), ('enableOrderBook', True))), 'market_not_executable')
    spec = CryptoResearchSpec(request.record_id, intake.team_id, intake.condition_id,
        intake.market_slug, request.forecast_cutoff_at, request.model_id)
    try: terms = market_terms(spec, s.market, s.decision_at)
    except CryptoLaunchBlocked:
        raise _Blocked('original_contract_or_observation_blocked') from None
    observation = assess_crypto_observation_time(team_id=intake.team_id, question=intake.task.question,
        resolution_criteria=intake.task.resolution_criteria, market_slug=intake.market_slug,
        as_of=s.decision_at, forecast_cutoff_at=request.forecast_cutoff_at,
        scheduled_end_at=datetime.fromisoformat(terms['scheduled_end_at']))
    _require(observation.new_launch_time_eligible, 'original_contract_or_observation_blocked')
    minimum = _number(raw.get('orderMinSize'))
    tick = _number(raw.get('orderPriceMinTickSize'), maximum=Decimal(1))
    _require(tick in (Decimal('0.1'), Decimal('0.01'), Decimal('0.001'), Decimal('0.0001')),
             'market_tick_unsupported')
    _require(s.requested_size >= minimum, 'below_market_minimum')
    labels, tokens = _array(raw.get('outcomes')), _array(raw.get('clobTokenIds'))
    _require(len(labels) == len(tokens) == 2 and all(type(x) is str for x in labels) and set(labels) == {'Yes', 'No'} and
        all(type(t) is str and re.fullmatch(r'[1-9][0-9]{0,77}', t) for t in tokens)
        and len(set(tokens)) == 2, 'market_token_mapping_invalid')
    mapping = dict(zip(labels, tokens, strict=True))
    yes = _book(s.yes_book, mapping['Yes'], intake.condition_id, s.decision_at, record.recorded_at, s.max_age_seconds, tick)
    no = _book(s.no_book, mapping['No'], intake.condition_id, s.decision_at, record.recorded_at, s.max_age_seconds, tick)
    fills = tuple(simulate_order_book_fill(PaperOrder(b.token_id, 'buy', s.requested_size), b) for b in (yes, no))
    # Offer only a complete-size alternative. Partial book walks remain visible,
    # but requested size is never silently shrunk or partials credited as trades.
    prices = tuple(f.worst_price if f.is_complete else None for f in fills)
    snapshot = PaperCostAwareEventMarketSnapshot(intake.market_slug, intake.task.question,
        research.probability_yes, research.confidence, yes.best_bid, prices[0], fills[0].filled_size,
        no.best_bid, prices[1], fills[1].filled_size,
        max(yes.best_ask-yes.best_bid, no.best_ask-no.best_bid), s.resolution_risk)
    strategy = build_paper_cost_aware_event_strategy_report(snapshot, cost_assumptions=s.costs,
        config=s.gates, generated_at=s.decision_at)
    # Legacy cost decisions round per-share output. Apply a conservative numeric
    # check to the chosen candidate, WITHOUT changing its original probability,
    # thresholds or reranking to another side after a rejection. This is not a
    # second forecasting/scoring system. Fee maximum may occur INSIDE the consumed
    # price range, so the worst ASK alone is not a per-share fee upper bound.
    selected = strategy.selected_side
    reason = strategy.status
    totals = None
    if selected != 'none':
        f = fills[0] if selected == 'yes' else fills[1]
        price = f.worst_price
        fair = research.probability_yes if selected == 'yes' else Decimal(1)-research.probability_yes
        fee_peak = min(price, max(f.best_ask, Decimal('.5')))
        quantum = Decimal('0.000001')
        fee = (s.costs.taker_fee_rate*fee_peak*(1-fee_peak)).quantize(quantum, rounding=ROUND_CEILING)
        nonfee = sum((v for k,v in asdict(s.costs).items() if k != 'taker_fee_rate'), Decimal(0))
        nonfee = nonfee.quantize(quantum, rounding=ROUND_CEILING)
        lower = (fair-price-fee-nonfee).quantize(quantum, rounding=ROUND_FLOOR)
        totals = dict(entry_notional_upper_bound=s.requested_size*price,
            assumed_fee_upper_bound=s.requested_size*fee, assumed_non_fee_cost_upper_bound=s.requested_size*nonfee,
            expected_net_edge_lower_bound=s.requested_size*lower,
            expected_net_edge_lower_bound_per_share=lower,
            assumed_total_cost_upper_bound=s.requested_size*(price+fee+nonfee))
        if lower < s.gates.min_net_edge:
            selected, reason = 'none', 'conservative_cost_bound_rejected'
    return dict(status='paper_scenario_ready' if selected != 'none' else 'paper_scenario_rejected',
        reason_code=reason, selected_side=selected,
        strategy=dict(status=strategy.status, config_version=strategy.config_version,
            yes_result=asdict(strategy.yes_result), no_result=asdict(strategy.no_result),
            gate_results=[asdict(g) for g in strategy.gate_results]),
        book_walks={'yes': asdict(fills[0]), 'no': asdict(fills[1])}, assumed_totals=totals)


@dataclass(frozen=True, slots=True)
class ResearchPaperEvaluation:
    """Recomputed composition of existing receipts; not durable paper history."""
    history: ResearchEvaluationReport = field(repr=False)
    scenarios: tuple[ResearchPaperScenario, ...] = field(repr=False)
    executions: tuple[CapturedResearchExecution, ...] = field(repr=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self):
        hard_flags(self)
        if type(self.history) is not ResearchEvaluationReport:
            raise ValueError('research_paper_history_invalid')
        object.__setattr__(self, 'history', replace(self.history))
        object.__setattr__(self, 'scenarios', copy_scenarios(self.scenarios))
        if type(self.executions) is not tuple or any(type(e) is not CapturedResearchExecution for e in self.executions):
            raise ValueError('research_paper_execution_invalid')
        executions = tuple(replace(e) for e in self.executions)
        records = {r.record_id: r for r in self.history.records}
        for s in self.scenarios:
            if (s.record_id not in records or records[s.record_id].content_sha256 != s.record_sha256
                    or s.decision_at > self.history.generated_at):
                raise ValueError('research_paper_record_binding_mismatch')
        needed = {d.record_id for d in self.history.decisions if d.reason_code in _ELIGIBLE
                  and d.record_id in {s.record_id for s in self.scenarios}}
        if len(executions) != len(needed) or {e.request.record_id for e in executions} != needed:
            raise ValueError('research_paper_execution_set_mismatch')
        for e in executions:
            if e.record != records[e.request.record_id]:
                raise ValueError('research_paper_execution_binding_mismatch')
        object.__setattr__(self, 'executions', executions)

    def to_dict(self):
        value = replace(self)
        scenarios = {s.record_id: s for s in value.scenarios}
        executions = {e.request.record_id: e for e in value.executions}
        rows = []
        with localcontext(_CONTEXT):
            for d in value.history.decisions:
                s = scenarios.get(d.record_id)
                row = dict(record_id=d.record_id, record_sha256=d.record_sha256,
                    team_id=d.team_id, model_id=d.model_id, protocol_version=d.protocol_version,
                    condition_id=d.condition_id, original_reason_code=d.reason_code,
                    scenario_binding=None if s is None else s.binding(),
                    status='not_simulated', reason_code=d.reason_code if d.reason_code not in _ELIGIBLE else 'paper_inputs_missing')
                if s is not None and d.reason_code in _ELIGIBLE:
                    try: row.update(_scenario(executions[d.record_id], s))
                    except _Blocked as error:
                        row.update(status='paper_scenario_rejected', reason_code=str(error))
                rows.append(row)
            return json_value(dict(schema_version='research-paper-scenarios-v1',
                history=value.history.to_dict(), paper_attempts=rows,
                input_sha256=content_hash(dict(history=value.history.input_sha256,
                    scenarios=[s.binding() for s in value.scenarios],
                    requests=[e.request.content_sha256 for e in value.executions])),
                attempt_count=len(rows), supplied_scenario_count=len(scenarios),
                ready_scenario_count=sum(r['status']=='paper_scenario_ready' for r in rows),
                retrospective_scenarios_only=True, paper_trades_created=0, durable_paper_evidence_created=False,
                actual_billed_fees=None, realized_pnl=None, tariff_verified=False,
                source_authentication_performed=False, forecast_authorization_performed=False,
                strategy_validation_performed=False, paper_only=True, report_only=True, readonly=True))


def evaluate_research_paper_with_psycopg(dsn: str, *, scenarios: tuple[ResearchPaperScenario, ...], **configuration):
    """Original complete-history gate, then immutable claim/result lookups.

    No model, network, inserts or alternate persistence. Lookups are separate
    snapshots; exact immutable-record equality is required, not inferred liveness.
    """
    scenarios = copy_scenarios(scenarios)
    history = load_captured_research_evaluation_with_psycopg(dsn, **configuration)
    if type(history) is not ResearchEvaluationReport:
        raise ValueError('research_paper_history_invalid')
    history = replace(history)
    records = {r.record_id: r for r in history.records}
    for s in scenarios:
        if (s.record_id not in records or records[s.record_id].content_sha256 != s.record_sha256
                or s.decision_at > history.generated_at):
            raise ValueError('research_paper_record_binding_mismatch')
    ids = {s.record_id for s in scenarios}
    executions = tuple(inspect_captured_research_with_psycopg(dsn, record_id=d.record_id)
        for d in history.decisions if d.record_id in ids and d.reason_code in _ELIGIBLE)
    return ResearchPaperEvaluation(history, scenarios, executions)


__all__ = ('ResearchPaperEvaluation', 'evaluate_research_paper_with_psycopg')
