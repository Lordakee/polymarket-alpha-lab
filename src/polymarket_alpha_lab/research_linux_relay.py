"""Bounded fixed-origin validating request relay: trusted parent side (L9, slice 1).

Implements the CROSSING-INDEPENDENT core of the L8-D "bounded fixed-origin
validating request relay" design (docs/research-local-agent.md, section
"Provider transport and credential ingress design"): the reviewed trust
configuration records, the relay bounds table, the closed outcome vocabulary,
the ephemeral port draw, and the trusted-parent validating engine itself as a
module string constant.

The relay is NOT a proxy. The engine accepts exactly the reviewed origin-form
request set from the contained vendor side, validates every framing byte it can
observe, creates the one upstream HTTPS connection itself, and returns one
bounded response per request. There is no CONNECT, no SOCKS, no HTTP proxy
semantics, no tunneling of arbitrary hosts and no automatic retry of any
request, connection, TLS handshake or response.

Slice boundary (deliberate omission): the plan's INNER_PEER_SOURCE and
STAGE_SOURCE constants are NOT implemented in this file yet. They depend on
the concurrently drafted design amendment that decides how the relay channel
crosses the bubblewrap namespace boundary, and they land only after that
amendment passes its plan gate - either in a follow-up slice of this same
module or beside it. This module compiles, imports and is fully testable
without them; the engine constant below only requires the two inherited relay
channel halves (a single bidirectional descriptor may be named twice for both
halves), so it stays valid under either crossing decision.

This module is pure standard library with ZERO project imports and performs no
I/O at import time. It stores no credential, prompt or response byte anywhere:
the only relay evidence anywhere in this design is fixed outcome codes and
numeric counter metadata.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import os
import re

RELAY_PROTOCOL_VERSION = 'research-linux-relay-v1'
DEFAULT_ORIGIN_HOSTNAME = 'api.anthropic.com'
RELAY_ORIGIN_SCHEME = 'https'
RELAY_ORIGIN_PORT = 443
RELAY_TLS_FLOOR = 'tls12'
RELAY_LOOPBACK_BIND_ADDRESS = '127.0.0.1'
ENDPOINT_BINDING = 'per-call-numeric-loopback-http'

# Bounds table from the reviewed L8-D design (default engineering bounds).
MAX_RELAY_REQUEST_BYTES = 16_000_000          # per request incl. headers
MAX_RELAY_RESPONSE_BYTES = 32 * 1024 * 1024   # 32 MiB per response
RELAY_RESPONSE_READ_CHUNK = 4096
RELAY_CONNECT_TIMEOUT_MS = 10_000             # upstream TCP connect
RELAY_HANDSHAKE_TIMEOUT_MS = 10_000           # upstream TLS handshake
RELAY_IDLE_TIMEOUT_MS = 30_000                # no byte in either direction
RELAY_TOTAL_TIMEOUT_CAP_MS = 24 * 60 * 60 * 1000
RELAY_PORT_WINDOW = (20000, 32767)            # per-call native draw window
MAX_RELAY_HEADER_COUNT = 32
MAX_RELAY_HEADER_BYTES = 8192                 # single header line
MAX_RELAY_HEAD_BYTES = 65536                  # request/response head
RELAY_CA_SIZE_CAP = 1024 * 1024               # 1 MiB pinned CA bundle
RELAY_TEARDOWN_DRAIN_CAP = 4096               # bounded discard drain bytes
RELAY_TEARDOWN_DRAIN_MS = 500                 # fixed linger bound
RELAY_HOSTNAME_MAX_BYTES = 253

PERMITTED_ADDRESS_RULES = frozenset((
    'public-global-unicast-only', 'qualification-loopback-only'))

# Closed outcome vocabulary. Every engine report and every call result uses
# exactly one of these fixed codes; no other outcome string exists.
RELAY_OUTCOMES = frozenset((
    'relay_ok', 'relay_stopped', 'relay_parent_lost',
    'relay_refused_method', 'relay_refused_target', 'relay_refused_authority',
    'relay_refused_header', 'relay_refused_framing', 'relay_refused_cardinality',
    'relay_redirect_refused', 'relay_dns_refused',
    'relay_request_bytes_exceeded', 'relay_response_bytes_exceeded',
    'relay_connect_timeout', 'relay_handshake_timeout', 'relay_idle_timeout',
    'relay_total_timeout', 'relay_channel_failed', 'relay_teardown_failed',
    'relay_preflight_not_approved',
))

FRAMING_HEADER_NAMES = frozenset(('content-length', 'transfer-encoding'))
FORWARDED_HEADER_NAMES = frozenset((
    'host', 'x-api-key', 'content-type', 'accept', 'accept-encoding',
    'anthropic-version', 'anthropic-beta'))

ENGINE_SOURCE = '''\
# Trusted parent-side validating relay engine (protocol research-linux-relay-v1).
# Standard library only: no application or database imports, no proxy or CONNECT
# or SOCKS semantics, no retry of any request, connection, handshake or
# response, and exactly one upstream TLS connection per approved request.
#
# The engine is crossing-independent: it only requires the two inherited relay
# channel halves named in CONF (one bidirectional descriptor may name both
# halves), plus control, report, liveness and the sealed pinned CA descriptor.
# It reads one hex-encoded CONF JSON line on stdin, reports fixed-code JSON
# lines only, and exits on parent-liveness EOF, STOP, or the total deadline.
# Nothing here ever writes a credential, prompt or response byte to a report.
import hashlib
import ipaddress
import json
import os
import select
import socket
import ssl
import sys
import time

PROTOCOL_VERSION = 'research-linux-relay-v1'
READ_CHUNK = 4096
TEARDOWN_DRAIN_CAP = 4096
TEARDOWN_DRAIN_MS = 500
MAX_REQUEST_BYTES = 16000000
MAX_RESPONSE_BYTES = 33554432
MAX_CA_BYTES = 1048576
MAX_HEADER_COUNT = 32
MAX_HEADER_BYTES = 8192
MAX_HEAD_BYTES = 65536
PORT_WINDOW = (20000, 32767)
LOOPBACK_BIND = '127.0.0.1'
HOSTNAME_MAX = 253
RULES = ('public-global-unicast-only', 'qualification-loopback-only')
FRAMING_NAMES = ('content-length', 'transfer-encoding')
DIGITS = b'0123456789'
HEX = b'0123456789abcdefABCDEF'
NAME_ALPHABET = b'abcdefghijklmnopqrstuvwxyz0123456789-'
HOST_ALPHABET = b'abcdefghijklmnopqrstuvwxyz.-0123456789'
TARGET_ALPHABET = (b'abcdefghijklmnopqrstuvwxyz'
                   b'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/?=&%~+.:_-')
_SELECT_OK = True


def _now_ms():
    return time.monotonic_ns() // 1000000


def _report(fd, value):
    line = json.dumps(value, separators=(',', ':')).encode('utf-8') + b'\\n'
    view = memoryview(line)
    while view:
        try:
            written = os.write(fd, view)
        except (BlockingIOError, InterruptedError):
            time.sleep(0.001)
            continue
        view = view[written:]


def _wait(fds, timeout_ms):
    # select over pipes and sockets on the production Linux host. Hosts whose
    # select refuses pipe descriptors fall back to reporting every watched
    # descriptor: the callers read nonblocking, so spurious readiness becomes a
    # caught BlockingIOError and deadlines are still enforced by the caller's
    # own monotonic clock. Only the WAIT differs, never the byte path.
    global _SELECT_OK
    if _SELECT_OK:
        try:
            return select.select(fds, [], [], min(max(timeout_ms, 0), 5000) / 1000.0)[0]
        except (OSError, ValueError):
            if not fds:
                raise
            _SELECT_OK = False
    time.sleep(min(max(timeout_ms, 1), 50) / 1000.0)
    return list(fds)


def _integer(value, low, high):
    return type(value) is int and low <= value <= high


def _token(text, alphabet, limit):
    if type(text) is not str or not 1 <= len(text) <= limit:
        return False
    try:
        encoded = text.encode('ascii')
    except UnicodeEncodeError:
        return False
    return all(byte in alphabet for byte in encoded)


def _validate_trust(trust):
    # Closed validation of the parent-supplied trust policy. The dict is the
    # SAME shape the parent's profile digest pins, so the enforced behavior is
    # bound to the reviewed authorization bit for bit. Returns (code, config).
    if type(trust) is not dict or trust.get('protocol_version') != PROTOCOL_VERSION:
        return 'relay_config_invalid', None
    origin = trust.get('origin')
    if type(origin) is not dict or origin.get('scheme') != 'https':
        return 'relay_config_invalid', None
    hostname = origin.get('hostname')
    if not _token(hostname, HOST_ALPHABET, HOSTNAME_MAX):
        return 'relay_config_invalid', None
    if not _integer(origin.get('port'), 1, 65535):
        return 'relay_config_invalid', None
    ca = trust.get('ca_bundle')
    if type(ca) is not dict:
        return 'relay_config_invalid', None
    digest = ca.get('sha256')
    if (type(digest) is not str or len(digest) != 64
            or any(c not in '0123456789abcdef' for c in digest)
            or not _integer(ca.get('size_bytes'), 1, MAX_CA_BYTES)):
        return 'relay_config_invalid', None
    if trust.get('permitted_address_rule') not in RULES:
        return 'relay_config_invalid', None
    if trust.get('tls_floor') != 'tls12':
        return 'relay_config_invalid', None
    if trust.get('endpoint_binding') != 'per-call-numeric-loopback-http':
        return 'relay_config_invalid', None
    limits = trust.get('limits')
    if type(limits) is not dict:
        return 'relay_config_invalid', None
    bounds = (('max_relay_request_bytes', 1, MAX_REQUEST_BYTES),
              ('max_relay_response_bytes', 1, MAX_RESPONSE_BYTES),
              ('relay_response_read_chunk', 1, READ_CHUNK),
              ('connect_timeout_ms', 1, 3600000),
              ('handshake_timeout_ms', 1, 3600000),
              ('idle_timeout_ms', 1, 3600000),
              ('max_header_count', 1, MAX_HEADER_COUNT),
              ('max_header_bytes', 1, MAX_HEADER_BYTES),
              ('max_head_bytes', 1, MAX_HEAD_BYTES))
    for name, low, high in bounds:
        if not _integer(limits.get(name), low, high):
            return 'relay_config_invalid', None
    if limits.get('total_timeout_ms') is not None \\
            and not _integer(limits.get('total_timeout_ms'), 1, 86400000):
        return 'relay_config_invalid', None
    if trust.get('preflight'):
        # No reviewed preflight approval exists yet: a policy declaring any
        # preflight entry is refused before any request is observed.
        return 'relay_preflight_not_approved', None
    entries = trust.get('requests')
    if type(entries) is not list or not entries:
        return 'relay_config_invalid', None
    parsed = []
    for entry in entries:
        if type(entry) is not dict or entry.get('method') != 'POST':
            return 'relay_config_invalid', None
        target = entry.get('target')
        query = entry.get('query')
        if not _token(target, TARGET_ALPHABET, MAX_HEADER_BYTES):
            return 'relay_config_invalid', None
        if query != '' and not _token(query, TARGET_ALPHABET, MAX_HEADER_BYTES):
            return 'relay_config_invalid', None
        if not target.startswith('/') or '?' in query:
            return 'relay_config_invalid', None
        rules = entry.get('forwarded_headers')
        if type(rules) is not list or not rules:
            return 'relay_config_invalid', None
        names = []
        required = {}
        for rule in rules:
            if type(rule) is not dict or rule.get('max_count') != 1 \\
                    or type(rule.get('required')) is not bool:
                return 'relay_config_invalid', None
            name = rule.get('name')
            if not _token(name, NAME_ALPHABET, 128) or name in FRAMING_NAMES:
                return 'relay_config_invalid', None
            names.append(name)
            required[name] = rule['required']
        if len(set(names)) != len(names) or 'host' not in names:
            return 'relay_config_invalid', None
        parsed.append({'method': 'POST', 'target': target, 'query': query,
                       'expected': target + (('?' + query) if query else ''),
                       'forwarded': tuple(names), 'required': required})
    limits_out = {name: limits[name] for name, _low, _high in bounds}
    return None, {'hostname': hostname, 'port': origin['port'],
                  'ca_sha256': digest, 'ca_size_bytes': ca['size_bytes'],
                  'rule': trust['permitted_address_rule'], 'limits': limits_out,
                  'requests': tuple(parsed)}


def _address_permitted(rule, text):
    # One reviewed permitted-address rule over a resolution result. The
    # default refuses loopback, private, link-local, multicast, unspecified
    # and IPv4-mapped forms; the qualification rule permits numeric IPv4
    # loopback only. A refusal never triggers a re-query.
    try:
        address = ipaddress.ip_address(text)
    except ValueError:
        return False
    if address.is_unspecified or address.is_multicast or address.is_link_local:
        return False
    if rule == 'qualification-loopback-only':
        return address.version == 4 and address.is_loopback
    if address.is_loopback or address.is_private:
        return False
    if address.version == 6 and address.ipv4_mapped is not None:
        return False
    return address.is_global


def _verify_ca(ca_fd, sha256_hex, size_bytes):
    # Verify the pinned sealed CA descriptor bytes once at startup: the relay
    # admits exactly the pinned bytes, never a reopened pathname.
    digest = hashlib.sha256()
    payload = bytearray()
    while len(payload) <= size_bytes:
        block = os.read(ca_fd, READ_CHUNK)
        if not block:
            break
        payload.extend(block)
        digest.update(block)
    if len(payload) != size_bytes or digest.hexdigest() != sha256_hex:
        return None
    return bytes(payload)


def _client_context(ca_fd, payload):
    # Trust ONLY the pinned verified descriptor bytes: never
    # create_default_context, never load_default_certs, never any ambient
    # system or user root store. A bundle that cannot load at all is a pin
    # mismatch (fixed code), never a crash and never an unverified context.
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    try:
        context.load_verify_locations(cafile='/proc/self/fd/%d' % ca_fd)
        return context
    except (OSError, ssl.SSLError):
        pass
    # Hosts without /proc/self/fd (test hosts): the SAME verified descriptor
    # bytes, PEM-decoded; still zero ambient trust material.
    try:
        context.load_verify_locations(cadata=payload.decode('ascii'))
    except (OSError, ssl.SSLError, UnicodeDecodeError):
        return None
    return context


def _split_head(head):
    # Strict CRLF framing. Returns (request line, [(name, value, raw line)])
    # with lowercased names for lookup and the raw line preserved for verbatim
    # forwarding, or None on any framing violation.
    if b'\\n' in head.replace(b'\\r\\n', b''):
        return None
    lines = head.split(b'\\r\\n')
    entries = []
    for line in lines[1:]:
        if not line:
            return None
        separator = line.find(b':')
        if separator <= 0:
            return None
        name = line[:separator]
        if b' ' in name or b'\\t' in name:
            return None
        value = line[separator + 1:].strip(b' \\t')
        entries.append((bytes(name).lower(), bytes(value), bytes(line)))
    return lines[0], entries


def _validate_request(config, line, entries, cursor, bound_authority):
    # Fixed order: request-line framing, header size/count caps, framing
    # headers (Host/Content-Length/Transfer-Encoding), bound authority, the
    # approved method/target literals, then the header allowlist. Every
    # refusal is one fixed code and ends the call with no resend.
    limits = config['limits']
    parts = line.split(b' ')
    if len(parts) != 3 or parts[2] != b'HTTP/1.1':
        return 'relay_refused_framing', None
    if len(entries) > limits['max_header_count']:
        return 'relay_refused_header', None
    for _name, _value, raw in entries:
        if len(raw) > limits['max_header_bytes']:
            return 'relay_refused_header', None
    method, target = parts[0], parts[1]
    host_values = []
    content_length = None
    # Guest header names arrive as lowercased BYTES from _split_head; every
    # framing comparison below is bytes-for-bytes.
    for name, value, _raw in entries:
        if name == b'host':
            host_values.append(value)
        elif name == b'content-length':
            if content_length is not None:
                return 'relay_refused_framing', None
            if not value or len(value) > 18 \\
                    or any(digit not in DIGITS for digit in value):
                return 'relay_refused_framing', None
            content_length = int(value)
        elif name == b'transfer-encoding':
            # Chunked (and any other TE) is refused at the inner hop.
            return 'relay_refused_framing', None
    if len(host_values) != 1:
        return 'relay_refused_authority', None
    if host_values[0] != bound_authority.encode('ascii'):
        return 'relay_refused_authority', None
    if method not in {entry['method'].encode('ascii')
                      for entry in config['requests']}:
        return 'relay_refused_method', None
    if cursor >= len(config['requests']):
        return 'relay_refused_cardinality', None
    expected = config['requests'][cursor]
    if target != expected['expected'].encode('ascii'):
        if target in {item['expected'].encode('ascii')
                      for item in config['requests']}:
            return 'relay_refused_cardinality', None
        return 'relay_refused_target', None
    counts = {}
    for name, _value, _raw in entries:
        counts[name] = counts.get(name, 0) + 1
    allowed = {name.encode('ascii') for name in expected['forwarded']}
    allowed |= {b'host', b'content-length'}
    for name, count in counts.items():
        if name not in allowed:
            return 'relay_refused_header', None
        if name not in (b'host', b'content-length') and count > 1:
            return 'relay_refused_header', None
    for name, must in expected['required'].items():
        if must and counts.get(name.encode('ascii'), 0) < 1:
            return 'relay_refused_header', None
    body_length = content_length if content_length is not None else 0
    return None, {'entry': expected, 'entries': entries,
                  'body_length': body_length}


def _reconstruct(config, validated, body):
    # The upstream request line and Host come ONLY from the approved origin;
    # allowlisted headers forward verbatim (raw guest spelling and value
    # bytes); Content-Length is rebuilt from the measured body length.
    entry = validated['entry']
    authority = config['hostname'] if config['port'] == 443 \\
        else '%s:%d' % (config['hostname'], config['port'])
    lines = ['%s %s HTTP/1.1' % (entry['method'], entry['expected']),
             'Host: ' + authority]
    forwarded = {name.encode('ascii') for name in entry['forwarded']}
    forwarded.discard(b'host')
    for name, _value, raw in validated['entries']:
        if name in forwarded:
            lines.append(raw.decode('latin-1'))
    head = ('\\r\\n'.join(lines) + '\\r\\nContent-Length: %d\\r\\n\\r\\n'
            % len(body)).encode('latin-1')
    return head + body


class _Response:
    """Raw response framing tracker over observed upstream bytes.

    Bytes are RELEASED for guest forwarding only after the head parsed and the
    status class is not a redirect, so 3xx bytes never cross and Location is
    never read or followed. Completion is detected from exact Content-Length,
    the terminal chunk, or upstream close, so the engine never reads a second
    response and never waits on a kept-alive connection. Bytes beyond the
    declared framing are never released; they die in the bounded teardown
    drain, counted only.
    """

    __slots__ = ('buf', 'fed', 'released', 'head_done', 'status', 'mode',
                 'remaining', 'walk', 'state', 'need', 'complete')

    def __init__(self):
        self.buf = bytearray()
        self.fed = 0
        self.released = 0
        self.head_done = False
        self.status = None
        self.mode = None
        self.remaining = 0
        self.walk = 0
        self.state = 'size'
        self.need = 0
        self.complete = False

    def feed(self, block, head_cap, response_cap):
        # Feed one observed block. Returns (code, release_count): code is None
        # while the exchange continues, 'relay_ok_complete' on detected
        # completion, otherwise one fixed failure code; release_count is the
        # newly forwardable byte count (never already-released bytes).
        self.buf.extend(block)
        self.fed += len(block)
        if self.fed > response_cap:
            return 'relay_response_bytes_exceeded', 0
        if not self.head_done:
            end = self.buf.find(b'\\r\\n\\r\\n')
            if end < 0:
                if self.fed > head_cap:
                    return 'relay_channel_failed', 0
                return None, 0
            head = bytes(self.buf[:end])
            lines = head.split(b'\\r\\n')
            parts = lines[0].split(b' ')
            if (len(parts) < 2 or not parts[0].startswith(b'HTTP/1.')
                    or len(parts[1]) != 3 or any(d not in DIGITS for d in parts[1])):
                return 'relay_channel_failed', 0
            self.status = int(parts[1])
            if 300 <= self.status <= 399:
                # A redirect is a failure; its bytes are never released and
                # Location is never read or followed.
                return 'relay_redirect_refused', 0
            for line in lines[1:]:
                separator = line.find(b':')
                if separator <= 0:
                    return 'relay_channel_failed', 0
                name = bytes(line[:separator]).lower()
                value = bytes(line[separator + 1:]).strip(b' \\t')
                if name == b'content-length':
                    if not value or len(value) > 18 \\
                            or any(d not in DIGITS for d in value):
                        return 'relay_channel_failed', 0
                    self.mode = 'length'
                    self.remaining = int(value)
                elif name == b'transfer-encoding' and b'chunked' in value.lower():
                    self.mode = 'chunked'
            self.head_done = True
            self.walk = end + 4
            if self.mode is None:
                self.mode = 'close'
        if self.mode == 'length':
            body = self.fed - self.walk
            if body >= self.remaining:
                self.complete = True
                limit = self.walk + self.remaining
                return 'relay_ok_complete', max(min(self.fed, limit)
                                                - self.released, 0)
            return None, max(self.fed - self.released, 0)
        if self.mode == 'close':
            return None, max(self.fed - self.released, 0)
        # chunked framing walk over releasable bytes (offsets persist across
        # feeds; no re-scan and no copy of already-walked bytes).
        while True:
            if self.state in ('size', 'trailer'):
                end = self.buf.find(b'\\r\\n', self.walk)
                if end < 0:
                    return None, max(self.fed - self.released, 0)
                line = bytes(self.buf[self.walk:end])
                if self.state == 'size':
                    token = line.split(b';')[0].strip()
                    if not token or any(c not in HEX for c in token):
                        return 'relay_channel_failed', 0
                    size = int(token, 16)
                    if size == 0:
                        self.state = 'trailer'
                    else:
                        self.need = size
                        self.state = 'data'
                elif line == b'':
                    self.complete = True
                    return 'relay_ok_complete', max(self.fed - self.released, 0)
                self.walk = end + 2
            else:
                if self.fed - self.walk < self.need + 2:
                    return None, max(self.fed - self.released, 0)
                self.walk += self.need
                if self.buf[self.walk:self.walk + 2] != b'\\r\\n':
                    return 'relay_channel_failed', 0
                self.walk += 2
                self.need = 0
                self.state = 'size'

    def eof(self):
        # Upstream EOF: completion for close-delimited responses, a fixed
        # failure for truncated framed ones, and the recorded zero-then-EOF
        # case when no status line was ever observed.
        if self.mode == 'close' and self.head_done:
            self.complete = True
            return 'relay_ok_complete'
        return 'relay_channel_failed'


def _connect(config, context, counters, limits):
    # ONE resolution per call, filtered by the reviewed permitted-address
    # rule; connect BY the resolved address with server_hostname from the
    # config. A refusal or failure returns one fixed code and never re-queries
    # or retries. The connection counter counts ATTEMPTS and is never
    # decremented: it proves no second connection under any condition.
    counters['dns_resolutions'] += 1
    try:
        results = socket.getaddrinfo(config['hostname'], config['port'], 0,
                                     socket.SOCK_STREAM)
    except OSError:
        return 'relay_dns_refused', None
    selected = None
    for family, socktype, proto, _canon, address in results:
        if socktype != socket.SOCK_STREAM:
            continue
        if not _address_permitted(config['rule'], address[0]):
            continue
        selected = (family, socktype, proto, address)
        break
    if selected is None:
        return 'relay_dns_refused', None
    family, socktype, proto, address = selected
    counters['upstream_connections'] += 1
    raw = socket.socket(family, socktype, proto)
    try:
        raw.settimeout(limits['connect_timeout_ms'] / 1000.0)
        raw.connect(address)
    except socket.timeout:
        try:
            raw.close()
        except OSError:
            pass
        return 'relay_connect_timeout', None
    except OSError:
        try:
            raw.close()
        except OSError:
            pass
        return 'relay_channel_failed', None
    try:
        raw.settimeout(limits['handshake_timeout_ms'] / 1000.0)
        return None, context.wrap_socket(raw, server_hostname=config['hostname'])
    except socket.timeout:
        try:
            raw.close()
        except OSError:
            pass
        return 'relay_handshake_timeout', None
    except OSError:
        try:
            raw.close()
        except OSError:
            pass
        return 'relay_channel_failed', None


def _teardown(sock, counters):
    # Bounded discard drain: at most a small fixed byte count within a fixed
    # linger, never waiting for upstream EOF, never forwarding or storing a
    # drained byte. Close failure is a teardown failure (fixed code) and
    # suppresses a successful outcome. Drained bytes are only ever counted.
    if sock is None:
        return False
    drained = 0
    failed = False
    try:
        try:
            sock.settimeout(0.05)
            deadline = _now_ms() + TEARDOWN_DRAIN_MS
            while drained < TEARDOWN_DRAIN_CAP and _now_ms() < deadline:
                try:
                    block = sock.recv(READ_CHUNK)
                except socket.timeout:
                    break
                except OSError:
                    break
                if not block:
                    break
                drained += len(block)
        finally:
            sock.close()
    except OSError:
        failed = True
    counters['teardown_drain_bytes'] += drained
    if failed:
        counters['teardown_failures'] += 1
    return failed


def main():
    line = sys.stdin.buffer.readline(1 << 20)
    if not line.endswith(b'\\n'):
        sys.exit(96)
    try:
        payload = bytes.fromhex(line[:-1].decode('ascii'))
    except ValueError:
        sys.exit(97)
    if not payload.startswith(b'CONF '):
        sys.exit(98)
    try:
        document = json.loads(payload[5:].decode('utf-8'))
    except ValueError:
        sys.exit(99)
    code, config = _validate_trust(document.get('trust'))
    if code is not None:
        report_fd = document.get('report_fd')
        if _integer(report_fd, 0, 1 << 20):
            try:
                _report(report_fd, {'type': 'error', 'code': code})
            except OSError:
                pass
        sys.exit(1)
    names = ('relay_read_fd', 'relay_write_fd', 'control_fd', 'report_fd',
             'liveness_fd', 'ca_fd')
    if any(not _integer(document.get(name), 0, 1 << 20) for name in names):
        sys.exit(99)
    values = [document[name] for name in names]
    others = values[2:]
    if len(set(others)) != len(others) or set(values[:2]) & set(others):
        sys.exit(99)
    chan_r, chan_w = values[0], values[1]
    control_fd, report_fd, liveness_fd, ca_fd = others
    if not _integer(document.get('total_timeout_ms'), 1, 86400000):
        sys.exit(99)
    bound = document.get('bound_authority')
    if type(bound) is not str or not bound.startswith(LOOPBACK_BIND + ':'):
        sys.exit(99)
    try:
        bound_port = int(bound.split(':', 1)[1])
    except ValueError:
        sys.exit(99)
    if not PORT_WINDOW[0] <= bound_port <= PORT_WINDOW[1]:
        sys.exit(99)
    ca_payload = _verify_ca(ca_fd, config['ca_sha256'],
                            config['ca_size_bytes'])
    if ca_payload is None:
        _report(report_fd, {'type': 'error', 'code': 'relay_ca_pin_mismatch'})
        sys.exit(1)
    for fd in (chan_r, chan_w, control_fd, liveness_fd):
        try:
            os.set_blocking(fd, False)
        except OSError:
            _report(report_fd, {'type': 'error', 'code': 'relay_channel_failed'})
            sys.exit(1)
    limits = config['limits']
    counters = {'requests_observed': 0, 'requests_refused': 0,
                'dns_resolutions': 0, 'upstream_connections': 0,
                'guest_bytes_in': 0, 'guest_bytes_out': 0,
                'teardown_drain_bytes': 0, 'teardown_failures': 0}
    deadline = _now_ms() + document['total_timeout_ms']
    idle_deadline = _now_ms() + limits['idle_timeout_ms']
    _report(report_fd, {'type': 'started',
                        'protocol_version': PROTOCOL_VERSION})
    inbuf = bytearray()
    parsed = None
    body = bytearray()
    upstream = None
    send_view = None
    outbuf = bytearray()
    response = None
    cursor = 0
    concluded = None
    pending_code = None
    closed_for_requests = False
    cardinality_flagged = False
    cardinality_reported = False
    outcome = None

    def refuse_request(refusal):
        # One fixed outcome for one observed refused request: nothing is ever
        # sent upstream for it and nothing is retried.
        nonlocal concluded, closed_for_requests, cardinality_reported
        counters['requests_observed'] += 1
        counters['requests_refused'] += 1
        concluded = refusal
        closed_for_requests = True
        cardinality_reported = True
        _report(report_fd, {'type': 'call_done', 'code': concluded,
                            'counters': dict(counters)})

    def begin_exchange(excess):
        # The exact approved request bytes are complete: one DNS resolution,
        # one connect-by-resolved-address, one TLS handshake, one send, one
        # response. Pipelined extra bytes refuse the call BEFORE any upstream
        # work. Never a retry, never a second connection.
        nonlocal upstream, send_view, response, parsed, cursor
        nonlocal cardinality_flagged
        if excess:
            cardinality_flagged = True
            refuse_request('relay_refused_cardinality')
            parsed = None
            del body[:]
            return
        context = _client_context(ca_fd, ca_payload)
        if context is None:
            parsed = None
            del body[:]
            concluded_for_exchange('relay_ca_pin_mismatch')
            return
        failure, tls = _connect(config, context, counters, limits)
        if failure is not None:
            parsed = None
            del body[:]
            concluded_for_exchange(failure)
            return
        request_bytes = _reconstruct(config, parsed, bytes(body))
        parsed = None
        del body[:]
        upstream = tls
        upstream.setblocking(False)
        send_view = memoryview(request_bytes)
        response = _Response()
        cursor += 1

    def concluded_for_exchange(code):
        # Schedule the call report: it fires after any still-buffered
        # response bytes have been flushed to the guest. More approved
        # entries may remain (multi-entry request sets stay open for the
        # next in-order request).
        nonlocal pending_code
        pending_code = code

    while True:
        now = _now_ms()
        if now >= deadline:
            outcome = 'relay_total_timeout'
            break
        watched = [chan_r, control_fd, liveness_fd]
        if upstream is not None:
            watched.append(upstream)
        ready = _wait(watched, 50)
        if liveness_fd in ready:
            try:
                if not os.read(liveness_fd, 4096):
                    outcome = 'relay_parent_lost'
                    break
            except BlockingIOError:
                pass
        if control_fd in ready:
            try:
                command = os.read(control_fd, 4096)
            except BlockingIOError:
                command = None
            if command is not None and command.strip() == b'STOP':
                # Stop is honored immediately: no new DNS query or upstream
                # connection starts after this point.
                outcome = 'relay_stopped'
                break
        if upstream is not None:
            if send_view is not None:
                try:
                    written = upstream.send(send_view)
                except ssl.SSLWantWriteError:
                    written = 0
                except OSError:
                    _teardown(upstream, counters)
                    upstream = None
                    concluded_for_exchange('relay_channel_failed')
                else:
                    if written:
                        send_view = send_view[written:]
                        if not len(send_view):
                            send_view = None
                        idle_deadline = _now_ms() + limits['idle_timeout_ms']
            if upstream is not None and send_view is None:
                try:
                    block = upstream.recv(limits['relay_response_read_chunk'])
                except (ssl.SSLWantReadError, ssl.SSLWantWriteError,
                        BlockingIOError, socket.timeout):
                    block = None
                except ssl.SSLZeroReturnError:
                    block = b''
                except OSError:
                    _teardown(upstream, counters)
                    upstream = None
                    concluded_for_exchange('relay_channel_failed')
                    block = None
                if upstream is not None and block is not None:
                    if block == b'':
                        result = response.eof()
                        failed = _teardown(upstream, counters)
                        upstream = None
                        if result == 'relay_ok_complete':
                            result = 'relay_teardown_failed' if failed else 'relay_ok'
                        if cardinality_flagged:
                            result = 'relay_refused_cardinality'
                        concluded_for_exchange(result)
                    elif block:
                        idle_deadline = _now_ms() + limits['idle_timeout_ms']
                        result, release = response.feed(
                            block, limits['max_head_bytes'],
                            limits['max_relay_response_bytes'])
                        if release > 0:
                            outbuf.extend(response.buf[
                                response.released:response.released + release])
                            response.released += release
                        if result == 'relay_ok_complete':
                            failed = _teardown(upstream, counters)
                            upstream = None
                            code = 'relay_teardown_failed' if failed else 'relay_ok'
                            if cardinality_flagged:
                                code = 'relay_refused_cardinality'
                            concluded_for_exchange(code)
                        elif result is not None:
                            _teardown(upstream, counters)
                            upstream = None
                            concluded_for_exchange(result)
        while outbuf:
            try:
                moved = os.write(chan_w, outbuf)
            except BlockingIOError:
                break
            except OSError:
                outcome = 'relay_channel_failed'
                break
            del outbuf[:moved]
            counters['guest_bytes_out'] += moved
            idle_deadline = _now_ms() + limits['idle_timeout_ms']
        if outcome is not None:
            break
        if pending_code is not None and not outbuf:
            concluded = pending_code
            pending_code = None
            if cardinality_flagged and concluded == 'relay_ok':
                concluded = 'relay_refused_cardinality'
            # Once every approved entry is consumed, any further guest
            # request is a cardinality refusal.
            if cursor >= len(config['requests']):
                closed_for_requests = True
            _report(report_fd, {'type': 'call_done', 'code': concluded,
                                'counters': dict(counters)})
        if pending_code is None and concluded is None and now >= idle_deadline:
            # No byte in either direction inside the call: covers the guest
            # stalling mid-request AND the upstream stalling mid-exchange.
            outcome = 'relay_idle_timeout'
            break
        if chan_r in ready:
            try:
                block = os.read(chan_r, READ_CHUNK)
            except BlockingIOError:
                block = None
            if block == b'':
                # The guest half closed: mid-exchange it fails the call; a
                # concluded call ends with its outcome; an exhausted or
                # missing request set ends as a cardinality failure (zero or
                # short of the reviewed request count fails the call).
                if upstream is not None or parsed is not None:
                    outcome = 'relay_channel_failed'
                elif concluded is not None:
                    if concluded == 'relay_ok' and cursor < len(config['requests']):
                        outcome = 'relay_refused_cardinality'
                    else:
                        outcome = concluded
                elif cursor < len(config['requests']):
                    outcome = 'relay_refused_cardinality'
                else:
                    outcome = 'relay_channel_failed'
                break
            if block:
                counters['guest_bytes_in'] += len(block)
                idle_deadline = _now_ms() + limits['idle_timeout_ms']
                if upstream is not None or pending_code is not None:
                    # Any guest byte during an exchange is an additional
                    # request: the call fails when the exchange completes,
                    # with no resend of anything.
                    if not cardinality_flagged:
                        cardinality_flagged = True
                        counters['requests_observed'] += 1
                        counters['requests_refused'] += 1
                    continue
                if closed_for_requests:
                    if not cardinality_reported:
                        cardinality_reported = True
                        counters['requests_observed'] += 1
                        counters['requests_refused'] += 1
                        _report(report_fd, {
                            'type': 'call_done',
                            'code': 'relay_refused_cardinality',
                            'counters': dict(counters)})
                    continue
                inbuf.extend(block)
                if parsed is None:
                    marker = inbuf.find(b'\\r\\n\\r\\n')
                    if marker < 0:
                        if len(inbuf) > limits['max_head_bytes']:
                            refuse_request('relay_refused_framing')
                            del inbuf[:]
                        continue
                    head = bytes(inbuf[:marker])
                    excess_after = bytes(inbuf[marker + 4:])
                    del inbuf[:]
                    split = _split_head(head)
                    refusal = 'relay_refused_framing'
                    validated = None
                    if split is not None:
                        refusal, validated = _validate_request(
                            config, split[0], split[1], cursor, bound)
                    if refusal is not None or validated is None:
                        refuse_request(refusal or 'relay_refused_framing')
                        continue
                    if (marker + 4 + validated['body_length']
                            > limits['max_relay_request_bytes']):
                        refuse_request('relay_request_bytes_exceeded')
                        continue
                    counters['requests_observed'] += 1
                    parsed = validated
                    body = bytearray(excess_after)
                    if len(body) >= parsed['body_length']:
                        excess = bytes(body[parsed['body_length']:])
                        del body[parsed['body_length']:]
                        begin_exchange(excess)
                    continue
                body.extend(inbuf)
                del inbuf[:]
                if len(body) >= parsed['body_length']:
                    excess = bytes(body[parsed['body_length']:])
                    del body[parsed['body_length']:]
                    begin_exchange(excess)
    if upstream is not None:
        _teardown(upstream, counters)
    final = outcome or concluded or 'relay_channel_failed'
    _report(report_fd, {'type': 'engine_done', 'code': final,
                        'counters': dict(counters)})
    sys.exit(0)


if __name__ == '__main__':
    main()
'''


def _engine_digest():
    """Digest of the exact engine source bytes (helper-digest pattern)."""
    return sha256(ENGINE_SOURCE.encode('utf-8')).hexdigest()


def _linux_path(value):
    """Linux host path rules, host-independent (local mirror; this module has
    zero project imports)."""
    return (type(value) is str and value.startswith('/') and value != '/'
            and '\\' not in value and '\x00' not in value
            and '..' not in value.split('/') and 1 <= len(value.encode('utf-8')) <= 4096)


def _sha256_hex(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def _bounded_int(name, value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError('relay_trust_config_invalid') from None


@dataclass(frozen=True, slots=True)
class RelayHeaderRule:
    """One reviewed forwarded-header rule: exact lowercase name, single
    cardinality, required presence."""
    name: str
    max_count: int = 1
    required: bool = True

    def __post_init__(self):
        if (type(self.name) is not str
                or re.fullmatch('[a-z0-9]([a-z0-9-]{0,126}[a-z0-9])?', self.name) is None
                or self.name in FRAMING_HEADER_NAMES):
            raise ValueError('relay_trust_config_invalid')
        if self.max_count != 1:
            raise ValueError('relay_trust_config_invalid')
        if type(self.required) is not bool:
            raise ValueError('relay_trust_config_invalid')

    def rule_dict(self):
        return dict(name=self.name, max_count=self.max_count,
                    required=self.required)


@dataclass(frozen=True, slots=True)
class RelayRequestEntry:
    """One approved origin-form request: closed method, exact unnormalized
    target and query literals, and the reviewed forwarded-header rules."""
    method: str = 'POST'
    target: str = '/v1/messages'
    query: str = 'beta=true'
    # sorted(): the default tuple order is policy-dict digest input and must
    # stay byte-identical across processes regardless of hash randomization.
    forwarded_headers: tuple[RelayHeaderRule, ...] = tuple(
        RelayHeaderRule(name) for name in sorted(FORWARDED_HEADER_NAMES))

    def __post_init__(self):
        if self.method != 'POST':
            raise ValueError('relay_trust_config_invalid')
        if (type(self.target) is not str or not 1 <= len(self.target) <= 8192
                or self.target.encode('ascii', 'ignore').decode('ascii') != self.target
                or any(byte < 0x21 or byte > 0x7e
                       for byte in self.target.encode('ascii'))):
            raise ValueError('relay_trust_config_invalid')
        if (type(self.query) is not str or len(self.query) > 8192
                or self.query.encode('ascii', 'ignore').decode('ascii') != self.query
                or any(byte < 0x21 or byte > 0x7e
                       for byte in self.query.encode('ascii'))):
            raise ValueError('relay_trust_config_invalid')
        if not self.target.startswith('/') or '?' in self.target \
                or '?' in self.query:
            raise ValueError('relay_trust_config_invalid')
        if (type(self.forwarded_headers) is not tuple or not self.forwarded_headers
                or any(type(rule) is not RelayHeaderRule
                       for rule in self.forwarded_headers)):
            raise ValueError('relay_trust_config_invalid')
        names = [rule.name for rule in self.forwarded_headers]
        if len(set(names)) != len(names) or 'host' not in names:
            raise ValueError('relay_trust_config_invalid')

    def entry_dict(self):
        return dict(method=self.method, target=self.target, query=self.query,
                    forwarded_headers=[rule.rule_dict()
                                       for rule in self.forwarded_headers])

    def expected_target(self):
        """The exact unnormalized request-line literal the relay compares
        against (no percent-decode, fold or reorder anywhere)."""
        return self.target + (('?' + self.query) if self.query else '')


@dataclass(frozen=True, slots=True)
class RelayCaBundlePin:
    """Pinned CA bundle identity: absolute Linux path plus exact SHA256 and
    byte size (locally validated; no project imports)."""
    path: str
    sha256: str
    size_bytes: int

    def __post_init__(self):
        if not _linux_path(self.path):
            raise ValueError('relay_trust_config_invalid')
        if not _sha256_hex(self.sha256):
            raise ValueError('relay_trust_config_invalid')
        _bounded_int('size_bytes', self.size_bytes, 1, RELAY_CA_SIZE_CAP)


@dataclass(frozen=True, slots=True)
class RelayTrustConfig:
    """Reviewed relay trust configuration: destination, TLS and identity
    binding, limits and the approved request set. Construction is inert and
    declaration-only; nothing is discovered at run time. ``total_timeout_ms``
    None means the remaining spec budget (resolved to a concrete number by the
    trusted parent when the engine is configured)."""
    ca_bundle: RelayCaBundlePin
    origin_hostname: str = DEFAULT_ORIGIN_HOSTNAME
    origin_scheme: str = RELAY_ORIGIN_SCHEME
    origin_port: int = RELAY_ORIGIN_PORT
    permitted_address_rule: str = 'public-global-unicast-only'
    tls_floor: str = RELAY_TLS_FLOOR
    max_relay_request_bytes: int = MAX_RELAY_REQUEST_BYTES
    max_relay_response_bytes: int = MAX_RELAY_RESPONSE_BYTES
    relay_response_read_chunk: int = RELAY_RESPONSE_READ_CHUNK
    connect_timeout_ms: int = RELAY_CONNECT_TIMEOUT_MS
    handshake_timeout_ms: int = RELAY_HANDSHAKE_TIMEOUT_MS
    idle_timeout_ms: int = RELAY_IDLE_TIMEOUT_MS
    total_timeout_ms: int | None = None
    max_header_count: int = MAX_RELAY_HEADER_COUNT
    max_header_bytes: int = MAX_RELAY_HEADER_BYTES
    max_head_bytes: int = MAX_RELAY_HEAD_BYTES
    requests: tuple[RelayRequestEntry, ...] = (RelayRequestEntry(),)
    preflight_entries: tuple[RelayRequestEntry, ...] = ()

    def __post_init__(self):
        if self.origin_scheme != RELAY_ORIGIN_SCHEME:
            raise ValueError('relay_trust_config_invalid')
        hostname = self.origin_hostname
        if (type(hostname) is not str
                or len(hostname.encode('utf-8')) > RELAY_HOSTNAME_MAX_BYTES
                or hostname != hostname.lower()
                or any(sep in hostname for sep in ('/', '?', '#', '@', ':', ' '))
                or re.fullmatch('[a-z0-9.-]{1,253}', hostname) is None):
            raise ValueError('relay_trust_config_invalid')
        if self.permitted_address_rule not in PERMITTED_ADDRESS_RULES:
            raise ValueError('relay_trust_config_invalid')
        if self.tls_floor != RELAY_TLS_FLOOR:
            raise ValueError('relay_trust_config_invalid')
        if type(self.ca_bundle) is not RelayCaBundlePin:
            raise ValueError('relay_trust_config_invalid')
        _bounded_int('origin_port', self.origin_port, 1, 65535)
        _bounded_int('max_relay_request_bytes', self.max_relay_request_bytes,
                     1, MAX_RELAY_REQUEST_BYTES)
        _bounded_int('max_relay_response_bytes', self.max_relay_response_bytes,
                     1, MAX_RELAY_RESPONSE_BYTES)
        _bounded_int('relay_response_read_chunk', self.relay_response_read_chunk,
                     1, RELAY_RESPONSE_READ_CHUNK)
        _bounded_int('connect_timeout_ms', self.connect_timeout_ms,
                     1, RELAY_TOTAL_TIMEOUT_CAP_MS)
        _bounded_int('handshake_timeout_ms', self.handshake_timeout_ms,
                     1, RELAY_TOTAL_TIMEOUT_CAP_MS)
        _bounded_int('idle_timeout_ms', self.idle_timeout_ms,
                     1, RELAY_TOTAL_TIMEOUT_CAP_MS)
        if not (self.total_timeout_ms is None
                or (type(self.total_timeout_ms) is int
                    and 1 <= self.total_timeout_ms <= RELAY_TOTAL_TIMEOUT_CAP_MS)):
            raise ValueError('relay_trust_config_invalid')
        _bounded_int('max_header_count', self.max_header_count,
                     1, MAX_RELAY_HEADER_COUNT)
        _bounded_int('max_header_bytes', self.max_header_bytes,
                     1, MAX_RELAY_HEADER_BYTES)
        _bounded_int('max_head_bytes', self.max_head_bytes, 1, MAX_RELAY_HEAD_BYTES)
        if (type(self.requests) is not tuple or len(self.requests) != 1
                or self.requests[0] != RelayRequestEntry()):
            # Closed today: exactly the one reviewed Messages POST entry; a
            # wider reviewed set requires the plan gate, not a config value.
            raise ValueError('relay_trust_config_invalid')
        if type(self.preflight_entries) is not tuple or any(
                type(entry) is not RelayRequestEntry
                for entry in self.preflight_entries):
            raise ValueError('relay_trust_config_invalid')
        if self.preflight_entries:
            # No reviewed preflight approval exists yet: declaring one is a
            # deliberate blocker, never widened by this validator.
            raise ValueError('relay_preflight_not_approved')

    def policy_dict(self):
        """Public digest input: protocol version, origin triple, CA pin,
        address rule, TLS floor, limits, request set, preflight set and the
        endpoint binding. Never a credential, ephemeral port, descriptor
        number, PID or any runtime-discovered value."""
        return dict(
            protocol_version=RELAY_PROTOCOL_VERSION,
            origin=dict(scheme=self.origin_scheme, hostname=self.origin_hostname,
                        port=self.origin_port),
            ca_bundle=dict(path=self.ca_bundle.path,
                           sha256=self.ca_bundle.sha256,
                           size_bytes=self.ca_bundle.size_bytes),
            permitted_address_rule=self.permitted_address_rule,
            tls_floor=self.tls_floor,
            limits=dict(max_relay_request_bytes=self.max_relay_request_bytes,
                        max_relay_response_bytes=self.max_relay_response_bytes,
                        relay_response_read_chunk=self.relay_response_read_chunk,
                        connect_timeout_ms=self.connect_timeout_ms,
                        handshake_timeout_ms=self.handshake_timeout_ms,
                        idle_timeout_ms=self.idle_timeout_ms,
                        total_timeout_ms=self.total_timeout_ms,
                        max_header_count=self.max_header_count,
                        max_header_bytes=self.max_header_bytes,
                        max_head_bytes=self.max_head_bytes),
            requests=[entry.entry_dict() for entry in self.requests],
            preflight=[entry.entry_dict() for entry in self.preflight_entries],
            endpoint_binding=ENDPOINT_BINDING)


def draw_relay_port():
    """One fresh os.urandom-derived draw per call inside the reviewed
    [20000, 32767] window (never sequential, never cached; the drawn port is
    never a digest input)."""
    span = RELAY_PORT_WINDOW[1] - RELAY_PORT_WINDOW[0] + 1
    return RELAY_PORT_WINDOW[0] + int.from_bytes(os.urandom(2), 'big') % span


def validate_relay_outcome(value):
    """Closed-vocabulary check for every relay outcome code."""
    if type(value) is not str or value not in RELAY_OUTCOMES:
        raise ValueError('relay_outcome_invalid')
    return value
