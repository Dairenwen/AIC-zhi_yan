from __future__ import annotations

import json
from typing import Any
from urllib import error, request

from flask import current_app
from langchain_openai import ChatOpenAI

from .services.platform_model_runtime import get_platform_model_runtime


AUTO_MODEL_VALUES = {"", "auto", "platform", "personal", "自动选择模型"}
VERTICAL_DOMAIN_MODEL_VALUES = {"vertical_domain", "垂域模型", "qwen3.6-dpo"}


def resolve_chat_model_name(value: str | None) -> str:
    model = (value or "").strip()
    if model in AUTO_MODEL_VALUES or model in VERTICAL_DOMAIN_MODEL_VALUES:
        return get_platform_model_runtime().model_name
    return model


def build_qwen_dpo_chat_model() -> ChatOpenAI:
    runtime = get_platform_model_runtime()
    return ChatOpenAI(
        api_key=runtime.api_key,
        base_url=runtime.base_url,
        model=runtime.model_name,
        temperature=0,
        timeout=runtime.timeout_seconds,
        max_retries=1,
    )


def run_openai_compatible_chat(
    *,
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 1024,
    base_url: str | None = None,
    api_key: str | None = None,
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    platform_runtime = get_platform_model_runtime()
    requested_model = (model or "").strip()
    uses_platform_model = requested_model in AUTO_MODEL_VALUES or requested_model in VERTICAL_DOMAIN_MODEL_VALUES
    resolved_model = platform_runtime.model_name if uses_platform_model else requested_model
    payload = {
        "model": resolved_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    effective_base_url = base_url or platform_runtime.base_url
    effective_api_key = str(platform_runtime.api_key if api_key is None else api_key).strip()
    effective_timeout = timeout_seconds or platform_runtime.timeout_seconds
    headers = {"Content-Type": "application/json"}
    if effective_api_key and effective_api_key.upper() != "EMPTY":
        headers["Authorization"] = f"Bearer {effective_api_key}"
    api_request = request.Request(
        f"{effective_base_url.rstrip('/')}/chat/completions",
        data=body,
        method="POST",
        headers=headers,
    )
    try:
        with request.urlopen(api_request, timeout=effective_timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"模型服务返回错误 {exc.code}: {detail[:300]}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"无法连接模型服务: {exc.reason}") from exc

    choices = data.get("choices") or []
    message = choices[0].get("message", {}) if choices else {}
    return {
        "model": data.get("model") or resolved_model,
        "content": message.get("content", ""),
        "usage": data.get("usage") or {},
    }
