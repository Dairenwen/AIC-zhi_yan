from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from knowledge_base_runtime.backend.service import retrieval_backends


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_ollama_embedding_backend_sends_batch_and_validates_dimension(monkeypatch):
    captured = {}

    def fake_urlopen(api_request, timeout):
        captured["url"] = api_request.full_url
        captured["body"] = json.loads(api_request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return FakeResponse({"embeddings": [[0.1] * 1024, [0.2] * 1024]})

    monkeypatch.setattr(retrieval_backends, "KB_EMBEDDING_BACKEND", "ollama")
    monkeypatch.setattr(retrieval_backends, "OLLAMA_EMBED_BASE_URL", "http://ollama.test:11434")
    monkeypatch.setattr(retrieval_backends, "OLLAMA_EMBED_MODEL", "bge-m3:latest")
    monkeypatch.setattr(retrieval_backends.urllib.request, "urlopen", fake_urlopen)

    vectors = retrieval_backends.embed_texts(["文本一", "text two"])

    assert captured["url"] == "http://ollama.test:11434/api/embed"
    assert captured["body"] == {"model": "bge-m3:latest", "input": ["文本一", "text two"]}
    assert len(vectors) == 2
    assert len(vectors[0]) == 1024


def test_ollama_embedding_backend_rejects_wrong_dimension(monkeypatch):
    monkeypatch.setattr(retrieval_backends, "KB_EMBEDDING_BACKEND", "ollama")
    monkeypatch.setattr(
        retrieval_backends.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: FakeResponse({"embeddings": [[0.1] * 768]}),
    )

    with pytest.raises(RuntimeError, match="does not match KB_MILVUS_DIM=1024"):
        retrieval_backends.embed_texts(["dimension test"])
