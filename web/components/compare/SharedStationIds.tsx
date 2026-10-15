"use client";

// /stations/compare?ids=1,2,3 으로 열면 그 역들을 역 비교함에 담는다(회사 SharedIds와 같은 방식)
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect } from "react";
import { getJson, type Schemas } from "@/lib/api";
import { useStationCompare } from "@/lib/compare";
import { stationLabel } from "@/lib/format";

export function SharedStationIds() {
  const params = useSearchParams();
  const router = useRouter();
  const { replace } = useStationCompare();
  const ids = params.get("ids");

  useEffect(() => {
    if (!ids || !/^\d+(,\d+){0,2}$/.test(ids)) return;
    Promise.all(ids.split(",").map((id) => getJson<Schemas["StationDetail"]>(`/stations/${id}/rent`)))
      .then((list) => replace(list.map((d) => ({ id: d.station_id, name: stationLabel(d.name) }))))
      .catch(() => undefined) // 없는 역이 섞인 링크면 지금 역 비교함을 그대로 둔다
      .finally(() => router.replace("/stations/compare"));
  }, [ids, replace, router]);

  return null;
}
