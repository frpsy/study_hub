"""두 AI에 주는 검수 프롬프트. 검수자 이름은 넣지 않아 두 검수가 서로 섞이지 않게 한다."""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))  # 저장소 루트
TEMPLATE = os.path.join(HERE, "review_prompt.md")
REVIEWERS = ("gemini", "chatgpt")
SOURCES = {
    "mini_courses.json": os.path.join(REPO, "data", "mini_courses.json"),
    "lecture_compact.json": os.path.join(REPO, "data", "lecture_compact.json"),
    "lectures.json": os.path.join(REPO, "lectures.json"),
}


def _load(name: str):
    with open(SOURCES[name], encoding="utf-8") as f:
        return json.load(f)


def _creators() -> dict[str, str]:
    data = _load("lectures.json")
    rows = data if isinstance(data, list) else data.get("lectures", [])
    return {r["id"]: r.get("creator", "") for r in rows}


def _fields(mini: dict, compact: dict, lid: str) -> list[tuple[str, str]]:
    out = [("lead", mini[lid]["lead"])]
    out += [(f"three[{i}]", t) for i, t in enumerate(mini[lid]["three"])]
    c = compact.get(lid, {})
    practice = c.get("practice") or {}
    for i, t in enumerate(practice.get("today", [])):
        out.append((f"practice.today[{i}]", t))
    for i, step in enumerate(practice.get("steps", [])):
        out.append((f"practice.steps[{i}].h", step.get("h", "")))
        for j, b in enumerate(step.get("b", [])):
            out.append((f"practice.steps[{i}].b[{j}]", b))
    for i, sec in enumerate(c.get("detail", [])):
        out.append((f"detail[{i}].h", sec.get("h", "")))
        for j, p in enumerate(sec.get("p", [])):
            out.append((f"detail[{i}].p[{j}]", p))
    return out


def build_prompt(batch_ids: list[str], reviewer: str) -> str:
    if reviewer not in REVIEWERS:
        raise ValueError(f"알 수 없는 검수자: {reviewer}")
    mini = _load("mini_courses.json")
    compact = _load("lecture_compact.json")
    creators = _creators()
    blocks = []
    for lid in batch_ids:
        lines = [f"### 강의 {lid} (창작자: {creators.get(lid, '')}, 제목: {mini[lid]['title']})"]
        lines += [f"- {field}: {text}" for field, text in _fields(mini, compact, lid)]
        blocks.append("\n".join(lines))
    with open(TEMPLATE, encoding="utf-8") as f:
        template = f.read()
    return template.replace("{{ITEMS}}", "\n\n".join(blocks))
