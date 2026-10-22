import datetime
import requests
import pandas as pd
import pytz
import altair as alt
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="일별 박스오피스 순위",
    page_icon="🎬",
    layout="wide"
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
    tz_kst = pytz.timezone('Asia/Seoul')
    now_kst = datetime.datetime.now(tz_kst)
    return now_kst.date() - datetime.timedelta(days=1)

api_key = get_api_key()
max_selectable_date = get_yesterday_kst()

# 3. 날짜 선택 UI
selected_date = st.date_input(
    label="📅 조회할 날짜 선택 (최대 어제까지 가능)",
    value=max_selectable_date,
    max_value=max_selectable_date,
    min_value=datetime.date(2004, 1, 1)
)

target_date = selected_date.strftime("%Y%m%d")
date_display = selected_date.strftime("%Y-%m-%d")
st.caption(f"기준 날짜: {date_display} (한국 시간 기준)")

if not api_key:
    st.error("🔑 API 키(KOBIS_KEY)를 찾을 수 없습니다.")
    st.info("Secrets 항목에 KOBIS_KEY를 등록해 주세요.")
    st.stop()

# 4. KOBIS 박스오피스 API 요청
url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
params = {
    'key': api_key,
    'targetDt': target_date
}

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

# 안정적인 회전 트로피 GIF 태그 정의 (Wikimedia 계열의 고화질 GIF)
trophy_gif = '<img src="https://upload.wikimedia.org/wikipedia/commons/d/d4/Trophy_icon.gif" width="28" style="vertical-align: middle; margin-left: 6px;">'

# 8. 1위 영화 상단 메트릭 카드
top_movie = df.iloc[0]
top_trophy = trophy_gif if top_movie["audiAcc"] >= 1000000 else ""

st.markdown(f"### 🥇 1위: {top_movie['movieNm']}{top_trophy}", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="당일 관객수", value=f"{int(top_movie['audiCnt']):,} 명")
with col2:
    st.metric(label="누적 관객수", value=f"{int(top_movie['audiAcc']):,} 명")
with col3:
    st.metric(label="상영 스크린수", value=f"{int(top_movie['scrnCnt']):,} 개")

st.divider()

# 9. 상위 5개 영화 막대그래프 (1등 황금색 강조)
st.subheader("📊 관객수 상위 5개 영화")
top5_df = df.head(5).copy()

top5_df["구분"] = top5_df["rank"].apply(lambda r: "🥇 1위 (황금)" if r == 1 else "일반 순위")

chart = alt.Chart(top5_df).mark_bar(
    cornerRadiusTopLeft=6,
    cornerRadiusTopRight=6
).encode(
    x=alt.X("movieNm:N", sort=None, title="영화명"),
    y=alt.Y("audiCnt:Q", title="당일 관객수(명)"),
    color=alt.Color(
        "구분:N",
        scale=alt.Scale(
            domain=["🥇 1위 (황금)", "일반 순위"],
            range=["#FFD700", "#4A90E2"]  # 1위는 황금색, 나머지는 파란색
        )
    ),
    tooltip=[
        alt.Tooltip("movieNm:N", title="영화명"),
        alt.Tooltip("audiCnt:Q", title="관객수", format=",")
    ]
).properties(height=350)

st.altair_chart(chart, use_container_width=True)

st.divider()

# 10. 전체 순위 리스트 (회전 트로피 GIF 정상 표시)
st.subheader("📋 박스오피스 전체 순위")

for idx, row in df.iterrows():
    is_million = row["audiAcc"] >= 1000000
    trophy_html = f" {trophy_gif} <span style='color: #d97706; font-size: 0.85rem; font-weight: bold;'>(100만 돌파!)</span>" if is_million else ""
    
    st.markdown(f"#### {int(row['rank'])}위. **{row['movieNm']}**{trophy_html}", unsafe_allow_html=True)
    
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
