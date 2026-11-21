"""배치 한 개를 실행한다: 기계 점검 → Gemini·ChatGPT 검수 → 검증 → 판정 초안.

사용법(저장소 루트): PYTHONPATH=scripts python3 -m ai_review.run_batch <배치번호 1–7>
산출물은 drafts/ai-review/batches/NN/ 에 쌓는다(저장소에 올리지 않는다). 판정(승인 표)은 사람이 마무리한다.
"""

import json
import os
import sys

from .batches import make_batches
from .mech_check import check_forbidden, check_lead, check_three
from .merge import merge
from .prompt import _creators, _fields, _load, build_prompt
from .run_chatgpt import run_chatgpt
from .run_gemini import run_gemini
from .screen import screen_item
from .validate_output import validate_items

from .prompt import REPO

ROOT = os.path.join(REPO, "drafts", "ai-review")
PILOT = ["2VTv6WW8Kn8", "kLizfh-5vuE", "MdDj5RZkMB4"]


def _dump(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def mechanical(ids: list[str]) -> dict:
    mini = _load("mini_courses.json")
    compact = _load("lecture_compact.json")
    creators = _creators()
    report = {}
    for lid in ids:
        errs = []
        errs += check_lead(mini[lid]["lead"])
        errs += check_three(mini[lid]["three"])
        for field, text in _fields(mini, compact, lid):
            errs += check_forbidden(text, creators.get(lid, ""))
        report[lid] = errs
    return report


def validate_by_lecture(items: list[dict], ids: list[str]) -> tuple[list[dict], list[str], list[dict]]:
    """형식 검증 → 자동 반려(screen) 순서로 거른다. (통과, 형식 오류, 자동 반려)를 돌려준다."""
    mini = _load("mini_courses.json")
    compact = _load("lecture_compact.json")
    ok, errors, rejected = [], [], []
    for lid in ids:
        source = dict(_fields(mini, compact, lid))
        mine = [x for x in items if isinstance(x, dict) and x.get("lecture_id") == lid]
        for x in mine:  # 항목마다 따로 검증해, 한 항목의 오류가 다른 항목을 버리지 않게 한다
            errs = validate_items([x], source)
            if errs:
                errors += [f"{lid} {e}" for e in errs]
                continue
            reason = screen_item(x, source[x["field"]])
            if reason:
                rejected.append(dict(x, auto_reject=reason))
            else:
                ok.append(x)
    return ok, errors, rejected


def main(n: int) -> None:
    ids_all = list(_load("mini_courses.json").keys())
    batch = make_batches(ids_all, PILOT)[n - 1]
    out = os.path.join(ROOT, "batches", f"{n:02d}")
    os.makedirs(out, exist_ok=True)

    mech = mechanical(batch)
    _dump(os.path.join(out, "input.json"), {"ids": batch, "mechanical": mech})

    results = {}
    for reviewer in ("gemini", "chatgpt"):
        prompt = build_prompt(batch, reviewer)
        with open(os.path.join(out, f"prompt-{reviewer}.md"), "w", encoding="utf-8") as f:
            f.write(prompt)
        sub = os.path.join(out, reviewer)
        if reviewer == "gemini":
            ok = run_gemini(prompt, sub)
        else:
            ok = run_chatgpt(prompt, sub)
        results[reviewer] = ok

    valid, errors, rejected = {}, {}, []
    for reviewer in ("gemini", "chatgpt"):
        path = os.path.join(out, reviewer, f"{reviewer}.json")
        if results[reviewer] and os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                items = json.load(f)
            valid[reviewer], errors[reviewer], rej = validate_by_lecture(items, batch)
            rejected += [dict(x, reviewer=reviewer) for x in rej]
        else:
            valid[reviewer], errors[reviewer] = [], ["실행 실패 또는 결과 없음"]

    merged = merge(valid["gemini"], valid["chatgpt"])
    merged["auto_rejected"] = rejected
    _dump(os.path.join(out, "validation.json"), {"errors": errors, "counts": {k: len(v) for k, v in valid.items()}})
    _dump(os.path.join(out, "merged.json"), merged)
    print(json.dumps({"batch": n, "ids": batch, "run": results,
                      "validated": {k: len(v) for k, v in valid.items()},
                      "errors": {k: len(v) for k, v in errors.items()},
                      "merged": {k: len(v) for k, v in merged.items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main(int(sys.argv[1]))
