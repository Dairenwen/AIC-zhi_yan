from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from flask import g

from app import create_app
from app.agents.paper_reading.service import (
    PaperReadingService,
    _safe_core_error,
    extract_arxiv_id,
    normalize_paper_reading_options,
)
from app.api.tasks import create_task
from app.api.uploads import upload_paper
from app.extensions import db


def test_extract_arxiv_id_from_supported_sources():
    assert extract_arxiv_id("https://arxiv.org/abs/1706.03762") == "1706.03762"
    assert extract_arxiv_id("arXiv:cs/9901001") == "cs/9901001"
    assert extract_arxiv_id("https://example.com/paper") is None


def test_paper_reading_options_include_latest_question_support():
    assert normalize_paper_reading_options(
        {"speed_profile": "quality", "follow_up_question": "Table 1 的结论可靠吗？"}
    ) == {
        "speed_profile": "quality",
        "follow_up_question": "Table 1 的结论可靠吗？",
    }


def test_core_errors_are_sanitized_for_users():
    assert "超时" in _safe_core_error("httpx.ReadTimeout: timed out")
    assert "E:\\private" not in _safe_core_error("E:\\private\\stack.py\nRuntimeError: failed")


def test_pdf_upload_is_stored_inside_user_directory(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "PAPER_UPLOAD_DIR": tmp_path,
            "PAPER_UPLOAD_MAX_BYTES": 1024,
        }
    )
    user_id = uuid4()
    with app.test_request_context(
        method="POST",
        data={"file": (BytesIO(b"%PDF-1.4\nfixture"), "paper.pdf")},
        content_type="multipart/form-data",
    ):
        g.current_user = SimpleNamespace(id=user_id)
        response, status = upload_paper()

    payload = response.get_json()["data"]
    assert status == 201
    assert (tmp_path / str(user_id) / f"{payload['uploadId']}.pdf").read_bytes().startswith(b"%PDF-")


def test_paper_source_is_required_when_agent_is_selected_by_id(monkeypatch):
    app = create_app({"TESTING": True})
    agent = SimpleNamespace(id=uuid4(), code="paper_reading", status="ACTIVE")
    monkeypatch.setattr("app.api.tasks.resolve_agent", lambda _payload: agent)

    with app.test_request_context(
        method="POST",
        json={
            "prompt": "精读这篇论文",
            "agent_id": str(agent.id),
            "attachment": "paper.pdf",
        },
    ):
        g.current_user = SimpleNamespace(id=uuid4())
        response, status = create_task()

    assert status == 400
    assert response.get_json()["error"]["code"] == "PAPER_SOURCE_REQUIRED"


def test_paper_reading_command_uses_locked_agent_environment(monkeypatch, tmp_path):
    root = tmp_path / "paper-agent"
    (root / "agent-core").mkdir(parents=True)
    (root / "scripts").mkdir()
    (root / "shared" / "contracts" / "schemas").mkdir(parents=True)
    (root / "scripts" / "run_real_pdf_agent.py").write_text("", encoding="utf-8")
    (root / "VERSION").write_text("0.6.4\n", encoding="utf-8")
    (root / "shared" / "contracts" / "schemas" / "reading_result.schema.json").write_text(
        "{}", encoding="utf-8"
    )
    app = create_app(
        {
            "TESTING": True,
            "PAPER_READING_RUNTIME_ROOT": root,
            "PAPER_READING_UV_EXECUTABLE": "uv",
            "PAPER_READING_UV_CACHE_DIR": tmp_path / "uv-cache",
            "QWEN_DPO_API_KEY": "secret-not-in-command",
        }
    )
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["env"] = kwargs["env"]
        Path(command[command.index("--json-output") + 1]).write_text("{}", encoding="utf-8")
        Path(command[command.index("--markdown-output") + 1]).write_text("# report", encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("app.agents.paper_reading.service.shutil.which", lambda _name: "uv.exe")
    monkeypatch.setattr("app.agents.paper_reading.service.subprocess.run", fake_run)
    report_path = tmp_path / "out" / "report.json"
    markdown_path = tmp_path / "out" / "report.md"
    timing_path = tmp_path / "out" / "timing.json"
    report_path.parent.mkdir()

    with app.app_context():
        PaperReadingService(app).run_core(
            ["fixture.pdf"],
            "理解论文方法",
            "balanced",
            report_path,
            markdown_path,
            timing_path,
            {
                "base_url": "https://personal-model.example/v1",
                "model_name": "personal-reading-model",
                "api_key": "personal-secret-not-in-command",
                "timeout_seconds": 180,
            },
            question="论文如何验证主要结论？",
        )

    command_text = " ".join(captured["command"])
    assert "--frozen" in captured["command"]
    assert "--no-managed-python" in captured["command"]
    assert "personal-secret-not-in-command" not in command_text
    assert captured["env"]["ZHIYAN_PAPER_READING_API_KEY"] == "personal-secret-not-in-command"
    assert captured["env"]["PAPER_READING_ENABLE_THINKING"] == "false"
    assert captured["env"]["PAPER_READING_VISION_ENABLE_THINKING"] == "false"
    assert captured["command"][captured["command"].index("--model-base-url") + 1] == "https://personal-model.example/v1"
    assert captured["command"][captured["command"].index("--model") + 1] == "personal-reading-model"
    assert captured["command"][captured["command"].index("--timeout-seconds") + 1] == "180"
    assert "--max-output-tokens" not in captured["command"]
    assert captured["command"][captured["command"].index("--question") + 1] == "论文如何验证主要结论？"


def test_task_rejects_unavailable_personal_model(monkeypatch):
    app = create_app({"TESTING": True})
    user_id = uuid4()
    agent = SimpleNamespace(id=uuid4(), code="paper_reading", status="ACTIVE")
    monkeypatch.setattr("app.api.tasks.resolve_agent", lambda _payload: agent)
    monkeypatch.setattr("app.api.tasks.resolve_agent_service", lambda _code: SimpleNamespace())
    monkeypatch.setattr(db.session, "scalar", lambda _query: None)

    with app.test_request_context(
        method="POST",
        json={
            "prompt": "精读这篇论文",
            "agent_code": "paper_reading",
            "attachment_id": str(uuid4()),
            "model_config_id": str(uuid4()),
        },
    ):
        g.current_user = SimpleNamespace(id=user_id)
        response, status = create_task()

    assert status == 409
    assert response.get_json()["error"]["code"] == "MODEL_CONFIG_NOT_AVAILABLE"
