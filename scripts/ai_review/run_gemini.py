"""Gemini 1차 검수 호출. 성공하면 gemini 결과와 status.json을 남기고, 실패하면 사유를 status.json에 남긴다."""

import json
import os

try:
    from .gemini_client import GeminiError, generate
except ImportError:  # 스크립트로 직접 실행할 때
    from gemini_client import GeminiError, generate

ENV_PATH = "/Users/home/Claude/ai-orchestrator/.env"


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
    try:
        # 모델 체인·재시도·경로 이중화는 gemini_client가 맡는다(429·503·빈 404 같은 간헐 오류 대응).
        r = generate(prompt, json_mode=True, timeout=420, key=key)
        items = json.loads(r.text)
        if not isinstance(items, list):
            raise ValueError("응답이 JSON 배열이 아니다")
    except (GeminiError, ValueError) as e:
        _write_status(out_dir, "failed", str(e)[:400])
        return False
    with open(os.path.join(out_dir, "gemini.json"), "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    _write_status(out_dir, "ok", model=r.model)
    return True
