import datetime
import urllib.parse
import requests
import altair as alt
import pandas as pd
import pytz
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


# API 키 확인 및 날짜 계산
api_key = get_api_key()
max_selectable_date = get_yesterday_kst()

# 3. 달력을 통한 조회 날짜 선택 UI
selected_date = st.date_input(
    label="📅 조회할 날짜를 선택하세요 (최대 어제까지 선택 가능)",
    value=max_selectable_date,
    max_value=max_selectable_date,
    min_value=datetime.date(2004, 1, 1),
)

target_date = selected_date.strftime("%Y%m%d")
st.caption(
    f" 기준 날짜: {selected_date.strftime('%Y-%m-%d')} (한국 시간 기준)"
)

# API 키 예외 처리
if not api_key:
    st.error("🔑 API 키(KOBIS_KEY)를 찾을 수 없습니다.")
    st.info(
        "**확인 및 조치 방법:**\n"
        "1. 로컬 환경일 경우 `.streamlit/secrets.toml` 파일에 `KOBIS_KEY = '발급받은키'`를 작성했는지 확인하세요.\n"
        "2. Streamlit Cloud 배포 환경일 경우 설정 메뉴의 **App settings -> Secrets**에 `KOBIS_KEY`가 올바르게 등록되었는지 확인하세요."
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


# 8. 인터넷 이미지 플레이스홀더 / 웹 검색용 포스터 URL 생성 함수
def get_poster_url(movie_name):
    # 인터넷 오픈 이미지 검색용 파라미터 생성 (영화 제목 기반 웹 썸네일 경로)
    encoded_title = urllib.parse.quote(movie_name)
    # 이미지 로딩이 안 될 경우를 대비한 자동 포스터 플레이스홀더
    return f"https://placehold.co/300x420/1e1e1e/FFD700?text={encoded_title}"


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

# 10. 상위 5개 영화 막대그래프 (1등 막대: 황금색)
st.subheader("📊 관객수 상위 5개 영화")
top5_df = df.head(5).copy()

top5_df["막대색상"] = top5_df["rank"].apply(
    lambda r: "✨ 1위 황금빛 챔피언" if r == 1 else "일반 영화"
)

chart = (
    alt.Chart(top5_df)
    .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
    .encode(
        x=alt.X("movieNm:N", sort=None, title="영화명"),
        y=alt.Y("audiCnt:Q", title="당일 관객수(명)"),
        color=alt.Color(
            "막대색상
