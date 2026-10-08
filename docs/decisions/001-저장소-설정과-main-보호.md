# 001. 저장소 설정과 main 보호

| 항목 | 내용 |
|---|---|
| 상태 | 채택 · 2026-10-08 |
| 관련 | SPEC 0장 · 12.3, NFR-COL-01, T3-01 · T3-02 |

## 배경

SPEC 12.3은 `main`을 보호하고 PR 승인 1명 이상, CI 통과, squash merge를 요구한다. 지금은 팀원이 합류하기 전이고 CI도 없어서 이 조건을 그대로 걸면 아무것도 병합할 수 없다.

## 결정

목표 규칙(SPEC 12.3)은 바꾸지 않고, 저장소 설정을 단계적으로 올린다.

**현재 설정 (2026-10-08 적용)**

| 위치 | 설정 |
|---|---|
| Settings → Rules → Rulesets `main 보호` | 기본 브랜치 대상, Bypass 없음. 삭제 금지, force push 금지, PR 필수(승인 0명, 병합 방식 squash만) |
| Settings → General → Pull Requests | squash merge만 허용, 커밋 제목 = PR 제목(본문 비움), 병합 후 head 브랜치 자동 삭제 |

**단계**

| 시점 | 바꿀 설정 |
|---|---|
| T3-02 CI 병합 후 | ruleset에 Require status checks 추가(CI 작업 이름 지정) |
| 팀원 합류 후 | 승인 1명, CODEOWNERS 리뷰 필수. 관리자 우회 여부는 팀이 정한다 |

## 결과

- `main`에는 PR로만 들어간다. 직접 push는 GitHub가 거부한다(`GH013`).
- PR 하나가 `main`의 커밋 하나가 되므로 PR 제목이 Conventional Commits 형식을 지켜야 한다.
- 승인 0명 단계에서는 리뷰 없이 병합할 수 있다. 팀원 합류 전까지만 허용한다.
