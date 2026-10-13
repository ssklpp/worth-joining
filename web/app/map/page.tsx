import { redirect } from "next/navigation";

// 지도는 첫 화면이 되었다(decisions/006). 예전 /map 링크는 첫 화면으로 보낸다
export default function MapPage() {
  redirect("/");
}
