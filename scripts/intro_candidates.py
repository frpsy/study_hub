"""강의 자막에서 강연자가 청중에게 권한 듯한 대목(권유형 문장) 후보를 시각과 함께 뽑는다.

탐색 전용이다. 후보는 ‘직접 권했는가’를 판정한 것이 아니다. 설명·수사적 질문·남의 말 인용이 섞여 있으니
사람이 자막 앞뒤를 읽고 골라야 한다(편집규칙 19절). 사용:

    python3 scripts/intro_candidates.py <강의 id> [--gap 20] [--limit 80] [--json]
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from quote_check import load_transcript, norm, stamp_label, stamp_seconds, transcript_path  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DIRECTIVE = {
    "ko": re.compile(r"(세요|십시오|하셔야|하지 마|하도록 하|하시기 바|권합니다|추천합니다|해 ?야 ?(돼|됩니다|해요|합니다)|하시면 ?(돼|됩니다)|해 ?주세요|드시|내려놓|찾아 ?보|기록하)"),
    "en": re.compile(r"\b(you should|you need to|you must|i recommend|i suggest|try to|try and|make sure|do not|don't|avoid|start by|i would|consider|aim to|it's important to|the key is|what i do)\b", re.I),
}


def candidates(lines, lang, gap=20, context=14):
    """권유형 표현이 있는 줄을 gap초 안에서 묶어 후보로 만든다. [(시작초, 대표줄, 맥락)]"""
    pattern = DIRECTIVE[lang]
    hits = [(sec, text) for sec, text in lines if pattern.search(text)]
    groups = []
    for sec, text in hits:
        # 묶음의 첫 적중에서 gap초 안은 같은 후보로 본다. 긴 권유 구간은 gap초마다 후보가 하나씩 나온다(마지막 적중이 아니라 첫 적중 기준이 의도).
        if groups and sec - groups[-1][0] <= gap:
            continue
        groups.append((sec, text))
    out = []
    for sec, text in groups:
        ctx = " ".join(t for s, t in lines if sec - 2 <= s <= sec + context)
        out.append((sec, text, ctx))
    return out


def lead_overlap(lead, ctx, size=12):
    a, b = norm(lead), norm(ctx)
    if not a:
        return False
    size = min(size, len(a))   # 짧은 한 문장도 통째로 겹치면 겹침이다
    return any(a[i:i + size] in b for i in range(len(a) - size + 1))


def used_times(record):
    """이미 도입의 해볼 일에 쓴 시각(초)."""
    times = []
    for block in record.get("intro") or []:
        if block["kind"] == "practice":
            times += [stamp_seconds(i["t"]) for i in block["items"] if "t" in i]
    return times


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("id")
    ap.add_argument("--gap", type=int, default=20)
    ap.add_argument("--limit", type=int, default=80)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    rows = {r["id"]: r for r in json.loads((ROOT / "lectures.json").read_text(encoding="utf-8"))}
    if args.id not in rows:
        sys.exit(f"등록되지 않은 강의 id: {args.id}")
    path = transcript_path(ROOT, rows[args.id])
    if not path:
        sys.exit("자막 파일이 없다(transcripts/<영상ID>.ko.txt 또는 .en.txt)")
    lang = "ko" if path.name.endswith(".ko.txt") else "en"
    lines = load_transcript(path)
    # 새 강의는 파생 데이터가 아직 없을 수 있다(자막만으로도 후보를 뽑는다).
    lead = json.loads((ROOT / "data/mini_courses.json").read_text(encoding="utf-8")).get(args.id, {}).get("lead", "")
    record = json.loads((ROOT / "data/lecture_compact.json").read_text(encoding="utf-8")).get(args.id, {})
    used = used_times(record)
    rows_out = []
    for sec, text, ctx in candidates(lines, lang, args.gap)[: args.limit]:
        rows_out.append({
            "t": stamp_label(sec), "line": text, "context": ctx,
            "overlaps_lead": bool(lead) and lead_overlap(lead, ctx),
            "already_used": any(abs(sec - u) <= 30 for u in used),
        })
    if args.json:
        print(json.dumps(rows_out, ensure_ascii=False, indent=1))
        return
    print(f"# {args.id} · 자막 {path.name} · 후보 {len(rows_out)}건(탐색 전용, 직접 권했는지는 사람이 판단한다)")
    for r in rows_out:
        flag = ("[한 문장과 겹침] " if r["overlaps_lead"] else "") + ("[이미 씀] " if r["already_used"] else "")
        print(f"\n## {r['t']} {flag}\n{r['context']}")


if __name__ == "__main__":
    main()
