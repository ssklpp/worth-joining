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
