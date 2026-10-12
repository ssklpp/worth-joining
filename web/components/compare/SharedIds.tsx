"use client";

// /compare?ids=1,2,3 으로 열면 그 회사들을 비교함에 담는다(SPEC Phase 8-9 비교 상태 URL 공유)
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect } from "react";
import { getJson, type Schemas } from "@/lib/api";
import { MAX_COMPARE, useCompare } from "@/lib/compare";

export function SharedIds() {
  const params = useSearchParams();
  const router = useRouter();
  const { replace } = useCompare();
  const ids = params.get("ids");

  useEffect(() => {
    if (!ids || !/^\d+(,\d+){0,2}$/.test(ids)) return;
    getJson<Schemas["CompareResult"]>(`/compare?ids=${ids}`)
      .then((r) => replace(r.items.slice(0, MAX_COMPARE).map((i) => ({ id: i.company_id, name: i.name }))))
      .catch(() => undefined) // 없는 회사가 섞인 링크면 지금 비교함을 그대로 둔다
      .finally(() => router.replace("/compare"));
  }, [ids, replace, router]);

  return null;
}
