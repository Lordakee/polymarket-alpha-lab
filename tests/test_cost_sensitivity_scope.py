from __future__ import annotations

import inspect

import polymarket_alpha_lab.cost_sensitivity as cost_sensitivity


def test_cost_sensitivity_public_names_stay_report_only():
    forbidden_terms = ("rank", "recommend", "advice")

    public_names = tuple(cost_sensitivity.__all__)

    assert all(
        term not in public_name.lower()
        for public_name in public_names
        for term in forbidden_terms
    )


def test_cost_sensitivity_module_avoids_live_operation_imports():
    source = inspect.getsource(cost_sensitivity).lower()
    forbidden_fragments = (
        "requests",
        "urllib",
        "httpx",
        "socket",
        "subprocess",
        "wallet",
        "order placement",
        "auth",
    )

    assert all(fragment not in source for fragment in forbidden_fragments)
