import pytest

from pipeline.geocode.projection import utmk_to_wgs84_formula

# 서울 범위 UTM-K 좌표 몇 곳(가상의 점)
POINTS = [(1_000_000, 2_000_000), (953_000, 1_952_000), (960_500, 1_945_300), (935_000, 1_960_000),
          (970_000, 1_938_000)]


def test_origin_maps_to_projection_center():
    lon, lat = utmk_to_wgs84_formula(1_000_000, 2_000_000)

    assert lon == pytest.approx(127.5, abs=1e-9) and lat == pytest.approx(38.0, abs=1e-9)


def test_seoul_point_is_in_seoul():
    lon, lat = utmk_to_wgs84_formula(953_000, 1_952_000)

    assert 126.7 < lon < 127.2 and 37.4 < lat < 37.7


@pytest.mark.parametrize("x, y", POINTS)
def test_formula_matches_pyproj(x, y):
    pyproj = pytest.importorskip("pyproj", exc_type=ImportError,
                                 reason="이 PC는 pyproj DLL이 막혀 있다(TS-021). CI에서 확인한다")
    expected = pyproj.Transformer.from_crs(5179, 4326, always_xy=True).transform(x, y)

    # 1e-7도 ≈ 1cm
    assert utmk_to_wgs84_formula(x, y) == pytest.approx(expected, abs=1e-7)
