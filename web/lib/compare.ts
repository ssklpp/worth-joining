"use client";

// 비교함(최대 3곳). 브라우저 저장소에 두어 페이지를 옮겨도 남고, 다른 탭의 변경도 따라간다.
// 저장소를 쓸 수 없으면(사생활 보호 모드 등) 이 탭 안에서만 유지한다.
import { useSyncExternalStore } from "react";

export const MAX_COMPARE = 3;
const KEY = "worth-joining.compare";

export type CompareItem = { id: number; name: string };

const EMPTY: CompareItem[] = [];
let items: CompareItem[] | null = null;
const listeners = new Set<() => void>();

function read(): CompareItem[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(KEY) ?? "[]");
    return Array.isArray(parsed)
      ? parsed.filter((i) => Number.isInteger(i?.id) && typeof i?.name === "string").slice(0, MAX_COMPARE)
      : [];
  } catch {
    return [];
  }
}

function write(next: CompareItem[]) {
  items = next;
  try {
    localStorage.setItem(KEY, JSON.stringify(next));
  } catch {
    // 저장하지 못해도 이 탭에서는 계속 쓴다
  }
  listeners.forEach((l) => l());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  const onStorage = (e: StorageEvent) => {
    if (e.key === KEY) {
      items = read();
      listener();
    }
  };
  window.addEventListener("storage", onStorage);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", onStorage);
  };
}

function snapshot() {
  if (items === null) items = read();
  return items;
}

function replace(next: CompareItem[]) {
  write(next.slice(0, MAX_COMPARE));
}

export function useCompare() {
  const list = useSyncExternalStore(subscribe, snapshot, () => EMPTY);
  return {
    items: list,
    full: list.length >= MAX_COMPARE,
    has: (id: number) => list.some((i) => i.id === id),
    add: (item: CompareItem) => {
      const now = snapshot();
      if (now.length < MAX_COMPARE && !now.some((i) => i.id === item.id)) write([...now, item]);
    },
    remove: (id: number) => write(snapshot().filter((i) => i.id !== id)),
    clear: () => write([]),
    replace,
  };
}
