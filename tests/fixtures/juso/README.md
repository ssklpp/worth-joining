# juso fixture

주소정보누리집 검색 API(`addrLinkApi.do`) · 좌표제공 API(`addrCoordApi.do`)의 JSON 응답 샘플. 가상 주소다.
개발자센터 문서의 응답 형식으로 만들었으므로, 키를 받으면 실제 응답 한 건과 필드 이름을 대조한다(troubleshooting TS-018).

`rnaddrkor_sample.txt`: "도로명주소 한글" 파일(CP949, `|` 24열) 형식의 가상 건물 5행과 깨진 행 1행. 같은 이름의 도로(가상로)가 다른 자치구에도 있다.

`RNENTDATA_2610_11000.txt`: "도로명주소 출입구" 파일(CP949, `|` 19열) 형식. 위 건물과 같은 건물관리번호에 가상 UTM-K 좌표를 붙였고, 다른구 건물은 좌표가 비어 있다.

`rnaddrkor_gyunggi.txt` · `RNENTDATA_2610_41000.txt`: 같은 형식의 성남시 분당구 가상 건물 2행(decisions/010). 지역별 파일 쌍(`rnaddr.REGION_FILES`)을 읽는지 확인한다.
