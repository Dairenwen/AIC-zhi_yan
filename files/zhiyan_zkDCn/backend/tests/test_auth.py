from types import SimpleNamespace
from uuid import uuid4

from flask import g
from werkzeug.security import check_password_hash

from app import create_app
from app.api.auth import normalize_organization, normalize_phone, require_role
from app.models import User
from app.api.tasks import find_task
from app.extensions import db


def test_normalize_chinese_mobile_number():
    assert normalize_phone("138 0000 0000") == "+8613800000000"
    assert normalize_phone("+86-138-0000-0000") == "+8613800000000"


def test_rejects_invalid_phone_number():
    assert normalize_phone("12345") is None


def test_empty_or_corrupted_organization_uses_explicit_placeholder():
    assert normalize_organization("") == "未设置机构"
    assert normalize_organization("??????") == "未设置机构"
    assert normalize_organization("武汉理工大学") == "武汉理工大学"


def test_role_check_rejects_normal_user():
    app = create_app({"TESTING": True})
    with app.test_request_context():
        g.current_user = SimpleNamespace(role_code="normal_user")
        response, status = require_role("system_admin")

    assert status == 403
    assert response.get_json()["error"]["code"] == "FORBIDDEN"


def test_task_lookup_is_isolated_by_owner(monkeypatch):
    app = create_app({"TESTING": True})
    owner_id = uuid4()
    other_user_id = uuid4()
    task = SimpleNamespace(user_id=owner_id)

    with app.test_request_context():
        monkeypatch.setattr(db.session, "get", lambda _model, _task_id: task)
        g.current_user = SimpleNamespace(id=other_user_id, role_code="normal_user")
        assert find_task(str(uuid4())) is None

        g.current_user = SimpleNamespace(id=other_user_id, role_code="system_admin")
        assert find_task(str(uuid4())) is task


def test_register_creates_user(monkeypatch):
    app = create_app({"TESTING": True})
    captured = {}

    def fake_scalar(_query):
        return None

    def fake_add(user):
        captured["user"] = user

    monkeypatch.setattr(db.session, "scalar", fake_scalar)
    monkeypatch.setattr(db.session, "add", fake_add)
    monkeypatch.setattr(db.session, "commit", lambda: None)

    client = app.test_client()
    response = client.post(
        "/api/v1/auth/register",
        json={
            "phone": "13800000000",
            "password": "password123",
            "name": "测试用户",
            "organization": "武汉理工大学",
        },
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["data"]["message"] == "注册成功，请返回登录"
    assert isinstance(captured["user"], User)
    assert captured["user"].phone == "+8613800000000"
    assert captured["user"].display_name == "测试用户"
    assert captured["user"].profile["organization"] == "武汉理工大学"
    assert check_password_hash(captured["user"].password_hash, "password123")


def test_register_rejects_duplicate_phone(monkeypatch):
    app = create_app({"TESTING": True})
    existing = SimpleNamespace(phone="+8613800000000", deleted_at=None)

    monkeypatch.setattr(db.session, "scalar", lambda _query: existing)

    client = app.test_client()
    response = client.post(
        "/api/v1/auth/register",
        json={
            "phone": "13800000000",
            "password": "password123",
            "name": "测试用户",
        },
    )

    assert response.status_code == 409
    payload = response.get_json()
    assert payload["error"]["code"] == "PHONE_ALREADY_REGISTERED"
