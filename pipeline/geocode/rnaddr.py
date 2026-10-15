"""주소정보누리집 서울 건물 파일 → 건물마다 주소 · 출입구 좌표
(decisions/004 3 · 4단계, decisions/007).

두 파일을 건물관리번호(첫 열)로 붙인다. 둘 다 CP949, '|' 구분, 머리글 없음.
- 도로명주소 한글(rnaddrkor_seoul.txt, 24열): 1 건물관리번호, 2 법정동코드, 7 산여부,
  8 · 9 지번 본번 · 부번, 11 도로명
- 도로명주소 출입구(RNENTDATA_YYMM_11000.txt, 19열): 1 건물관리번호, 18 · 19 출입구 X · Y(EPSG:5179)
좌표는 출입구 파일에서만 얻는다(juso 제공 좌표, SPEC 4장). 좌표가 빈 건물은 뺀다.
"""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

from pipeline.geocode.projection import utmk_to_wgs84

ADDRESS_PATH = Path("data/raw/juso/rnaddrkor_seoul.txt")
ENTRANCE_GLOB = "RNENTDATA_*_11000.txt"
ADDRESS_COLUMNS, ENTRANCE_COLUMNS = 24, 19


@dataclass(frozen=True)
class Building:
    mgmt_no: str  # 건물관리번호
    adm_cd: str  # 법정동코드 10자리
    road: str
    mountain: bool  # 지번이 산
    lot_main: int  # 지번 본번
    lot_sub: int
    lon: float
    lat: float

    @property
    def sgg(self) -> str:
        """시군구 코드 5자리(법정동코드 앞 5자리)."""
        return self.adm_cd[:5]


def entrance_path(folder: Path = ADDRESS_PATH.parent) -> Path | None:
    """가장 최근 출입구 파일(이름의 YYMM이 큰 것)."""
    found = sorted(folder.glob(ENTRANCE_GLOB))
    return found[-1] if found else None


def read_entrances(lines: Iterable[str]) -> dict[str, tuple[float, float]]:
    """건물관리번호 → (경도, 위도)."""
    points = {}
    for line in lines:
        f = line.rstrip("\r\n").split("|")
        if len(f) == ENTRANCE_COLUMNS and f[17] and f[18]:
            lon, lat = utmk_to_wgs84(float(f[17]), float(f[18]))
            points[f[0]] = (round(lon, 7), round(lat, 7))
    return points


def read(address_lines: Iterable[str], points: dict[str, tuple[float, float]]
         ) -> Iterator[Building]:
    """주소 행에 출입구 좌표를 붙인다. 열 수가 다르거나 좌표가 없는 건물은 건너뛴다."""
    for line in address_lines:
        f = line.rstrip("\r\n").split("|")
        if (len(f) != ADDRESS_COLUMNS or f[0] not in points
                or not (f[7].isdigit() and f[8].isdigit())):
            continue
        lon, lat = points[f[0]]
        yield Building(f[0], f[1], f[10], f[6] == "1", int(f[7]), int(f[8]), lon, lat)


def read_files(address: Path = ADDRESS_PATH, entrance: Path | None = None) -> Iterator[Building]:
    """주소 파일과 가장 최근 출입구 파일을 읽어 좌표가 있는 건물을 하나씩 낸다.
    출입구 파일이 없으면 FileNotFoundError.
    """
    entrance = entrance or entrance_path(address.parent)
    if entrance is None:
        raise FileNotFoundError(f"{address.parent}/{ENTRANCE_GLOB}이 없다(docs/runbook.md)")
    with entrance.open(encoding="cp949", errors="replace") as fh:
        points = read_entrances(fh)
    with address.open(encoding="cp949", errors="replace") as fh:
        yield from read(fh, points)
