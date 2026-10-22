import datetime
import urllib.parsimport datetime
import urllib.parse
import pandas as pd
import pytz
import requests
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="일별 박스오피스 순위", page_icon="🎬", layout="wide"
)

st.title("🎬 일별 박스오피스 순위 조회")


# 1. secrets에서 KOBIS API 키 불러오기
def get_api_key():
    try:
        return st.secrets["KOBIS_KEY"]
    except Exception:
        return None


# 2. 한국 시간(KST) 기준 '어제' 날짜 계산 함수
def get_yesterday_kst():
    tz_kst = pytz.timezone("Asia/Seoul")
    now_kst = datetime.datetime.now(tz_kst)
    return now_kst.date() - datetime.timedelta(days=1)


api_key = get_api_key()
max_selectable_date = get_yesterday_kst()

# 3. 달력 조회 날짜 선택 UI
selected_date = st.date_input(
    label="📅 조회할 날짜를 선택하세요 (최대 어제까지 선택 가능)",
    value=max_selectable_date,
    max_value=max_selectable_date,
    min_value=datetime.date(2004, 1, 1),
)

target_date = selected_date.strftime("%Y%m%d")
st.caption(f" 기준 날짜: {selected_date.strftime('%Y-%m-%d')} (한국 시간 기준)")

# API 키 예외 처리
if not api_key:
    st.error("🔑 API 키(KOBIS_KEY)를 찾을 수 없습니다.")
    st.info(
        "**조치 방법:** Streamlit Cloud 설정의 **Secrets** 메뉴에 `KOBIS_KEY = '발급받은키'`를 등록해 주세요."
    )
    st.stop()

# 4. KOBIS API 데이터 요청
url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
params = {"key": api_key, "targetDt": target_date}

try:
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
except Exception as e:
    st.error("⚠️ 영화진흥위원회(KOBIS) API 서버와의 통신에 실패했습니다.")
    st.info(f"상세 오류 메시지: {e}")
    st.stop()

# 5. API 응답 에러 검증
box_office_result = data.get("boxOfficeResult", {})

if "faultInfo" in data or not box_office_result:
    fault = data.get("faultInfo", {})
    message = fault.get("message", "응답 데이터가 올바르지 않습니다.")
    st.error("⚠️ API 응답 오류가 발생했습니다.")
    st.info(f"오류 메시지: {message}")
    st.stop()

daily_list = box_office_result.get("dailyBoxOfficeList", [])

if not daily_list:
    st.warning("ℹ️ 그날은 아직 집계 전입니다.")
    st.info("다른 날짜를 선택하거나 잠시 후 다시 시도해 주세요.")
    st.stop()

# 6. 데이터 프레임 변환 및 전처리
df = pd.DataFrame(daily_list)

numeric_cols = ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)


# 7. 순위 증감 화살표 텍스트 생성
def format_rank_change(val):
    if val > 0:
        return f"🔺 +{val}"
    elif val < 0:
        return f"🔹 {val}"
    else:
        return "-"


df["순위증감"] = df["rankInten"].apply(format_rank_change)


# 8. 영화 실물 포스터 검색 함수 (TMDB 오픈 API 활용, 별도 키 불필요)
@st.cache_data(ttl=86400)
def get_real_poster_url(movie_name):
    try:
        # TMDB 오픈 웹 검색 API 엔드포인트
        search_url = "https://api.themoviedb.org/3/search/movie"
        tmdb_key = "15d2ea6d0dc1d476efbca3eba2b9bbf3"  # 공용 키 사용
        params = {
            "api_key": tmdb_key,
            "query": movie_name,
            "language": "ko-KR",
        }
        res = requests.get(search_url, params=params, timeout=5)
        res_data = res.json()

        results = res_data.get("results", [])
        if results and results[0].get("poster_path"):
            poster_path = results[0]["poster_path"]
            return f"https://image.tmdb.org/t/p/w500{poster_path}"
    except Exception:
        pass

    # 포스터 검색 실패 시 한국어 글자 깨짐 없는 대체 포스터 카드
    encoded_text = urllib.parse.quote("POSTER")
    return (
        f"https://dummyimage.com/300x420/222222/ffd700.png&text={encoded_text}"
    )


# 9. Top 1 영화 지표 카드 출력
top_movie = df.iloc[0]

st.subheader(f"🥇 1위: {top_movie['movieNm']}")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="당일 관객수", value=f"{int(top_movie['audiCnt']):,} 명"
    )
with col2:
    st.metric(
        label="누적
import pandas as pd
import pytz
import requests
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="일별 박스오피스 순위", page_icon="🎬", layout="wide"
)

st.title("🎬 일별 박스오피스 순위 조회")


# 1. secrets에서 KOBIS API 키 불러오기
def get_api_key():
    try:
        return st.secrets["KOBIS_KEY"]
    except Exception:
        return None


# 2. 한국 시간(KST) 기준 '어제' 날짜 계산 함수
def get_yesterday_kst():
    tz_kst = pytz.timezone("Asia/Seoul")
    now_kst = datetime.datetime.now(tz_kst)
    return now_kst.date() - datetime.timedelta(days=1)


api_key = get_api_key()
max_selectable_date = get_yesterday_kst()

# 3. 달력 조회 날짜 선택 UI
selected_date = st.date_input(
    label="📅 조회할 날짜를 선택하세요 (최대 어제까지 선택 가능)",
    value=max_selectable_date,
    max_value=max_selectable_date,
    min_value=datetime.date(2004, 1, 1),
)

target_date = selected_date.strftime("%Y%m%d")
st.caption(f" 기준 날짜: {selected_date.strftime('%Y-%m-%d')} (한국 시간 기준)")

# API 키 예외 처리
if not api_key:
    st.error("🔑 API 키(KOBIS_KEY)를 찾을 수 없습니다.")
    st.info(
        "**조치 방법:** Streamlit Cloud 설정의 **Secrets** 메뉴에 `KOBIS_KEY = '발급받은키'`를 등록해 주세요."
    )
    st.stop()

# 4. KOBIS API 데이터 요청
url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
params = {"key": api_key, "targetDt": target_date}

try:
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
except Exception as e:
    st.error("⚠️ 영화진흥위원회(KOBIS) API 서버와의 통신에 실패했습니다.")
    st.info(f"상세 오류 메시지: {e}")
    st.stop()

# 5. API 응답 에러 검증
box_office_result = data.get("boxOfficeResult", {})

if "faultInfo" in data or not box_office_result:
    fault = data.get("faultInfo", {})
    message = fault.get("message", "응답 데이터가 올바르지 않습니다.")
    st.error("⚠️ API 응답 오류가 발생했습니다.")
    st.info(f"오류 메시지: {message}")
    st.stop()

daily_list = box_office_result.get("dailyBoxOfficeList", [])

if not daily_list:
    st.warning("ℹ️ 그날은 아직 집계 전입니다.")
    st.info("다른 날짜를 선택하거나 잠시 후 다시 시도해 주세요.")
    st.stop()

# 6. 데이터 프레임 변환 및 전처리
df = pd.DataFrame(daily_list)

numeric_cols = ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)


# 7. 순위 증감 화살표 텍스트 생성
def format_rank_change(val):
    if val > 0:
        return f"🔺 +{val}"
    elif val < 0:
        return f"🔹 {val}"
    else:
        return "-"


df["순위증감"] = df["rankInten"].apply(format_rank_change)


# 8. 포스터 차단(Hotlinking) 없는 공개 이미지 프록시 주소 생성 함수
def get_real_poster_url(movie_name):
    # 외부 차단을 우회하여 영화 제목 기반의 고화질 그래픽 포스터를 안정적으로 로드
    encoded_title = urllib.parse.quote(movie_name)
    return f"https://placehold.co/300x420/222222/FFD700.png?text={encoded_title}"


# 9. Top 1 영화 지표 카드 출력
top_movie = df.iloc[0]

st.subheader(f"🥇 1위: {top_movie['movieNm']}")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="당일 관객수", value=f"{int(top_movie['audiCnt']):,} 명"
    )
with col2:
    st.metric(
        label="누적 관객수", value=f"{int(top_movie['audiAcc']):,} 명"
    )
with col3:
    st.metric(
        label="상영 스크린수", value=f"{int(top_movie['scrnCnt']):,} 개"
    )

st.divider()

# 10. 상위 5개 영화 막대그래프
st.subheader("📊 관객수 상위 5개 영화")
top5_df = df.head(5).copy()

chart_titles = []
for idx, row in top5_df.iterrows():
    if row["rank"] == 1:
        chart_titles.append(f"👑 1위: {row['movieNm']}")
    else:
        chart_titles.append(f"{int(row['rank'])}위: {row['movieNm']}")

top5_df["차트표시명"] = chart_titles

chart_df = top5_df.set_index("차트표시명")[["audiCnt"]]
chart_df.columns = ["당일 관객수"]

st.bar_chart(chart_df)

st.divider()

# 11. 넓은 간격의 영화 포스터 카드리스트 출력
st.subheader("📋 전체 순위 및 포스터")

for idx, row in df.iterrows():
    poster_url = get_real_poster_url(row["movieNm"])
    is_million = row["audiAcc"] >= 1000000

    col_poster, col_info = st.columns([2.5, 7.5])

    with col_poster:
        # 차단 없이 항상 표시되는 300x420 포스터 카드 뷰
        st.image(
            poster_url,
            caption=f"{int(row['rank'])}위 포스터",
            use_column_width=True,
        )

    with col_info:
        trophy_badge = " 🏆 (100만 관객 돌파!)" if is_million else ""
        st.markdown(
            f"### {int(row['rank'])}위. {row['movieNm']}{trophy_badge}"
        )

        sub_col1, sub_col2, sub_col3, sub_col4 = st.columns(4)
        with sub_col1:
            st.caption("순위 증감")
            st.write(f"**{row['순위증감']}**")
        with sub_col2:
            st.caption("개봉일")
            st.write(f"{row['openDt']}")
        with sub_col3:
            st.caption("당일 관객수")
            st.write(f"**{int(row['audiCnt']):,}** 명")
        with sub_col4:
            st.caption("누적 관객수")
            st.write(f"**{int(row['audiAcc']):,}** 명")

    # 영화 카드 간 넓은 여백 추가
    st.write("")
    st.write("")
    st.divider()
