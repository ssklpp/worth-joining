// FastAPI의 OpenAPI 문서를 서버 없이 뽑아 lib/api/openapi.json으로 두고 TypeScript 타입을 만든다.
// 사용: npm run gen:api (저장소 루트의 .venv와 .env가 필요하다. API 계약이 바뀌면 다시 실행해 커밋한다)
import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";
import { join } from "node:path";
import openapiTS, { astToString } from "openapi-typescript";

const web = join(import.meta.dirname, "..");
const root = join(web, "..");
const python = process.platform === "win32"
  ? join(root, ".venv", "Scripts", "python.exe")
  : join(root, ".venv", "bin", "python");
const spec = execFileSync(python, ["-c",
  "import json, app.main as m; print(json.dumps(m.app.openapi(), ensure_ascii=False, indent=1))"],
  { cwd: root, encoding: "utf8", env: { ...process.env, PYTHONIOENCODING: "utf-8" } });
writeFileSync(join(web, "lib", "api", "openapi.json"), spec);
const header = "// npm run gen:api 로 만든 파일이다. 직접 고치지 않는다.\n";
writeFileSync(join(web, "lib", "api", "schema.d.ts"), header + astToString(await openapiTS(JSON.parse(spec))));
console.log("lib/api/openapi.json, lib/api/schema.d.ts");
