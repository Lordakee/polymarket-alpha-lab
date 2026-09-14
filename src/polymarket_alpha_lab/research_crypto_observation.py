"""Bounded terminal-candle calendar checks, NOT a semantic/source certificate.

Only explicit title dates (year in title or matching dated slug), title-linked
clock rules, ET/New York and UTC are supported. Never infer from today's year,
listing end, local machine timezone, a model or an operator-supplied verdict.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from importlib import resources
import re
from zoneinfo import ZoneInfo

from polymarket_alpha_lab.research_crypto_contract_scope import (
    _fold, _YES, _OTHERWISE, assess_crypto_contract_scope,
)
from polymarket_alpha_lab.research_resolution import utc
from polymarket_alpha_lab.team_research_intake import require_market_slug

VERSION = 'crypto-observation-time-v1'
_MONTHS = ('january', 'february', 'march', 'april', 'may', 'june', 'july',
           'august', 'september', 'october', 'november', 'december')
_MONTH = '(?:' + '|'.join(_MONTHS) + ')'
_DATE = re.compile(r' on (?P<month>' + _MONTH + r') (?P<day>\d{1,2})(?:,? (?P<year>20\d{2}))?\?$')
_SLUG_DATE = re.compile(r'-on-(?P<month>' + _MONTH + r')-(?P<day>\d{1,2})-(?P<year>20\d{2})$')
_CLOCK = re.compile(r'\bat (?P<hour>0?[1-9]|1[0-2]):(?P<minute>[0-5]\d)\s*(?P<ampm>am|pm)\s*(?P<zone>et|utc)\b'
                    r'|\b(?P<noon>12:00 in the et timezone \(noon\))')
_TITLE_DATE = re.compile(r'\bon (?:the date (?:(?:specified|listed) )?in the title|the title date|'
                         r'the date specified in the (?:title|question))\b')
_REASONS = ('scope_unsupported', 'date_unsupported', 'year_missing', 'date_conflict', 'date_invalid',
            'clock_unsupported', 'rules_date_unsupported', 'timezone_unavailable',
            'clock_nonexistent', 'clock_ambiguous', 'not_future', 'cutoff_not_before_observation',
            'listing_end_before_observation', 'requires_operator_review')


@dataclass(frozen=True, slots=True)
class CryptoObservationTime:
    reason: str
    candle_open_at: datetime | None = None
    timezone_key: str | None = None
    date_basis: str | None = None
    tzdata_version: str | None = None

    def __post_init__(self) -> None:
        if type(self.reason) is not str or self.reason not in _REASONS:
            raise ValueError('crypto_observation_result_invalid')
        computed = self.reason in ('not_future', 'cutoff_not_before_observation',
                                   'listing_end_before_observation', 'requires_operator_review')
        if computed:
            object.__setattr__(self, 'candle_open_at', utc('candle_open_at', self.candle_open_at))
            if self.timezone_key not in ('UTC', 'America/New_York') or self.date_basis not in ('question_year', 'dated_slug'):
                raise ValueError('crypto_observation_result_invalid')
            if self.timezone_key == 'UTC':
                if self.tzdata_version is not None:
                    raise ValueError('crypto_observation_result_invalid')
            elif type(self.tzdata_version) is not str or not re.fullmatch(r'\d{4}\.\d+:[0-9a-z]+', self.tzdata_version):
                raise ValueError('crypto_observation_result_invalid')
        elif any(value is not None for value in (self.candle_open_at, self.timezone_key, self.date_basis, self.tzdata_version)):
            raise ValueError('crypto_observation_result_invalid')

    @property
    def new_launch_time_eligible(self) -> bool:
        self.__post_init__()
        return self.reason == 'requires_operator_review'

    @property
    def reason_code(self) -> str:
        self.__post_init__()
        return ('crypto_launch_' if self.reason == 'cutoff_not_before_observation'
                else 'crypto_launch_observation_') + self.reason

    def to_dict(self) -> dict:
        self.__post_init__()
        return dict(version=VERSION, reason_code=self.reason_code,
            new_launch_time_eligible=self.new_launch_time_eligible,
            candle_open_at=None if self.candle_open_at is None else self.candle_open_at.isoformat(),
            candle_close_not_before=None if self.candle_open_at is None
                else (self.candle_open_at + timedelta(minutes=1)).isoformat(),
            timezone=self.timezone_key, date_basis=self.date_basis, tzdata_version=self.tzdata_version,
            timestamp_computed=self.candle_open_at is not None,
            observation_time_independently_verified=False, settlement_source_verified=False,
            operator_review_required=True)


def _new_york():
    # Load only the installed dependency, not host TZPATH or user environment.
    # Pinning the uv lock makes this identical across Windows/Linux installs.
    import tzdata
    with resources.files('tzdata.zoneinfo.America').joinpath('New_York').open('rb') as source:
        zone = ZoneInfo.from_file(source, key='America/New_York')
    return zone, tzdata.__version__ + ':' + tzdata.IANA_VERSION


def assess_crypto_observation_time(*, team_id: str, question: str, resolution_criteria: str,
                                  market_slug: str, as_of: datetime,
                                  forecast_cutoff_at: datetime, scheduled_end_at: datetime) -> CryptoObservationTime:
    """Compute a supported rule's minute window and enforce pre-OPEN forecasting.

    Listing end is used only as a consistency check, NEVER to supply the date or
    year. Daylight-saving gaps and folds are rejected, not resolved by guessing.
    The database runner subsequently enforces its clock < the SAME cutoff; it
    cannot backdate a claim using this earlier preview. Existing replays are not
    recertified. A computed time remains a limited template interpretation.
    """
    scope = assess_crypto_contract_scope(team_id, question, resolution_criteria)
    require_market_slug(market_slug)
    at = utc('as_of', as_of)
    cutoff = utc('forecast_cutoff_at', forecast_cutoff_at)
    end = utc('scheduled_end_at', scheduled_end_at)
    if not scope.new_launch_policy_eligible:
        return CryptoObservationTime('scope_unsupported')
    q, rules = _fold(question), _fold(resolution_criteria)
    date = _DATE.search(q)
    if date is None:
        return CryptoObservationTime('date_unsupported')
    slug_date = _SLUG_DATE.search(market_slug)
    month, day = _MONTHS.index(date['month']) + 1, int(date['day'])
    year = int(date['year']) if date['year'] else None
    basis = 'question_year' if year else 'dated_slug'
    if slug_date:
        if (slug_date['month'] != date['month'] or int(slug_date['day']) != day
                or year is not None and int(slug_date['year']) != year):
            return CryptoObservationTime('date_conflict')
        year = int(slug_date['year'])
    if year is None:
        return CryptoObservationTime('year_missing')
    try:
        local = datetime(year, month, day)
    except ValueError:
        return CryptoObservationTime('date_invalid')
    yes, otherwise = _YES.search(rules), _OTHERWISE.search(rules)
    clause = rules[yes.end():otherwise.start()]
    clocks = list(_CLOCK.finditer(rules))
    if (len(clocks) != 1 or len(re.findall(r'\b\d{1,2}:\d{2}\b', rules)) != 1
            or not _CLOCK.search(clause)):
        return CryptoObservationTime('clock_unsupported')
    # A title reference is required. Other date wording is deliberately not
    # interpreted; it must not override the title silently.
    if (len(_TITLE_DATE.findall(clause)) != 1 or re.search(r'\b' + _MONTH + r'\b|\b20\d{2}\b', rules)
            or re.search(r'\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b', rules)
            or re.search(r'\b(?:today|tomorrow|yesterday|next|previous|following|preceding)\b', rules)):
        return CryptoObservationTime('rules_date_unsupported')
    clock = clocks[0]
    if not _TITLE_DATE.match(rules[clock.end():].lstrip()):
        return CryptoObservationTime('clock_unsupported')
    if clock['noon']:
        local = local.replace(hour=12)
        zone_name = 'et'
    else:
        local = local.replace(hour=int(clock['hour']) % 12 + (12 if clock['ampm'] == 'pm' else 0),
                              minute=int(clock['minute']))
        zone_name = clock['zone']
    version = None
    if zone_name == 'utc':
        zone, key = UTC, 'UTC'
    else:
        try:
            zone, version = _new_york()
        except (ImportError, OSError, ValueError):
            return CryptoObservationTime('timezone_unavailable')
        key = 'America/New_York'
    candidates = set()
    for fold in (0, 1):
        candidate = local.replace(tzinfo=zone, fold=fold).astimezone(UTC)
        if candidate.astimezone(zone).replace(tzinfo=None) == local:
            candidates.add(candidate)
    if not candidates:
        return CryptoObservationTime('clock_nonexistent')
    if len(candidates) != 1:
        return CryptoObservationTime('clock_ambiguous')
    opening = candidates.pop()
    if at >= opening:
        reason = 'not_future'
    elif cutoff >= opening:
        reason = 'cutoff_not_before_observation'
    elif end < opening:
        reason = 'listing_end_before_observation'
    elif at >= cutoff:
        # Input validation in the launcher already catches this; standalone
        # diagnostics must not call an elapsed cutoff startable either.
        reason = 'not_future'
    else:
        reason = 'requires_operator_review'
    return CryptoObservationTime(reason, opening, key, basis, version)


__all__ = ('CryptoObservationTime', 'assess_crypto_observation_time')
