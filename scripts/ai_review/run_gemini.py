"""Gemini 1차 검수 호출. 성공하면 gemini 결과와 status.json을 남기고, 실패하면 사유를 status.json에 남긴다."""

import json
import os
import re
import subprocess

try:
    from .gemini_client import GeminiError, generate
except ImportError:  # 스크립트로 직접 실행할 때
    from gemini_client import GeminiError, generate

ENV_PATH = "/Users/home/Claude/ai-orchestrator/.env"
# 공용 래퍼: agy(구독 쿼터) → API flash → API lite 순서. 429가 나도 agy가 살아 있으면 품질이 유지된다.
WRAPPER = "/Users/home/.claude/ai-collab/ai-gemini.sh"
_MODEL_TAG = re.compile(r"\[(agy|gemini):([^\]]+)\]")


def _via_wrapper(prompt: str, out_dir: str, wrapper: str):
    """래퍼로 호출해 (결과 텍스트, 모델명)을 돌려준다. 실패하면 None."""
    path = os.path.join(out_dir, "gemini-prompt.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(prompt)
    try:
        r = subprocess.run([wrapper, "-f", path, "-e", "medium"], capture_output=True,
                           text=True, timeout=420)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0 or not r.stdout.strip():
        return None
    tags = _MODEL_TAG.findall(r.stderr)
    model = f"{tags[-1][0]}:{tags[-1][1]}" if tags else "wrapper"
    return r.stdout, model


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


def run_gemini(prompt: str, out_dir: str, env_path: str = ENV_PATH, wrapper: str = WRAPPER) -> bool:
    os.makedirs(out_dir, exist_ok=True)
    got = _via_wrapper(prompt, out_dir, wrapper) if wrapper and os.path.exists(wrapper) else None
    if got:
        text, model = got
        try:
            items = json.loads(text)
            if not isinstance(items, list):
                raise ValueError("응답이 JSON 배열이 아니다")
        except ValueError:
            got = None  # 형식이 깨졌으면 API 경로로 다시 시도한다
        else:
            with open(os.path.join(out_dir, "gemini.json"), "w", encoding="utf-8") as f:
                json.dump(items, f, ensure_ascii=False, indent=1)
            _write_status(out_dir, "ok", model=model)
            return True
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
