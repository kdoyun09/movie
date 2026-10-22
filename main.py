import datetime
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


# 2. 한국 시간 기준 어제 날짜 구하기
def get_yesterday_kst():
    tz_kst = pytz.timezone("Asia/Seoul")
    now_kst = datetime.datetime.now(tz_kst)
    return now_kst.date() - datetime.timedelta(days=1)


api_key = get_api_key()
max_selectable_date = get_yesterday_kst()

# 3. 날짜 선택 UI
selected_date = st.date_input(
    label="📅 조회할 날짜 선택 (최대 어제까지 가능)",
    value=max_selectable_date,
    max_value=max_selectable_date,
    min_value=datetime.date(2004, 1, 1),
)

target_date = selected_date.strftime("%Y%m%d")
date_display = selected_date.strftime("%Y-%m-%d")
st.caption(f"기준 날짜: {date_display} (한국 시간 기준)")

# API 키 유효성 확인
if not api_key:
    st.error("🔑 API 키(KOBIS_KEY)를 찾을 수 없습니다.")
    st.info("Secrets 항목에 KOBIS_KEY를 등록해 주세요.")
    st.stop()

# 4. KOBIS 박스오피스 API 요청
url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
params = {"key": api_key, "targetDt": target_date}

try:
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
except Exception as e:
    st.error("⚠️ API 서버 통신에 실패했습니다.")
    st.info(f"오류 메시지: {e}")
    st.stop()

# 5. API 응답 검증
box_office_result = data.get("boxOfficeResult", {})

if "faultInfo" in data or not box_office_result:
    fault = data.get("faultInfo", {})
    msg = fault.get("message", "응답 데이터 오류")
    st.error("⚠️ API 응답 오류가 발생했습니다.")
    st.info(f"오류 내용: {msg}")
    st.stop()

daily_list = box_office_result.get("dailyBoxOfficeList", [])

if not daily_list:
    st.warning("ℹ️ 그날은 아직 집계 전입니다.")
    st.info("다른 날짜를 선택해 주세요.")
    st.stop()

# 6. 데이터프레임 변환
df = pd.DataFrame(daily_list)

numeric_cols = ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)


# 7. 순위 증감 포맷팅
def format_rank_change(val):
    if val > 0:
        return f"🔺 +{val}"
    elif val < 0:
        return f"🔹 {val}"
    else:
        return "-"


df["순위증감"] = df["rankInten"].apply(format_rank_change)


# 8. 실물 영화 포스터 검색 함수
@st.cache_data(ttl=86400)
def get_real_poster_url(movie_name):
    try:
        encoded_query = urllib.parse.quote(movie_name)
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key=f89a6c172ad052478546b533f8e5b4fe&query={encoded_query}&language=ko-KR"
        res = requests.get(search_url, timeout=4)
        if res.status_code == 200:
            results = res.json().get("results", [])
            if results and results[0].get("poster_path"):
                return f"https://image.tmdb.org/t/p/w500{results[0]['poster_path']}"
    except Exception:
        pass

    encoded_title = urllib.parse.quote(movie_name[:6])
    return f"https://dummyimage.com/300x420/1e293b/f8fafc.png&text={encoded_title}"


# 9. 1위 영화 상단 카드 출력
top_movie = df.iloc[0]

st.subheader(f"🥇 1위: {top_movie['movieNm']}")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="당일 관객수", value=f"{int(top_movie['audiCnt']):,} 명")
with col2:
    st.metric(label="누적 관객수", value=f"{int(top_movie['audiAcc']):,} 명")
with col3:
    st.metric(label="상영 스크린수", value=f"{int(top_movie['scrnCnt']):,} 개")

st.divider()

# 10. 관객수 상위 5개 영화 막대그래프
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

# 11. 넓은 간격의 영화 포스터 갤러리
st.subheader("📋 전체 순위 및 포스터")

for idx, row in df.iterrows():
    poster_url = get_real_poster_url(row["movieNm"])
    is_million = row["audiAcc"] >= 1000000

    col_poster, col_info = st.columns([2.5, 7.5])

    with col_poster:
        st.image(
            poster_url,
            caption=f"{int(row['rank'])}위 포스터",
            use_container_width=True,
        )

    with col_info:
        badge = " 🏆 (100만 관객 돌파!)" if is_million else ""
        st.markdown(f"### {int(row['rank'])}위. {row['movieNm']}{badge}")

        s1, s2, s3, s4 = st.columns(4)
        with s1:
            st.caption("순위 증감")
            st.write(f"**{row['순위증감']}**")
        with s2:
            st.caption("개봉일")
            st.write(f"{row['openDt']}")
        with s3:
            st.caption("당일 관객수")
            st.write(f"**{int(row['audiCnt']):,}** 명")
        with s4:
            st.caption("누적 관객수")
            st.write(f"**{int(row['audiAcc']):,}** 명")

    st.write("")
    st.divider()
