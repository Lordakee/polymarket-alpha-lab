"""Explicit opt-in GLM function-calling adapter for team research.

Fixed HTTPS destination, no redirects, proxy/env discovery, retries, logging,
credential storage, database access, or exchange authentication. Public,
operator-approved task/evidence text is transmitted ONLY on complete().
"""
from __future__ import annotations

import json
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from polymarket_alpha_lab.team_research_agent import research_tool_definitions
from polymarket_alpha_lab.team_research_agent_types import (
    ResearchModelReply, ResearchToolCall, integer, strict_json, text,
)

ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
MAX_RESPONSE_BYTES = 131072


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class GLMResearchModel:
    """Caller-supplied model/token; inert until explicitly enabled and invoked.

    Not a dataclass: the token must not be copied into asdict reports. Do not
    serialize this client. Core runtime is provider-neutral and credential-free.
    """
    __slots__ = ("_api_token", "model", "allow_model_calls", "timeout_seconds")

    def __init__(self, *, api_token: str, model: str,
                 allow_model_calls: bool = False, timeout_seconds: int = 20) -> None:
        text("model", model, 128)
        if any(char.isspace() for char in model):
            raise ValueError("invalid model")
        if (type(api_token) is not str or not api_token or len(api_token) > 4096
                or any(char.isspace() or ord(char) < 32 for char in api_token)):
            raise ValueError("invalid model API token")
        if type(allow_model_calls) is not bool:
            raise ValueError("allow_model_calls must be a bool")
        integer("timeout_seconds", timeout_seconds, 1, 60)
        self._api_token = api_token
        self.model = model
        self.allow_model_calls = allow_model_calls
        self.timeout_seconds = timeout_seconds

    def __repr__(self) -> str:
        return "GLMResearchModel(api_token=<redacted>)"

    def complete(self, *, messages_json: str, max_output_tokens: int) -> ResearchModelReply:
        if self.allow_model_calls is not True:
            raise ValueError("model calls are disabled")
        integer("max_output_tokens", max_output_tokens, 1, 8192)
        text("messages_json", messages_json, 500000)
        try:
            messages = strict_json(messages_json)
            if type(messages) is not list or not messages:
                raise ValueError("invalid messages")
            body = json.dumps({"model": self.model, "messages": messages,
                               "tools": research_tool_definitions(), "tool_choice": "auto",
                               "max_tokens": max_output_tokens, "stream": False,
                               "thinking": {"type": "disabled"}}, allow_nan=False).encode("utf-8")
            request = Request(ENDPOINT, data=body, method="POST", headers={
                "Authorization": f"Bearer {self._api_token}", "Content-Type": "application/json"})
            opener = build_opener(ProxyHandler({}), _NoRedirect())
            with opener.open(request, timeout=self.timeout_seconds) as response:
                if response.geturl() != ENDPOINT:
                    raise ValueError("unexpected response origin")
                raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise ValueError("model response too large")
            envelope = strict_json(raw.decode("utf-8"))
            choices = envelope["choices"]
            if type(choices) is not list or len(choices) != 1:
                raise ValueError("exactly one choice is required")
            choice = choices[0]
            message = choice["message"]
            if message.get("role") != "assistant" or choice["finish_reason"] != "tool_calls":
                raise ValueError("expected function calling response")
            calls = message["tool_calls"]
            if type(calls) is not list or not 1 <= len(calls) <= 8:
                raise ValueError("invalid tool calls")
            parsed = []
            for call in calls:
                if call["type"] != "function":
                    raise ValueError("invalid tool type")
                function = call["function"]
                parsed.append(ResearchToolCall(call["id"], function["name"], function["arguments"]))
            # Usage must be explicit; missing/bool/string usage cannot become zero.
            return ResearchModelReply(tuple(parsed), envelope["usage"]["total_tokens"], choice["finish_reason"])
        except Exception:
            # No HTTP response, token, prompt, raw model output or exception text escapes.
            raise ValueError("research model request failed") from None


__all__ = ("GLMResearchModel",)
