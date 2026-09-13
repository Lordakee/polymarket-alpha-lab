"""Bounded body validation for public readers; no network or retry policy here."""
from __future__ import annotations

import re


class PublicBodyError(ValueError):
    """Fixed reason only; never propagate headers, URLs or partial body text."""


def read_public_body(response, max_bytes: int) -> bytes:
    """Read at most limit+1 bytes and enforce declared HTTP message framing.

    http.client.read(amt) can return a short Content-Length body without raising
    IncompleteRead. Even syntactically valid JSON is not a complete snapshot in
    that case. Chunked truncation exceptions propagate to the caller; never use
    their partial bytes. Close-delimited bodies have no independently known size.
    Caller owns/ closes the response, verifies origin/status/type, and handles
    its existing fixed errors. No automatic retry is added to existing readers.
    """
    if type(max_bytes) is not int or not 1 <= max_bytes <= 4 * 1024 * 1024:
        raise ValueError('public_body_limit_invalid')
    lengths = response.headers.get_all('Content-Length', [])
    transfers = response.headers.get_all('Transfer-Encoding', [])
    encodings = response.headers.get_all('Content-Encoding', [])
    if (len(lengths) > 1 or len(transfers) > 1 or len(encodings) > 1
            or (lengths and transfers)
            or (transfers and transfers[0].strip().lower() != 'chunked')
            or (encodings and encodings[0].strip().lower() != 'identity')):
        raise PublicBodyError('public_response_framing_invalid')
    expected = None
    if lengths:
        value = lengths[0].strip()
        if re.fullmatch(r'[0-9]{1,10}', value) is None:
            raise PublicBodyError('public_response_framing_invalid')
        expected = int(value)
        if expected > max_bytes:
            raise PublicBodyError('public_response_too_large')
    raw = response.read(max_bytes + 1)
    if type(raw) is not bytes or len(raw) > max_bytes:
        raise PublicBodyError('public_response_too_large')
    if expected is not None and len(raw) != expected:
        raise PublicBodyError('public_response_incomplete')
    if not raw:
        raise PublicBodyError('public_response_empty')
    return raw
