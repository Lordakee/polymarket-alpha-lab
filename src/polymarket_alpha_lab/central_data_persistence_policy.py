"""Pure safety policy for the central evidence persistence boundary.

This module deliberately has no database, environment, network, logging, or
filesystem dependency.  It validates the data before a store is allowed to
bind raw bytes to a SQL statement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Mapping
from urllib.parse import urlsplit


MAX_RESPONSE_BYTES = 2 * 1024 * 1024
_URL_SENSITIVE_RE = re.compile(
    r"(?i)(?:bearer\s+|basic\s+|(?:password|secret|token|api[-_]?key|"
    r"private[-_]?key|cookie|authorization)\s*[:=]|email|phone|wallet|"
    r"[?&](?:id|uid|user_id|account_id|wallet)=)"
)
_BODY_SENSITIVE_RE = re.compile(
    r"(?i)(?:\"?(?:password|secret|token|api[-_]?key|private[-_]?key|"
    r"cookie|authorization|proxy[-_]?authorization|email|phone|wallet|"
    r"account|username|user_id|account_id|wallet_id)\"?\s*[:=])"
)
_EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d ()-]{9,}\d)(?!\d)")
_WALLET_RE = re.compile(r"(?i)\b0x[a-f0-9]{40}\b")
_MIME_RE = re.compile(r"[a-z0-9!#$&^_.+-]+/[a-z0-9!#$&^_.+-]+\Z")
_HEADER_NAME_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,127}\Z")
_SAFE_HEADER_ALLOWLIST = frozenset(
    {
        "cache-control",
        "content-length",
        "content-type",
        "date",
        "etag",
        "last-modified",
        "server",
        "strict-transport-security",
        "x-content-type-options",
        "x-frame-options",
        "x-xss-protection",
    }
)
_SAFE_RESPONSE_MEDIA_TYPES = frozenset(
    {"application/json", "application/rss+xml", "application/xml", "text/xml"}
)


@dataclass(frozen=True)
class PolicyRejection:
    """A fixed public rejection code with no sensitive detail in ``repr``."""

    reason: str
    detail: str = field(repr=False)

    def __str__(self) -> str:
        return self.reason

    def __repr__(self) -> str:
        return f"PolicyRejection(reason={self.reason!r})"


class CentralDataPolicyError(ValueError):
    """Fixed, redacted policy error."""


def _reject(reason: str) -> PolicyRejection:
    return PolicyRejection(reason, reason)


def _contains_sensitive(value: str) -> bool:
    return bool(
        _URL_SENSITIVE_RE.search(value)
        or _BODY_SENSITIVE_RE.search(value)
        or _EMAIL_RE.search(value)
        or _PHONE_RE.search(value)
        or _WALLET_RE.search(value)
    )


def _validate_concrete_url(value: object) -> bool:
    if type(value) is not str or not value or any(ch.isspace() for ch in value):
        return False
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        return False
    if parsed.username is not None or parsed.password is not None:
        return False
    if parsed.query or parsed.fragment or parsed.port is not None:
        return False
    return True


class CentralDataPersistencePolicy:
    """Closed policy gate for raw response persistence."""

    def evaluate_raw_response(
        self,
        response: Any,
        *,
        source_definition: Any | None = None,
    ) -> PolicyRejection | None:
        body = getattr(response, "body", None)
        content_type = getattr(response, "content_type", None)
        headers = getattr(response, "headers", None)
        request_url = getattr(response, "request_url", None)
        final_url = getattr(response, "url", None)
        status_code = getattr(response, "status_code", None)
        if isinstance(response, Mapping):
            body = response.get("body", response.get("raw_body"))
            content_type = response.get("content_type")
            headers = response.get("headers", response.get("safe_headers", {}))
            request_url = response.get("request_url")
            final_url = response.get("final_url", response.get("url"))
            status_code = response.get("status_code")
        if request_url is None:
            request_url = final_url

        if type(body) is not bytes:
            return _reject("invalid_body_type")
        if len(body) > MAX_RESPONSE_BYTES:
            return _reject("oversize_body")
        if type(status_code) is not int or not 100 <= status_code <= 599:
            return _reject("invalid_status_code")
        if content_type is None:
            return _reject("missing_content_type")
        if type(content_type) is not str:
            return _reject("invalid_content_type")
        normalized_type = content_type.split(";", 1)[0].strip().lower()
        if _MIME_RE.fullmatch(normalized_type) is None:
            return _reject("invalid_content_type")
        if normalized_type not in _SAFE_RESPONSE_MEDIA_TYPES:
            return _reject("unsupported_media")

        if request_url is not None and not _validate_concrete_url(request_url):
            return _reject("unsafe_url")
        if final_url is not None and not _validate_concrete_url(final_url):
            return _reject("unsafe_url")
        if request_url is not None and final_url is not None and request_url != final_url:
            return _reject("redirect_not_allowed")
        if source_definition is not None:
            endpoint = getattr(source_definition, "url_template", None)
            if endpoint is None:
                endpoint = getattr(source_definition, "endpoint_url", None)
            if type(endpoint) is not str or request_url != endpoint or final_url != endpoint:
                return _reject("source_endpoint_mismatch")
            source_content_type = getattr(source_definition, "content_type", None)
            if type(source_content_type) is not str:
                return _reject("source_content_type_mismatch")
            expected_type = source_content_type.split(";", 1)[0].strip().lower()
            if expected_type == "*/*":
                if normalized_type not in _SAFE_RESPONSE_MEDIA_TYPES:
                    return _reject("unsupported_media")
            elif normalized_type != expected_type:
                return _reject("source_content_type_mismatch")

        if not isinstance(headers, Mapping):
            return _reject("invalid_headers")
        for key, value in headers.items():
            if type(key) is not str or type(value) is not str:
                return _reject("invalid_header")
            key_l = key.lower()
            if _HEADER_NAME_RE.fullmatch(key_l) is None:
                return _reject("invalid_header")
            if key_l not in _SAFE_HEADER_ALLOWLIST:
                return _reject("unsafe_header")
            if any(ch in value for ch in "\r\n") or len(value) > 512:
                return _reject("invalid_header")
            if _contains_sensitive(value):
                return _reject("sensitive_data_detected")

        try:
            body_text = body.decode("utf-8")
        except UnicodeDecodeError:
            return _reject("invalid_utf8")
        if _contains_sensitive(body_text):
            return _reject("sensitive_data_detected")
        for value in (request_url, final_url):
            if isinstance(value, str) and _contains_sensitive(value):
                return _reject("sensitive_data_detected")
        return None

    def require_raw_response(self, response: Any, *, source_definition: Any | None = None) -> None:
        rejection = self.evaluate_raw_response(response, source_definition=source_definition)
        if rejection is not None:
            raise CentralDataPolicyError(rejection.reason)


__all__ = (
    "CentralDataPersistencePolicy",
    "CentralDataPolicyError",
    "MAX_RESPONSE_BYTES",
    "PolicyRejection",
)
