"""기계 점검: 길이, 쉼표, 문장 끝, 금지어. 판단이 아니라 형식만 본다."""

import re


KIM_FORBIDDEN = ("강사는", "강사의", "강사가")


def _is_quoted(text: str) -> bool:
    return text.startswith("“") and text.endswith("”")


def check_lead(text: str) -> list[str]:
    errors = []
    if _is_quoted(text):
        inner = text[1:-1]
        if inner.count(".") != 1 or not inner.endswith("."):
            errors.append("인용형 한 문장은 안쪽 마침표가 하나이고 끝이 ‘.’이어야 한다")
        if not 15 <= len(text) <= 170:
            errors.append(f"인용형 길이 {len(text)}자는 15–170자 범위를 벗어난다")
        return errors
    if not text.endswith("다."):
        errors.append("lead는 ‘-다.’로 끝나야 한다")
    if not 60 <= len(text) <= 120:
        errors.append(f"lead 길이 {len(text)}자는 60–120자 범위를 벗어난다")
    if text.count(",") > 1:
        errors.append("lead 쉼표는 1개 이하여야 한다")
    return errors


def check_three(items: list[str]) -> list[str]:
    errors = []
    if len(items) != 3:
        errors.append(f"three 항목은 3개여야 하는데 {len(items)}개다")
    for i, item in enumerate(items):
        errors += check_three_item(i, item)
    return errors


def check_three_item(i: int, item: str) -> list[str]:
    if not item.strip():
        return [f"three[{i}]가 비어 있다"]
    errors = []
    if not item.endswith("다."):
        errors.append(f"three[{i}]는 ‘-다.’로 끝나야 한다")
    if len(item) > 90:
        errors.append(f"three[{i}] 길이 {len(item)}자는 최대 90자를 넘는다")
    if item.count(",") > 1:
        errors.append(f"three[{i}] 쉼표는 1개 이하여야 한다")
    return errors


def check_intro_field(field: str, text: str) -> list[str]:
    """도입(intro) 필드 형식. 핵심 문장은 three와 같은 기준, 해볼 일의 칸은 길이와 끝맺음을 본다."""
    if re.fullmatch(r"intro\[\d+\](\.h|\.items\[\d+\](\.\w+|\.b\[\d+\])?)", field) and not text.strip():
        return [f"{field}가 비어 있다"]
    if re.fullmatch(r"intro\[\d+\]\.h", field):
        return [f"{field} 길이 {len(text)}자는 최대 24자를 넘는다"] if len(text) > 24 else []
    m = re.fullmatch(r"intro\[\d+\]\.items\[\d+\](?:\.(\w+))?", field)
    if not m:
        return []
    key, errors = m.group(1), []
    if key in (None, "t"):
        if not text.endswith("다."):
            errors.append(f"{field}는 ‘-다.’로 끝나야 한다")
        if len(text) > 90:
            errors.append(f"{field} 길이 {len(text)}자는 최대 90자를 넘는다")
        if text.count(",") > 1:
            errors.append(f"{field} 쉼표는 1개 이하여야 한다")
    elif key in ("do", "check"):
        if not text.endswith("다."):
            errors.append(f"{field}는 ‘-다.’로 끝나야 한다")
        if len(text) > 80:
            errors.append(f"{field} 길이 {len(text)}자는 최대 80자를 넘는다")
    elif key == "when":
        if len(text) > 45 or text.endswith("."):
            errors.append(f"{field}는 마침표 없는 45자 이내의 구여야 한다")
    return errors


def check_forbidden(text: str, creator: str) -> list[str]:
    if creator != "김주환":
        return []
    return [f"김주환 강의 본문에 ‘{w}’를 쓰지 않는다" for w in KIM_FORBIDDEN if w in text]
