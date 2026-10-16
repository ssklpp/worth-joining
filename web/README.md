# web

다닐만한가 프론트엔드(Next.js App Router). 화면 구성은 SPEC 9장, 모양은 [docs/03_ui_design.md](../docs/03_ui_design.md)를 따른다.

```bash
npm install
npm run dev          # http://localhost:3000 (API는 http://localhost:8000에 띄워 둔다)
npm run lint
npm run typecheck
npm run build
npm run gen:api      # API 계약이 바뀌면: FastAPI OpenAPI → lib/api/openapi.json · schema.d.ts (저장소 루트 .venv · .env 필요)
```

- API 주소는 `NEXT_PUBLIC_API_BASE_URL`(기본 `http://localhost:8000`). 로컬에서 바꾸려면 `web/.env.local`에 둔다.
- 데이터는 브라우저에서 불러온다(`lib/api.ts`의 `useApi`). 데이터 영역마다 로딩 · 오류(다시 시도) 상태를 둔다.
- 색은 `app/globals.css`의 토큰만 쓴다. 컴포넌트에 색을 직접 쓰지 않는다.
- API 타입(`lib/api/schema.d.ts`)은 직접 고치지 않는다.

## 화면 테스트 (Playwright, `e2e/`)

```bash
npm run test:e2e          # smoke 8개. 저장된 API 응답(e2e/api/*.json)으로 돈다. DB · API · 지도 키 필요 없음(CI와 같음)
npm run test:e2e:map      # 지도 2개(첫 화면 목록 · 역 반경 원). 로컬 API(:8000)와 지도 키(.env.local)가 있어야 한다
npm run test:e2e:record   # 로컬 API에 붙어 e2e/api/*.json을 다시 저장한다
npx playwright show-trace test-results/<테스트>/trace.zip   # 실패한 테스트를 한 단계씩 다시 본다
```

- 로컬은 떠 있는 개발 서버(:3000)와 설치된 Edge를 쓴다. CI는 빌드한 앱과 Chromium을 쓰고, 실패하면 `playwright-report`를 결과물로 올린다.
- **녹화를 다시 할 때:** 화면이 부르는 API가 바뀌었거나(새 파라미터 · 새 요청) 응답 형식이 바뀌었을 때. 바뀐 JSON을 코드와 같은 PR로 커밋한다. 저장된 파일이 없는 요청은 끊기므로(abort) 빠뜨리면 테스트가 실패해서 알 수 있다.
- **요소는 역할과 이름으로 찾는다**(`getByRole("button", { name: "비교에 담기" })`). 화면 문구를 바꾸면 테스트도 같이 고친다. 접근성 이름을 함께 검사하는 효과가 있다.
- **개발 서버(`npm run dev`)가 떠 있을 때 `npm run build`를 하지 않는다.** 같은 `.next`를 덮어써 개발 서버 화면이 깨진다. 운영 빌드로 확인하려면 다른 폴더(worktree)에서 빌드하고 `E2E_PORT=3100`으로 돌린다.
- 지도 핀(`/map/companies`)은 지도 범위마다 주소가 달라 smoke에서는 끊고, 지도 동작은 `map.spec.ts`가 본다.
