"""생성기를 모두 돌리고, 선택하면 화면 버전을 올리고, 검증한다. 한 명령으로 빠뜨림을 막는다.

    python3 scripts/build_all.py                      # 홈과 강의 페이지를 다시 만든다
    python3 scripts/build_all.py --bump "변경 설명"    # 화면 버전을 올린 뒤 다시 만든다
    python3 scripts/build_all.py --check              # 만든 결과와 검증(design·site·--check 둘)을 확인한다
    python3 scripts/build_all.py --check --tests      # 위에 단위 테스트와 노드 테스트까지

브라우저 테스트(Playwright)는 포함하지 않는다(AGENTS.md의 명령을 따로 돌린다).
"""
import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def next_version(current, today):
    """`YYYY.MM.DD.N` 형식. 같은 날이면 N을 하나 올리고, 날짜가 바뀌면 1부터 시작한다."""
    date = f"{today.year:04d}.{today.month:02d}.{today.day:02d}"
    parts = current.split(".")
    if ".".join(parts[:3]) == date and parts[3:]:
        return f"{date}.{int(parts[3]) + 1}"
    return f"{date}.1"


def bump(change, today=None, root=ROOT):
    today = today or datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date()
    path = Path(root) / "build-info.json"
    info = json.loads(path.read_text(encoding="utf-8"))
    info["version"] = next_version(info["version"], today)
    info["change"] = change
    path.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return info["version"]


def run(*cmd):
    print("$", " ".join(str(c) for c in cmd), flush=True)
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode:
        raise SystemExit(f"실패: {' '.join(str(c) for c in cmd)}")


def build(args, root=ROOT, runner=run):
    """생성 → 검증. --bump 뒤에 어느 단계든 실패하면 build-info.json을 원래대로 되돌린다(버전만 오른 채 남지 않게)."""
    info_path = Path(root) / "build-info.json"
    original = info_path.read_text(encoding="utf-8")
    try:
        if args.bump:
            print("화면 버전:", bump(args.bump, root=root))
        runner(PY, "scripts/build_library.py")
        runner(PY, "scripts/build_compact_lectures.py")
        if args.check or args.tests:
            runner(PY, "scripts/validate_design_system.py")
            runner(PY, "scripts/validate_site.py")
            runner(PY, "scripts/build_library.py", "--check")
            runner(PY, "scripts/build_compact_lectures.py", "--check")
        if args.tests:
            runner(PY, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py")
            node = sorted(str(p.relative_to(root)) for p in (Path(root) / "tests").rglob("test_*.cjs"))
            if node:
                runner("node", "--test", *node)
    except BaseException:
        if args.bump:
            info_path.write_text(original, encoding="utf-8")
            print("실패해서 build-info.json을 되돌렸다. 생성된 파일이 일부 바뀌었을 수 있으니 git status로 확인한다.", file=sys.stderr)
        raise


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--bump", metavar="변경 설명")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--tests", action="store_true")
    build(ap.parse_args(argv))
    print("끝")


if __name__ == "__main__":
    main()
