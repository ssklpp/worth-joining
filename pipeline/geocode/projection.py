"""EPSG:5179(UTM-K, GRS80 횡메르카토르) → EPSG:4326(경도, 위도).

SPEC은 pyproj로 변환하도록 정했다. 이 PC처럼 pyproj의 DLL이 응용 프로그램 제어 정책에
막히면(troubleshooting TS-021) 같은 투영의 역변환 공식(Snyder, Map Projections 1987,
식 8-12 ~ 8-25)으로 계산한다. 두 결과가 같은지는 CI(pyproj 동작)의 테스트가 확인한다.
"""

import math

# EPSG:5179: GRS80, 원점 위도 38°, 중앙 경선 127.5°, 축척 0.9996, 가산값 E 1e6 · N 2e6
A = 6378137.0
F = 1 / 298.257222101
K0 = 0.9996
LAT0 = math.radians(38.0)
LON0 = math.radians(127.5)
FE, FN = 1_000_000.0, 2_000_000.0

E2 = F * (2 - F)
EP2 = E2 / (1 - E2)


def _meridian(phi: float) -> float:
    e4, e6 = E2 * E2, E2 ** 3
    return A * ((1 - E2 / 4 - 3 * e4 / 64 - 5 * e6 / 256) * phi
                - (3 * E2 / 8 + 3 * e4 / 32 + 45 * e6 / 1024) * math.sin(2 * phi)
                + (15 * e4 / 256 + 45 * e6 / 1024) * math.sin(4 * phi)
                - (35 * e6 / 3072) * math.sin(6 * phi))


M0 = _meridian(LAT0)


def utmk_to_wgs84_formula(x: float, y: float) -> tuple[float, float]:
    """(경도, 위도). 한반도 범위에서 pyproj와 1cm 안으로 같다."""
    m = M0 + (y - FN) / K0
    mu = m / (A * (1 - E2 / 4 - 3 * E2 ** 2 / 64 - 5 * E2 ** 3 / 256))
    e1 = (1 - math.sqrt(1 - E2)) / (1 + math.sqrt(1 - E2))
    phi1 = (mu + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * math.sin(2 * mu)
            + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * math.sin(4 * mu)
            + (151 * e1 ** 3 / 96) * math.sin(6 * mu)
            + (1097 * e1 ** 4 / 512) * math.sin(8 * mu))
    sin1, cos1, tan1 = math.sin(phi1), math.cos(phi1), math.tan(phi1)
    c1, t1 = EP2 * cos1 ** 2, tan1 ** 2
    n1 = A / math.sqrt(1 - E2 * sin1 ** 2)
    r1 = A * (1 - E2) / (1 - E2 * sin1 ** 2) ** 1.5
    d = (x - FE) / (n1 * K0)
    lat = phi1 - (n1 * tan1 / r1) * (
        d ** 2 / 2
        - (5 + 3 * t1 + 10 * c1 - 4 * c1 ** 2 - 9 * EP2) * d ** 4 / 24
        + (61 + 90 * t1 + 298 * c1 + 45 * t1 ** 2 - 252 * EP2 - 3 * c1 ** 2) * d ** 6 / 720)
    lon = LON0 + (
        d - (1 + 2 * t1 + c1) * d ** 3 / 6
        + (5 - 2 * c1 + 28 * t1 - 3 * c1 ** 2 + 8 * EP2 + 24 * t1 ** 2) * d ** 5 / 120
    ) / cos1
    return math.degrees(lon), math.degrees(lat)


try:
    from pyproj import Transformer

    _TO_WGS84 = Transformer.from_crs(5179, 4326, always_xy=True)

    def utmk_to_wgs84(x: float, y: float) -> tuple[float, float]:
        return _TO_WGS84.transform(x, y)

    BACKEND = "pyproj"
except ImportError:  # TS-021
    utmk_to_wgs84 = utmk_to_wgs84_formula
    BACKEND = "formula"
