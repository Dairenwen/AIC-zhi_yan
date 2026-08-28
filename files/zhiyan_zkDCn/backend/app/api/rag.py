from __future__ import annotations

from flask import Blueprint, current_app, g, request

from ..services.model_credentials import decrypt_api_key
from .model_configs import find_default_chat_config, find_owned_config
from .responses import error, ok


bp = Blueprint("rag", __name__)


@bp.post("/rag/answers")
def create_rag_answer():
    payload = request.get_json(silent=True) or {}
    question = str(payload.get("question") or "").strip()
    if not question:
        return error("请输入知识库问题", code="RAG_QUESTION_REQUIRED")
    if len(question) > 4000:
        return error("知识库问题不能超过 4000 个字符", code="RAG_QUESTION_TOO_LONG")
    document_ids = payload.get("document_ids") or []
    if not isinstance(document_ids, list) or any(not isinstance(item, str) for item in document_ids):
        return error("文献范围格式无效", code="RAG_DOCUMENT_SCOPE_INVALID")
    if len(document_ids) != len(set(document_ids)):
        return error("文献范围不能包含重复项", code="RAG_DOCUMENT_SCOPE_INVALID")
    if payload.get("stream", False) is not False:
        return error("当前仅支持非流式知识库问答", code="RAG_STREAM_UNSUPPORTED")

    requested_model = str(payload.get("model") or "vertical_domain")
    if requested_model in {"auto", ""}:
        default_config = find_default_chat_config(g.current_user.id)
        requested_model = f"model_config:{default_config.id}" if default_config else "vertical_domain"
    model_runtime = {}
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
        requested_model = config.model_name
        model_runtime = {
            "base_url": config.base_url,
            "api_key": api_key,
            "timeout_seconds": float((config.settings or {}).get("timeout_seconds", 120)),
        }

    service = current_app.extensions["personal_academic_rag"]
    try:
        result = service.answer(
            question=question,
            user_id=str(g.current_user.id),
            role=str(g.current_user.role_code),
            document_ids=document_ids,
            model=requested_model,
            model_runtime=model_runtime,
        )
    except PermissionError:
        return error("请求包含未授权文献", code="RAG_FORBIDDEN_SCOPE", status=403)
    except RuntimeError as exc:
        current_app.logger.exception("personal RAG request failed")
        return error(str(exc), code="RAG_UNAVAILABLE", status=503)
    return ok(result)
