// 모든 추정치 옆의 "추정" 표기와 툴팁(SPEC 9장 공통)
const SALARY = "국민연금 소득 상한 때문에 실제보다 낮게 나올 수 있는 하한 추정치입니다.";

export function Estimate({ text = SALARY }: { text?: string }) {
  return (
    <abbr title={text} style={{ textDecoration: "underline dotted", cursor: "help", fontStyle: "normal" }}>
      추정
    </abbr>
  );
}
