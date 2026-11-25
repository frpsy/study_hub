---
name: lecture-study
description: 내면의 서재(frpsy/study_hub)에 강의를 추가하거나 핵심 요약·타임스탬프를 작성·검수할 때 사용
---

# 강의 추가·수정 절차

기준 문서: `AGENTS.md`(구성·검증) → `편집규칙.md`(문장·타임스탬프·자막 규칙). 이전 판(마인드맵·상세 해설 시기)은 `docs/archive/lecture-study-SKILL-2026-11-06.md`.

YouTube 요약의 작성·수정과 상세 본문 윤문에는 기본적으로 [무손실 한국어 윤문 스킬](../lecture-polish/SKILL.md)을 함께 적용한다.

## 새 강의
1. 영상 ID를 먼저 확정한다(확인 안 된 ID를 만들지 않는다).
2. 자막 확보(편집규칙 8절 순서). 원문 그대로 `transcripts/<영상ID>.<언어>.txt`(+SRT/VTT)로 저장한다. 아직 없으면 편집규칙 10절대로 `caption-queue/<영상ID>.json`과 2시간 재확인으로 관리한다.
3. 김주환 영상은 설명란 전문을 `transcripts/<영상ID>.description.txt`에 저장하고(편집규칙 16절) 최종 정리에 반영한다. 자막 전 구간과 설명란을 읽고, 읽은 범위를 `study-audits/<영상ID>.json`에 기록한다.
4. `lectures.json` 맨 앞(최신순)에 등록: `id`, `date`, `added`(사이트에 등록하는 시각, KST ISO 예 `2026-11-12T17:30:00+09:00`; 홈의 ‘추가된순’ 정렬 기준), `title`, `duration`, `description`, `tags`, `creator`, `kind`(lecture), 필요 시 `video_url`.
5. `data/mini_courses.json`에 `lead`(한 문장) 작성 — 편집규칙 2절의 35~65자 직접 서술 기준. 다음 단계 `intro`의 첫 `points` 항목에도 같은 문장을 쓴다. `three`는 쓰지 않는다(핵심 주장은 6단계의 `intro`).
6. `data/lecture_compact.json`에 — 김주환 강의: `timeline`(편집규칙 4절 형식)과 `detail`(16절: 평서문·질문형 소제목, 웹 보충은 편집자 주), 그리고 `intro`(19절: 핵심 주장 `points`는 항상, 해볼 일 `practice`와 `steps`는 강연자가 실제로 권했을 때만). 그 외 강연자: `timeline`과 `detail`(자막 기반 상세 요약, 필요 시 웹 보충은 편집자 주 ‘강의 밖 보충 자료’에, 편집규칙 14절). 공통: `sources`(label·url, 실제 확인한 링크만), 필요 시 `note`·`aliases`.
7. (이미지를 요청받았을 때만) 대표 이미지 1장과 필요하면 본문 이미지 최대 3장을 만든다. 규칙은 `docs/design-system.md`의 ‘강의 대표 이미지’·‘상세 요약 안 이미지’이다. ChatGPT(Codex)만 쓰고, 필름 사진 느낌 프롬프트에 글자·인물·과한 빛 연출은 뺀다. JPEG 450KB 이하로 `assets/lectures/<id>.jpg`에 두고 `lectures.json`의 `image`를 채운다. 만든 사진은 직접 열어 확인한다.
8. 자막 오인식은 편집규칙 18절 순서로 점검한다. 용어는 `용어집.md`가 원본이고, 새 오인식은 그 표에 한 줄 추가한다. `tests/test_caption_terms.py`가 별칭 잔존을 막는다.
9. `build-info.json` 버전을 올리고 `build_library.py`, `build_compact_lectures.py`를 실행한다. 버전이 바뀌면 모든 강의 페이지가 바뀌므로 생성된 `lectures/*.html` 전체와 `index.html`을 커밋한다.
10. 모든 강의는 편집규칙 14절의 자체 검수(사실·출처, 문장·문법, 형식)를 끝낸다. AGENTS.md의 검증 명령 전부 통과 → PR(네 제목) → CI의 `quality`와 `browser`가 **모두 pass**인지 확인 → 병합 → 공개 페이지에서 새 문구 확인 → 링크 보고.

## 기존 요약 다듬기
- 윤문 기준과 절차는 [`lecture-polish`](../lecture-polish/SKILL.md)가 원본이다. 여기에 같은 내용을 다시 쓰지 않는다.
- 한 줄 요약은 `mini_courses.json`의 `lead`와 `intro` 첫 `points` 항목을 같은 문장으로 맞춘다. 상세 본문은 `lecture_compact.json`의 `detail`을 고친 뒤 재생성한다. 뜻을 바꾸는 수정은 저장된 자막(`transcripts/`)으로 근거를 확인한다.

## 김주환 강의
- `timeline` + `detail` + `intro`(19절), 평서문·질문형 소제목·질문→정의→근거→실천. "교수님은 ~했습니다"·"강사는"·비문 금지, 확인한 보충은 편집자 주에만 쓴다(편집규칙 16·17절).

## 김주환 새 강의 만드는 법 (기준 예시: `peaceful-life-live`)
- 문체는 `docs/kimjuhwan-style.md`를 따른다. 데이터 형식은 `data/lecture_compact.json`·`mini_courses.json`의 `peaceful-life-live` 항목을 그대로 본뜬다(타임스탬프 → 상세 요약 소제목 8개 → 도입 순으로 쓰면 수월하다).
- 순서: 설명란·메타데이터(제목·게시일·길이) 확인 → 자막 전 구간 읽기 → 확인할 항목(고유명사·번역·계보·수치) 목록 → 웹 검색으로 실제 열어 본 출처만 편집자 주에 → 쓰기 → 휴머나이저식 문장 검수 → 생성·검증.
- `intro`는 필수다(19절). `points`(1~4개)는 항상 쓰고, `practice`(1~3개, 언제·할 일과 `t`·`quote`, 확인은 강연자가 점검 기준을 말했을 때만)는 강연자가 청중에게 직접 권했거나 점검 기준으로 말한 대목이 있을 때만 쓴다. 개수를 3개에 맞추지 않는다. 강연에 없는 처방·기간·수치·신체 부위를 만들지 않는다. 시각과 인용은 자막 `grep`으로 확인하고, 인용은 자막 낱말만 쓴다(AI가 준 시각·인용은 틀릴 수 있다). 근거는 `study-audits`의 `intro_check`에 적는다. 후보는 `scripts/intro_candidates.py <id>`(탐색 전용)로 뽑고, 쓴 뒤에는 `python3 scripts/build_all.py --bump "변경 설명" --check --tests`로 생성·검증한다.
- 확인하지 못한 값(방송 날짜, 영상 길이, 번역 귀속 등)은 비우거나 "약"으로 쓰고 `note`·`study-audits/`·PR 남은 위험에 적는다.

## 자주 놓치는 것
- `git add -A`를 쓰지 않고 올릴 파일을 지정한다. 같은 폴더를 쓰는 다른 세션의 미완성 파일이 섞여 병합된 적이 있다(2026-11-22).
- 이미 올라간 김주환 강의의 타임스탬프는 고치지 않는다. 본문 오류만 고친다(편집규칙 17절).
- `quality`가 실패한 채 병합하지 않는다. `gh pr checks`에서 두 검사가 모두 pass인지 눈으로 확인한 뒤 병합한다. 버전만 올리고 생성 결과 일부를 빼먹으면 `quality`의 생성 검사가 실패한다.
- `id`는 밑줄로 시작하지 않는 주제형 키로 쓴다. 영상 ID가 `_`로 시작하면 `video_url`에만 쓴다(Pages의 Jekyll이 밑줄 파일을 제외할 수 있다).
- `video_url`은 `watch?v=<영상ID>` 형식으로 쓴다. 실천 포인트의 시각 링크(`&t=`)가 이 형식을 전제하므로 `live/` 주소를 쓰면 링크가 깨진다. 사용자가 준 `live/` 주소는 `sources`에 둔다.
- 김주환 강의 데이터 어디에도 "강사"라는 말이 들어가면 테스트가 실패한다. 공개 페이지에는 "자막은 ", "자막 없음", "교수의 해석" 같은 제작 메모도 금지다.
- `lectures.json`에 새 강의를 넣으면 `mini_courses.json`(`title`·`lead`만)·`lecture_compact.json`에 같은 `id`가 모두 있어야 한다.
- Playwright가 `@playwright/test`를 못 찾으면 CLI와 같은 버전을 임시 폴더에 설치하고 `NODE_PATH`를 지정해 그 폴더의 `playwright`로 실행한다.
- 푸시가 403이면 이 세션에 저장소 쓰기 권한이 없는 것이다. 우회하지 말고 GitHub App 설치나 커넥터 재연결이 필요하다고 알린다.

## 김주환 외 강의
- 실제 자막 시각에 맞춘 `timeline`과 `detail`을 함께 둔다. 사족 없이 쓰고 출처를 남긴다. 보고 전 사실·출처 검수와 문장·문법 검수를 끝낸다(편집규칙 14절).

## 자주 걸리는 검사
- `tests/test_korean_leads.py`: lead는 문장부호 1개, ‘다.’로 끝, 하드 한계 15~100자(35~65자는 목표라 벗어나면 경고), 메타 주어 없는 직접 서술, 첫 핵심 항목·생성 HTML과 일치.
- `tests/test_compact_courses.py`: 옛 형식의 three는 3개·‘다.’ 종결·머리말 금지. `intro`가 있으면 `three`·`practice` 금지, 블록 1~3개(같은 종류 중복 금지, `points` 필수, 제목에 개수 금지), 해볼 일은 `when`·`do`·`t`·`quote` 필수(`check`는 선택, 있으면 ‘다.’ 종결·80자 이내)이고 `quote`의 낱말이 그 시각의 자막에 있어야 한다.
- `tests/test_caption_terms.py`: 용어집의 ‘점검할 표현’(배경자, 개별적인 자 등)과 음절이 빠진 ‘자’가 공개 본문에 남으면 실패.
- `tests/test_lecture_images.py`: 대표·본문 이미지의 개수(본문 3장 이하), 450KB 이하, alt, 크기, 순서.
- Playwright: 한 문장 글자 ≤17px, 목록 ≤16px, 제목 위계 h1>h2>h3, 가로 넘침 없음.
