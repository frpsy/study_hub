"""ChatGPT(Codex) 2차 독립 검수 호출. 결과와 status.json을 out_dir에 남긴다. 실패는 사유를 기록한다."""

import json
import os
import subprocess
import tempfile

from .validate_output import parse_output


def _write_status(out_dir: str, status: str, reason: str = "") -> None:
    with open(os.path.join(out_dir, "status.json"), "w", encoding="utf-8") as f:
        json.dump({"reviewer": "chatgpt", "status": status, "reason": reason},
                  f, ensure_ascii=False, indent=1)


def run_chatgpt(prompt: str, out_dir: str, codex_bin: str = "codex", timeout: int = 900) -> bool:
    os.makedirs(out_dir, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        last = os.path.join(tmp, "last.txt")
        # 프롬프트는 stdin("-")으로 넘긴다. -o는 마지막 응답만 파일로 남긴다.
        cmd = [codex_bin, "exec", "-s", "read-only", "--skip-git-repo-check",
               "--ephemeral", "-o", last, "-"]
        try:
            proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=timeout)
        except FileNotFoundError:
            _write_status(out_dir, "failed", f"codex 실행 파일을 찾지 못했다: {codex_bin}")
            return False
        except subprocess.TimeoutExpired:
            _write_status(out_dir, "failed", "시간 초과")
            return False
        if proc.returncode != 0 or not os.path.exists(last):
            _write_status(out_dir, "failed", f"종료 코드 {proc.returncode}: {proc.stderr[-300:]}")
            return False
        with open(last, encoding="utf-8") as f:
            items = parse_output(f.read())
    if items is None:
        _write_status(out_dir, "failed", "응답이 JSON 배열이 아니다")
        return False
    with open(os.path.join(out_dir, "chatgpt.json"), "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    _write_status(out_dir, "ok")
    return True
