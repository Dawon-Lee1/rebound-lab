# 프로젝트 규칙 (Claude Code용)

## 프로젝트
- 2027 판타지 베이스볼 드래프트용 타자 반등·거품 분석 사이트 (영어, 미국 사용자 대상)
- 지표: proj = (PA*(w*xwOBA + (1-w)*wOBA) + k*리그평균wOBA) / (PA + k), Rebound Score = proj - wOBA = luck + regression
  - luck = PA*w*(xwOBA - wOBA)/(PA+k), regression = k*(리그평균 - wOBA)/(PA+k)
  - 공식은 analysis/model.py 한 곳에만 둔다. w, k는 04_projection.py가 내년 wOBA RMSE로 골라 analysis/results/model_params.json에 저장
- 구조: analysis/ 파이썬 → site/src/data/players.json → Astro 정적 사이트 → Cloudflare Pages
- 마감: 2026-11-30 배포 + Google Search Console 사이트맵 제출

## 저장 규칙
- 코드는 이 저장소(C:\dev\rebound-lab)에, 문서는 OneDrive 폴더(C:\Users\wild8_v9xjmev\OneDrive\바탕 화면\웹사이트 포트폴리오 도전기\docs)에 저장한다
- 작업을 마칠 때마다 C:\Users\wild8_v9xjmev\OneDrive\바탕 화면\웹사이트 포트폴리오 도전기\docs\진행로그\YYYY-MM-DD.md에 한 일, 결정, 다음 할 일을 3~5줄로 추가한다
- 중요한 방향 결정은 C:\Users\wild8_v9xjmev\OneDrive\바탕 화면\웹사이트 포트폴리오 도전기\docs\결정기록.md에 날짜와 이유를 남긴다

## 제약
- 비용 0원. 유료 API, 유료 호스팅 사용 금지
- 로그인, 쿠키, 개인정보 수집 없음 (분석은 Cloudflare Web Analytics만)
- 투구·타구 단위 원본 데이터와 일괄 다운로드 기능(CSV 버튼 등) 금지. 화면 설명에 필요한 시즌 합계 지표만 소수 3자리로 표시하고, 모든 페이지에 'Data: Baseball Savant' 출처 표기
- 선수 사진, 구단·리그 로고 사용 금지. 글꼴은 OFL 라이선스만
- 베팅·상금 콘테스트·스포츠베팅 제휴 링크 금지
- WCAG 2.1 AA (대비 4.5:1, 키보드 이동, alt 텍스트)
- 근거 없는 성능 주장 금지: 숫자는 백테스트 결과에서만

## 작업 방식
- 새 기능은 superpowers로 계획 먼저, 코드는 그다음
- 기능 하나가 끝나면 /code-review 실행
- 답변과 문서는 한국어, 사이트 화면 문구는 영어
