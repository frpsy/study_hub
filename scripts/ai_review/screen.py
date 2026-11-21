"""자동 반려: 파일럿에서 사람이 매번 반려한 유형을 기계로 먼저 거른다.

반환값이 None이면 사람 판정으로 넘기고, 문자열이면 그 이유로 자동 반려한다.
"""

import re

from .mech_check import check_lead, check_three_item

TRANSLATIONESE = ("에 대한", "를 통해", "을 통해", "에 의해")


def screen_item(item: dict, field_text: str):
    original, suggestion, field = item["original"], item["suggestion"], item["field"]
    if original.strip() == suggestion.strip():
        return "변경 없음"
    if field == "lead" and field_text.startswith("“") and field_text.endswith("”"):
        return "인용형 lead는 원문 낱말을 유지한다(편집규칙 2절)"
    for marker in TRANSLATIONESE:
        if suggestion.count(marker) > original.count(marker):
            return f"번역투 추가: ‘{marker}’(편집규칙 2·5절)"
    new_text = field_text.replace(original, suggestion, 1)
    if field == "lead":
        errs = check_lead(new_text)
    else:
        m = re.fullmatch(r"three\[(\d)\]", field)
        errs = check_three_item(int(m.group(1)), new_text) if m else []
    if errs:
        return "기계 점검 위반: " + "; ".join(errs)
    return None
