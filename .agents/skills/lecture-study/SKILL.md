---
name: lecture-study
description: 내면의 서재(frpsy/study_hub)에 강의를 추가하거나 핵심 요약·타임스탬프를 작성·검수할 때 사용
---

# 강의 추가·수정 절차

기준 문서: `AGENTS.md`(구성·검증) → `편집규칙.md`(문장·타임스탬프·자막 규칙). 이전 판(마인드맵·상세 해설 시기)은 `docs/archive/lecture-study-SKILL-2026-11-06.md`.

## 새 강의
1. 영상 ID를 먼저 확정한다(확인 안 된 ID를 만들지 않는다).
2. 자막 확보(편집규칙 8절 순서). 원문 그대로 `transcripts/<영상ID>.<언어>.txt`(+SRT/VTT)로 저장한다. 아직 없으면 편집규칙 10절대로 `caption-queue/<영상ID>.json`과 2시간 재확인으로 관리한다.
3. 김주환 영상은 설명란 전문을 `transcripts/<영상ID>.description.txt`에 저장하고(편집규칙 16절) 최종 정리에 반영한다. 자막 전 구간과 설명란을 읽고, 읽은 범위를 `study-audits/<영상ID>.json`에 기록한다.
4. `lectures.json` 맨 앞(최신순)에 등록: `id`, `date`, `added`(사이트에 등록하는 시각, KST ISO 예 `2026-11-12T17:30:00+09:00`; 홈의 ‘추가된순’ 정렬 기준), `title`, `duration`, `description`, `tags`, `creator`, `kind`(lecture), 필요 시 `video_url`.
5. `data/mini_courses.json`에 `lead`(한 문장)·`three`(세 문장) 작성 — 편집규칙 2·3절 기준.
6. `data/lecture_compact.json`에 — 김주환 강의: `timeline`(편집규칙 4절 형식)과 `detail`(16절: 평서문·질문형 소제목·[보충] 구분). 그 외 강연자: `timeline` 없이 `detail`(자막 기반 상세 요약, 필요 시 웹 보충은 `[보충]` 표시, 편집규칙 14절). 공통: `sources`(label·url, 실제 확인한 링크만), 필요 시 `note`·`aliases`.
7. `build-info.json` 버전을 올리고 `build_library.py`, `build_compact_lectures.py` 실행.
8. 모든 강의는 편집규칙 14절의 자체 검수(사실·출처, 문장·문법, 형식)를 끝낸다. AGENTS.md의 검증 명령 전부 통과 → PR(네 제목) → CI → 머지 → 공개 페이지에서 새 문구 확인 → 링크 보고.

## 기존 요약 다듬기
- `mini_courses.json`만 고치고 재생성한다. 뜻을 바꾸는 수정은 저장된 자막·`data/summaries.json` 원고로 근거를 확인한다.
- 비문·어색한 연결·같은 서술어 반복을 없애고, 처음 읽는 사람도 바로 이해되게 쓴다.
- 타임스탬프 원문·연구 수치·직접 인용은 문체를 이유로 고치지 않는다.

## 김주환 강의
- `timeline` + `detail` + `practice`, 평서문·질문형 소제목·질문→정의→근거→실천. "교수님은 ~했습니다"·"강사는"·비문 금지, 확인한 사실만 `[보충]`(편집규칙 16절).

## 김주환 새 강의 만드는 법 (기준 예시: `peaceful-life-live`)
- 문체는 `docs/kimjuhwan-style.md`를 따른다. 데이터 형식은 `data/lecture_compact.json`·`mini_courses.json`·`summaries.json`의 `peaceful-life-live` 항목을 그대로 본뜬다(타임스탬프 → 상세 요약 소제목 8개 → 실천 포인트 순으로 쓰면 수월하다).
- 순서: 설명란·메타데이터(제목·게시일·길이) 확인 → 자막 전 구간 읽기 → 확인할 항목(고유명사·번역·계보·수치) 목록 → 웹 검색으로 실제 열어 본 출처만 `[보충]` → 쓰기 → 휴머나이저식 문장 검수 → 생성·검증.
- `practice`는 필수다. `today` 3개, `steps`는 각 `t`(타임스탬프에 있는 시각)·`h`·`b`를 갖고, `note`에 덧붙인 안내를 밝힌다. 강연에 없는 처방·기간·수치를 만들지 않는다.
- 확인하지 못한 값(방송 날짜, 영상 길이, 번역 귀속 등)은 비우거나 "약"으로 쓰고 `note`·`study-audits/`·PR 남은 위험에 적는다.

## 자주 놓치는 것
- `id`는 밑줄로 시작하지 않는 주제형 키로 쓴다. 영상 ID가 `_`로 시작하면 `video_url`에만 쓴다(Pages의 Jekyll이 밑줄 파일을 제외할 수 있다).
- `video_url`은 `watch?v=<영상ID>` 형식으로 쓴다. 실천 포인트의 시각 링크(`&t=`)가 이 형식을 전제하므로 `live/` 주소를 쓰면 링크가 깨진다. 사용자가 준 `live/` 주소는 `sources`에 둔다.
- 김주환 강의 데이터 어디에도 "강사"라는 말이 들어가면 테스트가 실패한다. 공개 페이지에는 "자막은 ", "자막 없음", "교수의 해석" 같은 제작 메모도 금지다.
- `lectures.json`에 새 강의를 넣으면 `mini_courses.json`·`summaries.json`·`lecture_compact.json`에 같은 `id`가 모두 있어야 한다.
- Playwright가 `@playwright/test`를 못 찾으면 CLI와 같은 버전을 임시 폴더에 설치하고 `NODE_PATH`를 지정해 그 폴더의 `playwright`로 실행한다.
- 푸시가 403이면 이 세션에 저장소 쓰기 권한이 없는 것이다. 우회하지 말고 GitHub App 설치나 커넥터 재연결이 필요하다고 알린다.

## 김주환 외 강의
- 타임스탬프 금지, `detail`로 상세 요약. 사족 없이 쓰고 출처를 남긴다. 보고 전 사실·출처 검수와 문장·문법 검수를 끝낸다(편집규칙 14절).

## 자주 걸리는 검사
- `tests/test_korean_leads.py`: lead는 문장부호 1개, ‘다.’로 끝, 55–170자, 생성 HTML과 일치.
- `tests/test_compact_courses.py`: three는 3개, 모두 ‘다.’로 끝, 머리말 금지.
- Playwright: 한 문장 글자 ≤17px, 목록 ≤16px, 제목 위계 h1>h2>h3, 가로 넘침 없음.
