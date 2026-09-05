"""Typed, spec-driven query construction for registered public sources.

Query strings are first-class validated data: names and values are checked
against the source's registered ``RequestParamSpec`` tuple before any URL
composition, and canonical ordering makes request identity deterministic.
This module is pure; it imports only the central contracts.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Mapping

from .central_data_contracts import (
    RESERVED_REQUEST_PARAM_NAMES,
    RequestParamSpec,
    SourceDefinition,
)


__all__ = (
    "PaginationPolicy",
    "build_request_query",
    "canonical_query_string",
    "request_query_identity",
    "RESERVED_REQUEST_PARAM_NAMES",
)


@dataclass(frozen=True)
class PaginationPolicy:
    """Explicit per-source pagination budget."""

    max_pages: int
    min_items_per_page: int
    max_items_per_page: int

    def __post_init__(self) -> None:
        for name in ("max_pages", "min_items_per_page", "max_items_per_page"):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f"{name} must be a positive int")
        if self.min_items_per_page > self.max_items_per_page:
            raise ValueError("pagination items-per-page bounds are inverted")


def canonical_query_string(query: Mapping[str, str]) -> str:
    """Render a query mapping deterministically (name-sorted, quote-encoded)."""

    pairs = sorted((str(name), str(value)) for name, value in query.items())
    return "&".join(f"{name}={value}" for name, value in pairs)


def build_request_query(
    source_def: SourceDefinition,
    params: Mapping[str, object] | None = None,
) -> dict[str, str]:
    """Validate caller parameters against the source spec and canonicalize."""

    if type(source_def) is not SourceDefinition:
        raise ValueError("source_def must be a SourceDefinition")
    if params is not None and not isinstance(params, Mapping):
        raise ValueError("params must be a mapping")
    supplied = dict(params or {})
    specs = {spec.name: spec for spec in source_def.query_params}
    unknown = sorted(set(supplied) - set(specs))
    if unknown:
        raise ValueError(f"unknown request parameters: {', '.join(unknown)}")
    query: dict[str, str] = {}
    for name in sorted(specs):
        spec = specs[name]
        if name in supplied:
            value = supplied[name]
            if type(value) is int and spec.kind == "int_range":
                value = str(value)
            if type(value) is not str:
                raise ValueError(f"parameter {name} must be a canonical string")
            query[name] = spec.validate_value(value)
        elif spec.default is not None:
            query[name] = spec.default
        elif spec.required:
            raise ValueError(f"missing required request parameter: {name}")
    return dict(sorted(query.items()))


def request_query_identity(source_id: str, query: Mapping[str, str]) -> str:
    """Stable SHA-256 identity for one source request shape."""

    if type(source_id) is not str or not source_id:
        raise ValueError("source_id must be a canonical string")
    payload = f"{source_id}|{canonical_query_string(query)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
