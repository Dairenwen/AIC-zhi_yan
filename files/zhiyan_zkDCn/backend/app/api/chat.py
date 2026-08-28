from __future__ import annotations

from uuid import UUID

from flask import Blueprint, g, request
from sqlalchemy import select

from ..extensions import db
from ..llm import run_openai_compatible_chat
from ..models import Message
from ..services.model_credentials import decrypt_api_key
from .model_configs import find_default_chat_config, find_owned_config
from .projects import append_message, get_conversation_access
from .responses import error, ok


bp = Blueprint("chat", __name__)


@bp.post("/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    prompt = str(payload.get("prompt", "")).strip()
    raw_messages = payload.get("messages") or []
    if not prompt and not raw_messages:
        return error("请输入对话内容", code="PROMPT_REQUIRED")

    conversation_id = None
    if payload.get("conversation_id"):
        try:
            conversation_id = UUID(str(payload["conversation_id"]))
        except ValueError:
            return error("对话标识无效", code="CONVERSATION_ID_INVALID")
        access = get_conversation_access(conversation_id, edit=True)
        if access is None:
            return error("对话不存在", code="CONVERSATION_NOT_FOUND", status=404)
        if payload.get("project_id") and str(access[0].project_id) != str(payload["project_id"]):
            return error("对话不属于当前项目", code="CONVERSATION_PROJECT_MISMATCH", status=409)

    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": (
                "你是知研科研助手，回答应简洁、可靠、适合科研工作场景。"
                "当用户需要文献检索、报告或年度脉络图时，提醒用户可选择文献检索 Agent 进入专业工作台。"
            ),
        }
    ]
    persisted_messages = []
    if conversation_id:
        persisted_messages = db.session.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sequence.desc())
            .limit(10)
        ).all()[::-1]
    history_source = (
        [{"role": item.role.lower(), "content": item.content} for item in persisted_messages]
        if persisted_messages
        else raw_messages[-10:]
    )
    for item in history_source:
        role = str(item.get("role", "")).strip()
        content = str(item.get("content", "")).strip()
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content})
    if prompt:
        messages.append({"role": "user", "content": prompt})
        if conversation_id:
            append_message(conversation_id, "user", prompt)
            db.session.commit()

    requested_model = str(payload.get("model") or "vertical_domain")
    if requested_model in {"auto", ""}:
        default_config = find_default_chat_config(g.current_user.id)
        requested_model = f"model_config:{default_config.id}" if default_config else "vertical_domain"
    runtime = {}
    if requested_model.startswith("model_config:"):
        config = find_owned_config(requested_model.removeprefix("model_config:"), active_only=True)
        if config is None:
            return error("所选对话模型不存在、未验证或已停用", code="MODEL_CONFIG_UNAVAILABLE", status=409)
        if not config.encrypted_api_key or not config.key_nonce or not config.key_version:
            return error("所选对话模型的密钥不可用", code="MODEL_CONFIG_KEY_INVALID", status=409)
        try:
            api_key = decrypt_api_key(config.encrypted_api_key, config.key_nonce, config.key_version)
        except RuntimeError:
            return error("所选对话模型的密钥不可用", code="MODEL_CONFIG_KEY_INVALID", status=409)
        runtime = {
            "model": config.model_name,
            "base_url": config.base_url,
            "api_key": api_key,
            "timeout_seconds": float((config.settings or {}).get("timeout_seconds", 120)),
        }
    else:
        runtime = {"model": requested_model}
    try:
        result = run_openai_compatible_chat(messages=messages, **runtime)
    except RuntimeError as exc:
        return error(str(exc), code="MODEL_UNAVAILABLE", status=502)
    if conversation_id:
        assistant_content = str(result.get("content") or "").strip()
        if assistant_content:
            assistant_message = append_message(conversation_id, "assistant", assistant_content)
            db.session.commit()
            result = {**result, "message_id": str(assistant_message.id), "conversation_id": str(conversation_id)}
    return ok(result)
