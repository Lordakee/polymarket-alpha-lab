"""Pure, bounded JSON/RSS/XML normalization for central public evidence."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
import json
import re
from typing import Any, Iterable, Mapping
from xml.etree import ElementTree

from .central_data_contracts import (
    EvidenceReference,
    FailureStatus,
    Freshness,
    NormalizedObservation,
    ObservationValueState,
    ParseState,
    SourceDefinition,
)
from .central_data_persistence_policy import MAX_RESPONSE_BYTES


MAX_XML_ELEMENTS = 10_000
MAX_XML_DEPTH = 64
MAX_XML_ATTRIBUTES = 64
MAX_XML_TEXT_CHARACTERS = MAX_RESPONSE_BYTES
_UNSAFE_DECLARATION_RE = re.compile(r"<!\s*(?:doctype|entity)\b", re.IGNORECASE)


class NormalizationError(ValueError):
    """A fixed parse-boundary failure that never includes input content."""


def _reject_constant(_value: str) -> None:
    raise NormalizationError("non_finite_number")


def _pairs_no_duplicates(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise NormalizationError("duplicate_json_key")
        result[key] = value
    return result


def _normalize_value(value: Any, *, depth: int = 0) -> Any:
    if depth > 128:
        raise NormalizationError("value_nesting_limit")
    if value is None or type(value) is bool or type(value) is str:
        return value
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise NormalizationError("non_finite_number")
        return value
    if type(value) is int or type(value) is float:
        raise NormalizationError("numeric_values_require_decimal")
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise NormalizationError("object_key_must_be_string")
            result[key] = _normalize_value(item, depth=depth + 1)
        return result
    if isinstance(value, (list, tuple)):
        return [_normalize_value(item, depth=depth + 1) for item in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    raise NormalizationError("unsupported_normalized_value")


def _as_text(value: object) -> str:
    if type(value) is not str:
        raise NormalizationError("document_must_be_text")
    if len(value.encode("utf-8")) > MAX_RESPONSE_BYTES:
        raise NormalizationError("document_size_limit")
    return value


def _local_name(value: str) -> str:
    return value.rsplit("}", 1)[-1]


def _element_value(root: ElementTree.Element) -> dict[str, Any]:
    element_count = 0
    text_count = 0

    def convert(element: ElementTree.Element, depth: int) -> dict[str, Any]:
        nonlocal element_count, text_count
        element_count += 1
        if element_count > MAX_XML_ELEMENTS:
            raise NormalizationError("xml_element_limit")
        if depth > MAX_XML_DEPTH:
            raise NormalizationError("xml_depth_limit")
        if len(element.attrib) > MAX_XML_ATTRIBUTES:
            raise NormalizationError("xml_attribute_limit")
        text = element.text or ""
        tail = element.tail or ""
        text_count += len(text) + len(tail)
        if text_count > MAX_XML_TEXT_CHARACTERS:
            raise NormalizationError("xml_text_limit")
        attributes = {key: element.attrib[key] for key in sorted(element.attrib)}
        return {
            "tag": _local_name(element.tag),
            "attributes": attributes,
            "text": text,
            "children": [convert(child, depth + 1) for child in list(element)],
        }

    return convert(root, 1)


class CentralDataNormalizer:
    """Generic parser with no source-specific market mappings."""

    @staticmethod
    def parse_json(document: str, source_metadata: Mapping[str, Any] | None = None) -> Any:
        del source_metadata
        document = _as_text(document)
        try:
            value = json.loads(
                document,
                parse_int=Decimal,
                parse_float=Decimal,
                parse_constant=_reject_constant,
                object_pairs_hook=_pairs_no_duplicates,
            )
        except NormalizationError:
            raise
        except (json.JSONDecodeError, RecursionError, UnicodeError):
            raise NormalizationError("json_parse_failed") from None
        return _normalize_value(value)

    @staticmethod
    def normalize_value(value: Any) -> Any:
        return _normalize_value(value)

    @staticmethod
    def parse_xml(document: str) -> dict[str, Any]:
        document = _as_text(document)
        if _UNSAFE_DECLARATION_RE.search(document):
            raise NormalizationError("xml_declaration_rejected")
        try:
            root = ElementTree.fromstring(document)
        except (ElementTree.ParseError, RecursionError):
            raise NormalizationError("xml_parse_failed") from None
        return _element_value(root)

    @staticmethod
    def parse_rss(document: str) -> dict[str, Any]:
        parsed = CentralDataNormalizer.parse_xml(document)
        if parsed["tag"].lower() not in {"rss", "feed", "rdf"}:
            raise NormalizationError("rss_root_required")
        return parsed

    @staticmethod
    def parse_document(document: str, content_type: str) -> Any:
        media_type = content_type.split(";", 1)[0].strip().lower()
        if media_type == "application/json":
            return CentralDataNormalizer.parse_json(document)
        if media_type == "application/rss+xml":
            return CentralDataNormalizer.parse_rss(document)
        if media_type in {"application/xml", "text/xml"}:
            return CentralDataNormalizer.parse_xml(document)
        raise NormalizationError("unsupported_media")

    @staticmethod
    def build_observation(
        source_definition: SourceDefinition,
        raw_identity: Any,
        *,
        observation_time: datetime,
        value: Any,
        freshness: Freshness,
        parse_state: ParseState = ParseState.SUCCESS,
        failure_status: FailureStatus = FailureStatus.NONE,
        value_state: ObservationValueState = ObservationValueState.PRESENT,
        reason_codes: tuple[str, ...] = (),
        parser_version: str = "central-data-v1",
    ) -> NormalizedObservation:
        if type(source_definition) is not SourceDefinition:
            raise ValueError("source_definition must be a SourceDefinition")
        required = ("source_id", "retrieval_time", "raw_payload_sha256", "endpoint_url")
        if any(not hasattr(raw_identity, name) for name in required):
            raise ValueError("raw_identity is required")
        if raw_identity.source_id != source_definition.source_id:
            raise ValueError("raw_identity source does not match source definition")
        if raw_identity.endpoint_url != source_definition.url_template:
            raise ValueError("raw_identity endpoint does not match source definition")
        from .central_data_db_row import RawEventIdentity
        if type(raw_identity) is not RawEventIdentity:
            raise ValueError("raw_identity must be a RawEventIdentity")
        if parse_state is not ParseState.SUCCESS and value is not None:
            raise ValueError("failed parse observations cannot carry a value")
        if parse_state is not ParseState.SUCCESS and value_state not in (
            ObservationValueState.NULL,
            ObservationValueState.UNKNOWN,
        ):
            raise ValueError("failed parse observations must be null or unknown")
        evidence = EvidenceReference(
            source_id=source_definition.source_id,
            retrieval_time=raw_identity.retrieval_time,
            observation_time=observation_time,
            payload_hash=raw_identity.raw_payload_sha256,
            parser_version=parser_version,
        )
        return NormalizedObservation(
            source_id=source_definition.source_id,
            observation_time=observation_time,
            value=_normalize_value(value),
            freshness=freshness,
            parse_state=parse_state,
            evidence_reference=evidence,
            value_state=value_state,
            failure_status=failure_status,
            reason_codes=reason_codes,
        )


__all__ = (
    "CentralDataNormalizer",
    "MAX_XML_ATTRIBUTES",
    "MAX_XML_DEPTH",
    "MAX_XML_ELEMENTS",
    "MAX_XML_TEXT_CHARACTERS",
    "NormalizationError",
)
