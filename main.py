import datetime
import requestimport datetime
import requests
import pandas as pd
import pytz
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="마인크래프트 박스오피스",
    page_icon="⛏️",
    layout="wide"
)

# 🎨 마인크래프트 CSS 스타일
CSS_TEXT = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Noto+Sans+KR:wght@700;900&display=swap');

.stApp {
    background-color: #1e1e1e;
    background-image: 
        radial-gradient(circle at 50% 50%, rgba(0, 0, 0, 0.5) 0%, rgba(0, 0, 0, 0.9) 100%),
        url('https://images.unsplash.com/photo-1627856013091-fed6e4e30025?q=80&w=1000&auto=format&fit=crop');
    background-attachment: fixed;
    background-size: cover;
    font-family: 'Noto Sans KR', sans-serif;
    color: #ffffff;
}

.mc-header-container {
    background: linear-gradient(180deg, rgba(35, 25, 15, 0.95) 0%, rgba(15, 15, 15, 0.98) 100%);
    border: 4px solid #5c3818;
    box-shadow: inset -4px -4px 0px #2a180b, inset 4px 4px 0px #8f5828, 0px 8px 16px rgba(0,0,0,0.8);
    padding: 20px;
    border-radius: 4px;
    text-align: center;
    margin-bottom: 20px;
}

.mc-title {
    font-family: 'Press Start 2P', cursive;
    color: #55FF55;
    text-shadow: 3px 3px 0px #00AA00, 5px 5px 0px #000000;
    font-size: 1.8rem;
    margin-bottom: 10px;
}

.mob-badge-group {
    display: flex;
    justify-content: center;
    gap: 10px;
    margin-top: 10px;
    flex-wrap: wrap;
}

.mob-badge {
    background: #000000;
    border: 2px solid #555555;
    padding: 5px 10px;
    font-size: 0.85rem;
    font-weight: bold;
}

div[data-testid="stMetric"], div.stDataFrame {
    background: rgba(18, 18, 18, 0.92) !important;
    border: 3px solid #4a4a4a !important;
    box-shadow: inset -3px -3px 0px #111111, inset 3px 3px 0px #666666, 0 4px 12px rgba(0,0,0,0.8) !important;
    padding: 15px !important;
}

[data-testid="stMetricLabel"] {
    color: #FFFF55 !important;
    font-weight: bold !important;
}

[data-testid="stMetricValue"] {
    color: #FFFFFF !important;
    font-weight: 900 !important;
}

h2, h3 {
    color: #FFAA00 !important;
    text-shadow: 2px 2px 0px #000000;
}

hr {
    border-top: 3px dashed #55FF55 !important;
}
</style>
"""
st.markdown(CSS_TEXT, unsafe_allow_html=True)

# ⛏️ 헤더
HEADER_HTML = """
<div class="mc-header-container">
    <div class="mc-title">⛏️ MINECRAFT BOX OFFICE ⛏️</div>
    <div style="color: #DDDDDD; font-weight: bold;">마인크래프트 세상에서 확인하는 일별 영화 순위</div>
    <div class="mob-badge-group">
        <span class="mob-badge" style="color: #55FF55;">🟩 크리퍼</span>
        <span class="mob-badge" style="color: #FF5555;">🗡️ 스티브</span>
        <span class="mob-badge" style="color: #FF55FF;">👁️ 엔더맨</span>
        <span class="mob-badge" style="color: #FFAA00;">🟧 알렉스</span>
        <span class="mob-badge" style="color: #FF2277;">🐷 돼지</span>
    </div>
</div>
"""
st.markdown(HEADER_HTML, unsafe_allow_html=True)


# 1. API 키 불러오기
def get_api_key():
    try:
        return st.secrets["KOBIS_KEY"]
    except Exception:
        return None


# 2. 어제 날짜 구하기
def get_yesterday_kst():
    tz_kst = pytz.timezone("Asia/Seoul")
    now_kst = datetime.datetime.now(tz_kst)
    return now_kst.date() - datetime.timedelta(days=1)


api_key = get_api_key()
max_selectable_date = get_yesterday_kst()

# 3. 날짜 선택
selected_date = st.date_input(
    label="📅 탐험할 날짜 선택 (최대 어제까지 가능)",
    value=max_selectable_date,
    max_value=max_selectable_date,
    min_value=datetime.date(2004, 1, 1),
)

target_date = selected_date.strftime("%Y%m%d")
date_str = selected_date.strftime("%Y-%m-%d")

st.caption(f"🧱 현재 세계 시각: {date_str} (한국 표준시 기준)")

# API 키 점검
if not api_key:
    st.error("🔑 [오류] KOBIS_KEY를 찾을 수 없습니다.")
    st.info("Secrets 항목에 KOBIS_KEY를 등록해 주세요.")
    st.stop()

# 4. API 요청
url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
params = {"key": api_key, "targetDt": target_date}

try:
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
except Exception as e:
    st.error("💥 [크리퍼 폭발] API 통신 실패!")
    st.info(f"오류 내용: {e}")
    st.stop()

# 5. 응답 검증
box_office_result = data.get("boxOfficeResult", {})

if "faultInfo" in data or not box_office_result:
    fault = data.get("faultInfo", {})
    msg = fault.get("message", "잘못된 응답입니다.")
    st.error("⚠️ API 인증 오류 발생!")
    st.info(f"오류 메시지: {msg}")
    st.stop()

daily_list = box_office_result.get("dailyBoxOfficeList", [])

if not daily_list:
    st.warning("🧟 그날은 아직 집계 전입니다.")
    st.info("해당 날짜의 데이터가 아직 집계되지 않았습니다.")
    st.stop()

# 6. 데이터프레임 처리
df = pd.DataFrame(daily_list)

numeric_cols = ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)


# 7. 순위 증감
def format_rank_change(val):
    if val > 0:
        return f"🔺 +{val}"
    elif val < 0:
        return f"🔹 {val}"
    else:
        return "-"


df["순위증감"] = df["rankInten"].apply(format_rank_change)


# 8. 트로피 표기
def format_movie_title(row):
    title = row["movieNm"]
    if row["audiAcc"] >= 1000000:
        return f"{title} 🏆"
    return title


df["표시영화명"] = df.apply(format_movie_title, axis=1)

# 9. 1위 영화 카드
top_movie = df.iloc[0]

st.subheader(f"👑 1위 챔피언: {top_movie['표시영화명']}")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="⚔️ 당일 관객수", value=f"{int(top_movie['audiCnt']):,} 명")
with col2:
    st.metric label="💎 누적 관객수", value=f"{int(top_movie['audiAcc']):,} 명"
with col3:
    st.metric(label="🛡️ 상영 스크린수", value=f"{int(top_movie['scrnCnt']):,} 개")

st.divider()

# 10. 상위 5개 영화 차트
st.subheader("📊 인기 영화 TOP 5")
top5_df = df.head(5).copy()

chart_df = top5_df.set_index("movieNm")[["audiCnt"]]
chart_df.columns = ["당일 관객수"]

st.bar_chart(chart_df)

st.divider()

# 11. 전체 순위 표
st.subheader("📜 박스오피스 전체 순위")

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
import pandas as pd
import pytz
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="마인크래프트 박스오피스",
    page_icon="⛏️",
    layout="wide"
)

# ---------------------------------------------------------
# 🎨 마인크래프트 CSS 스타일
# ---------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Noto+Sans+KR:wght@700;900&display=swap');

.stApp {
    background-color: #1e1e1e;
    background-image: 
        radial-gradient(circle at 50% 50%, rgba(0, 0, 0, 0.5) 0%, rgba(0, 0, 0, 0.9) 100%),
        url('https://images.unsplash.com/photo-1627856013091-fed6e4e30025?q=80&w=1000&auto=format&fit=crop');
    background-attachment: fixed;
    background-size: cover;
    font-family: 'Noto Sans KR', sans-serif;
    color: #ffffff;
}

.mc-header-container {
    background: linear-gradient(180deg, rgba(35, 25, 15, 0.95) 0%, rgba(15, 15, 15, 0.98) 100%);
    border: 4px solid #5c3818;
    box-shadow: inset -4px -4px 0px #2a180b, inset 4px 4px 0px #8f5828, 0px 8px 16px rgba(0,0,0,0.8);
    padding: 25px;
    border-radius: 4px;
    text-align: center;
    margin-bottom: 25px;
}

.mc-title {
    font-family: 'Press Start 2P', cursive;
    color: #55FF55;
    text-shadow: 3px 3px 0px #00AA00, 5px 5px 0px #000000;
    font-size: 1.8rem;
    margin-bottom: 15px;
}

.mob-badge-group {
    display: flex;
    justify-content: center;
    gap: 12px;
    margin-top: 15px;
    flex-wrap: wrap;
}

.mob-badge {
    background: #000000;
    border: 2px solid #555555;
    padding: 6px 12px;
    font-size: 0.9rem;
    font-weight: bold;
    border-radius: 2px;
    box-shadow: 2px 2px 0px #000;
}

div[data-testid="stMetric"], div.stDataFrame {
    background: rgba(18, 18, 18, 0.92) !important;
    border: 3px solid #4a4a4a !important;
    box-shadow: inset -3px -3px 0px #111111, inset 3px 3px 0px #666666, 0 4px 12px rgba(0,0,0,0.8) !important;
    padding: 15px !important;
    border-radius: 2px !important;
}

[data-testid="stMetricLabel"] {
    color: #FFFF55 !important;
    font-weight: bold !important;
    font-size: 1.05rem !important;
}

[data-testid="stMetricValue"] {
    color: #FFFFFF !important;
    font-weight: 900 !important;
}

h2, h3 {
    color: #FFAA00 !important;
    text-shadow: 2px 2px 0px #000000;
    font-weight: 900 !important;
}

hr {
    border-top: 3px dashed #55FF55 !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# ⛏️ 헤더
# ---------------------------------------------------------
st.markdown(
    """
<div class="mc-header-container">
    <div class="mc-title">⛏️ MINECRAFT BOX OFFICE ⛏️</div>
    <div style="color: #DDDDDD; font-weight: bold; font-size: 1.05rem;">
        마인크래프트 세상에서 확인하는 일별 영화 순위
    </div>
    <div class="mob-badge-group">
        <span class="mob-badge" style="color: #55FF55;">🟩 크리퍼 (Creeper)</span>
        <span class="mob-badge" style="color: #FF5555;">🗡️ 스티브 (Steve)</span>
        <span class="mob-badge" style="color: #FF55FF;">👁️ 엔더맨 (Enderman)</span>
        <span class="mob-badge" style="color: #FFAA00;">🟧 알렉스 (Alex)</span>
        <span class="mob-badge" style="color: #FF2277;">🐷 돼지 (Pig)</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)


# 1. API 키 불러오기
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
    label="📅 탐험할 날짜 선택 (최대 어제까지 가능)",
    value=max_selectable_date,
    max_value=max_selectable_date,
    min_value=datetime.date(2004, 1, 1),
)

target_date = selected_date.strftime("%Y%m%d")
date_str = selected_date.strftime("%Y-%m-%d")

# 단순 문자열 연결로 문법 오류 발생 방지
st.caption("🧱 현재 세계 시각: " + date_str + " (한국 표준시 기준)")

# API 키 유효성 체크
if not api_key:
    st.error("🔑 [오류] KOBIS_KEY 비밀 금고 열쇠를 찾을 수 없습니다!")
    st.info(
        "**조치 방법:** Streamlit Cloud 설정의 Secrets 항목에 KOBIS_KEY = '발급받은키
