"""채택한 제안을 원고 데이터에 반영한다. 필드 안에서 original이 정확히 한 번 있을 때만 바꾼다.

필드 이름은 프롬프트와 같다: lead, three[i], practice.today[i], practice.steps[i].h,
practice.steps[i].b[j], detail[i].h, detail[i].p[j].
"""

import re

_PATTERNS = [
    (re.compile(r"lead"), lambda m, mini, comp: (mini, ["lead"])),
    (re.compile(r"three\[(\d+)\]"), lambda m, mini, comp: (mini, ["three", int(m[1])])),
    (re.compile(r"practice\.today\[(\d+)\]"), lambda m, mini, comp: (comp, ["practice", "today", int(m[1])])),
    (re.compile(r"practice\.steps\[(\d+)\]\.h"), lambda m, mini, comp: (comp, ["practice", "steps", int(m[1]), "h"])),
    (re.compile(r"practice\.steps\[(\d+)\]\.b\[(\d+)\]"),
     lambda m, mini, comp: (comp, ["practice", "steps", int(m[1]), "b", int(m[2])])),
    (re.compile(r"detail\[(\d+)\]\.h"), lambda m, mini, comp: (comp, ["detail", int(m[1]), "h"])),
    (re.compile(r"detail\[(\d+)\]\.p\[(\d+)\]"), lambda m, mini, comp: (comp, ["detail", int(m[1]), "p", int(m[2])])),
]


def _locate(mini_l: dict, compact_l: dict, field: str):
    for pattern, resolve in _PATTERNS:
        m = pattern.fullmatch(field)
        if m:
            root, path = resolve(m, mini_l, compact_l)
            parent = root
            for key in path[:-1]:
                parent = parent[key]
            return parent, path[-1]
    raise ValueError(f"알 수 없는 필드: {field}")


def apply_edit(mini: dict, compact: dict, lecture_id: str, field: str, original: str, suggestion: str) -> None:
    parent, key = _locate(mini[lecture_id], compact.get(lecture_id, {}), field)
    text = parent[key]
    count = text.count(original)
    if count != 1:
        raise ValueError(f"{lecture_id} {field}: original이 {count}번 있다(정확히 1번이어야 한다)")
    parent[key] = text.replace(original, suggestion, 1)
