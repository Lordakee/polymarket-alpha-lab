"""Explicit Claude Code bare/no-session profile; NOT a zero-state certificate.

No config discovery/writes, installation, login, keychain or environment lookup.
API authentication is supplied only by the owning application's explicit inert
callback at command preparation, never in the profile digest. No real CLI
activation or subscription-login adoption is shipped by this source module.

The contained v3 relay branch (a launch whose closed egress policy is the
'relay-fixed-origin' value) declares only the symbolic per-call
numeric-loopback endpoint form and binds the relay-bearing launch policy. It
names the L8-D bounded fixed-origin validating relay design boundary and
authorizes no real endpoint, credential or activation.
"""
from dataclasses import asdict, dataclass, field, replace
from hashlib import sha256
import json
from pathlib import Path
from threading import Lock
from urllib.parse import urlsplit

from polymarket_alpha_lab.research_claude_exec import CLAUDE_VERSION, ClaudeExecInput, ClaudeProcessModel
from polymarket_alpha_lab.research_dispatch_runner import ResearchDispatchStop
from polymarket_alpha_lab.research_process import ResearchProcessSpec
from polymarket_alpha_lab.research_process_linux import LinuxLaunchSpec
from polymarket_alpha_lab.research_uncapped import copy_authorization

MODEL_ID = 'claude-opus-5'
_PATH_ENV = frozenset(('HOME', 'CLAUDE_CONFIG_DIR', 'USERPROFILE', 'SYSTEMROOT', 'WINDIR',
                       'TMPDIR', 'TMP', 'TEMP'))
_FIXED_ENV = {
    'CLAUDE_CODE_MAX_RETRIES': '0', 'CLAUDE_CODE_DISABLE_NONSTREAMING_FALLBACK': '1',
    'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC': '1', 'CLAUDE_CODE_DISABLE_FAST_MODE': '1',
    'CLAUDE_CODE_DISABLE_ATTACHMENTS': '1', 'CLAUDE_CODE_DISABLE_AUTO_MEMORY': '1',
    'CLAUDE_CODE_DISABLE_BACKGROUND_TASKS': '1', 'CLAUDE_CODE_DISABLE_ADVISOR_TOOL': '1',
    'CLAUDE_CODE_DISABLE_TERMINAL_TITLE': '1', 'CLAUDE_CODE_DISABLE_FILE_CHECKPOINTING': '1',
    'CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS': '1', 'CLAUDE_CODE_DISABLE_BUNDLED_SKILLS': '1',
    'CLAUDE_CODE_DISABLE_OFFICIAL_MARKETPLACE_AUTOINSTALL': '1',
    'DISABLE_COMPACT': '1', 'DISABLE_UPDATES': '1', 'DISABLE_TELEMETRY': '1',
    'DISABLE_ERROR_REPORTING': '1',
}
# Immutable public configuration: callers cannot modify a returned settings map.
_FIXED_ENV = tuple(sorted(_FIXED_ENV.items()))
# Keys a contained launch must accept for the prepared vendor environment
# (the credential itself arrives by one-use pipe, never the launcher env).
_CONTAINED_ENV_KEYS = frozenset(key for key, _ in _FIXED_ENV) | frozenset((
    'ANTHROPIC_API_KEY', 'ANTHROPIC_BASE_URL', 'CLAUDE_CODE_MAX_OUTPUT_TOKENS',
    'CLAUDE_CONFIG_DIR', 'HOME'))
_LINUX_TEAMS = ('crypto_btc', 'crypto_eth')
# Contained v3 relay branch (the L8-D bounded fixed-origin validating relay
# design boundary). RELAY_EGRESS_POLICY is the closed launch egress value that
# selects the branch; RELAY_ENDPOINT_DECLARATION is the ONLY endpoint form the
# branch accepts — a symbolic declaration whose port 0 means the reviewed
# per-call loopback port draw performed by the launch machinery, never by the
# profile (no path/query/userinfo/fragment, literal host, http scheme).
# RELAY_ENDPOINT_BINDING is the v3 digest declaration of that binding. The
# v1/v2 https endpoint validation and digest bytes are unchanged; the symbolic
# form is valid ONLY inside the v3 branch.
RELAY_EGRESS_POLICY = 'relay-fixed-origin'
RELAY_PROFILE_SCHEMA = 'research-claude-profile-linux-v3'
RELAY_ENDPOINT_BINDING = 'per-call-numeric-loopback-http'
RELAY_ENDPOINT_DECLARATION = 'http://127.0.0.1:0'


def _json(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, allow_nan=False, separators=(',', ':'))


def _endpoint(value):
    if (type(value) is not str or not 1 <= len(value) <= 2048
            or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in value)):
        raise ValueError
    value.encode('utf-8')
    url = urlsplit(value)
    if (url.scheme != 'https' or not url.hostname or url.username is not None or url.password is not None
            or '?' in value or '#' in value or '\\' in value or '%' in url.netloc
            or url.port is not None and url.port <= 0):
        raise ValueError


def _relay_endpoint(value):
    """v3-only endpoint form: EXACTLY the symbolic numeric-loopback http
    declaration. Any other byte sequence — every https form, any other port,
    host, path, query, userinfo or fragment — fails closed."""
    if value != RELAY_ENDPOINT_DECLARATION:
        raise ValueError


def _is_relay_launch(launch):
    """Closed egress key for the v3 branch: a duck-typed attribute read that
    binds when the relay-bearing launch value lands. Offline launches (and
    the historical v1/v2 digests) are unaffected byte for byte."""
    return launch is not None and launch.egress_policy == RELAY_EGRESS_POLICY


def _validate_endpoint(launch, value):
    """Endpoint form is branch-scoped: https for v1/v2 profiles, the symbolic
    per-call numeric-loopback declaration for the v3 relay branch only."""
    if _is_relay_launch(launch):
        _relay_endpoint(value)
    else:
        _endpoint(value)


def _supplier_policy_dict():
    """The finite supplier/stop-admission policy shared verbatim by the
    contained v2 and v3 digest branches."""
    return dict(type='finite-in-memory-team-scoped',
        construction='explicit-slots-only-no-env-file-or-network-lookup',
        stop_binding='identity-at-construction-required',
        admission='supplier-lock-then-stop-admission-then-permanent-consume',
        recycling='none', sharing='one-supplier-across-both-team-clients')


def _relay_v3_digest(value, launch_policy):
    """v3 relay-branch digest: the public contract value plus the
    relay-bearing launch policy dict and the endpoint-binding declaration.
    ``launch_policy`` is the launch's own ``policy_dict()`` (duck-typed: the
    documented relay extension carrying the relay section and the reviewed
    trust configuration); the supplier policy is identical to v2."""
    contained = dict(value, schema_version=RELAY_PROFILE_SCHEMA,
        authentication='delayed-one-use-pipe-after-readiness',
        endpoint_binding=RELAY_ENDPOINT_BINDING,
        linux_launch=launch_policy,
        supplier_policy=_supplier_policy_dict())
    return sha256(_json(contained).encode('utf-8')).hexdigest()


@dataclass(frozen=True, slots=True)
class ClaudeExecProfile:
    process: ResearchProcessSpec = field(repr=False)
    endpoint_url: str = field(repr=False)
    model_id: str = MODEL_ID
    cli_version: str = CLAUDE_VERSION
    linux_launch: LinuxLaunchSpec | None = None

    def __post_init__(self):
        try:
            if (type(self.process) is not ResearchProcessSpec or type(self.model_id) is not str
                    or self.model_id != MODEL_ID or type(self.cli_version) is not str
                    or self.cli_version != CLAUDE_VERSION):
                raise ValueError
            if self.linux_launch is not None:
                # Declaration-only containment binding: no filesystem access,
                # hashing or I/O happens here (inert v2 profiles construct on
                # any host); the launch's identity pins live in its digest.
                if type(self.linux_launch) is not LinuxLaunchSpec:
                    raise ValueError
                # The pinned official CLI prints its identity banner, not a
                # bare version line, for --version (see the retained official
                # probe fixture): exactly ``<version> (Claude Code)``.
                if self.linux_launch.expected_version_output != self.cli_version + ' (Claude Code)\n':
                    raise ValueError
                if not _CONTAINED_ENV_KEYS <= set(self.linux_launch.allowed_guest_env):
                    raise ValueError
            process = replace(self.process)
            if len(process.argv) != 1:
                raise ValueError
            # Branch-scoped endpoint form: https for v1/v2, the symbolic
            # per-call numeric-loopback declaration for a relay launch only.
            # A relay launch paired with any non-symbolic endpoint fails
            # closed here as research_claude_profile_invalid.
            _validate_endpoint(self.linux_launch, self.endpoint_url)
            env = dict(process.environment)
            if not {'HOME', 'CLAUDE_CONFIG_DIR'} <= set(env) <= _PATH_ENV:
                raise ValueError
            for value in env.values():
                if not Path(value).is_absolute():
                    raise ValueError
            object.__setattr__(self, 'process', process)
            # Validate the whole public command/environment eagerly without a
            # secret, disk access or arbitrary caller code.
            self._spec(8192, None)
        except Exception:
            raise ValueError('research_claude_profile_invalid') from None

    def _spec(self, max_output_tokens, api_key):
        argv = (self.process.argv[0], '--print', '--bare', '--restricted',
            '--no-session-persistence', '--input-format', 'text', '--output-format', 'json',
            '--model', self.model_id, '--effort', 'max', '--max-turns', '1',
            '--tools', '', '--disallowedTools', '*', '--disable-slash-commands',
            '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}',
            '--setting-sources', '', '--permission-prompts', 'none', '--no-chrome')
        env = dict(self.process.environment)
        env.update(_FIXED_ENV)
        env.update(ANTHROPIC_BASE_URL=self.endpoint_url, CLAUDE_CODE_MAX_OUTPUT_TOKENS=str(max_output_tokens))
        if api_key is not None:
            env['ANTHROPIC_API_KEY'] = api_key
        return replace(self.process, argv=argv, environment=tuple(sorted(env.items())))

    def _contract_value(self):
        # Public declarations only. The exact output request is in the original
        # task and per-call audit; credential material is NEVER a hash input.
        # The v1 branch is byte-identical to the historical uncontained digest.
        return dict(schema_version='research-claude-profile-v1', cli_version=self.cli_version,
            model_id=self.model_id, process=asdict(self.process), endpoint_url=self.endpoint_url,
            command_template=asdict(self._spec(8192, None)),
            output_limit_policy='original-call-cap', authentication='explicit-api-key-callback',
            prompt_protocol=ClaudeExecInput(self.model_id, '[{}]', 8192).prompt_json)

    @property
    def contract_sha256(self):
        value = self._contract_value()
        if self.linux_launch is None:
            return sha256(_json(value).encode('utf-8')).hexdigest()
        launch_policy = self.linux_launch.policy_dict()
        if _is_relay_launch(self.linux_launch):
            # Contained v3 binds the relay-bearing launch policy dict — the
            # relay section with the relay helper pin, the exact (20000, 32767)
            # per-call port window and the reviewed trust configuration the
            # launch carries — plus the endpoint-binding declaration.
            # Credentials, prompt/transcript contents, the drawn per-call
            # port, descriptor numbers and PIDs are never inputs.
            return _relay_v3_digest(value, launch_policy)
        # Contained v2 binds every new public policy: separate wrapper/helper/
        # interpreter/runtime pins, namespace/mount policy and guest layout,
        # environment/descriptor rules, resource bounds, the two-phase
        # version/model protocol, offline egress, and the finite team-scoped
        # supplier and stop-admission policy. Credentials, prompt/transcript
        # contents, random allocation names, descriptor numbers, PIDs and
        # ephemeral ports are never inputs.
        contained = dict(value, schema_version='research-claude-profile-linux-v2',
            authentication='delayed-one-use-pipe-after-readiness',
            linux_launch=launch_policy,
            supplier_policy=_supplier_policy_dict())
        return sha256(_json(contained).encode('utf-8')).hexdigest()

    def prepare(self, request, *, api_key):
        """Build only; provided key goes to child env, not argv/prompt/digest.

        This does not securely erase memory or hide process environments from
        privileged host observers; the entire host remains a trust boundary.
        """
        try:
            profile = replace(self)
            if type(request) is not ClaudeExecInput:
                raise ValueError
            request = replace(request)
            if request.model_id != profile.model_id:
                raise ValueError
            if (type(api_key) is not str or not 1 <= len(api_key) <= 4096
                    or any(not 33 <= ord(c) <= 126 for c in api_key)):
                raise ValueError
            return profile._spec(request.max_output_tokens, api_key)
        except Exception:
            raise ValueError('research_claude_profile_unavailable') from None


class FiniteInMemoryApiKeySupplier:
    """Explicitly supplied finite per-team credential slots; nothing else.

    Construction binds the rotation's stop token by identity (a REQUIRED
    argument, stored immutably, checked with ``is`` by the operator). There is
    no environment, file, login, keychain or network lookup anywhere. One
    shared lock covers both team clients; admission is always: acquire the
    supplier lock, call the bound stop token's admission operation, and only
    then remove one team slot permanently. A later stop, verification failure
    or process failure never returns a consumed slot. An exhausted supplier
    still permits inert replays that never call it.
    """

    __slots__ = ('_lock', '_stop', '_slots')

    def __init__(self, *, stop, crypto_btc=(), crypto_eth=()):
        if type(stop) is not ResearchDispatchStop:
            raise ValueError('research_claude_supplier_stop_invalid')
        slots = {}
        for team, values in (('crypto_btc', crypto_btc), ('crypto_eth', crypto_eth)):
            if type(values) is not tuple or len(values) > 4096:
                raise ValueError('research_claude_supplier_slots_invalid')
            for value in values:
                if (type(value) is not str or not 1 <= len(value) <= 4096
                        or any(not 33 <= ord(character) <= 126 for character in value)):
                    raise ValueError('research_claude_supplier_slots_invalid')
            slots[team] = list(values)
        self._lock = Lock()
        self._stop = stop
        self._slots = slots

    def __repr__(self):
        remaining = {team: len(values) for team, values in self._slots.items()}
        return 'FiniteInMemoryApiKeySupplier(remaining=%r)' % (remaining,)

    def bound_stop_is(self, stop):
        """Identity check against the construction-time stop token (``is``)."""
        return stop is self._stop

    @property
    def bound_stop(self):
        """The construction-bound stop token (identity only; no secret)."""
        return self._stop

    def acquire(self, team_id):
        if team_id not in _LINUX_TEAMS:
            raise ValueError('research_claude_supplier_team_invalid')
        with self._lock:
            if not self._stop._admit():
                raise ValueError('research_claude_supplier_stopped')
            if not self._slots[team_id]:
                raise ValueError('research_claude_supplier_exhausted')
            return self._slots[team_id].pop(0)

    def remaining(self, team_id):
        with self._lock:
            return len(self._slots.get(team_id, ()))


def claude_profile_factory(*, profile, authorization, api_key_supplier,
                           allow_process_start=False, allow_api_key_use=False, stop=None):
    """Inert opt-in binding. No key supplier call until the audited model call.

    Select this factory explicitly; it never replaces a failed Codex client.
    The caller must use the SAME authorization on require_durable_audit=True.
    Approval/profile binding is not a proof of actual CLI state or model identity.

    A contained (``linux_launch``) profile additionally requires the EXACT
    ``FiniteInMemoryApiKeySupplier`` type bound by identity to ``stop``; each
    factory-created client admits through its own team's scope. Binding
    validates type and immutable scope, never mutable remaining capacity.
    """
    if (type(profile) is not ClaudeExecProfile or allow_process_start is not True
            or allow_api_key_use is not True):
        raise ValueError('research_claude_profile_opt_in_required')
    if stop is not None and type(stop) is not ResearchDispatchStop:
        raise ValueError('research_claude_stop_invalid')
    if profile.linux_launch is not None:
        if type(api_key_supplier) is not FiniteInMemoryApiKeySupplier:
            raise ValueError('research_claude_profile_supplier_invalid')
        if stop is None or not api_key_supplier.bound_stop_is(stop):
            raise ValueError('research_claude_profile_supplier_stop_mismatch')
    elif not callable(api_key_supplier):
        raise ValueError('research_claude_profile_opt_in_required')
    profile, authorization = replace(profile), copy_authorization(authorization)
    if (profile.model_id != authorization.model_id
            or profile.contract_sha256 != authorization.adapter_contract_sha256):
        raise ValueError('research_claude_profile_authorization_mismatch')
    digest = profile.contract_sha256
    def checked(request, supply):
        if type(request) is not ClaudeExecInput:
            raise ValueError('research_claude_input_invalid')
        request = replace(request)
        if (request.model_id != profile.model_id or profile.contract_sha256 != digest
                or len(request.prompt_json.encode('utf-8')) > profile.process.max_stdin_bytes):
            raise ValueError('research_claude_profile_input_incompatible')
        # Preparation above may take time. Recheck immediately before entering
        # the credential callback, not only at the model's earlier admission.
        # This is cooperative stop handling, not an atomic cancel/callback lock.
        if stop is not None and stop.is_stopped():
            raise ValueError('research_claude_profile_stopped')
        # No stored credential lookup here. The owning local application chooses
        # its explicit supplier; supplier exceptions are fixed-code upstream.
        return profile.prepare(request, api_key=supply())
    def prepare(request):
        return checked(request, api_key_supplier)
    def factory(team_id):
        if team_id not in _LINUX_TEAMS:
            raise ValueError('research_claude_profile_team_invalid')
        if profile.linux_launch is None:
            return ClaudeProcessModel(model_id=profile.model_id, prepare_command=prepare,
                                      allow_process_start=True, stop=stop)
        # Each admission belongs to its original team: the per-team closure
        # routes the shared finite supplier through the team scope.
        def team_prepare(request):
            return checked(request, lambda: api_key_supplier.acquire(team_id))
        return ClaudeProcessModel(model_id=profile.model_id, prepare_command=team_prepare,
                                  allow_process_start=True, stop=stop,
                                  linux_launch=profile.linux_launch)
    return factory
