"""생성기를 모두 돌리고 검증한다. 한 명령으로 빠뜨림을 막는다. 화면 버전은 자산 해시라 손으로 올리지 않는다.

    python3 scripts/build_all.py                      # 홈과 강의 페이지를 다시 만든다
    python3 scripts/build_all.py --check              # 만든 결과와 검증(design·site·--check 둘)을 확인한다
    python3 scripts/build_all.py --check --tests      # 위에 단위 테스트와 노드 테스트까지

브라우저 테스트(Playwright)는 포함하지 않는다(AGENTS.md의 명령을 따로 돌린다).
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def run(*cmd):
    print("$", " ".join(str(c) for c in cmd), flush=True)
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode:
        raise SystemExit(f"실패: {' '.join(str(c) for c in cmd)}")


def build(args, root=ROOT, runner=run):
    """생성 → 검증."""
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


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--tests", action="store_true")
    build(ap.parse_args(argv))
    print("끝")


if __name__ == "__main__":
    main()
