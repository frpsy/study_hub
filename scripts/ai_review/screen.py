"""자동 반려: 파일럿에서 사람이 매번 반려한 유형을 기계로 먼저 거른다.

반환값이 None이면 사람 판정으로 넘기고, 문자열이면 그 이유로 자동 반려한다.
"""

import re

from .mech_check import check_intro_field, check_lead, check_three_item

TRANSLATIONESE = ("에 대한", "를 통해", "을 통해", "에 의해")
# 『』 책 제목과 「」 강의 제목은 원문 그대로 인용하는 것이라 번역투 검사에서 뺀다.
_TITLE = re.compile(r"[『「][^』」]*[』」]")
# 제안이 원문 밖의 같은 구절을 다시 넣는지 본다. 이 길이 이상이 원문 다른 자리에 있으면 중복이다.
_DUP_MIN_CHARS = 15


def _strip_titles(text: str) -> str:
    return _TITLE.sub("", text)


def _duplicates_elsewhere(original: str, suggestion: str, field_text: str) -> str | None:
    """제안이 원문 밖 다른 자리의 긴 구절을 다시 넣어 문장이 겹치면 그 구절을 돌려준다."""
    rest = field_text.replace(original, "", 1)
    words = re.findall(r"\S+", suggestion)
    for i in range(len(words)):
        for j in range(i + 1, len(words) + 1):
            chunk = " ".join(words[i:j])
            if len(chunk) < _DUP_MIN_CHARS:
                continue
            if chunk in rest and chunk not in original:
                return chunk
    return None


def screen_item(item: dict, field_text: str):
    original, suggestion, field = item["original"], item["suggestion"], item["field"]
    if original.strip() == suggestion.strip():
        return "변경 없음"
    if field == "lead" and field_text.startswith("“") and field_text.endswith("”"):
        return "인용형 lead는 원문 낱말을 유지한다(편집규칙 2절)"
    sug_plain, ori_plain = _strip_titles(suggestion), _strip_titles(original)
    for marker in TRANSLATIONESE:
        if sug_plain.count(marker) > ori_plain.count(marker):
            return f"번역투 추가: ‘{marker}’(편집규칙 2·5절)"
    dup = _duplicates_elsewhere(original, suggestion, field_text)
    if dup:
        return f"중복 생성: 원문 다른 자리의 ‘{dup[:20]}…’을 다시 넣음"
    new_text = field_text.replace(original, suggestion, 1)
    if field == "lead":
        errs = check_lead(new_text)
    else:
        m = re.fullmatch(r"three\[(\d)\]", field)
        errs = check_three_item(int(m.group(1)), new_text) if m else check_intro_field(field, new_text)
    if errs:
        return "기계 점검 위반: " + "; ".join(errs)
    return None
