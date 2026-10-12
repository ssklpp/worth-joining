// API 클라이언트. 타입은 FastAPI의 /openapi.json에서 만든다(npm run gen:api).
"use client";

import { useCallback, useEffect, useState } from "react";
import type { components } from "./api/schema";

export type Schemas = components["schemas"];

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(API_BASE + path, { signal });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, typeof body.detail === "string" ? body.detail : res.statusText);
  }
  return res.json() as Promise<T>;
}

export type ApiState<T> =
  | { status: "loading" }
  | { status: "error"; error: ApiError | Error; retry: () => void }
  | { status: "ok"; data: T };

/** 데이터 영역마다 로딩 · 오류(다시 시도) 상태를 갖게 한다(SPEC 9장 공통). path가 null이면 부르지 않는다 */
export function useApi<T>(path: string | null): ApiState<T> {
  const [state, setState] = useState<ApiState<T>>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);
  const retry = useCallback(() => setAttempt((n) => n + 1), []);

  useEffect(() => {
    if (path === null) return;
    const controller = new AbortController();
    setState({ status: "loading" });
    getJson<T>(path, controller.signal)
      .then((data) => setState({ status: "ok", data }))
      .catch((error) => {
        if (!controller.signal.aborted) setState({ status: "error", error, retry });
      });
    return () => controller.abort();
  }, [path, attempt, retry]);

  return state;
}
