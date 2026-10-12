import { Suspense } from "react";
import { Loading } from "@/components/Status";
import { Search } from "./Search";

export default function Home() {
  return (
    <div className="page">
      <Suspense fallback={<Loading height={200} />}>
        <Search />
      </Suspense>
    </div>
  );
}
