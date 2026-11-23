"""강연자 인용을 원본 자막과 대조한다. 테스트(tests/test_compact_courses.py)와 intro_candidates.py가 함께 쓴다.

자막은 한 줄이 `[시:분:초] 문장`이다. 인용의 낱말은 인용 시각 앞 3초~뒤 75초의 자막에 같은 순서로 있어야 한다.
군더더기·오인식 교정, 띄어쓰기, 구두점 차이는 허용하고 ‘…’는 생략을 뜻한다.
같은 조각(…으로 나뉜 한 덩어리) 안에서 낱말 사이에 자막의 다른 말이 MAX_GAP자(정규화한 글자 수)를 넘게 끼어 있으면
실패한다. 그만큼 건너뛰려면 ‘…’로 표시해야 한다. 한국어 자막 기준이며 영어 자막의 인용은 대조하지 않는다.
"""
import re
from pathlib import Path

LINE = re.compile(r"\[(\d+):(\d+):(\d+)\] (.*)")
BEFORE, AFTER = 3, 75
MAX_GAP = 12   # 같은 조각 안에서 허용하는 건너뜀(‘막 그’ 같은 군더더기 수준)


def norm(text):
    """한글·영문·숫자만 남긴다(띄어쓰기와 구두점은 비교하지 않는다)."""
    return re.sub(r"[^0-9A-Za-z가-힣]", "", text)


def stamp_seconds(stamp):
    total = 0
    for part in stamp.split(":"):
        total = total * 60 + int(part)
    return total


def stamp_label(seconds):
    """사이트 형식 `M:SS`, `H:MM:SS`(앞 0 없음)."""
    h, rest = divmod(int(seconds), 3600)
    m, s = divmod(rest, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def video_key(row):
    """lectures.json 항목의 영상 ID. `watch?v=<ID>`가 없으면 강의 id를 그대로 쓴다."""
    m = re.search(r"[?&]v=([A-Za-z0-9_-]{11})", row.get("video_url") or "")
    return m.group(1) if m else row["id"]


def transcript_path(root, row):
    """transcripts/<영상ID>.ko.txt 또는 .en.txt 중 있는 것. 없으면 None."""
    key = video_key(row)
    for lang in ("ko", "en"):
        path = Path(root) / "transcripts" / f"{key}.{lang}.txt"
        if path.exists():
            return path
    return None


def load_transcript(path):
    """[(초, 문장)] 목록."""
    lines = []
    for raw in Path(path).read_text(encoding="utf-8-sig").splitlines():
        m = LINE.match(raw)
        if m:
            lines.append((int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3]), m[4]))
    return lines


def window_text(lines, t, before=BEFORE, after=AFTER):
    return "".join(norm(text) for sec, text in lines if t - before <= sec <= t + after)


def quote_problems(quote, lines, t, before=BEFORE, after=AFTER, max_gap=MAX_GAP):
    """인용에 문제가 있으면 이유 목록을, 없으면 빈 목록을 돌려준다."""
    window = window_text(lines, t, before, after)
    if not window:
        return ["그 시각 앞뒤에 자막이 없다"]
    if len(norm(quote)) < 10:
        return ["인용의 글자(한글·영문·숫자)가 10자 미만이다"]
    problems, pos = [], 0
    for fragment in quote.split("…"):
        first = True
        for word in fragment.split():
            token = norm(word)
            if not token:
                continue
            found = window.find(token, pos)
            if found < 0:
                problems.append(f"‘{word}’가 그 시각의 자막에 없거나 순서가 다르다")
                continue
            if not first and found - pos > max_gap:
                problems.append(f"‘{word}’ 앞에 자막의 다른 말이 {found - pos}자 끼어 있다(건너뛰려면 ‘…’로 표시한다)")
            first = False
            pos = found + len(token)
    return problems
