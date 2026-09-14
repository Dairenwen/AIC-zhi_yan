from __future__ import annotations

from uuid import UUID

from flask import current_app
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from ..extensions import db
from ..models import ModelConfig
from .model_credentials import encrypt_api_key


ACCOUNT_API_CONFIG_NAME = "API 对话模型"


def ensure_user_api_config(user_id: UUID | str) -> ModelConfig | None:
    """Provision one editable API chat slot for every user, including legacy users."""
    try:
        item = db.session.scalar(
            select(ModelConfig).where(
                ModelConfig.owner_user_id == user_id,
                ModelConfig.config_scope == "USER",
                ModelConfig.is_account_api.is_(True),
                ModelConfig.deleted_at.is_(None),
            )
        )
        if item is not None:
            return item

        api_key = str(current_app.config.get("USER_API_MODEL_API_KEY") or "").strip()
        encrypted = nonce = key_version = None
        key_last_four = None
        if api_key:
            encrypted, nonce, key_version = encrypt_api_key(api_key)
            key_last_four = api_key[-4:]
        item = ModelConfig(
            config_scope="USER",
            owner_user_id=user_id,
            provider_code="openai_compatible",
            model_type_code="chat",
            name=ACCOUNT_API_CONFIG_NAME,
            base_url=str(current_app.config.get("USER_API_MODEL_BASE_URL") or "https://api.siliconflow.cn/v1").rstrip("/"),
            model_name=str(current_app.config.get("USER_API_MODEL_NAME") or "deepseek-ai/DeepSeek-V4-Flash"),
            capabilities=["chat_completions"],
            settings={
                "timeout_seconds": int(current_app.config.get("USER_API_MODEL_TIMEOUT_SECONDS", 120)),
                "max_output_tokens": int(current_app.config.get("USER_API_MODEL_MAX_OUTPUT_TOKENS", 3072)),
            },
            default_for=[],
            encrypted_api_key=encrypted,
            key_nonce=nonce,
            key_version=key_version,
            key_last_four=key_last_four,
            allow_platform_fallback=False,
            status="DRAFT",
            is_account_api=True,
        )
        db.session.add(item)
        db.session.commit()
        return item
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.warning("account API model provisioning is unavailable", exc_info=True)
        return None
