"""Equivalent numeric configuration must not split calibration cohorts."""
from decimal import Decimal, localcontext

import pytest

from polymarket_alpha_lab.team_research_cross_source import CrossSourcePolicy
from tests.test_research_crypto_launch import spec


@pytest.mark.parametrize('left,right', [('100','100.00'),('0','-0.000'),('1E+2','100.000')])
def test_equivalent_decimal_policy_has_one_protocol(left,right):
    a=spec(policy=CrossSourcePolicy(Decimal(left)))
    b=spec(policy=CrossSourcePolicy(Decimal(right)))
    assert a.policy==b.policy
    assert a.protocol()==b.protocol()


def test_protocol_is_independent_of_ambient_decimal_context():
    config=spec(policy=CrossSourcePolicy(Decimal('123.456789')))
    expected=config.protocol()
    with localcontext() as ctx:
        ctx.prec=1
        assert config.protocol()==expected
