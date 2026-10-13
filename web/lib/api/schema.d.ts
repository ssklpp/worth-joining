// npm run gen:api 로 만든 파일이다. 직접 고치지 않는다.
export interface paths {
    "/companies": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * 회사 검색
         * @description 최신 월에 가입자가 있는 회사만 검색한다. 최근 자료 없는 회사는 결과에 없다(docs/05 A5).
         */
        get: operations["search_companies_companies_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/companies/{company_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * 회사 상세
         * @description 최근 자료 없음(stale)이면 id · name · as_of · status · flags · last_seen_ym만 준다.
         */
        get: operations["company_detail_companies__company_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/companies/{company_id}/trend": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 월별 추이 */
        get: operations["company_trend_companies__company_id__trend_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/companies/{company_id}/financials": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * 재무
         * @description DART와 연결된 회사만 rows가 있다. 연결되지 않았으면 dart null, rows [].
         */
        get: operations["company_financials_companies__company_id__financials_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/companies/{company_id}/housing": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * 회사 근처 역 주거비
         * @description 회사에서 1km 안의 역(최대 3곳)마다 원룸 시세와 주거비 부담률(시세 ÷ 추정 월급).
         *     회사 좌표가 대략 위치(도로 · 동 중심)면 approx_location: 거리와 역은 참고용이다.
         */
        get: operations["company_housing_companies__company_id__housing_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/compare": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * 회사 비교
         * @description 회사별 12개월 전 = 100 가입자 지수와 요약 지표. 없는 ID가 있으면 404.
         */
        get: operations["compare_compare_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/industries": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * 업종 목록
         * @description 회사가 있는 업종만, 회사 수가 많은 순.
         */
        get: operations["list_industries_industries_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/industries/{code}/distribution": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * 업종 내 분포
         * @description 표본 부족(가입자 10명 미만) 회사를 뺀 p25 · p50 · p75. 비율은 소수, 연봉은 원.
         */
        get: operations["industry_distribution_industries__code__distribution_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/map/companies": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * 지도 핀
         * @description 좌표가 있는 회사 중 가입자 많은 순 최대 200곳. 넘으면 truncated.
         */
        get: operations["map_companies_map_companies_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/meta/methodology": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 계산 방법 · 한계 · 출처 */
        get: operations["get_methodology_meta_methodology_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/health": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * 상태 확인
         * @description DB에 접속하지 못하면 500이다. latest_nps_ym이 null이면 mart가 비어 있다.
         */
        get: operations["health_health_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/stations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * 서울 역과 원룸 시세
         * @description 12개월 원룸 환산 월세 중앙값. 원룸 계약이 없는 역은 monthly_median null, n 0.
         */
        get: operations["list_stations_stations_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/stations/{station_id}/rent": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * 역 원룸 시세
         * @description 월세 계약이 20건 미만이면 24개월로 넓히고 period_extended_to_24m을 단다.
         */
        get: operations["station_rent_stations__station_id__rent_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** Burden */
        Burden: {
            /**
             * Low
             * @description 환산 월세 p25 ÷ 추정 월급
             */
            low: number | null;
            /**
             * Mid
             * @description 중앙값 ÷ 추정 월급
             */
            mid: number | null;
            /**
             * High
             * @description p75 ÷ 추정 월급
             */
            high: number | null;
        };
        /** CompanyDetail */
        CompanyDetail: {
            /** Company Id */
            company_id: number;
            /** Name */
            name: string;
            /**
             * As Of
             * @description 데이터 기준월 YYYYMM. 데이터가 없으면 null
             */
            as_of: number | null;
            /**
             * Status
             * @default ok
             * @enum {string}
             */
            status: "ok" | "stale";
            /** Flags */
            flags: ("salary_is_lower_bound" | "small_sample" | "short_history" | "stale" | "approx_location" | "name_matched" | "period_extended_to_24m")[];
            /**
             * Last Seen Ym
             * @description stale일 때 가입자가 있던 마지막 달
             */
            last_seen_ym?: number | null;
            industry?: components["schemas"]["Industry"] | null;
            region?: components["schemas"]["Region"] | null;
            /** Form Type */
            form_type?: ("corporation" | "individual") | null;
            /** Workplace Count */
            workplace_count?: number | null;
            /** Members */
            members?: number | null;
            /** Growth 12M */
            growth_12m?: number | null;
            /** Quit Rate 12M */
            quit_rate_12m?: number | null;
            /** Avg Salary Est */
            avg_salary_est?: number | null;
            /** @description 서울 사업장 중 대표 업종 안 백분위. 표본 부족이면 모두 null */
            percentiles?: components["schemas"]["Percentiles"] | null;
            /** @description DART 연결. 연결되지 않았으면 null */
            dart?: components["schemas"]["DartLink"] | null;
            /** @description 지도 위치(company_location). 좌표가 없으면 null */
            rep_location?: components["schemas"]["Location"] | null;
        };
        /** CompanyFinancials */
        CompanyFinancials: {
            /** Company Id */
            company_id: number;
            /**
             * As Of
             * @description 데이터 기준월 YYYYMM. 데이터가 없으면 null
             */
            as_of: number | null;
            /**
             * Flags
             * @description 이름 유사도(1.0 미만)로 연결했으면 name_matched
             */
            flags: ("salary_is_lower_bound" | "small_sample" | "short_history" | "stale" | "approx_location" | "name_matched" | "period_extended_to_24m")[];
            dart: components["schemas"]["DartLink"] | null;
            /**
             * Rows
             * @description 사업보고서 기준, 연결 우선 · 없으면 별도. 최근 연도부터
             */
            rows: components["schemas"]["FinancialRow"][];
        };
        /** CompanyHousing */
        CompanyHousing: {
            /** Company Id */
            company_id: number;
            /**
             * As Of
             * @description 데이터 기준월 YYYYMM. 데이터가 없으면 null
             */
            as_of: number | null;
            /**
             * Rent As Of
             * @description 전월세 집계 기준월(신고가 끝난 달) YYYYMM
             */
            rent_as_of: number | null;
            /**
             * Flags
             * @description approx_location, salary_is_lower_bound, stale
             */
            flags: ("salary_is_lower_bound" | "small_sample" | "short_history" | "stale" | "approx_location" | "name_matched" | "period_extended_to_24m")[];
            /**
             * Monthly Pay Est
             * @description 추정 월급(원) = 추정 연봉 ÷ 12, 하한 추정
             */
            monthly_pay_est: number | null;
            /**
             * Stations
             * @description 회사에서 1km 안의 역, 가까운 순 최대 3곳
             */
            stations: components["schemas"]["NearStation"][];
        };
        /** CompanyList */
        CompanyList: {
            /**
             * As Of
             * @description 데이터 기준월 YYYYMM. 데이터가 없으면 null
             */
            as_of: number | null;
            /** Items */
            items: components["schemas"]["CompanyListItem"][];
            /**
             * Next Cursor
             * @description 다음 페이지 커서. 마지막 페이지면 null
             */
            next_cursor: string | null;
        };
        /** CompanyListItem */
        CompanyListItem: {
            /** Company Id */
            company_id: number;
            /** Name */
            name: string;
            industry: components["schemas"]["Industry"];
            region: components["schemas"]["Region"];
            /** Members */
            members: number;
            /**
             * Growth 12M
             * @description 12개월 증감률. 12개월 전 자료가 없으면 null
             */
            growth_12m: number | null;
            /** Quit Rate 12M */
            quit_rate_12m: number | null;
            /**
             * Avg Salary Est
             * @description 추정 평균 연봉(원, 하한 추정치)
             */
            avg_salary_est: number | null;
            /**
             * Open Jobs
             * @description 진행 중 공고 수. 사람인 연동(Phase 10) 전에는 null
             */
            open_jobs?: number | null;
        };
        /** CompanyTrend */
        CompanyTrend: {
            /** Company Id */
            company_id: number;
            /**
             * As Of
             * @description 데이터 기준월 YYYYMM. 데이터가 없으면 null
             */
            as_of: number | null;
            /** Flags */
            flags: ("salary_is_lower_bound" | "small_sample" | "short_history" | "stale" | "approx_location" | "name_matched" | "period_extended_to_24m")[];
            /** Points */
            points: components["schemas"]["TrendPoint"][];
        };
        /** CompareItem */
        CompareItem: {
            /** Company Id */
            company_id: number;
            /** Name */
            name: string;
            /**
             * Status
             * @enum {string}
             */
            status: "ok" | "stale";
            /** Flags */
            flags: ("salary_is_lower_bound" | "small_sample" | "short_history" | "stale" | "approx_location" | "name_matched" | "period_extended_to_24m")[];
            industry?: components["schemas"]["Industry"] | null;
            region?: components["schemas"]["Region"] | null;
            /** Members */
            members?: number | null;
            /** Growth 12M */
            growth_12m?: number | null;
            /** Quit Rate 12M */
            quit_rate_12m?: number | null;
            /**
             * Avg Salary Est
             * @description 추정 평균 연봉(원, 하한 추정치)
             */
            avg_salary_est?: number | null;
            /**
             * Index Series
             * @description 최근 13개월(기준월과 12개월 전 포함)
             */
            index_series: components["schemas"]["IndexPoint"][];
        };
        /** CompareResult */
        CompareResult: {
            /**
             * As Of
             * @description 데이터 기준월 YYYYMM. 데이터가 없으면 null
             */
            as_of: number | null;
            /**
             * Items
             * @description 요청한 ids 순서
             */
            items: components["schemas"]["CompareItem"][];
        };
        /** DartLink */
        DartLink: {
            /** Corp Code */
            corp_code: string;
            /** Corp Name */
            corp_name: string;
            /**
             * Match Type
             * @description exact: 사업자번호 6자리 + 이름 일치, fuzzy: 이름 유사도(docs/matching.md)
             * @enum {string}
             */
            match_type: "exact" | "fuzzy" | "manual";
        };
        /** Distribution */
        Distribution: {
            /**
             * As Of
             * @description 데이터 기준월 YYYYMM. 데이터가 없으면 null
             */
            as_of: number | null;
            /** Code */
            code: string;
            /** Name */
            name: string;
            /**
             * Metric
             * @enum {string}
             */
            metric: "salary" | "quit" | "growth";
            /** P25 */
            p25: number | null;
            /** P50 */
            p50: number | null;
            /** P75 */
            p75: number | null;
            /**
             * N
             * @description 분포에 쓴 회사 수. 가입자 10명 미만 회사는 뺀다
             */
            n: number;
        };
        /** FinancialRow */
        FinancialRow: {
            /** Year */
            year: number;
            /**
             * Revenue
             * @description 매출액(금융업은 영업수익), 원
             */
            revenue: number | null;
            /** Operating Income */
            operating_income: number | null;
            /** Net Income */
            net_income: number | null;
            /**
             * Debt Ratio
             * @description 부채총계 ÷ 자본총계. 자본이 0 이하이면 null
             */
            debt_ratio: number | null;
        };
        /** Formula */
        Formula: {
            /** Metric */
            metric: string;
            /** Formula */
            formula: string;
            /** Note */
            note: string;
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** Health */
        Health: {
            /**
             * Status
             * @default ok
             */
            status: string;
            /**
             * Db
             * @default ok
             */
            db: string;
            /**
             * Latest Nps Ym
             * @description mart에 반영된 국민연금 최신 월
             */
            latest_nps_ym: number | null;
        };
        /** IndexPoint */
        IndexPoint: {
            /** Ym */
            ym: number;
            /** Members */
            members: number;
            /**
             * Idx
             * @description 12개월 전 가입자 = 100. 12개월 전 자료가 없으면 null
             */
            idx: number | null;
        };
        /** Industry */
        Industry: {
            /** Code */
            code: string | null;
            /** Name */
            name: string | null;
        };
        /** IndustryItem */
        IndustryItem: {
            /** Code */
            code: string;
            /** Name */
            name: string;
            /**
             * N Companies
             * @description 최신 월에 가입자가 있는 회사 수(표본 부족 포함)
             */
            n_companies: number;
        };
        /** IndustryList */
        IndustryList: {
            /**
             * As Of
             * @description 데이터 기준월 YYYYMM. 데이터가 없으면 null
             */
            as_of: number | null;
            /** Items */
            items: components["schemas"]["IndustryItem"][];
        };
        /** Location */
        Location: {
            /** Lon */
            lon: number;
            /** Lat */
            lat: number;
            /**
             * Accuracy
             * @description building이 아니면 대략 위치
             * @enum {string}
             */
            accuracy: "building" | "road" | "dong";
            /**
             * Basis
             * @description dart_hq: DART 본사 주소 기준(decisions/004)
             * @enum {string}
             */
            basis: "dart_hq" | "name_search" | "road" | "dong";
        };
        /** MapCompanies */
        MapCompanies: {
            /**
             * As Of
             * @description 데이터 기준월 YYYYMM. 데이터가 없으면 null
             */
            as_of: number | null;
            /**
             * Metric
             * @enum {string}
             */
            metric: "growth" | "quit" | "salary";
            /**
             * Items
             * @description 가입자 많은 순 최대 200곳
             */
            items: components["schemas"]["MapCompany"][];
            /**
             * Truncated
             * @description 조건에 맞는 회사가 200곳보다 많다. 범위를 좁히라고 안내
             */
            truncated: boolean;
            /**
             * Ungeocoded Count
             * @description 업종 · 지역 조건에 맞지만 좌표가 없어 빠진 회사 수
             */
            ungeocoded_count: number;
        };
        /** MapCompany */
        MapCompany: {
            /** Company Id */
            company_id: number;
            /** Name */
            name: string;
            /** Lon */
            lon: number;
            /** Lat */
            lat: number;
            /**
             * Accuracy
             * @description building이 아니면 대략 위치
             * @enum {string}
             */
            accuracy: "building" | "road" | "dong";
            /**
             * Basis
             * @description dart_hq: DART 본사 주소 기준(decisions/004)
             * @enum {string}
             */
            basis: "dart_hq" | "name_search" | "road" | "dong";
            /**
             * Value
             * @description metric으로 고른 값. 비율은 소수, 연봉은 원
             */
            value: number | null;
            /** Members */
            members: number;
            /** Growth 12M */
            growth_12m: number | null;
            /** Quit Rate 12M */
            quit_rate_12m: number | null;
            /**
             * Avg Salary Est
             * @description 추정 평균 연봉(원, 하한 추정치)
             */
            avg_salary_est: number | null;
        };
        /** Methodology */
        Methodology: {
            /**
             * As Of
             * @description 데이터 기준월 YYYYMM. 데이터가 없으면 null
             */
            as_of: number | null;
            /**
             * Period From
             * @description 국민연금 자료 첫 달 YYYYMM
             */
            period_from: number | null;
            /** Formulas */
            formulas: components["schemas"]["Formula"][];
            /** Limitations */
            limitations: string[];
            /** Sources */
            sources: components["schemas"]["Source"][];
        };
        /**
         * MonthsParam
         * @description 쿼리 파라미터 months. 문자열 "6"을 받으려고 Literal 대신 IntEnum을 쓴다.
         * @enum {integer}
         */
        MonthsParam: 6 | 12 | 24;
        /** NearStation */
        NearStation: {
            /** Station Id */
            station_id: number;
            /** Name */
            name: string;
            /** Lines */
            lines: string[];
            /**
             * Distance M
             * @description 회사 좌표에서 역까지(대략 위치면 참고용)
             */
            distance_m: number;
            /** @description 역 500m 안 원룸 계약이 없으면 null */
            rent: components["schemas"]["StationRent"] | null;
            /** @description 추정 연봉이나 시세가 없으면 null */
            burden: components["schemas"]["Burden"] | null;
            /**
             * Flags
             * @description period_extended_to_24m, small_sample(24개월에도 20건 미만)
             */
            flags: ("salary_is_lower_bound" | "small_sample" | "short_history" | "stale" | "approx_location" | "name_matched" | "period_extended_to_24m")[];
        };
        /** Percentiles */
        Percentiles: {
            /** Growth */
            growth: number | null;
            /**
             * Stability
             * @description 100 - 퇴사율 백분위
             */
            stability: number | null;
            /** Salary */
            salary: number | null;
        };
        /** Region */
        Region: {
            /** Sido */
            sido: string | null;
            /** Sigungu */
            sigungu: string | null;
        };
        /** Source */
        Source: {
            /** Name */
            name: string;
            /** Provider */
            provider: string;
            /** Url */
            url: string;
        };
        /** StationDetail */
        StationDetail: {
            /** Station Id */
            station_id: number;
            /** Name */
            name: string;
            /** Lines */
            lines: string[];
            /**
             * As Of
             * @description 전월세 집계 기준월 YYYYMM
             */
            as_of: number | null;
            rent: components["schemas"]["StationRent"] | null;
            /**
             * Jeonse Share
             * @description 원룸 계약 중 전세 비율
             */
            jeonse_share: number | null;
            /** Flags */
            flags: ("salary_is_lower_bound" | "small_sample" | "short_history" | "stale" | "approx_location" | "name_matched" | "period_extended_to_24m")[];
        };
        /** StationList */
        StationList: {
            /**
             * As Of
             * @description 전월세 집계 기준월 YYYYMM
             */
            as_of: number | null;
            /** Items */
            items: components["schemas"]["StationListItem"][];
        };
        /** StationListItem */
        StationListItem: {
            /** Station Id */
            station_id: number;
            /** Name */
            name: string;
            /** Lines */
            lines: string[];
            /**
             * Monthly Median
             * @description 12개월 원룸 환산 월세 중앙값(원)
             */
            monthly_median: number | null;
            /**
             * N
             * @description 12개월 원룸 월세 계약 수
             */
            n: number;
        };
        /** StationRent */
        StationRent: {
            /**
             * Months
             * @description 실제로 쓴 기간. 계약이 20건 미만이면 24개월로 넓힌다
             * @enum {integer}
             */
            months: 6 | 12 | 24;
            /**
             * N Monthly
             * @description 원룸 월세 계약 수
             */
            n_monthly: number;
            /** N Jeonse */
            n_jeonse: number;
            /**
             * Monthly P25
             * @description 환산 월세(원)
             */
            monthly_p25: number | null;
            /** Monthly Median */
            monthly_median: number | null;
            /** Monthly P75 */
            monthly_p75: number | null;
            /**
             * Deposit Median Man
             * @description 월세 계약의 보증금 중앙값(만원)
             */
            deposit_median_man: number | null;
            /**
             * Rent Median Man
             * @description 월세 계약의 월세 중앙값(만원)
             */
            rent_median_man: number | null;
            /** Jeonse P25 Man */
            jeonse_p25_man: number | null;
            /** Jeonse Median Man */
            jeonse_median_man: number | null;
            /** Jeonse P75 Man */
            jeonse_p75_man: number | null;
        };
        /** TrendPoint */
        TrendPoint: {
            /** Ym */
            ym: number;
            /** Members */
            members: number;
            /** New */
            new: number;
            /** Lost */
            lost: number;
            /**
             * Hire Rate
             * @description 직전 달이 없으면 null
             */
            hire_rate: number | null;
            /** Quit Rate */
            quit_rate: number | null;
            /** Avg Salary Est */
            avg_salary_est: number | null;
        };
        /** ValidationError */
        ValidationError: {
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
            /** Input */
            input?: unknown;
            /** Context */
            ctx?: Record<string, never>;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    search_companies_companies_get: {
        parameters: {
            query?: {
                /** @description 회사명 앞부분. (주) · 공백은 무시 */
                q?: string | null;
                /** @description 사업자번호 앞 6자리 */
                biz_no6?: string | null;
                /** @description 업종 코드 6자리 */
                industry?: string | null;
                /** @description 시군구 코드 5자리 */
                region?: string | null;
                sort?: "name" | "growth";
                limit?: number;
                cursor?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CompanyList"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    company_detail_companies__company_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                company_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CompanyDetail"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    company_trend_companies__company_id__trend_get: {
        parameters: {
            query?: {
                /** @description YYYYMM */
                from_ym?: number | null;
                /** @description YYYYMM */
                to_ym?: number | null;
            };
            header?: never;
            path: {
                company_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CompanyTrend"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    company_financials_companies__company_id__financials_get: {
        parameters: {
            query?: {
                years?: number;
            };
            header?: never;
            path: {
                company_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CompanyFinancials"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    company_housing_companies__company_id__housing_get: {
        parameters: {
            query?: {
                /** @description 6 · 12 · 24개월(docs/04 D7) */
                months?: components["schemas"]["MonthsParam"];
            };
            header?: never;
            path: {
                company_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CompanyHousing"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    compare_compare_get: {
        parameters: {
            query: {
                /** @description 회사 ID를 쉼표로 1 ~ 3개. 예: 12,34,56 */
                ids: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CompareResult"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_industries_industries_get: {
        parameters: {
            query?: {
                /** @description 업종 이름 일부 */
                q?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["IndustryList"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    industry_distribution_industries__code__distribution_get: {
        parameters: {
            query?: {
                metric?: "salary" | "quit" | "growth";
            };
            header?: never;
            path: {
                code: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Distribution"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    map_companies_map_companies_get: {
        parameters: {
            query?: {
                /** @description 업종 코드 6자리 */
                industry?: string | null;
                /** @description 시도 2자리 또는 시군구 5자리 */
                region?: string | null;
                metric?: "growth" | "quit" | "salary";
                /** @description min_lon,min_lat,max_lon,max_lat (WGS84) */
                bbox?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MapCompanies"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_methodology_meta_methodology_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Methodology"];
                };
            };
        };
    };
    health_health_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Health"];
                };
            };
        };
    };
    list_stations_stations_get: {
        parameters: {
            query?: {
                /** @description 역 이름 앞부분 */
                q?: string | null;
                /** @description 노선 이름(예: 2호선) */
                line?: string | null;
                sort?: "name" | "monthly_median";
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["StationList"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    station_rent_stations__station_id__rent_get: {
        parameters: {
            query?: {
                /** @description 6 · 12 · 24개월(docs/04 D7) */
                months?: components["schemas"]["MonthsParam"];
            };
            header?: never;
            path: {
                station_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["StationDetail"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
}
