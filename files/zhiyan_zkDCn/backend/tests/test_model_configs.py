import base64
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from flask import g

from app import create_app
from app.api.model_configs import (
    builtin_vertical_model,
    find_owned_config,
    serialize_config,
    verify_openai_compatible,
)
from app.extensions import db
from app.services.model_credentials import decrypt_api_key, encrypt_api_key


def test_model_api_key_is_encrypted_and_never_serialized():
    encryption_key = base64.urlsafe_b64encode(b"m" * 32).decode("ascii")
    app = create_app({"TESTING": True, "MODEL_CONFIG_ENCRYPTION_KEY": encryption_key})
    with app.app_context():
        encrypted, nonce, version = encrypt_api_key("sk-private-value")
        assert encrypted != b"sk-private-value"
        assert decrypt_api_key(encrypted, nonce, version) == "sk-private-value"

    now = datetime.now(UTC)
    item = SimpleNamespace(
        id=uuid4(),
        provider_code="openai_compatible",
        name="研究模型",
        base_url="https://model.example/v1",
        model_name="research-model",
        status="ACTIVE",
        settings={},
        encrypted_api_key=encrypted,
        key_last_four="alue",
        last_verified_at=now,
        last_error_code=None,
        created_at=now,
        updated_at=now,
    )
    payload = serialize_config(item)
    assert payload["masked_api_key"] == "••••alue"
    assert "encrypted_api_key" not in payload
    assert "sk-private-value" not in str(payload)


def test_serialized_config_marks_chat_default():
    now = datetime.now(UTC)
    item = SimpleNamespace(
        id=uuid4(),
        provider_code="openai_compatible",
        name="默认研究模型",
        base_url="https://model.example/v1",
        model_name="research-model",
        status="ACTIVE",
        default_for=["chat"],
        settings={},
        encrypted_api_key=b"encrypted",
        key_last_four="1234",
        last_verified_at=now,
        last_error_code=None,
        created_at=now,
        updated_at=now,
    )

    payload = serialize_config(item)

    assert payload["default_for"] == ["chat"]
    assert payload["is_default"] is True


def test_builtin_default_is_vertical_domain_model():
    app = create_app({"TESTING": True, "QWEN_DPO_MODEL": "vertical-test-model"})
    with app.app_context():
        payload = builtin_vertical_model()

    assert payload == {
        "value": "vertical_domain",
        "name": "平台通用模型",
        "model_name": "vertical-test-model",
        "source": "builtin",
        "config_id": None,
    }


def test_owned_model_lookup_includes_current_user_filter(monkeypatch):
    app = create_app({"TESTING": True})
    captured = {}

    def fake_scalar(statement):
        captured["statement"] = str(statement)
        return None

    monkeypatch.setattr(db.session, "scalar", fake_scalar)
    with app.test_request_context():
        g.current_user = SimpleNamespace(id=uuid4())
        assert find_owned_config(str(uuid4())) is None

    sql = captured["statement"]
    assert "model_configs.owner_user_id" in sql
    assert "model_configs.deleted_at IS NULL" in sql


def test_model_verification_uses_chat_completions_without_exposing_key(monkeypatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return b'{"choices":[{"message":{"content":"OK"}}]}'

    def fake_urlopen(api_request, timeout):
        captured["url"] = api_request.full_url
        captured["authorization"] = api_request.headers["Authorization"]
        captured["body"] = api_request.data
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("app.api.model_configs.url_request.urlopen", fake_urlopen)
    verify_openai_compatible(
        base_url="https://model.example/v1",
        model_name="research-model",
        api_key="sk-secret",
        timeout=12,
    )
    assert captured["url"] == "https://model.example/v1/chat/completions"
    assert captured["authorization"] == "Bearer sk-secret"
    assert b"sk-secret" not in captured["body"]
    assert captured["timeout"] == 12
