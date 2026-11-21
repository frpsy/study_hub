"""AI 검수 출력 검증: JSON 모양, 필수 키, 허용 값, 원문 일치."""

import json
import re

REQUIRED_KEYS = {
    "lecture_id", "field", "original", "suggestion",
    "type", "reason", "meaning_change", "confidence",
}
ALLOWED_TYPES = {"번역투", "쉼표", "길이", "어색한 연결", "오탈자", "유지"}
ALLOWED_CONFIDENCE = {"높음", "중간", "낮음"}


def parse_output(raw: str):
    text = raw.strip()
    fence = re.match(r"^```(?:json)?\s*\n(.*)\n```$", text, re.S)
    if fence:
        text = fence.group(1)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, list) else None


def validate_items(items: list[dict], source: dict[str, str]) -> list[str]:
    errors = []
    for n, item in enumerate(items):
        missing = REQUIRED_KEYS - set(item)
        if missing:
            errors.append(f"[{n}] 필수 키 누락: {sorted(missing)}")
            continue
        field = item["field"]
        if field not in source:
            errors.append(f"[{n}] 원문에 없는 필드: {field}")
        elif item["original"] not in source[field]:
            errors.append(f"[{n}] original이 원문 {field}에 없다")
        if item["type"] not in ALLOWED_TYPES:
            errors.append(f"[{n}] 허용되지 않은 type: {item['type']}")
        if not isinstance(item["meaning_change"], bool):
            errors.append(f"[{n}] meaning_change는 bool이어야 한다")
        if item["confidence"] not in ALLOWED_CONFIDENCE:
            errors.append(f"[{n}] 허용되지 않은 confidence: {item['confidence']}")
    return errors
