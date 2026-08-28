from __future__ import annotations

import os
import subprocess
import threading
from pathlib import Path
from time import perf_counter

from flask import Flask


class FormulaRecognitionNotReady(RuntimeError):
    pass


class FormulaRecognitionFailed(RuntimeError):
    def __init__(self, message: str, *, detail: str = ""):
        super().__init__(message)
        self.detail = detail


class FormulaRecognitionService:
    def __init__(self, app: Flask):
        self.app = app
        self._inference_lock = threading.Lock()

    def status(self) -> dict[str, object]:
        root = Path(self.app.config["FORMULA_RECOGNITION_ROOT"])
        python = Path(self.app.config["FORMULA_RECOGNITION_PYTHON"])
        script = root / "recognize.py"
        model = root / "unimernet" / "models" / "unimernet_base" / "pytorch_model.pth"
        checks = {
            "runtime": script.is_file(),
            "pythonEnvironment": python.is_file(),
            "model": model.is_file(),
        }
        return {
            "ready": all(checks.values()),
            "checks": checks,
            "device": str(self.app.config["FORMULA_RECOGNITION_DEVICE"]),
        }

    def recognize(self, image_path: Path) -> dict[str, object]:
        status = self.status()
        if not status["ready"]:
            raise FormulaRecognitionNotReady("UniMERNet 识别环境尚未完成配置")

        root = Path(self.app.config["FORMULA_RECOGNITION_ROOT"])
        command = [
            str(Path(self.app.config["FORMULA_RECOGNITION_PYTHON"])),
            str(root / "recognize.py"),
            str(image_path.resolve()),
            "--device",
            str(self.app.config["FORMULA_RECOGNITION_DEVICE"]),
        ]
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        # Do not let a user's global Python packages override the vendored
        # runtime; mixed Torch/NumPy installations can make torchvision fail
        # before the model is even loaded.
        env["PYTHONNOUSERSITE"] = "1"
        env["PYTHONUTF8"] = "1"
        started_at = perf_counter()
        try:
            with self._inference_lock:
                result = subprocess.run(
                    command,
                    cwd=root,
                    env=env,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=float(self.app.config["FORMULA_RECOGNITION_TIMEOUT_SECONDS"]),
                    check=False,
                )
        except subprocess.TimeoutExpired as exc:
            raise FormulaRecognitionFailed("公式识别超时，请稍后重试") from exc
        except OSError as exc:
            raise FormulaRecognitionFailed("无法启动公式识别运行时", detail=str(exc)) from exc

        if result.returncode != 0:
            detail = "\n".join(line for line in result.stderr.splitlines() if line.strip())[-4000:]
            raise FormulaRecognitionFailed("公式识别执行失败", detail=detail)
        latex = result.stdout.strip()
        if not latex:
            raise FormulaRecognitionFailed("识别服务未返回 LaTeX 结果", detail=result.stderr[-4000:])
        return {
            "latex": latex,
            "device": status["device"],
            "durationMs": round((perf_counter() - started_at) * 1000),
        }
