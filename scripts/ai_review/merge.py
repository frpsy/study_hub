"""두 AI의 검증 통과 제안을 판정 규칙(스펙 5절)으로 묶는다."""


def _key(item: dict) -> tuple:
    return (item["lecture_id"], item["field"])


def merge(g: list[dict], c: list[dict]) -> dict:
    gi = {_key(x): x for x in g}
    ci = {_key(x): x for x in c}
    result = {"adopt_candidates": [], "review": [], "conflict": [], "user_queue": []}
    for key in sorted(set(gi) | set(ci)):
        a, b = gi.get(key), ci.get(key)
        present = [x for x in (a, b) if x is not None]
        if any(x["meaning_change"] for x in present):
            result["user_queue"].append(present[0])
        elif a and b:
            if a["suggestion"] == b["suggestion"]:
                result["adopt_candidates"].append(a)
            else:
                result["conflict"].append({"gemini": a, "chatgpt": b})
        else:
            result["review"].append(present[0])
    return result
