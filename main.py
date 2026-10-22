import datetime
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
    st.info(
        "**확인 및 조치 방법:**\n"
        "1. 인터넷 연결 상태를 확인해주세요.\n"
        "2. API 서비스 점검 중이거나 일시적인 네트워크 오류일 수 있으니 잠시 후 다시 시도해 주세요.\n"
        f"(상세 오류 메시지: {e})"
    )
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


# 8. 100만 이상 관객 영화 트로피 추가
def format_movie_title(row):
    title = row["movieNm"]
    if row["audiAcc"] >= 1000000:
        return f"{title} 🏆"
    return title


df["표시영화명"] = df.apply(format_movie_title, axis=1)

# 9. Top 1 영화 지표 카드 출력
top_movie = df.iloc[0]

st.subheader(f"🥇 1위: {top_movie['표시영화명']}")
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

# 10. 상위 5개 영화 막대그래프 시각화 (1등 막대: 반짝이는 황금색 강조)
st.subheader("📊 관객수 상위 5개 영화")
top5_df = df.head(5).copy()

# 막대 색상 구분을 위한 컬럼 추가 (1위: 황금색, 나머지: 일반 파랑)
top5_df["막대색상"] = top5_df["rank"].apply(
    lambda r: "✨ 1위 황금빛 챔피언" if r == 1 else "일반 영화"
)

# Altair 막대그래프 생성
chart = (
    alt.Chart(top5_df)
    .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
    .encode(
        x=alt.X("movieNm:N", sort=None, title="영화명"),
        y=alt.Y("audiCnt:Q", title="당일 관객수(명)"),
        color=alt.Color(
            "막대색상:N",
            scale=alt.Scale(
                domain=["✨ 1위 황금빛 챔피언", "일반 영화"],
                range=["#FFD700", "#4A90E2"],  # 황금색 및 파란색
            ),
            legend=alt.Legend(title="구분"),
        ),
        tooltip=[
            alt.Tooltip("movieNm:N", title="영화명"),
            alt.Tooltip("audiCnt:Q", title="관객수", format=","),
        ],
    )
    .properties(height=380)
)

# 막대 상단 숫자의 텍스트 표기
text = chart.mark_text(
    align="center", baseline="bottom", dy=-5, color="white"
).encode(text=alt.Text("audiCnt:Q", format=","))

st.altair_chart(chart + text, use_container_width=True)

st.divider()

# 11. 전체 순위 데이터 표 출력
st.subheader("📋 박스오피스 전체 순위")

display_df = df[
    [
        "rank",
        "순위증감",
        "표시영화명",
        "openDt",
        "audiCnt",
        "audiAcc",
        "scrnCnt",
    ]
].copy()
display_df.columns = [
    "순위",
    "순위 증감",
    "영화명",
    "개봉일",
    "관객수(명)",
    "누적관객수(명)",
    "스크린수(개)",
]

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "순위": st.column_config.NumberColumn(format="%d"),
        "관객수(명)": st.column_config.NumberColumn(format="%d"),
        "누적관객수(명)": st.column_config.NumberColumn(format="%d"),
        "스크린수(개)": st.column_config.NumberColumn(format="%d"),
    },
)
