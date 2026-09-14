"""Value projection for already validated research dataclasses, not a decoder.

Keep existing JSON codecs/hashes authoritative. Project timestamp leaves to UTC
before recursively copying containers: dataclasses.asdict would deepcopy tzinfo,
which fails for legitimate ZoneInfo.from_file clocks. No pickle, I/O, class
construction or serialized type dispatch. The caller still validates its exact
root/nested schema and the existing codec still validates canonical wire bytes.
"""
from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal


def _values(value):
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError('research record timestamp must be aware')
        return value.astimezone(UTC)
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError('nonfinite research record number')
        return value
    if type(value) in (tuple, list):
        return type(value)(_values(item) for item in value)
    if type(value) is dict:
        if any(type(key) is not str for key in value):
            raise ValueError('research record keys must be strings')
        return {key: _values(item) for key, item in value.items()}
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: _values(getattr(value, item.name)) for item in fields(value)}
    raise ValueError('unsupported research record value')


def record_dict(value) -> dict:
    """Copy a validated record graph without mutating its timestamp objects."""
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError('research record dataclass required')
    return _values(value)
