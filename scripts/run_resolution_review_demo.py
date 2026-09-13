"""Synthetic resolution states, no public network/model/database activity."""
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
import json

from polymarket_alpha_lab.research_resolution import (
    IndependentResolutionConfirmation, ResolutionSubmission, assess_resolution,
)
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot


def main() -> int:
    now = datetime(2026,9,13,tzinfo=UTC)
    cid = '0x'+'a'*64
    rows = []
    for name, status, prices, confirmed in (
        ('proposal','proposed',['1','0'],False),
        ('binary_candidate','resolved',['1','0'],False),
        ('split_payout','resolved',['0.5','0.5'],False),
        ('operator_confirmed_fixture','resolved',['1','0'],True),
    ):
        raw = json.dumps(dict(conditionId=cid,slug='synthetic-resolution',outcomes=['Yes','No'],
            outcomePrices=prices,closed=True,acceptingOrders=False,umaResolutionStatus=status)).encode()
        snap = GammaMarketSnapshot('synthetic-resolution',now,raw)
        proof = None if not confirmed else IndependentResolutionConfirmation(cid,snap.market_slug,
            True,now-timedelta(seconds=1),now,snap.content_sha256,'synthetic-operator',
            'https://example.invalid/synthetic-official-result','Synthetic evidence; not a real settlement.',
            independently_verified=True)
        rows.append({'scenario':name,**asdict(assess_resolution(ResolutionSubmission(name,cid,snap,now,proof)))})
    print(json.dumps({'synthetic_demo':True,'public_network_called':False,
        'live_model_called':False,'database_written':False,'results':rows},indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
