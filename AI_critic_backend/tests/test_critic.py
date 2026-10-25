import httpx

import pytest
from groq import RateLimitError
from google import genai
from google.genai import errors

from app.services.ai import critic_gemini as critic


def _text_response(text, finish_reason="STOP", block_reason=None):
    candidate = type(
        "Candidate",
        (),
        {
            "content": type("Content", (), {"parts": [object()]})(),
            "finish_reason": finish_reason,
        },
    )()
    feedback = type("PromptFeedback", (), {"block_reason": block_reason})()
    return type(
        "Response",
        (),
        {
            "parsed": None,
            "candidates": [candidate],
            "prompt_feedback": feedback,
            "text": text,
        },
    )()


def _rate_limit(retry_after="1"):
    return RateLimitError(
        "rate limited",
        response=httpx.Response(
            429,
            headers={"retry-after": retry_after},
            request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
        ),
        body=None,
    )


def test_groq_retry_respects_retry_after(monkeypatch):
    attempts, delays = [], []

    class FakeCompletions:
        def create(self, **kwargs):
            attempts.append(kwargs)
            if len(attempts) == 1:
                raise _rate_limit("2")
            message = type("Message", (), {"content": '{"findings": []}'})()
            choice = type("Choice", (), {"message": message})()
            return type("Response", (), {"choices": [choice]})()

    class FakeGroq:
        def __init__(self, **kwargs):
            self.chat = type("Chat", (), {"completions": FakeCompletions()})()

    monkeypatch.setattr(critic, "Groq", FakeGroq)
    monkeypatch.setattr(critic.settings, "groq_api_key", "test-key")
    monkeypatch.setattr(critic.time, "sleep", delays.append)

    assert critic._call_groq("evidence") == {"findings": []}
    assert len(attempts) == 2
    assert delays == [2.0]
    assert attempts[0]["max_completion_tokens"] == critic.MAX_CRITIC_OUTPUT_TOKENS


def test_groq_rate_limit_is_bounded(monkeypatch):
    class FakeCompletions:
        def create(self, **kwargs):
            raise _rate_limit("0")

    class FakeGroq:
        def __init__(self, **kwargs):
            self.chat = type("Chat", (), {"completions": FakeCompletions()})()

    monkeypatch.setattr(critic, "Groq", FakeGroq)
    monkeypatch.setattr(critic.settings, "groq_api_key", "test-key")
    monkeypatch.setattr(critic.time, "sleep", lambda _: None)

    with pytest.raises(critic.CriticRateLimitError):
        critic._call_groq("evidence")


@pytest.mark.parametrize(
    "provider, caller",
    [("groq", "_call_groq"), ("gemini", "_call_gemini"), ("ollama", "_call_ollama")],
)
def test_uses_configured_critic_provider(monkeypatch, provider, caller):
    called = []
    monkeypatch.setattr(critic.settings, "critic_provider", provider)
    for name in ("_call_groq", "_call_gemini", "_call_ollama"):
        monkeypatch.setattr(
            critic,
            name,
            lambda prompt, name=name: called.append(name) or {"findings": []},
        )

    assert critic.analyze_with_critic({}) == critic.CriticResponse(findings=[])
    assert called == [caller]


def test_invalid_critic_json_is_rejected():
    with pytest.raises(ValueError, match="invalid JSON"):
        critic._extract_json("not json")


def test_extract_json_accepts_markdown_fenced_json():
    assert critic._extract_json("```json\n{\"findings\": []}\n```") == {
        "findings": []
    }


def test_gemini_uses_sdk_structured_response(monkeypatch):
    calls = []

    class FakeModels:
        def generate_content(self, **kwargs):
            calls.append(kwargs)
            return type(
                "Response",
                (),
                {
                    "parsed": {"findings": []},
                    "text": property(lambda _: (_ for _ in ()).throw(AssertionError())),
                },
            )()

    class FakeClient:
        def __init__(self, **kwargs):
            self.models = FakeModels()

        def close(self):
            return None

    monkeypatch.setattr(genai, "Client", FakeClient)
    monkeypatch.setattr(critic.settings, "gemini_api_key", "test-key")

    assert critic._call_gemini("evidence") == {"findings": []}
    assert calls[0]["config"].response_mime_type == "application/json"
    assert calls[0]["config"].response_schema is critic.CriticResponse
    assert (
        calls[0]["config"].max_output_tokens
        == critic.settings.critic_gemini_max_output_tokens
    )


def test_gemini_accepts_structured_finding(monkeypatch):
    finding = {
        "id": "AI-001",
        "category": "navigation",
        "severity": "medium",
        "element": "primary navigation",
        "problem": "Labels are ambiguous.",
        "evidence": "Two labels use the same text.",
        "user_impact": "Users may select the wrong destination.",
        "recommendation": "Use distinct labels.",
        "confidence": 0.8,
    }

    class FakeModels:
        def generate_content(self, **kwargs):
            return type("Response", (), {"parsed": {"findings": [finding]}})()

    class FakeClient:
        def __init__(self, **kwargs):
            self.models = FakeModels()

        def close(self):
            return None

    monkeypatch.setattr(genai, "Client", FakeClient)
    monkeypatch.setattr(critic.settings, "gemini_api_key", "test-key")

    assert critic._call_gemini("evidence") == {"findings": [finding]}


def test_gemini_uses_json_text_fallback(monkeypatch):
    class FakeModels:
        def generate_content(self, **kwargs):
            return _text_response('{"findings": []}')

    class FakeClient:
        def __init__(self, **kwargs):
            self.models = FakeModels()

        def close(self):
            return None

    monkeypatch.setattr(genai, "Client", FakeClient)
    monkeypatch.setattr(critic.settings, "gemini_api_key", "test-key")

    assert critic._call_gemini("evidence") == {"findings": []}


def test_gemini_rejects_missing_candidate(monkeypatch):
    class FakeModels:
        def generate_content(self, **kwargs):
            return type(
                "Response",
                (),
                {"parsed": None, "candidates": [], "prompt_feedback": None},
            )()

    class FakeClient:
        def __init__(self, **kwargs):
            self.models = FakeModels()

        def close(self):
            return None

    monkeypatch.setattr(genai, "Client", FakeClient)
    monkeypatch.setattr(critic.settings, "gemini_api_key", "test-key")

    with pytest.raises(critic.CriticResponseFormatError, match="no response candidate"):
        critic._call_gemini("evidence")


def test_gemini_rejects_safety_blocked_response(monkeypatch):
    class FakeModels:
        def generate_content(self, **kwargs):
            return type(
                "Response",
                (),
                {
                    "parsed": None,
                    "candidates": [],
                    "prompt_feedback": type(
                        "PromptFeedback", (), {"block_reason": "SAFETY"}
                    )(),
                },
            )()

    class FakeClient:
        def __init__(self, **kwargs):
            self.models = FakeModels()

        def close(self):
            return None

    monkeypatch.setattr(genai, "Client", FakeClient)
    monkeypatch.setattr(critic.settings, "gemini_api_key", "test-key")

    with pytest.raises(critic.CriticResponseFormatError, match="no response candidate"):
        critic._call_gemini("evidence")


def test_gemini_rejects_max_tokens_response_even_if_parsed():
    candidate = type("Candidate", (), {"finish_reason": "MAX_TOKENS"})()
    response = type(
        "Response",
        (),
        {"parsed": {"findings": []}, "candidates": [candidate]},
    )()

    with pytest.raises(critic.CriticResponseFormatError, match="truncated"):
        critic._gemini_payload(response)


@pytest.mark.parametrize("text", ["", '{"findings": ['])
def test_gemini_rejects_empty_or_truncated_text(monkeypatch, text):
    class FakeModels:
        def generate_content(self, **kwargs):
            return _text_response(text, finish_reason="MAX_TOKENS")

    class FakeClient:
        def __init__(self, **kwargs):
            self.models = FakeModels()

        def close(self):
            return None

    monkeypatch.setattr(genai, "Client", FakeClient)
    monkeypatch.setattr(critic.settings, "gemini_api_key", "test-key")

    with pytest.raises(critic.CriticResponseFormatError):
        critic._call_gemini("evidence")


def test_gemini_retries_transient_server_error(monkeypatch):
    calls, delays = [], []

    class FakeModels:
        def generate_content(self, **kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                raise errors.ServerError(
                    503,
                    {"error": {"status": "UNAVAILABLE"}},
                    response=httpx.Response(
                        503,
                        headers={"retry-after": "2"},
                        request=httpx.Request("POST", "https://generativelanguage.googleapis.com"),
                    ),
                )
            return type("Response", (), {"parsed": {"findings": []}})()

    class FakeClient:
        def __init__(self, **kwargs):
            self.models = FakeModels()

        def close(self):
            return None

    monkeypatch.setattr(genai, "Client", FakeClient)
    monkeypatch.setattr(critic.settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(critic.time, "sleep", delays.append)
    monkeypatch.setattr(critic.random, "uniform", lambda *_: 0)

    assert critic._call_gemini("evidence") == {"findings": []}
    assert len(calls) == 2
    assert delays == [2.0]


def test_gemini_transient_retry_is_bounded(monkeypatch):
    calls = []

    class FakeModels:
        def generate_content(self, **kwargs):
            calls.append(kwargs)
            raise errors.ServerError(503, {"error": {"status": "UNAVAILABLE"}})

    class FakeClient:
        def __init__(self, **kwargs):
            self.models = FakeModels()

        def close(self):
            return None

    monkeypatch.setattr(genai, "Client", FakeClient)
    monkeypatch.setattr(critic.settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(critic.time, "sleep", lambda _: None)

    with pytest.raises(critic.CriticUnavailableError, match="temporarily unavailable"):
        critic._call_gemini("evidence")
    assert len(calls) == critic.MAX_GEMINI_RETRIES + 1


def test_gemini_does_not_retry_permanent_client_error(monkeypatch):
    calls = []

    class FakeModels:
        def generate_content(self, **kwargs):
            calls.append(kwargs)
            raise errors.ClientError(401, {"error": {"status": "UNAUTHENTICATED"}})

    class FakeClient:
        def __init__(self, **kwargs):
            self.models = FakeModels()

        def close(self):
            return None

    monkeypatch.setattr(genai, "Client", FakeClient)
    monkeypatch.setattr(critic.settings, "gemini_api_key", "test-key")

    with pytest.raises(critic.CriticUnavailableError):
        critic._call_gemini("evidence")
    assert len(calls) == 1


def test_schema_validation_failure_is_not_converted_to_empty_findings(monkeypatch):
    monkeypatch.setattr(critic.settings, "critic_provider", "gemini")
    monkeypatch.setattr(
        critic,
        "_call_gemini",
        lambda prompt: {"findings": [{"id": "AI-1", "category": "nav"}]},
    )

    with pytest.raises(critic.CriticResponseFormatError, match="expected schema"):
        critic.analyze_with_critic({})
