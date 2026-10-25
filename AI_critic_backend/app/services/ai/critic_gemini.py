"""Evidence-limited critic with configurable provider dispatch."""

import json
import logging
import random
import re
import time
from typing import Any, Literal

import requests
from groq import APIStatusError, Groq, RateLimitError
from pydantic import BaseModel, Field, ValidationError

from app.core.config import settings

logger = logging.getLogger(__name__)

MAX_GROQ_RETRIES = 2
MAX_GROQ_RETRY_DELAY_SECONDS = 30.0
GROQ_RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}
GROQ_REQUEST_TIMEOUT_SECONDS = 45.0
MAX_CRITIC_OUTPUT_TOKENS = 180
MAX_GEMINI_RETRIES = 2
MAX_GEMINI_RETRY_DELAY_SECONDS = 30.0

SYSTEM_PROMPT = """
You are Preflight's evidence-based HCI website critic. Identify at most three additional usability issues using only the supplied crawler, HCI, and VLM evidence.

CORE RULES
- Use only the supplied evidence. Never invent website elements, interactions, or behaviours.
- Do not repeat existing findings or make unsupported claims.
- Return only the requested structured response.
- Keep every field concise and focused on one main point.
- Each finding must explain the problem, provide specific evidence, describe the user impact, and give an actionable recommendation.
- Return an empty findings list if no additional issue is supported.

TITLE RULES
- Write a short title of 3–6 words, ideally under 40 characters.
- Use a simple noun phrase, not a complete sentence.
- Name the main usability problem, not its explanation.
- Avoid filler phrases and unnecessary technical terminology.
- Do not include evidence, consequences, or recommendations in the title.

Examples:
Bad: "The hero section's background image has high visual complexity and inconsistent contrast."
Good: "Inconsistent Hero Contrast"

Bad: "The navigation bar mixes informational links with a transactional action without visual distinction."
Good: "Booking Link Lacks Emphasis"

DESCRIPTION RULES
- Explain the main problem in one or two short sentences.
- Use clear, natural language that a non-technical website owner can understand.
- Explain why the issue matters to visitors.
- Avoid repeating the title or including implementation details.

EVIDENCE RULES
- Use one or two short sentences, ideally under 35 words in total.
- Describe only what is directly visible or explicitly supported by the supplied evidence.
- Refer to specific website elements and their visible appearance or placement.
- Use plain language rather than technical audit terminology.
- Do not repeat the full problem description or explain the entire reasoning process.
- Avoid jargon such as "transactional action," "discoverability," "visual distinction," and "conversion point" when simpler wording communicates the same fact.
- Do not mention internal tools, model names, evidence sources, screenshot-processing details, or technical implementation unless essential.
- Make the evidence concrete enough that the website owner can verify the issue.

SOURCE-SPECIFIC RULES
When a finding's source is `hci_rule`:
- Treat the supplied rule result as technical evidence, not as user-facing copy.
- Translate heuristic names, rule identifiers, and technical terminology into plain language.
- Explain the actual interface problem identified by the rule, rather than merely repeating the rule name.
- Keep evidence to one or two short sentences, ideally under 30 words.
- Describe the specific interface element or behaviour only when it is identified in the supplied evidence.
- Do not invent screenshot observations, user actions, or consequences that the rule result does not support.
- If the evidence contains only a rule name without enough detail to identify a concrete issue, do not invent an explanation. Return no additional finding unless the issue is otherwise supported.

When a finding's source is `vlm`:
- Describe the relevant visible interface element and its appearance or placement.
- Use simple language and avoid lengthy visual analysis.
- Do not claim that an element behaves in a particular way unless the supplied evidence supports that claim.

For findings from either source:
- The title must identify the underlying usability problem in 3–6 words.
- The evidence must state the concrete supporting fact, not repeat the title or the recommendation.
- The recommendation must address the supported problem directly.

USER IMPACT RULES
- Explain the likely effect on visitors in one concise sentence.
- Do not exaggerate the severity or claim that users definitely experience a problem when the evidence only suggests a risk.

RECOMMENDATION RULES
- Give one specific, practical action in one concise sentence.
- Recommend a change that directly addresses the observed issue.
- Avoid vague advice such as "improve the design" or "make it better."

STYLE
- Prefer familiar words and short sentences.
- Avoid redundant phrases and excessive detail.
- Do not use the same information in multiple fields.
- Be precise, helpful, and constructive.

"""


class CriticFinding(BaseModel):
    id: str = Field(min_length=1)
    category: str
    severity: Literal["critical", "high", "medium", "low"]
    element_description: str = Field(alias="element")
    problem: str
    evidence: str
    user_impact: str
    recommendation: str
    confidence: float = Field(ge=0.0, le=1.0)


class CriticResponse(BaseModel):
    findings: list[CriticFinding] = Field(default_factory=list)


class CriticUnavailableError(RuntimeError):
    """The optional critic could not complete, while upstream results remain valid."""


class CriticRateLimitError(CriticUnavailableError):
    """Groq rate-limit retries were exhausted."""


class CriticResponseFormatError(ValueError):
    """A critic response was successful but did not match the response contract."""


def _to_dict(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", by_alias=True)
    if hasattr(value, "dict"):
        return value.dict(by_alias=True)
    if isinstance(value, dict):
        return {str(key): _to_dict(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_dict(item) for item in value]
    return value


def _compact(value: Any, depth: int = 0) -> Any:
    if depth >= 4:
        return "[omitted]"
    if isinstance(value, dict):
        blocked = {
            "screenshot",
            "screenshot_path",
            "image_data",
            "base64",
            "outer_html",
            "inner_html",
            "full_html",
            "html_content",
            "full_dom",
            "dom_dump",
        }
        return {
            str(key): _compact(item, depth + 1)
            for key, item in list(value.items())[:25]
            if str(key).lower() not in blocked
            and not any(
                term in str(key).lower()
                for term in ("base64", "outer_html", "inner_html")
            )
        }
    if isinstance(value, (list, tuple)):
        return [_compact(item, depth + 1) for item in value[:8]]
    if isinstance(value, str):
        return value[:250]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)[:150]


def _compact_crawl_evidence(crawl_data: dict) -> dict:
    if not isinstance(crawl_data, dict):
        return {}
    result = {}
    for section, limit in {
        "metadata": 800,
        "structure": 1600,
        "interactive": 2200,
        "forms": 1200,
        "accessibility": 1800,
        "media": 1000,
        "layout": 1600,
    }.items():
        if section not in crawl_data:
            continue
        value = _compact(_to_dict(crawl_data[section]))
        if len(json.dumps(value, ensure_ascii=False, default=str)) <= limit:
            result[section] = value
        else:
            result[section] = {
                "summary": "Section omitted because it exceeded its size budget."
            }
    if isinstance(crawl_data.get("url"), str):
        result["url"] = crawl_data["url"][:300]
    return result


def _compact_findings(findings: Any, max_items: int = 6) -> list[dict]:
    normalized = _to_dict(findings or [])
    if not isinstance(normalized, list):
        return []
    rank = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    items = [item for item in normalized if isinstance(item, dict)]
    items.sort(
        key=lambda item: rank.get(str(item.get("severity", "medium")).lower(), 2)
    )
    allowed = (
        "id",
        "heuristic",
        "category",
        "severity",
        "element",
        "element_description",
        "problem",
        "evidence",
        "user_impact",
        "recommendation",
        "confidence",
    )
    compacted = []
    for finding in items[:max_items]:
        item = {}
        for key in allowed:
            if key not in finding:
                continue
            value = finding[key]
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False, default=str)
            item[key] = value[:250] if isinstance(value, str) else value
        compacted.append(item)
    return compacted


def _extract_json(text: str) -> dict:
    if not text or not text.strip():
        logger.warning("Critic returned empty response text.")
        raise CriticResponseFormatError("Critic returned an empty response.")

    normalized = text.strip()
    fenced = re.fullmatch(
        r"```(?:json)?\s*(.*?)\s*```",
        normalized,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if fenced:
        normalized = fenced.group(1)

    try:
        result = json.loads(normalized)
    except json.JSONDecodeError as error:
        is_truncated = error.pos >= max(0, len(normalized) - 1)
        category = "truncated output" if is_truncated else "invalid JSON"
        logger.warning(
            "Critic JSON decoding failed: %s (response length: %s).",
            category,
            len(normalized),
        )
        raise CriticResponseFormatError(
            "Critic returned truncated JSON."
            if is_truncated
            else "Critic returned invalid JSON."
        ) from error
    if not isinstance(result, dict) or not isinstance(result.get("findings", []), list):
        logger.warning("Critic JSON did not contain a findings list.")
        raise CriticResponseFormatError("Critic response must contain a findings list.")
    return result


def _build_user_prompt(crawl_data: dict, hci_findings: list, vlm_findings: list) -> str:
    payload = {
        "crawler_evidence": _compact_crawl_evidence(crawl_data),
        "existing_hci_findings": _compact_findings(hci_findings),
        "existing_vlm_findings": _compact_findings(vlm_findings),
    }
    prompt = (
        "Identify only additional evidence-supported findings.\n\nWebsite evidence:\n"
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)
    )
    logger.info(
        "Critic prompt size: %s characters; HCI findings sent: %s; VLM findings sent: %s",
        len(prompt),
        len(payload["existing_hci_findings"]),
        len(payload["existing_vlm_findings"]),
    )
    return prompt


def _retry_after_seconds(error: RateLimitError) -> float | None:
    headers = getattr(getattr(error, "response", None), "headers", None)
    if not headers:
        return None
    for name in ("retry-after", "x-ratelimit-reset-tokens"):
        try:
            value = float(headers.get(name))
        except (TypeError, ValueError):
            continue
        if value >= 0:
            return value
    return None


def _groq_retry_delay(error: RateLimitError, attempt: int) -> float:
    retry_after = _retry_after_seconds(error)
    if retry_after is not None:
        return min(retry_after, MAX_GROQ_RETRY_DELAY_SECONDS)
    return min(2**attempt + random.uniform(0, 0.5), MAX_GROQ_RETRY_DELAY_SECONDS)


def _call_groq(prompt: str) -> dict:
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY is not configured.")
    client = Groq(
        api_key=settings.groq_api_key,
        timeout=GROQ_REQUEST_TIMEOUT_SECONDS,
        max_retries=0,
    )
    for attempt in range(MAX_GROQ_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=settings.critic_groq_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            SYSTEM_PROMPT + "\n\nYou MUST return valid JSON only. "
                            "The response must be a JSON object containing "
                            'a "findings" array. Do not include Markdown fences.'
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Analyze the following website evidence and return "
                            "the result as JSON.\n\n" + prompt
                        ),
                    },
                ],
                response_format={"type": "json_object"},
                max_completion_tokens=MAX_CRITIC_OUTPUT_TOKENS,
                temperature=0.2,
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Groq returned an empty critic response.")
            return _extract_json(content)
        except RateLimitError as error:
            if attempt == MAX_GROQ_RETRIES:
                logger.warning(
                    "Groq critic rate limit exhausted after %s retries. Model: %s",
                    attempt,
                    settings.critic_groq_model,
                )
                raise CriticRateLimitError(
                    "Groq critic is rate limited; retries were exhausted."
                ) from error

            delay = _groq_retry_delay(error, attempt)
            logger.warning(
                "Groq critic rate limited; retrying in %.1f seconds "
                "(attempt %s/%s).",
                delay,
                attempt + 1,
                MAX_GROQ_RETRIES,
            )
            time.sleep(delay)

        except APIStatusError as error:
            status_code = getattr(error, "status_code", None)
            if status_code not in GROQ_RETRYABLE_STATUS_CODES:
                logger.error(
                    "Groq critic non-retryable API error. Model=%s HTTP=%s",
                    settings.critic_groq_model,
                    status_code,
                )
                raise CriticUnavailableError(
                    f"Groq critic API request failed (HTTP {status_code})."
                ) from error

            if attempt == MAX_GROQ_RETRIES:
                logger.error(
                    "Groq critic retries exhausted. Model=%s HTTP=%s Attempts=%s",
                    settings.critic_groq_model,
                    status_code,
                    attempt + 1,
                )
                raise CriticUnavailableError(
                    f"Groq critic failed after {attempt + 1} attempts "
                    f"(HTTP {status_code})."
                ) from error

            retry_after = _provider_retry_after_seconds(error)
            delay = (
                min(retry_after, MAX_GROQ_RETRY_DELAY_SECONDS)
                if retry_after is not None
                else min(
                    2**attempt + random.uniform(0, 0.5), MAX_GROQ_RETRY_DELAY_SECONDS
                )
            )
            logger.warning(
                "Groq critic transient failure. Model=%s HTTP=%s "
                "Attempt=%s/%s Delay=%.1fs",
                settings.critic_groq_model,
                status_code,
                attempt + 1,
                MAX_GROQ_RETRIES,
                delay,
            )
            time.sleep(delay)


def _call_ollama(prompt: str) -> dict:
    try:
        response = requests.post(
            f"{settings.ollama_base_url.rstrip('/')}/api/chat",
            json={
                "model": settings.critic_ollama_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "format": "json",
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": MAX_CRITIC_OUTPUT_TOKENS,
                },
            },
            timeout=45,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        raise CriticUnavailableError("Ollama critic request failed.") from error
    content = response.json().get("message", {}).get("content", "")
    if not content:
        raise ValueError("Ollama returned an empty critic response.")
    return _extract_json(content)


def _provider_retry_after_seconds(error: Any) -> float | None:
    headers = getattr(getattr(error, "response", None), "headers", None)
    if not headers:
        return None
    try:
        retry_after = float(headers.get("retry-after"))
    except (TypeError, ValueError):
        return None
    return retry_after if retry_after >= 0 else None


def _gemini_retry_delay(error: Any, attempt: int) -> float:
    retry_after = _provider_retry_after_seconds(error)
    if retry_after is not None:
        return min(retry_after, MAX_GEMINI_RETRY_DELAY_SECONDS)
    return min(
        2**attempt + random.uniform(0, 0.5),
        MAX_GEMINI_RETRY_DELAY_SECONDS,
    )


def _gemini_response_context(response: Any) -> tuple[str | None, str | None]:
    candidates = getattr(response, "candidates", None) or []
    candidate = candidates[0] if candidates else None
    finish_reason = getattr(candidate, "finish_reason", None)
    prompt_feedback = getattr(response, "prompt_feedback", None)
    block_reason = getattr(prompt_feedback, "block_reason", None)
    return (
        str(finish_reason) if finish_reason is not None else None,
        str(block_reason) if block_reason is not None else None,
    )


def _gemini_usage_metadata(response: Any) -> dict[str, Any]:
    usage = getattr(response, "usage_metadata", None)
    if usage is None:
        return {}

    fields = (
        "prompt_token_count",
        "candidates_token_count",
        "thoughts_token_count",
        "total_token_count",
    )
    return {
        field: getattr(usage, field)
        for field in fields
        if getattr(usage, field, None) is not None
    }


def _validate_critic_payload(payload: Any) -> dict:
    try:
        validated = CriticResponse.model_validate(payload)
    except ValidationError as error:
        logger.warning(
            "Critic response failed schema validation: %s errors.",
            len(error.errors()),
        )
        raise CriticResponseFormatError(
            "Critic response did not match the expected schema."
        ) from error
    return validated.model_dump(mode="json", by_alias=True)


def _gemini_payload(response: Any) -> dict:
    finish_reason, block_reason = _gemini_response_context(response)
    usage = _gemini_usage_metadata(response)
    logger.info(
        "Gemini critic response metadata: finish reason=%s; block reason=%s; "
        "usage=%s; output budget=%s.",
        finish_reason or "none",
        block_reason or "none",
        usage or "unavailable",
        settings.critic_gemini_max_output_tokens,
    )

    if finish_reason and "MAX_TOKENS" in finish_reason:
        logger.warning(
            "Gemini critic output was truncated at the configured budget of %s tokens.",
            settings.critic_gemini_max_output_tokens,
        )
        raise CriticResponseFormatError("Gemini critic output was truncated.")

    parsed = getattr(response, "parsed", None)
    if parsed is not None:
        logger.debug("Gemini critic response used SDK structured parsing.")
        return _validate_critic_payload(_to_dict(parsed))

    candidates = getattr(response, "candidates", None) or []
    if not candidates:
        logger.warning(
            "Gemini critic response has no candidates (block reason: %s).",
            block_reason or "none",
        )
        raise CriticResponseFormatError("Gemini returned no response candidate.")

    content = getattr(candidates[0], "content", None)
    parts = getattr(content, "parts", None) if content is not None else None
    if not parts:
        logger.warning(
            "Gemini critic response has no text parts (finish reason: %s; "
            "block reason: %s).",
            finish_reason or "none",
            block_reason or "none",
        )
        raise CriticResponseFormatError("Gemini returned no text content.")

    try:
        content = response.text
    except (AttributeError, ValueError) as error:
        logger.warning(
            "Gemini critic response did not expose readable text "
            "(finish reason: %s; block reason: %s).",
            finish_reason or "none",
            block_reason or "none",
        )
        raise CriticResponseFormatError(
            "Gemini returned no readable response text."
        ) from error

    logger.debug(
        "Gemini critic response used text fallback (length: %s; finish reason: %s).",
        len(content or ""),
        finish_reason or "none",
    )
    try:
        return _validate_critic_payload(_extract_json(content))
    except CriticResponseFormatError:
        logger.warning(
            "Gemini critic response format failure (finish reason: %s; "
            "block reason: %s).",
            finish_reason or "none",
            block_reason or "none",
        )
        raise


def _gemini_error_details(error: Exception) -> str:
    """Extract diagnostic details from a Gemini API exception."""
    details = {
        "exception_type": type(error).__name__,
        "http_status": getattr(error, "code", None),
        "message": getattr(error, "message", None) or str(error),
    }

    # Some SDK versions expose the original response body.
    response_json = getattr(error, "response_json", None)
    if response_json is not None:
        try:
            details["response_body"] = json.dumps(
                response_json, ensure_ascii=False, default=str
            )[:2000]
        except (TypeError, ValueError):
            details["response_body"] = str(response_json)[:2000]

    # Capture request IDs when the SDK exposes response headers.
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", None)
    if headers:
        for name in ("x-request-id", "request-id", "retry-after"):
            value = headers.get(name)
            if value is not None:
                details[name] = str(value)[:200]

    return json.dumps(details, ensure_ascii=False, default=str)


def _call_gemini(prompt: str) -> dict:
    try:
        from google import genai
        from google.genai import errors
        from google.genai import types
    except ImportError as error:
        raise CriticUnavailableError(
            "Gemini provider package is not installed."
        ) from error

    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY is not configured.")

    client = genai.Client(api_key=settings.gemini_api_key)

    try:
        for attempt in range(MAX_GEMINI_RETRIES + 1):
            try:
                response = client.models.generate_content(
                    model=settings.critic_gemini_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        response_schema=CriticResponse,
                        max_output_tokens=(settings.critic_gemini_max_output_tokens),
                        temperature=0.2,
                    ),
                )

                return _gemini_payload(response)

            except errors.APIError as error:
                details = _gemini_error_details(error)

                is_transient = isinstance(error, errors.ServerError) or error.code in {
                    408,
                    429,
                }

                if not is_transient:
                    logger.error(
                        "Gemini critic non-retryable API error. " "Model=%s Details=%s",
                        settings.critic_gemini_model,
                        details,
                    )
                    raise CriticUnavailableError(
                        f"Gemini API request failed: {details}"
                    ) from error

                if attempt == MAX_GEMINI_RETRIES:
                    logger.error(
                        "Gemini critic retries exhausted. "
                        "Model=%s Attempts=%s Details=%s",
                        settings.critic_gemini_model,
                        attempt + 1,
                        details,
                    )
                    raise CriticUnavailableError(
                        f"Gemini API failed after {attempt + 1} attempts: " f"{details}"
                    ) from error

                delay = _gemini_retry_delay(error, attempt)

                logger.warning(
                    "Gemini critic transient failure. "
                    "Model=%s HTTP=%s Attempt=%s/%s Delay=%.1fs Details=%s",
                    settings.critic_gemini_model,
                    error.code,
                    attempt + 1,
                    MAX_GEMINI_RETRIES,
                    delay,
                    details,
                )

                time.sleep(delay)

    finally:
        close = getattr(client, "close", None)
        if callable(close):
            close()


def analyze_with_critic(
    crawl_data: dict,
    hci_findings: list | None = None,
    vlm_findings: list | None = None,
) -> CriticResponse:
    prompt = _build_user_prompt(
        crawl_data,
        hci_findings or [],
        vlm_findings or [],
    )

    provider = settings.critic_provider.strip().lower()

    callers = {
        "groq": _call_groq,
        "ollama": _call_ollama,
        "gemini": _call_gemini,
    }

    if provider not in callers:
        raise ValueError(
            f"Unsupported critic provider: {provider}. "
            "Choose 'groq', 'ollama', or 'gemini'."
        )

    active_provider = provider

    try:
        try:
            result = callers[provider](prompt)

        except CriticUnavailableError as gemini_error:
            # Only fall back when Gemini was the configured provider.
            if provider != "gemini":
                raise

            logger.warning(
                "Gemini critic unavailable. Attempting Groq fallback. " "Reason: %s",
                gemini_error,
            )

            try:
                result = _call_groq(prompt)
                active_provider = "groq"

            except Exception as groq_error:
                logger.warning(
                    "Groq fallback failed after Gemini became unavailable: %s",
                    groq_error,
                    exc_info=True,
                )
                raise CriticUnavailableError(
                    "Gemini critic failed and Groq fallback also failed."
                ) from groq_error

        parsed = CriticResponse.model_validate(result)

    except ValidationError as error:
        logger.warning(
            "Critic response failed schema validation: %s errors.",
            len(error.errors()),
        )
        raise CriticResponseFormatError(
            "Critic response did not match the expected schema."
        ) from error

    logger.info(
        "Critic completed using %s. Additional findings: %s",
        active_provider,
        len(parsed.findings),
    )

    return parsed
