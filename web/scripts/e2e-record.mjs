// smoke 테스트의 API 응답(e2e/api/*.json)을 다시 녹화한다. 로컬 API(:8000)와 개발 서버(:3000)가 떠 있어야 한다.
// 화면이 부르는 API나 응답이 바뀌면 실행하고, 바뀐 JSON을 함께 커밋한다(web/README.md "화면 테스트")
import { spawnSync } from "node:child_process";

const r = spawnSync("npx", ["playwright", "test", "--project=smoke", ...process.argv.slice(2)], {
  stdio: "inherit",
  shell: true,
  env: { ...process.env, E2E_RECORD: "1" },
});
process.exit(r.status ?? 1);
