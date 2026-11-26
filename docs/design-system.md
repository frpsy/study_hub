# 디자인 기준 (현행 v16)

> 현행 기준만 둔다. 2026-11-26 v16 개편 전까지의 기록(v10~v15, 블랙·레드·그레이, 조용한 서재, 옛 목차 버튼 등)은 `docs/archive/design-system-v10-v15-2026-11-26.md`에 그대로 보존했다. 그 이전은 `docs/archive/design-system-2026-11-07.md`에 있다. 개편 계획과 측정 기준선은 `docs/design-overhaul-plan-2026-11-26.md`.
> 최종 기준은 `assets/site.css`(맨 끝 ‘v16 · 개편 층’이 새 디자인의 유일한 정의 위치이고 위쪽 옛 층은 덮어쓴다), `assets/site.js`, `assets/search.js`이다.

## 1. 토큰
### 1-1. 공통 토큰 (계약: `scripts/validate_design_system.py`)
| 범주 | 토큰 | 값/역할 |
|---|---|---|
| 배경 | --paper / --surface | #faf9f6 / #fefdfa |
| 글자 | --ink / --muted | #1f2328 / #5e5e66 |
| 강조 | --accent / --tint | #0b57d0 / #d3e3fd (primary / primary-container) |
| 경계선 | --line | rgba(15,15,16,.12) |
| 옛 반경 | --radius-card / --radius-control | 6px / 4px (값은 계약으로 고정, 새 화면은 1-2의 반경을 쓴다) |
| 본문 | --font-body-size / --line-height-body | 16px / 1.8 |
| 작은 UI | --font-ui-size | 14px |
| 간격 | --space-1, 2, 3, 4, 5, 6, 8, 12 | 4, 8, 12, 16, 20, 24, 32, 48px |
| 읽기 폭 | --site-max-width | 800px (강의 상세·오프라인) |
| 터치 | --tap-target | 최소 44px |

### 1-2. v16 토큰 (존재를 검사한다)
| 범주 | 토큰 | 값 |
|---|---|---|
| 반경 | --v16-radius-sm·md·lg·xl·full | 8·14·20·28·999px. 큰 면 xl, 카드·대표 이미지 lg, 작은 조작 md, 알약 full |
| 유동 글자 | --type-display / home-title / section / lead / card-title | `clamp()`. 상세 제목 28~44px, 홈 제목 24~34px, 섹션 21~26px, 오늘의 문장 18~22px, 카드 제목 18~20px |
| 움직임 | --ease-standard / emphasized / spring, --dur-1·2·3 | 스프링은 `linear()`. 시간 .12·.2·.32초, 동작 줄이기에서 0 |
| 면 톤 | --surface-1·2·3 | 강조색을 면에 4·8·13% 섞음 |
| 글래스 | --glass-bg·edge·filter·shadow | 종이색 70% + `saturate(180%) blur(20px)` |
| 홈 폭 | --home-max-width | 1120px |

`color-mix()`를 못 쓰는 브라우저는 옛 면 색으로 대체한다(`@supports not`).

### 1-3. Material 블루 색 역할 (2026-11-25 확정, 비교 기록: `design/theme-proposals/README.md`)
| 역할 | 토큰 | 라이트 | 다크 |
|---|---|---|---|
| primary | --accent, --focus-color | #0b57d0 | #a8c7fa |
| on-primary | --on-accent | #ffffff | #062e6f |
| primary-container | --tint | #d3e3fd | #0842a0 |
| on-primary-container | --on-accent-container | #041e49 | #d3e3fd |
| 강조된 읽기 면 | --feature-surface | #eef3fc | #202b3f |

아이콘(`assets/icon.svg`, Material 3 열린 책)도 같은 두 색이다. 글꼴은 시스템 글꼴이고 웹폰트는 쓰지 않는다(오프라인 캐시 용량, 2026-11-26 재확인). 오늘의 한 문장은 로컬 명조 계열이다.

## 2. 구성과 반응형
- 모든 페이지: 공통 헤더·본문·푸터, h1 하나, 44px 이상 터치 대상, 왼쪽 정렬. 분기점은 780px 이하(모바일), 360px 이하(매우 작은 화면).
- 폭: 홈만 1120px(`body:has(.home-main)`이 헤더·본문·푸터 안쪽 폭을 함께 넓혀 왼쪽 선을 맞춘다). 강의 상세는 800px, 상세 요약 줄 길이 38em. 모바일은 좌우 16px.
- 데이터 원본: 홈은 `lectures.json` → `scripts/build_library.py`, 강의는 `data/lecture_compact.json` → `scripts/build_compact_lectures.py`. HTML은 손으로 고치지 않고 페이지별 인라인 style을 넣지 않는다(`validate_site.py`).
- 기존 URL 앵커(`#lecture-overview`, `#detail-N`, `#lecture-sources`, 옛 앵커)는 지우지 않는다.

## 3. 홈
- 순서: 제목 → 벤토 바로가기 → 검색·주제·북마크·정렬 → 이어 읽기 한 줄 → 강의 목록.
- **벤토(`section.bento`, ‘서재 바로가기’):** 오늘의 한 문장 큰 타일(PC 2×2) + 주제 타일(아이콘·편수, `index.html?topic=…#lecture-list`) + 최근 추가(`added` 최댓값)·많이 본 강의(`views` 최댓값). PC 4열, 모바일 2열, 360px 이하는 고른 강의 타일이 한 줄을 다 쓴다. 타일은 모두 링크이고 안의 글은 단어 단위로 줄을 바꾼다. 검색어가 있으면 벤토를 숨긴다.
- **오늘의 한 문장:** 스크립트가 날짜마다 다른 강의의 첫 요점으로 바꾸고, `다른 문장 보기`로 다른 강의의 첫 요점을 보여 준다. 스크립트가 없으면 최신 강의가 보인다.
- **검색·필터:** 기존 홈 검색(제목·설명·태그·핵심 주장·상세 요약 본문, 검색된 문맥 표시)과 주제 칩·북마크만·정렬(최신순·추가된순·조회수순, `?sort=`·localStorage)을 그대로 쓴다. 주제 칩에는 편수를 표시하지 않는다(벤토에만).
- **강의 목록:** PC 두 열(`minmax(420px,1fr)` 자동 채움), 모바일 한 열. 카드는 제목·한 줄 요약(두 줄)·주제·강연자·날짜·예상 읽기 시간, 오른쪽 위 책갈피, 메타 오른쪽 읽음 체크(둘 다 44px). 카드는 컨테이너 쿼리로 좁을 때 글자를 줄인다. 조회수 숫자는 표시하지 않는다.

## 4. 강의 상세
- 순서: 이동 경로 → 제목·메타(예상 읽기 시간·날짜·원본 길이·강연자·원본 영상)·읽음 표시 → 대표 이미지(있을 때) → 목차 띠 → 핵심 요약 → 상세 요약 → 타임스탬프 → 출처와 편집자 주(접힘) → 최근/지난 강의.
- **목차 띠(`.reading-nav`):** 헤더 아래 고정, 종이색 92% + 블러. 현재 섹션은 `--tint`. 앵커로 이동하면 섹션 위 선이 목차 아래 선과 겹친다(`--anchor-offset`).
- **핵심 요약:** 요점 묶음은 `--surface-1` 카드(lg 반경). 해볼 일 카드·인용 규칙은 `편집규칙.md` 19절.
- **상세 요약:** 소제목 목록은 기본 접힘 details, 핵심 문장 3~5곳에 강조 밑색, 소제목 위 가는 선과 첫 문단 조금 진하게.
- **타임스탬프:** 제목·`타임스탬프 복사`·원문(첫 네 줄 미리보기와 전체 보기)만 둔다. 영상 임베드와 타임라인 막대는 없다(2026-11-23 사용자 요청). 원문 줄은 링크가 아니다.
- **문서 간 전환:** `@view-transition{navigation:auto}`. 홈에서 누른 카드 제목에만 JS가 `view-transition-name:lecture-title`을 붙이고 상세 제목은 CSS로 같은 이름이라, 제목이 이어지듯 옮겨 간다. 동작 줄이기에서는 끈다. Chromium 126+·Safari 18.2+만 보인다.

### 강의 대표 이미지 (2026-11-21 사용자 요청)
- `lectures.json`의 `image`(`src`·`alt`·`width`·`height`)가 있는 강의에만 제목 아래 한 장(`figure.lecture-hero`). 홈 카드에는 넣지 않는다.
- 파일은 `assets/lectures/<강의 id>.jpg`, 450KB 이하 JPEG, 폭 1600px 안팎. AI 티가 나지 않는 사진 느낌, 글자·인물 얼굴·과한 빛 연출 금지.
- 표시 비율은 PC 2:1, 모바일 21:9(`object-fit:cover`). 390px에서 높이 약 155px라 핵심 요약 첫 항목이 첫 화면에 들어온다.
- 서비스 워커가 함께 사전 캐시한다. `tests/test_lecture_images.py`가 크기·alt·위치를 검사한다.

### 상세 요약 안 이미지 (2026-11-21 사용자 요청)
- 상세 요약 문단 사이 `{"image": {"src","alt","width","height","caption"}}`(`figure.detail-figure`, `lazy`). 문단의 비유나 장면을 보여 줄 때만 쓴다.
- 한 강의 최대 3장, `assets/lectures/<강의 id>-<이름>.jpg`, 450KB 이하, alt·캡션 120자 이하. 사진 규칙은 대표 이미지와 같다. 사전 캐시하지 않는다.

## 5. 공통 조작부 (글래스)
- 반투명은 헤더·하단 도구 막대·목차 시트·검색 팔레트에만 쓴다. 본문 면은 불투명하다. `prefers-reduced-transparency: reduce`면 네 곳 모두 불투명 면이다.
- **헤더:** 브랜드, `검색`(PC는 `/` 표시, 모바일은 아이콘만), `Aa 보기`(글자 크기 작게·보통·크게 = `--reading-scale` .92·1·1.14, 테마 시스템·라이트·다크). 설정은 이 기기에만 저장하고 렌더링 전 스크립트가 복원한다. 내려 읽으면 숨고 올리면 보인다(`html.header-hidden`).
- **하단 도구 막대(`nav.dock`, ‘빠른 이동’):** 강의는 목차·검색·보기·맨 위, 홈은 검색·보기·맨 위. 240px 넘게 내려가면 켜지고, 내려 읽는 동안(헤더 숨김)과 푸터가 보일 때는 비켜난다. 모바일은 화면 폭, PC는 가운데 알약. 버튼 52px 높이, 면색(`--surface`) 82% + 블러.
- **목차 시트(`dialog.outline-sheet`):** 섹션과 상세 요약 소제목을 한 목록으로. 링크를 누르면 닫힌다.
- **검색 팔레트(`dialog.search-sheet`):** `/`·Ctrl/⌘+K·헤더·하단 막대로 연다. `assets/search.js`는 처음 열 때 불러온다. 색인 `search-index.json`(`build_library.py` 생성, 제목·한 줄 요약·강연자·주제·태그·상세 요약 소제목, 50KB 상한)에서 찾고, 소제목이 맞으면 `#detail-N`으로 간다. ↑↓·Enter·Esc, 닫으면 연 버튼으로 초점이 돌아간다. 결과는 텍스트 노드로만 만든다. 모바일은 전체 화면.
- **읽기 진행 막대:** 헤더 아래 3px. `animation-timeline: scroll(root block)`이 그린다(위치 표시라 동작 줄이기에서도 유지). 미지원 브라우저만 JS가 `--p`를 넘긴다.

## 6. 공통 상호작용 계약
- 댓글 복사는 `data-copy-target`이 가리키는 원문 textContent만 복사한다. 성공: 버튼 ‘복사 완료 ✓’, 상태 ‘복사됨’, 2.2초 뒤 복원. 실패: 원문을 선택하고 ‘텍스트 선택됨’과 직접 복사 안내. 상태는 `role=status`·`aria-live=polite`.
- 북마크(`study-hub-bookmarks`)·읽음(`study-hub-read`)·이어 읽기(`study-hub-resume`, 마지막 미완독 강의의 소제목 한 곳)는 이 브라우저에만 저장한다. 서버 기록·로그인 없음.
- 오프라인: 서비스 워커가 공통 자산·강의 페이지·대표 이미지·`search.js?v=`·`search-index.json`을 사전 캐시한다. 페이지와 색인은 네트워크 우선, 버전이 붙은 자산은 그 버전의 사본만 쓴다. 색인을 못 받으면 팔레트가 오프라인·실패를 알린다.

## 7. 움직임
- 누르면 `scale(.92)`로 줄었다가 `--ease-spring`으로 돌아온다(북마크·읽음·복사·칩·하단 막대·타일 등). 애니메이션이 아니라 전환이라 저장된 상태가 페이지를 열 때 튀지 않는다.
- 상태 전환은 `--ease-standard`, 나타나는 조작부는 `--ease-emphasized`. 호버는 마우스 환경(`hover:hover and pointer:fine`)에서만.
- `prefers-reduced-motion: reduce`: 전환·누름 크기 변화·문서 간 전환을 끈다. 애니메이션은 transform과 opacity만 쓴다.

## 8. 접근성과 레이아웃 이동
- 터치 대상 44px 이상, 새 조작부의 키보드 초점은 3px `--focus-color` 테두리. 새 대화상자는 열면 초점이 안으로, 닫으면 원래 자리로.
- 대비: v16 면 12곳(벤토 타일, 핵심 요약 카드, 현재 목차 탭, 하단 막대, 검색 결과)을 라이트·다크에서 4.5:1 이상으로 검사한다(`tests/v16-chrome.spec.cjs`, 반투명 면은 종이색 위에 합성). 오늘의 한 문장·저장·읽음·선택·복사 색은 `tests/pwa.spec.cjs`가 검사한다.
- 레이아웃 이동 0: 스크립트가 나중에 켜는 요소는 처음부터 자리를 잡는다. `읽음 표시`·`다른 문장 보기`·헤더 `검색`은 `[hidden]`일 때도 `display:inline-flex!important;visibility:hidden`이다(전역 `[hidden]{display:none!important}`를 이기려면 `!important`가 필요하다). 오늘의 한 문장은 문장 3줄(`min-height:3lh`)·출처 2줄 높이를 미리 잡는다.

## 9. 줄바꿈
- 본문·제목·목록은 `word-break:break-all`로 글자 단위 줄바꿈을 허용한다(2026-11-21 사용자 요청, iPhone에서 단어 단위 줄바꿈이 오른쪽 여백을 크게 남겼다). `text-wrap:pretty·balance`는 끈다.
- 예외(단어 단위): 버튼·칩·목차·헤더·푸터·메타 등 UI, 벤토 타일, 검색 결과. 타임스탬프 원문(`pre`)은 `keep-all`이라 원문과 복사 결과가 그대로다.

## 10. 측정 기준 (`tests/design-metrics.spec.cjs`)
- 390×844: 홈 첫 화면 행선지 링크 6개 이상, 오늘의 한 문장 첫 화면 안, 상세 핵심 요약 첫 항목 첫 화면 안.
- 레이아웃 이동(CPU 4배 감속, 3초) 0.01 미만(홈·고정 강의 두 편).
- 용량(원본 바이트): `site.js` 29,254 이하, 검색 색인 50KB 이하, 사전 캐시 총량 기준(1,808,331) 대비 110% 이내. `site.js`를 늘리려면 다른 곳을 줄이거나 지연 로드 파일에 둔다.
- 가로 넘침 0: 분기점 ±1px 16개 폭, 가로 모드, 200% 확대 상당, 글자 3단계 × 라이트·다크.

## 11. AI 변경 절차와 검증 증거
1. AGENTS.md → 편집규칙.md → 이 문서 → 저장소 스킬을 읽고 현행 레이아웃과 데이터 생성 경로를 확인한다.
2. 디자인은 `assets/site.css`의 v16 층에서만 바꾼다. 토큰을 바꾸면 이 문서와 `validate_design_system.py`를 같은 PR에서 고친다.
3. 로컬 검사: `python3 scripts/build_all.py --check --tests`와 `bash scripts/pw_local.sh`.
4. PR의 네 항목: 변경 범위 / 영향 기능 / 검증 증거 / 남은 위험. CI `quality`·`browser`를 확인한다(main 푸시에서는 WebKit도 돈다).
5. 브라우저 자동화는 실물 아이폰 Safari 검사의 대체물이 아니다. 검증하지 않은 환경은 미검증으로 적는다.

## 12. 변경 금지와 예외
- UI 작업 때 강의 텍스트·원자료·영상 시각·원문 댓글을 의도 없이 고치지 않는다.
- 과거 레이아웃(옛 목차 버튼, 영상 임베드, 타임라인 막대, 학습 기록 화면 등)은 사용자 요청 없이 되살리지 않는다.
- 새 규칙은 기존 규칙과 중복·충돌하지 않는지 확인하고 AGENTS.md, 편집규칙.md, 스킬, 테스트 중 필요한 곳을 함께 고친다.

## 13. 한국어 화면 문구
- 간결하고 자연스러운 한국어. UI는 짧은 명사구, 해설은 자연스러운 완결문. 모든 문장을 ‘~한다/~이다’로 끝내도록 강제하지 않는다.
- 상태는 바로 이해되게 쓴다(‘불러오는 중’, ‘검색 결과가 없습니다.’). 홈과 팔레트는 같은 표현을 쓴다(결과 수 ‘N개 강의’).
- 학습 콘텐츠의 연구·인과·한계·출처는 스타일을 이유로 지우지 않는다. 세부 기준은 편집규칙.md의 ‘한국어 문체와 화면 문구’.
