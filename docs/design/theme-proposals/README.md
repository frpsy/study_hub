# Material 3 테마 색상 비교와 선택

2026-11-25. 같은 콘텐츠와 레이아웃에서 세 후보를 비교했다. A안 Google 블루를 확정했다.

후속 반영: 사용자 피드백에 따라 실제 배포 책 아이콘도 #0b57d0 / #d3e3fd로 통일했다. 아래 비교 이미지는 아이콘을 보라색으로 유지했던 테마 선택 당시의 기록이다.

| 후보 | 라이트 primary | 다크 primary | 판단 |
|---|---|---|---|
| **A · Google 블루 (선택)** | #0b57d0 | #a8c7fa | Google 서비스에서 익숙한 조작 색이다. 보라색 아이콘을 브랜드 색으로 남기고, 링크·진행·포커스·선택 상태를 같은 차가운 계열로 묶을 수 있다. |
| B · Material 바이올렛 | #6750a4 | #d0bcff | 아이콘과 가장 직접적으로 일치한다. 브랜드 일체감은 좋지만, 사용자에게 익숙한 Google 블루 조작 색을 우선했다. |
| C · 차분한 틸 | #006a6a | #80d5d3 | 명상·휴식의 인상에 어울린다. 보라색 아이콘과의 색상 차이가 더 커 선택하지 않았다. |

가장 사용자 친화적인 색을 보편적인 순위로 단정하지 않았다. 익숙한 조작 색, 상태의 일관성, 실제 텍스트 대비, 기존 아이콘과의 조화를 이 사이트의 판단 기준으로 삼았다.

## 비교 시안

실제 홈과 상세 페이지를 390px 폭, 같은 문장과 저장·읽음 상태로 촬영했다. 비교용으로만 후보 색을 주입했으며, 배포 CSS에는 A안만 적용한다.

- [라이트 비교](preview-light.png)
- [다크 비교](preview-dark.png)

## 적용 범위

읽기 진행 막대, 링크·목차, 복사 버튼, 포커스, 글자 선택, 저장·읽음, 주제 선택, 오늘의 한 문장의 링크·면을 공통 역할로 맞췄다. 아이콘과 콘텐츠, 카드 높이·배치는 유지했다. 라이트·다크의 primary/on-primary와 container/on-container를 별도로 지정했다.

브라우저 회귀 검사는 다음을 확인한다.

- 홈의 링크·저장·읽음과 상세의 진행 막대·복사 버튼이 같은 primary를 쓴다.
- 두 테마의 주요 글자와 조작 상태에서 실제 전경/배경 대비가 4.5:1 이상이다.
- 키보드 포커스는 같은 primary로 표시한다.
- 전체 53개 브라우저 검사와 정적 검사를 실행하며, 최종 결과는 PR 검증 기록에 남긴다.

## 공식 근거와 해석 범위

- [Google 공식 버튼 사양](https://developers.google.com/identity/gsi/web/reference/html-reference): 현재 blue-filled 버튼에 #0B57D0을 명시한다. 이 사이트에는 로그인 기능을 추가하지 않았다. 색상 사용 근거로만 참고했다.
- [Material 3 색상 역할](https://m3.material.io/styles/color/the-color-system): primary·container·각 on-color를 역할에 따라 함께 사용하는 원칙을 참고했다.
- [Google Workspace의 Material 3 전환](https://workspaceupdates.googleblog.com/2023/03/refreshed-ui-google-drive-docs-sheets-slides.html): 여러 제품의 익숙한 Material UI를 참고한 근거다. 2023년의 전환 기록이며 색상별 점유율 통계가 아니다.

Google 전체의 색상별 사용 빈도 통계는 확인하지 못했으므로 ‘가장 많이 사용되는 색’이라고 단정하지 않는다. 익숙한 Google 블루와 실측 접근성을 근거로 선택했다. container·surface의 구체적인 조합은 이 사이트를 위해 정한 테마이며 Google 모든 제품의 공통 팔레트라는 뜻이 아니다.
