"""디자인 토큰 및 댓글 복사 동작의 공통 계약을 검사한다."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
TOKENS = {
    "--paper": "#faf9f6",
    "--surface": "#fefdfa",
    "--ink": "#1f2328",
    "--muted": "#5e5e66",
    "--line": "rgba(15,15,16,.12)",
    "--accent": "#0b57d0",
    "--tint": "#d3e3fd",
    "--on-accent-container": "#041e49",
    "--feature-surface": "#eef3fc",
    "--selection-bg": "#d3e3fd",
    "--hover-glow": "rgba(11,87,208,.2)",
    "--radius": "6px",
    "--radius-card": "var(--radius)",
    "--radius-control": "4px",
    "--font-body-size": "16px",
    "--font-ui-size": "14px",
    "--line-height-body": "1.8",
    "--space-1": "4px", "--space-2": "8px", "--space-3": "12px",
    "--space-4": "16px", "--space-5": "20px", "--space-6": "24px",
    "--space-8": "32px", "--space-12": "48px",
    "--site-max-width": "800px",
    "--tap-target": "44px",
    "--button-pad-y": "9px", "--button-pad-x": "15px",
    "--brand-ink": "#0f0f10",
    "--brand-soft": "rgba(15,15,16,.035)",
    "--brand-outline": "rgba(15,15,16,.14)",
    "--reading-measure": "760px",
    "--card-shadow": "none",
}
# v16 개편 층의 토큰(docs/design-overhaul-plan-2026-11-26.md). 값이 아니라 존재를 검사한다.
V16_TOKENS = (
    "--v16-radius-sm", "--v16-radius-md", "--v16-radius-lg", "--v16-radius-xl", "--v16-radius-full",
    "--type-display", "--type-home-title", "--type-section", "--type-lead", "--type-card-title",
    "--ease-standard", "--ease-emphasized", "--ease-spring", "--dur-1", "--dur-2", "--dur-3",
    "--surface-1", "--surface-2", "--surface-3", "--glass-bg", "--glass-edge", "--glass-filter",
    "--home-max-width",
)
CSS_CONTRACT = (
    "font:var(--font-body-size)/var(--line-height-body)",
    "width:min(var(--site-max-width),",
    "border-radius:var(--radius-control);padding:var(--button-pad-y) var(--button-pad-x)",
    "min-height:var(--tap-target)",
    ".lecture-section pre{",
    "white-space:pre-wrap;overflow-wrap:anywhere",
    "@media(max-width:780px)",
)
JS_CONTRACT = (
    "document.querySelectorAll('[data-copy-target]')",
    "navigator.clipboard.writeText(source.textContent)",
    "button.textContent='복사 완료 ✓'",
    "status.textContent='복사됨'",
    "status.textContent='선택한 내용을 직접 복사해 주세요.'",
    "setTimeout(()=>{button.textContent=originalLabel;if(status)status.textContent=''},2200)",
)


def contract_errors(root=ROOT):
    issues = []
    css = (root / "assets/site.css").read_text(encoding="utf-8")
    js = (root / "assets/site.js").read_text(encoding="utf-8")
    match = re.search(r":root\s*\{([^}]*)\}", css)
    variables = dict(re.findall(r"(--[a-z\d-]+)\s*:\s*([^;]+)", match.group(1))) if match else {}
    for name, value in TOKENS.items():
        if variables.get(name, "").strip() != value:
            issues.append(f"design token changed or missing: {name}")
    for name in V16_TOKENS:
        if not re.search(re.escape(name) + r"\s*:", css):
            issues.append(f"v16 token missing: {name}")
    if "prefers-reduced-motion:reduce){:root{--dur-1:0s" not in css:
        issues.append("v16 motion tokens must collapse under reduced motion")
    for snippet in CSS_CONTRACT:
        if snippet not in css:
            issues.append(f"shared CSS contract missing: {snippet}")
    for snippet in JS_CONTRACT:
        if snippet not in js:
            issues.append(f"copy behavior contract missing: {snippet}")
    if "복사했다." in js:
        issues.append("legacy copy feedback reintroduced")
    return issues


if __name__ == "__main__":
    errors = contract_errors()
    print("\n".join(errors) if errors else "PASS: shared design tokens and copy feedback contract")
    sys.exit(bool(errors))
