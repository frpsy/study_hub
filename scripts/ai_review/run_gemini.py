"""Gemini 1차 검수 호출. 성공하면 gemini 결과와 status.json을 남기고, 실패하면 사유를 status.json에 남긴다."""

import json
import os
import time
import urllib.request

ENV_PATH = "/Users/home/Claude/ai-orchestrator/.env"
MODELS = [
    "gemini-3.5-flash",
    "gemini-flash-latest",
    "gemini-3-flash-preview",
    "gemini-3.1-pro-preview",
]
URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _key(env_path: str):
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip() or None
    return None


def _write_status(out_dir: str, status: str, reason: str = "", model: str = "") -> None:
    with open(os.path.join(out_dir, "status.json"), "w", encoding="utf-8") as f:
        json.dump({"reviewer": "gemini", "status": status, "reason": reason, "model": model},
                  f, ensure_ascii=False, indent=1)


def run_gemini(prompt: str, out_dir: str, env_path: str = ENV_PATH) -> bool:
    os.makedirs(out_dir, exist_ok=True)
    try:
        key = _key(env_path)
    except OSError:
        key = None
    if not key:
        _write_status(out_dir, "failed", "no key: GEMINI_API_KEY를 찾지 못했다")
        return False
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }).encode("utf-8")
    last_error = ""
    for model in MODELS:
        try:
            req = urllib.request.Request(
                URL.format(model=model), body,
                {"x-goog-api-key": key, "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=420) as resp:
                data = json.load(resp)
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            items = json.loads(text)
            if not isinstance(items, list):
                raise ValueError("응답이 JSON 배열이 아니다")
            with open(os.path.join(out_dir, "gemini.json"), "w", encoding="utf-8") as f:
                json.dump(items, f, ensure_ascii=False, indent=1)
            _write_status(out_dir, "ok", model=model)
            return True
        except Exception as e:  # 모델별 실패는 다음 모델로 넘긴다
            last_error = f"{model}: {str(e)[:200]}"
            time.sleep(3)
    _write_status(out_dir, "failed", last_error)
    return False
