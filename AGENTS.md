# 내면의 서재 — AI 작업 기준 (Claude·ChatGPT·Codex 공통 원본)

> 매 대화에 읽히는 파일이라 항상 필요한 것만 둔다. 작업별 상세는 아래 표의 문서를 그 작업 때만 읽는다. 2026-11-06까지의 긴 이력 규칙은 `docs/archive/`에 보존했고, 이 파일과 다르면 이 파일이 우선한다.

## 사이트
- 개인 학습 사이트 「내면의 서재」: 강의별 핵심 요약과 타임스탬프(김주환 강의) 또는 상세 요약(그 외 강연자). 공개 주소 https://frpsy.github.io/study_hub/ (GitHub Pages, main 머지 후 자동 배포).
- 화면은 홈(강의 목록, H1 ‘강의 요약’)과 강의 페이지뿐. 강의 페이지 = 한 문장 + 핵심 세 가지 + 실천 포인트 + 상세 요약(출처 포함; 김주환 강의는 새 강의부터 필수) + 타임스탬프(김주환 강의만) + 접힌 ‘원본과 참고 자료’ + 더 최근/지난 강의 이동. 상단 메뉴 없음.
- 로그인·학습 기록·5분 요약·미니강좌·용어 화면은 되살리지 않는다.

## 데이터와 생성 (생성 HTML은 손으로 고치지 않는다)
| 무엇 | 원본 |
|---|---|
| 강의 등록(최신순) | `lectures.json` → `python3 scripts/build_library.py` |
| 한 문장·핵심 세 가지 | `data/mini_courses.json`의 `lead`·`three` |
| 타임스탬프(김주환만)·상세 요약 `detail`·실천 포인트 `practice`(선택)·출처·옛 앵커 | `data/lecture_compact.json` → `python3 scripts/build_compact_lectures.py` |
| 화면 버전 | `build-info.json`의 `version` (보이는 변경마다 올리고 재생성) |
| 원본 자막·근거 | `transcripts/`(가공 금지), `study-audits/<영상ID>.json` |

## 검증 (병합 전 모두 통과)
```
python3 scripts/validate_design_system.py && python3 scripts/validate_site.py
python3 scripts/build_library.py --check && python3 scripts/build_compact_lectures.py --check
python3 -m unittest discover -s tests -p 'test_*.py' && node --test tests/test_*.cjs
npx playwright test --config=tests/playwright.config.cjs
```
PR 본문에는 `## 변경 범위` `## 영향 기능` `## 검증 증거` `## 남은 위험` 네 제목이 필요하다(CI 검사). 실기기 Safari 미검증 등은 남은 위험에 적는다.

## 작업 방식
- 브랜치 → 검증 → PR → CI 통과 → squash 머지 → 공개 페이지 확인까지 묻지 않고 진행한다(사용자 허용). 배포를 확인하지 않았으면 완료라고 하지 않는다.
- 보고는 짧게: 바뀐 점 요약과 링크.
- 김주환 외 강의는 타임스탬프 없이 자막 기반 상세 요약과 출처를 쓴다(`편집규칙.md` 14절). 김주환 새 강의는 상세 요약 + 타임스탬프를 함께 쓰고, 문체는 평서문(~이다·~한다)·질문형 소제목·질문→정의→근거→실천 흐름이며 "교수님은 ~했습니다"·"강사는"과 비문은 금지한다(16절). 사실·출처 검수와 문장·문법 검수를 끝낸 뒤에만 완료라고 보고한다(김주환 강의도 같다). 날짜·길이처럼 확인하지 못한 값은 지어내지 않고 비우거나 `study-audits/`와 PR 남은 위험에 적는다.
- 강의 내용 질문에는 `transcripts/`의 원본 자막에서 해당 구간을 찾아 시각과 함께 인용해 답한다.

## 작업별 문서 (해당 작업 때만 읽기)
| 작업 | 문서 |
|---|---|
| 강의 추가·요약·타임스탬프·상세 요약 수정, 자막 확보 | `편집규칙.md` → `.agents/skills/lecture-study/SKILL.md` |
| 디자인·CSS·화면 동작 | `docs/design-system.md` |
| 서비스 워커·캐시·성능 | `편집규칙.md` 13절, `docs/navigation-performance-2026-11-01.md` |
| 책·논문 등 다른 자료 등록 | `docs/content-model.md` |
| 지난 결정의 배경 | `docs/archive/`, `docs/*-review-*.md` |
