"""강의 ID를 파일럿 포함 7배치(배치당 3편)로 나눈다."""

import json
import sys

BATCH_SIZE = 3
EXPECTED_TOTAL = 21


def make_batches(ids: list[str], pilot: list[str]) -> list[list[str]]:
    if len(ids) != EXPECTED_TOTAL:
        raise ValueError(f"강의 수가 {EXPECTED_TOTAL}편이어야 하는데 {len(ids)}편이다")
    if not set(pilot) <= set(ids):
        raise ValueError("파일럿 강의가 전체 목록에 없다")
    rest = sorted(i for i in ids if i not in pilot)
    ordered = list(pilot) + rest
    return [ordered[i:i + BATCH_SIZE] for i in range(0, len(ordered), BATCH_SIZE)]


if __name__ == "__main__":
    # 사용법: PYTHONPATH=scripts python3 -m ai_review.batches data/mini_courses.json
    path = sys.argv[1]
    pilot = ["2VTv6WW8Kn8", "kLizfh-5vuE", "MdDj5RZkMB4"]
    ids = list(json.load(open(path, encoding="utf-8")).keys())
    print(json.dumps(make_batches(ids, pilot), ensure_ascii=False, indent=1))
