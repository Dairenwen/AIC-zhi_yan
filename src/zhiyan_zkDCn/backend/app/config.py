import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]


def as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def project_path(value: str | Path) -> Path:
    path = Path(value)
    return (path if path.is_absolute() else BASE_DIR / path).resolve()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    MODEL_CONFIG_ENCRYPTION_KEY = os.getenv("MODEL_CONFIG_ENCRYPTION_KEY", "")
    AUTH_COOKIE_NAME = os.getenv("AUTH_COOKIE_NAME", "zhiyan_session")
    AUTH_TOKEN_MAX_AGE = int(os.getenv("AUTH_TOKEN_MAX_AGE", str(7 * 24 * 60 * 60)))
    AUTH_COOKIE_SECURE = as_bool(os.getenv("AUTH_COOKIE_SECURE"), False)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://zhiyan:zhiyan@localhost:5432/zhiyan",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    }
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]
    KNOWLEDGE_BASE_SERVICE_URL = os.getenv(
        "KNOWLEDGE_BASE_SERVICE_URL", "http://127.0.0.1:8768"
    )
    KNOWLEDGE_BASE_ROOT = project_path(
        os.getenv("KNOWLEDGE_BASE_ROOT", "knowledge_base_runtime")
    )
    KNOWLEDGE_BASE_EMBEDDED = as_bool(os.getenv("KNOWLEDGE_BASE_EMBEDDED"), True)
    KNOWLEDGE_BASE_DB_SCHEMA = os.getenv("KB_DB_SCHEMA", "knowledge_base")
    KNOWLEDGE_BASE_SHARED_USER_SCHEMA = os.getenv("KB_SHARED_USER_SCHEMA", "zhiyan")
    KNOWLEDGE_BASE_DATA_DIR = os.getenv(
        "KB_DATA_DIR", str(KNOWLEDGE_BASE_ROOT / "infrastructure" / "file-storage" / "data")
    )
    KNOWLEDGE_BASE_ELASTICSEARCH_ENABLED = as_bool(os.getenv("ELASTICSEARCH_ENABLED"), False)
    KNOWLEDGE_BASE_MILVUS_ENABLED = as_bool(os.getenv("KB_MILVUS_ENABLED"), False)
    KNOWLEDGE_BASE_PROXY_TIMEOUT_SECONDS = float(
        os.getenv("KNOWLEDGE_BASE_PROXY_TIMEOUT_SECONDS", "120")
    )
    FORMULA_RECOGNITION_ROOT = Path(
        os.getenv(
            "FORMULA_RECOGNITION_ROOT",
            BASE_DIR.parents[2]
            / "小组传输文件"
            / "戴rw"
            / "formula-image-to-latex",
        )
    ).resolve()
    FORMULA_RECOGNITION_PYTHON = Path(
        os.getenv(
            "FORMULA_RECOGNITION_PYTHON",
            FORMULA_RECOGNITION_ROOT
            / ".venv"
            / ("Scripts/python.exe" if os.name == "nt" else "bin/python"),
        )
    ).resolve()
    FORMULA_RECOGNITION_DEVICE = os.getenv("FORMULA_RECOGNITION_DEVICE", "auto")
    FORMULA_RECOGNITION_TIMEOUT_SECONDS = float(
        os.getenv("FORMULA_RECOGNITION_TIMEOUT_SECONDS", "300")
    )
    FORMULA_UPLOAD_DIR = Path(
        os.getenv("FORMULA_UPLOAD_DIR", BASE_DIR / "uploads" / "formulas")
    ).resolve()
    FORMULA_UPLOAD_MAX_BYTES = int(
        os.getenv("FORMULA_UPLOAD_MAX_BYTES", str(10 * 1024 * 1024))
    )
    FORMULA_MAX_IMAGE_PIXELS = int(os.getenv("FORMULA_MAX_IMAGE_PIXELS", "40000000"))
    LITERATURE_PPT_RUNTIME_ROOT = Path(
        os.getenv(
            "LITERATURE_PPT_RUNTIME_ROOT",
            BASE_DIR.parents[2] / "小组传输文件" / "戴rw" / "literature_ppt_tools",
        )
    ).resolve()
    LITERATURE_PPT_PYTHON = Path(
        os.getenv(
            "LITERATURE_PPT_PYTHON",
            LITERATURE_PPT_RUNTIME_ROOT / ".venv-windows" / "Scripts" / "python.exe",
        )
    ).resolve()
    LITERATURE_PPT_UPLOAD_DIR = Path(
        os.getenv("LITERATURE_PPT_UPLOAD_DIR", BASE_DIR / "uploads" / "literature-ppt")
    ).resolve()
    LITERATURE_PPT_DATA_DIR = Path(
        os.getenv("LITERATURE_PPT_DATA_DIR", BASE_DIR / "generated" / "literature-ppt")
    ).resolve()
    LITERATURE_PPT_UPLOAD_MAX_BYTES = int(
        os.getenv("LITERATURE_PPT_UPLOAD_MAX_BYTES", str(50 * 1024 * 1024))
    )
    LITERATURE_PPT_TIMEOUT_SECONDS = int(os.getenv("LITERATURE_PPT_TIMEOUT_SECONDS", "1800"))
    JSON_AS_ASCII = False
    SKILL_CRAWL_FILE = Path(
        os.getenv(
            "SKILL_CRAWL_FILE",
            BASE_DIR.parents[2]
            / "小组传输文件"
            / "宋xr"
            / "Skill"
            / "innovation_mining_skills.json",
        )
    ).resolve()
    SKILL_IMPORT_TIMEOUT_SECONDS = float(os.getenv("SKILL_IMPORT_TIMEOUT_SECONDS", "20"))
    SKILL_IMPORT_MAX_FILE_BYTES = int(os.getenv("SKILL_IMPORT_MAX_FILE_BYTES", str(1_500_000)))
    SKILL_IMPORT_MAX_TOTAL_BYTES = int(os.getenv("SKILL_IMPORT_MAX_TOTAL_BYTES", str(8_000_000)))
    AGENT_GENERATED_DIR = Path(
        os.getenv("AGENT_GENERATED_DIR", BASE_DIR / "generated" / "literature_search")
    ).resolve()
    INNOVATION_DATA_DIR = Path(
        os.getenv("INNOVATION_DATA_DIR", BASE_DIR / "generated" / "ip")
    ).resolve()
    PAPER_UPLOAD_DIR = Path(os.getenv("PAPER_UPLOAD_DIR", BASE_DIR / "uploads" / "papers")).resolve()
    PAPER_UPLOAD_MAX_BYTES = int(os.getenv("PAPER_UPLOAD_MAX_BYTES", str(50 * 1024 * 1024)))
    PERSONAL_KB_UPLOAD_DIR = Path(
        os.getenv("PERSONAL_KB_UPLOAD_DIR", BASE_DIR / "uploads" / "personal-knowledge")
    ).resolve()
    PERSONAL_KB_UPLOAD_MAX_BYTES = int(
        os.getenv("PERSONAL_KB_UPLOAD_MAX_BYTES", str(50 * 1024 * 1024))
    )
    COMPLIANCE_UPLOAD_DIR = Path(
        os.getenv("COMPLIANCE_UPLOAD_DIR", BASE_DIR / "uploads" / "compliance")
    ).resolve()
    COMPLIANCE_UPLOAD_MAX_BYTES = int(
        os.getenv("COMPLIANCE_UPLOAD_MAX_BYTES", str(50 * 1024 * 1024))
    )
    TRANSLATION_UPLOAD_DIR = Path(
        os.getenv("TRANSLATION_UPLOAD_DIR", BASE_DIR / "uploads" / "translations")
    ).resolve()
    TRANSLATION_UPLOAD_MAX_BYTES = int(
        os.getenv("TRANSLATION_UPLOAD_MAX_BYTES", str(50 * 1024 * 1024))
    )
    PATENT_UPLOAD_DIR = Path(
        os.getenv("PATENT_UPLOAD_DIR", BASE_DIR / "uploads" / "patents")
    ).resolve()
    PATENT_UPLOAD_MAX_BYTES = int(
        os.getenv("PATENT_UPLOAD_MAX_BYTES", str(50 * 1024 * 1024))
    )
    PATENT_DRAFTING_RUNTIME_ROOT = Path(
        os.getenv(
            "PATENT_DRAFTING_RUNTIME_ROOT",
            BASE_DIR / "app" / "agents" / "patent_drafting" / "runtime",
        )
    ).resolve()
    PATENT_DRAFTING_DATA_DIR = Path(
        os.getenv(
            "PATENT_DRAFTING_DATA_DIR",
            BASE_DIR / "generated" / "patent_drafting",
        )
    ).resolve()
    PATENT_DRAFTING_TIMEOUT_SECONDS = int(
        os.getenv("PATENT_DRAFTING_TIMEOUT_SECONDS", "3600")
    )
    PATENT_DRAFTING_FAKE_MODE = as_bool(os.getenv("PATENT_DRAFTING_FAKE_MODE"), False)
    PATENT_DRAFTING_ALLOW_FIXTURE_FALLBACK = as_bool(
        os.getenv("PATENT_DRAFTING_ALLOW_FIXTURE_FALLBACK"), False
    )
    FIGURE_UPLOAD_DIR = Path(
        os.getenv("FIGURE_UPLOAD_DIR", BASE_DIR / "uploads" / "figures")
    ).resolve()
    FIGURE_UPLOAD_MAX_BYTES = int(
        os.getenv("FIGURE_UPLOAD_MAX_BYTES", str(50 * 1024 * 1024))
    )
    ACADEMIC_FIGURE_RUNTIME_ROOT = Path(
        os.getenv(
            "ACADEMIC_FIGURE_RUNTIME_ROOT",
            BASE_DIR / "app" / "agents" / "academic_figure" / "runtime",
        )
    ).resolve()
    ACADEMIC_FIGURE_DATA_DIR = Path(
        os.getenv(
            "ACADEMIC_FIGURE_DATA_DIR",
            BASE_DIR / "generated" / "academic_figure",
        )
    ).resolve()
    ACADEMIC_FIGURE_TIMEOUT_SECONDS = int(
        os.getenv("ACADEMIC_FIGURE_TIMEOUT_SECONDS", "1800")
    )
    ACADEMIC_FIGURE_MODEL_MAX_RETRIES = int(
        os.getenv("ACADEMIC_FIGURE_MODEL_MAX_RETRIES", "4")
    )
    ARXIV_DAILY_RUNTIME_ROOT = Path(
        os.getenv(
            "ARXIV_DAILY_RUNTIME_ROOT",
            BASE_DIR / "app" / "agents" / "arxiv_daily" / "runtime",
        )
    ).resolve()
    ARXIV_DAILY_CACHE_TTL_SECONDS = int(
        os.getenv("ARXIV_DAILY_CACHE_TTL_SECONDS", "3600")
    )
    ARXIV_DAILY_TIMEOUT_SECONDS = int(
        os.getenv("ARXIV_DAILY_TIMEOUT_SECONDS", "120")
    )
    ARXIV_DAILY_PDF_CACHE_DIR = Path(
        os.getenv(
            "ARXIV_DAILY_PDF_CACHE_DIR",
            BASE_DIR / "generated" / "arxiv_daily_pdfs",
        )
    ).resolve()
    ARXIV_DAILY_PDF_MAX_BYTES = int(
        os.getenv("ARXIV_DAILY_PDF_MAX_BYTES", str(50 * 1024 * 1024))
    )
    PAPER_READING_RUNTIME_ROOT = Path(
        os.getenv(
            "PAPER_READING_RUNTIME_ROOT",
            BASE_DIR / "app" / "agents" / "paper_reading" / "runtime",
        )
    ).resolve()
    PAPER_READING_UV_EXECUTABLE = os.getenv("PAPER_READING_UV_EXECUTABLE", "uv")
    PAPER_READING_UV_CACHE_DIR = Path(
        os.getenv(
            "PAPER_READING_UV_CACHE_DIR",
            BASE_DIR.parents[2] / "tmp" / "uv-paper-reading-cache",
        )
    ).resolve()
    PAPER_READING_TIMEOUT_SECONDS = int(os.getenv("PAPER_READING_TIMEOUT_SECONDS", "3600"))
    PAPER_READING_MODEL_TIMEOUT_SECONDS = float(
        os.getenv("PAPER_READING_MODEL_TIMEOUT_SECONDS", "180")
    )
    INNOVATION_AGENT_ROOT = Path(
        os.getenv(
            "INNOVATION_AGENT_ROOT",
            BASE_DIR / "runtimes" / "paper-insight-generate",
        )
    ).resolve()
    INNOVATION_AGENT_TIMEOUT_SECONDS = int(os.getenv("INNOVATION_AGENT_TIMEOUT_SECONDS", "1800"))
    INNOVATION_AGENT_MAX_DOCUMENTS = int(os.getenv("INNOVATION_AGENT_MAX_DOCUMENTS", "80"))
    COMPLIANCE_AGENT_ROOT = Path(
        os.getenv(
            "COMPLIANCE_AGENT_ROOT",
            BASE_DIR / "runtimes" / "academic_compliance_agent",
        )
    ).resolve()
    COMPLIANCE_AGENT_TIMEOUT_SECONDS = int(os.getenv("COMPLIANCE_AGENT_TIMEOUT_SECONDS", "1800"))
    COMPLIANCE_AGENT_USE_LLM = as_bool(os.getenv("COMPLIANCE_AGENT_USE_LLM"), True)
    COMPLIANCE_AGENT_MEMORY_ENABLED = as_bool(
        os.getenv("COMPLIANCE_AGENT_MEMORY_ENABLED"), False
    )
    TRANSLATION_AGENT_ROOT = Path(
        os.getenv(
            "TRANSLATION_AGENT_ROOT",
            BASE_DIR / "runtimes" / "academic-translation-agent",
        )
    ).resolve()
    TRANSLATION_AGENT_TIMEOUT_SECONDS = int(
        os.getenv("TRANSLATION_AGENT_TIMEOUT_SECONDS", "3600")
    )
    TRANSLATION_HEARTBEAT_SECONDS = max(
        5, int(os.getenv("TRANSLATION_HEARTBEAT_SECONDS", "30"))
    )
    TRANSLATION_OLLAMA_BASE_URL = os.getenv(
        "TRANSLATION_OLLAMA_BASE_URL", "http://192.168.247.161:11434"
    )
    TRANSLATION_OLLAMA_MODEL = os.getenv(
        "TRANSLATION_OLLAMA_MODEL", "translategemma:12b"
    )
    TRANSLATION_PDF2ZH_COMMAND = os.getenv("TRANSLATION_PDF2ZH_COMMAND", "")
    LITERATURE_EXTERNAL_SEARCH = as_bool(os.getenv("LITERATURE_EXTERNAL_SEARCH"), True)
    LITERATURE_FORCE_OFFLINE_MODEL = as_bool(os.getenv("LITERATURE_FORCE_OFFLINE_MODEL"), False)
    LITERATURE_REPORT_LIMIT = int(os.getenv("LITERATURE_REPORT_LIMIT", "10"))
    QWEN_DPO_BASE_URL = os.getenv("QWEN_DPO_BASE_URL", "http://192.168.247.161:8001/v1")
    QWEN_DPO_MODEL = os.getenv("QWEN_DPO_MODEL", "qwen3.6-sft")
    QWEN_DPO_API_KEY = os.getenv("QWEN_DPO_API_KEY", "")
    QWEN_DPO_TIMEOUT_SECONDS = float(os.getenv("QWEN_DPO_TIMEOUT_SECONDS", "60"))
    MANUSCRIPT_ALLOW_DETERMINISTIC_FALLBACK = as_bool(
        os.getenv("MANUSCRIPT_ALLOW_DETERMINISTIC_FALLBACK"), True
    )
    AGENT_READINESS_CACHE_SECONDS = max(
        5, int(os.getenv("AGENT_READINESS_CACHE_SECONDS", "30"))
    )
    AGENT_READINESS_CONNECT_TIMEOUT_SECONDS = max(
        0.1, float(os.getenv("AGENT_READINESS_CONNECT_TIMEOUT_SECONDS", "0.8"))
    )
    AGENT_TEAM_STAGE_TIMEOUT_SECONDS = int(os.getenv("AGENT_TEAM_STAGE_TIMEOUT_SECONDS", "3600"))
