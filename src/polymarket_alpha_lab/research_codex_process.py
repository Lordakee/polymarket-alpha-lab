"""Concrete subprocess transport for the existing Codex event decoder.

The owner application supplies an inert, reviewed command builder. This module
actually starts that command; it does NOT select CLI flags/credentials, certify
Codex filesystem/network/persistence isolation, or enable the standalone CLI.
"""
from dataclasses import replace
from threading import Lock

from polymarket_alpha_lab.research_codex_exec import CodexExecInput, CodexExecOutput
from polymarket_alpha_lab.research_process import ResearchProcessSpec, run_research_process
from polymarket_alpha_lab.research_dispatch_runner import ResearchDispatchStop


class CodexProcessTransport:
    """One process per run; exact prompt on stdin and bounded event bytes back.

    prepare_command receives a validated, copied CodexExecInput including model,
    output_schema_json and max_output_tokens. It must be an inert application
    function, never model-supplied. Its selected-version native flags/config and
    allowed persistence still require separate review; a command's exit zero or
    image hash does not certify its model, hidden calls, permissions or fee bound.
    """
    __slots__ = ('_prepare', '_stop', '_lock', '_failed')

    def __init__(self, *, prepare_command, allow_process_start=False, stop=None):
        if allow_process_start is not True or not callable(prepare_command):
            raise ValueError('research_codex_process_opt_in_required')
        if stop is not None and type(stop) is not ResearchDispatchStop:
            raise ValueError('research_codex_process_stop_invalid')
        self._prepare, self._stop = prepare_command, stop
        self._lock, self._failed = Lock(), False

    def __repr__(self):
        return 'CodexProcessTransport(command=<private>)'

    def run(self, request):
        with self._lock:
            if self._failed:
                raise ValueError('research_codex_process_stopped')
            try:
                if type(request) is not CodexExecInput:
                    raise ValueError('research_codex_process_input_invalid')
                request = replace(request)
                if self._stop is not None and self._stop.is_stopped():
                    raise ValueError('research_codex_process_stopped')
                # Snapshot the actual prompt before calling application code.
                payload = request.prompt_json.encode('utf-8')
                spec = self._prepare(replace(request))
                if type(spec) is not ResearchProcessSpec:
                    raise ValueError('research_codex_process_spec_invalid')
                result = run_research_process(spec=spec, stdin=payload,
                    allow_process_start=True, stop=self._stop)
                return CodexExecOutput(0, result.stdout)
            except BaseException as error:
                self._failed = True
                if not isinstance(error, Exception):
                    raise
                raise ValueError('research_codex_process_failed') from None
