import datetime
import requests
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
    yesterday = now_kst.date() - datetime.timedelta(days=1)
    return yesterday


# API 키 확인
api_key = get_api_key()

# KST 기준 어제 날짜 계산 (달력 선택 최대 한계값)
max_selectable_date = get_yesterday_kst()

# 3. 달력을 통한 조회 날짜 선택 UI (기본값: 어제, 선택 가능한 최대 날짜: 어제)
selected_date = st.date_input(
    label="📅 조회할 날짜를 선택하세요 (최대 어제까지 선택 가능)",
    value=max_selectable_date,
    max_value=max_selectable_date,
    min_value=datetime.date(2004, 1, 1),  # KOBIS 제공 시작 연도
)

# 선택한 날짜를 API 규격(YYYYMMDD) 문자열로 변환
target_date = selected_date.strftime("%Y%m%d")

st.caption(
    f" 기준 날짜: {selected_date.strftime('%Y-%m-%d')} (한국 시간 기준)"
)

# API 키가 secrets에 없는 경우 예외 처리
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

# 5. API 응답 에러 검증 (인증키 오류 시 faultInfo 응답 처리)
box_office_result = data.get("boxOfficeResult", {})

if "faultInfo" in data or not box_office_result:
    fault = data.get("faultInfo", {})
    message = fault.get("message", "응답 데이터가 올바르지 않습니다.")
    st.error("⚠️ API 응답 오류가 발생했습니다.")
    st.info(
        "**확인 및 조치 방법:**\n"
        f"1. **오류 메시지:** {message}\n"
        "2. Secrets에 등록된 KOBIS API 인증키가 정당한 키인지 확인해 주세요.\n"
        "3. 영화진흥위원회 오픈API 마이페이지에서 키 상태 및 일일 사용량을 확인해 주세요."
    )
    st.stop()

daily_list = box_office_result.get("dailyBoxOfficeList", [])

# 영화 목록이 비어 있는 경우 예외 처리 (요청사항 반영)
if not daily_list:
    st.warning("ℹ️ 그날은 아직 집계 전입니다.")
    st.info(
        "**확인 및 조치 방법:**\n"
        "1. 해당 날짜의 박스오피스 데이터 집계가 아직 완료되지 않았을 수 있습니다.\n"
        "2. 날짜를 변경하거나 잠시 후 다시 시도해 주세요."
    )
    st.stop()

# 6. 데이터 프레임 변환 및 전처리
df = pd.DataFrame(daily_list)

# 숫자형 컬럼 변환
numeric_cols = ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)


# 7. 순위 증감 화살표 텍스트 생성 함수
def format_rank_change(val):
    if val > 0:
        return f"🔺 +{val}"  # 순위 상승 (빨간 위 화살표)
    elif val < 0:
        return f"🔹 {val}"  # 순위 하강 (파란 아래 화살표)
    else:
        return "-"  # 변동 없음


df["순위증감"] = df["rankInten"].apply(format_rank_change)


# 8. 누적관객 100만 명 이상 영화명 옆에 트로피(🏆) 이모지 추가 함수
def format_movie_title(row):
    title = row["movieNm"]
    if row["audiAcc"] >= 1000000:
        return f"{title} 🏆"
    return title


df["표시영화명"] = df.apply(format_movie_title, axis=1)

# 9. Top 1 영화 지표 카드(Metric) 출력
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

# 10. 상위 5개 영화 관객수 막대그래프 시각화
st.subheader("📊 관객수 상위 5개 영화")
top5_df = df.head(5).copy()

# 막대그래프용 데이터셋 준비
chart_df = top5_df.set_index("movieNm")[["audiCnt"]]
chart_df.columns = ["당일 관객수"]

st.bar_chart(chart_df)

st.divider()

# 11. 전체 순위 데이터 표(Table) 출력
st.subheader("📋 박스오피스 전체 순위")

# 표에 출력할 컬럼 순서 및 이름 지정
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

# 데이터 프레임 출력
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
