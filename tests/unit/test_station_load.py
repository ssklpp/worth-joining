"""역 적재기 (SPEC Phase 9-1, decisions/007). 가상 역 · 좌표."""

import pandas as pd
import pytest
from sqlalchemy import text

from pipeline.stations import load as st

SEOUL = "서울특별시 가상구 가상로 1"


def frame(rows):
    """(역사명, 노선명, 위도, 경도, 주소) → 표준데이터와 같은 열 이름의 DataFrame."""
    return pd.DataFrame(rows, columns=["역사명", "노선명", "역위도", "역경도", "역사도로명주소"],
                        dtype=str)


def stations(rows, locate=None):
    parsed, dropped = st.read_rows(frame(rows), locate)
    found = st.distinguish([st.station_of(g) for g in st.cluster(parsed)])
    return {s["key"]: s for s in found}, dropped


@pytest.mark.parametrize("name, base, names", [
    ("용산역", "용산", {"용산"}),
    ("총신대입구(이수)", "총신대입구", {"총신대입구", "이수"}),
    ("신촌(지하)", "신촌", {"신촌", "지하"}),
    ("역삼", "역삼", {"역삼"}),  # 두 글자는 "역"을 떼지 않는다
])
def test_names(name, base, names):
    assert st.base_name(name) == base
    assert st.aliases(name) == names


def test_line_label_drops_operator_prefix():
    assert st.line_label("수도권  도시철도 9호선") == "9호선"
    assert st.line_label("서울 도시철도 9호선") == "9호선"


def test_transfer_rows_become_one_station_and_far_namesakes_stay_apart():
    result, dropped = stations([
        ("교대", "2호선", "37.4934", "127.0140", SEOUL),
        ("교대", "3호선", "37.4937", "127.0146", SEOUL),
        ("이수", "7호선", "37.4855", "126.9817", SEOUL),
        ("총신대입구(이수)", "4호선", "37.4870", "126.9820", SEOUL),
        ("신촌(지하)", "2호선", "37.5551", "126.9369", SEOUL),
        ("신촌역", "경의중앙선", "37.5598", "126.9425", SEOUL),  # 약 700m
        ("서울역", "1호선", "37.5547", "126.9707", SEOUL),
        ("서울", "인천국제공항선", "37.5545", "126.9700", SEOUL),
        ("부산역", "1호선", "35.1150", "129.0410", "부산광역시 동구 중앙대로 206"),  # 서울 아님
    ])

    assert dropped == 0
    assert result["교대"]["lines"] == "2호선,3호선"
    assert result["교대"]["lat"] == pytest.approx(37.49355)
    assert result["이수"]["lines"] == "4호선,7호선"  # 괄호 안 이름으로 묶인다
    assert {"신촌(2호선)", "신촌(경의중앙선)"} <= result.keys()
    assert result["서울"]["name"] == "서울역"
    assert len(result) == 5


def test_coordinate_outside_seoul_is_fixed_by_address_or_dropped():
    wrong = [("양원역", "경의중앙선", "36.9637", "129.0913", "서울시 중랑구 송림길 147(망우동)")]
    asked = []

    def locate(keyword):
        asked.append(keyword)
        return 127.1, 37.6

    fixed, _ = stations(wrong, locate)
    gone, dropped = stations(wrong)

    assert asked == ["서울특별시 중랑구 송림길 147"]
    assert (fixed["양원"]["lon"], fixed["양원"]["lat"]) == (127.1, 37.6)
    assert gone == {} and dropped == 1


@pytest.fixture
def engine(pipeline_engine):
    yield pipeline_engine
    with pipeline_engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE station"))
        conn.execute(text("DELETE FROM ingestion_log WHERE source = 'station'"))


def test_run_loads_skips_same_file_and_keeps_ids(engine, tmp_path):
    path = tmp_path / "stations.xlsx"
    frame([("교대", "2호선", "37.4934", "127.0140", SEOUL)]).to_excel(path, index=False)

    assert st.run(engine, path, None) == "success"
    assert st.run(engine, path, None) == "skipped"
    frame([("교대", "2호선", "37.4934", "127.0140", SEOUL),
           ("교대", "3호선", "37.4937", "127.0146", SEOUL)]).to_excel(path, index=False)
    with engine.connect() as conn:
        first_id = conn.execute(text("SELECT station_id FROM station")).scalar()
    assert st.run(engine, path, None) == "success"

    with engine.connect() as conn:
        row = conn.execute(text(
            "SELECT station_id, station_name, line_names, ST_X(pt), ST_Y(pt) FROM station")).one()
    assert row[:3] == (first_id, "교대", "2호선,3호선")
    assert (round(row[3], 5), round(row[4], 5)) == (127.0143, 37.49355)
