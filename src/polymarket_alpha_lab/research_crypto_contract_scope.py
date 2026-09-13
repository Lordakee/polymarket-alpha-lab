"""Conservative rule-shape gate for the recent-hourly crypto research launcher.

This is NOT a natural-language oracle or an authenticated contract parser. Only
narrow terminal-price hints may proceed to the existing operator-approval gate.
Path/aggregate/unknown shapes cannot be supported by extending a recent lookback.
No I/O, price inference, date inference, model invocation or outcome generation.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import re
import unicodedata

from polymarket_alpha_lab.team_research_agent_types import text

VERSION = 'crypto-contract-scope-v1'
_REASONS = {
    'path_dependent': 'crypto_launch_path_history_required',
    'aggregate_price': 'crypto_launch_aggregate_history_required',
    'terminal_price_hint': 'crypto_launch_terminal_requires_operator_review',
    'unclassified': 'crypto_launch_contract_scope_unsupported',
}
_ASSETS = {'crypto_btc': ('bitcoin', 'btc'), 'crypto_eth': ('ethereum', 'eth')}
_MONTH = (r'(?:january|february|march|april|may|june|july|august|september|october|'
          r'november|december)')
_QUESTION = re.compile(
    r'will (?:the price of )?(?P<asset>bitcoin|btc|ethereum|eth) (?:be|close) '
    r'(?P<direction>above|below) \$(?P<price>\d+(?:,\d{3})*(?:\.\d+)?) on '
    + _MONTH + r' \d{1,2}(?:,? 20\d{2})?\?')
_PATH = re.compile(
    r'\b(?:dip(?:s|ped|ping)?|touch(?:es|ed|ing)?|reach(?:es|ed|ing)?|hit(?:s|ting)?|'
    r'ever|never|throughout|remain(?:s|ed|ing)?|stay(?:s|ed|ing)?|lowest|highest|low|high)\b'
    r'|\bat any (?:time|point)\b|\bat least once\b|\bat no (?:time|point)\b'
    r'|\b(?:any|every|all) (?:\S+ ){0,3}(?:candle|candlestick)s?\b')
_AGGREGATE = re.compile(r'\b(?:average|averaged|averaging|mean|median|twap|vwap)\b')
_MINUTE = re.compile(r'\b(?:1[- ]minute|one[- ]minute)\b')
_CLOCK = re.compile(r'\bat (?:0?[1-9]|1[0-2]):[0-5]\d\s*(?:am|pm)\s*(?:et|utc)\b'
                    r'|\b12:00 in the et timezone \(noon\)')
_AMOUNT = re.compile(r'\$(\d+(?:,\d{3})*(?:\.\d+)?)')
_YES = re.compile(r'\bthis market will resolve to [\"\']?yes[\"\']? if\b')
_OTHERWISE = re.compile(r'\botherwise[, ]+(?:it|this market) will resolve to [\"\']?no[\"\']?')


def _fold(value: str) -> str:
    # Normalize presentation, never strip arbitrary words, HTML or negations.
    value = unicodedata.normalize('NFKC', value).casefold()
    return ' '.join(value.translate(str.maketrans({'“': '"', '”': '"', '’': "'", '‘': "'"})).split())


@dataclass(frozen=True, slots=True)
class CryptoContractScope:
    kind: str
    warning_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.kind) is not str or self.kind not in _REASONS:
            raise ValueError('crypto_contract_scope_invalid')
        allowed = ('reference_feeds_not_settlement_verification', 'observation_time_not_verified',
                   'binance_vs_reference_venues', 'usd_vs_usdt', 'hourly_vs_minute')
        if (type(self.warning_codes) is not tuple or self.warning_codes[:2] != allowed[:2]
                or len(set(self.warning_codes)) != len(self.warning_codes)
                or any(type(item) is not str or item not in allowed for item in self.warning_codes)):
            raise ValueError('crypto_contract_scope_warnings_invalid')

    @property
    def new_launch_policy_eligible(self) -> bool:
        self.__post_init__()
        return self.kind == 'terminal_price_hint'

    @property
    def reason_code(self) -> str:
        self.__post_init__()
        return _REASONS[self.kind]

    def to_dict(self) -> dict:
        self.__post_init__()
        history = (None if self.kind == 'unclassified'
                   else self.kind in ('path_dependent', 'aggregate_price'))
        return dict(version=VERSION, kind=self.kind, reason_code=self.reason_code,
            new_launch_policy_eligible=self.new_launch_policy_eligible,
            operator_terms_approval_required=True, classification_is_semantic_proof=False,
            settlement_source_verified=False, observation_time_verified=False,
            complete_contract_history_required=history, history_coverage_verified=False,
            reference_venues=['coinbase', 'kraken'], reference_quote='USD',
            reference_candle_seconds=3600, warning_codes=list(self.warning_codes))


def assess_crypto_contract_scope(team_id: str, question: str, resolution_criteria: str) -> CryptoContractScope:
    """Classify hints conservatively; missing/ambiguous evidence NEVER means NO.

    Negative/path markers anywhere in question OR rules win over terminal hints.
    Unknown language/templates, compound conditions and conflicting directions
    are unsupported, not automatically terminal. The caller must still review
    the ENTIRE fresh rules and timestamp: this gate cannot prove truth, parse the
    exact observation instant, or verify that a supposedly terminal event has
    not already occurred. It never consumes a caller-supplied scope verdict.
    """
    if type(team_id) is not str or team_id not in _ASSETS:
        raise ValueError('crypto_contract_scope_team_invalid')
    text('question', question, 2000)
    text('resolution_criteria', resolution_criteria, 4000)
    q, rules = _fold(question), _fold(resolution_criteria)
    body = q + ' ' + rules
    warnings = ['reference_feeds_not_settlement_verification', 'observation_time_not_verified']
    if re.search(r'\bbinance\b', body):
        warnings.append('binance_vs_reference_venues')
    if re.search(r'\b(?:btc|eth)?/?usdt\b', body):
        warnings.append('usd_vs_usdt')
    if _MINUTE.search(body):
        warnings.append('hourly_vs_minute')
    kind = 'unclassified'
    if _PATH.search(body):
        kind = 'path_dependent'
    elif _AGGREGATE.search(body):
        kind = 'aggregate_price'
    else:
        question_match = _QUESTION.fullmatch(q)
        yes, otherwise = _YES.search(rules), _OTHERWISE.search(rules)
        if question_match and question_match['asset'] in _ASSETS[team_id] and yes and otherwise and yes.end() < otherwise.start():
            clause = rules[yes.end():otherwise.start()]
            ticker = _ASSETS[team_id][1]
            asset = re.search(r'\b(?:' + _ASSETS[team_id][0] + '|' + ticker + r'(?:/?usdt|/?usd)?)\b', clause)
            forward = r'\b(?:above|higher than|greater than)\b'
            reverse = r'\b(?:below|lower than|less than)\b'
            wanted, opposite = (forward, reverse) if question_match['direction'] == 'above' else (reverse, forward)
            threshold = Decimal(question_match['price'].replace(',', ''))
            amounts_agree = all(Decimal(amount.replace(',', '')) == threshold for amount in _AMOUNT.findall(clause))
            if (amounts_agree and asset and _MINUTE.search(clause) and _CLOCK.search(clause) and re.search(r'\bclose\b', clause)
                    and re.search(wanted, clause) and not re.search(opposite, clause)
                    and not re.search(r'\b(?:and|or|unless|not|if)\b', clause)
                    and len(_YES.findall(rules)) == len(_OTHERWISE.findall(rules)) == 1):
                kind = 'terminal_price_hint'
    return CryptoContractScope(kind, tuple(warnings))


__all__ = ('CryptoContractScope', 'assess_crypto_contract_scope')
