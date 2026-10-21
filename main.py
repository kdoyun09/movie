import datetime
import requests
import pandas as pd
import pytz
import streamlit as st

# 페이지 기본 설정 (제목 및 레이아웃)
st.set_page_config(
    page_title="어제 박스오피스 순위", page_icon="🎬", layout="wide"
)

st.title("🎬 어제 일별 박스오피스 순위")


# 1. secrets에서 KOBIS API 키 불러오기
def get_api_key():
    try:
        return st.secrets["KOBIS_KEY"]
    except Exception:
        return None


# 2. 한국 시간(KST) 기준 '어제' 날짜 계산 함수
def get_yesterday_kst():
    # 서버 시계와 상관없이 한국 표준시(Asia/Seoul)를 기준으로 현재 시간 계산
    tz_kst = pytz.timezone("Asia/Seoul")
    now_kst = datetime.datetime.now(tz_kst)
    # 오늘에서 하루(1일)를 빼서 어제 날짜 구하기
    yesterday = now_kst - datetime.timedelta(days=1)
    # API 요청 규격인 YYYYMMDD 형태의 문자열로 변환 (예: 20261020)
    return yesterday.strftime("%Y%m%d")


# API 키 확인 및 날짜 계산
api_key = get_api_key()
target_date = get_yesterday_kst()

# 한국어 날짜 표시용 (YYYY-MM-DD)
formatted_date = f"{target_date[:4]}-{target_date[4:6]}-{target_date[6:]}"
st.caption(f" 기준 날짜: {formatted_date} (한국 시간 기준 어제)")

# API 키가 secrets에 없는 경우 예외 처리
if not api_key:
    st.error("🔑 API 키(KOBIS_KEY)를 찾을 수 없습니다.")
    st.info(
        "**확인 및 조치 방법:**\n"
        "1. 로컬 환경일 경우 `.streamlit/secrets.toml` 파일에 `KOBIS_KEY = '발급받은키'`를 작성했는지 확인하세요.\n"
        "2. Streamlit Cloud 배포 환경일 경우 설정 메뉴의 **App settings -> Secrets**에 `KOBIS_KEY`가 올바르게 등록되었는지 확인하세요."
    )
    st.stop()

# 3. KOBIS API 데이터 요청
url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
params = {"key": api_key, "targetDt": target_date}

try:
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()  # HTTP 상태 코드 200번대가 아닌 경우 에러 발생
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

# 4. API 응답 에러 검증 (인증키 오류 시 faultInfo 응답 처리)
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

# 영화 목록이 비어 있는 경우 예외 처리
if not daily_list:
    st.warning("ℹ️ 어제 날짜의 박스오피스 데이터가 아직 집계되지 않았거나 비어 있습니다.")
    st.info(
        "**확인 및 조치 방법:**\n"
        "1. KOBIS API의 일별 집계 반영 시간이 지났는지 확인해 주세요.\n"
        "2. 잠시 후 페이지를 새로고침(F5)하여 다시 확인해 주세요."
    )
    st.stop()

# 5. 데이터 프레임 변환 및 전처리
df = pd.DataFrame(daily_list)

# 숫자로 변환해야 하는 컬럼 리스트 (KOBIS API는 숫자를 문자열로 반환함)
numeric_cols = ["rank", "audiCnt", "audiAcc", "scrnCnt"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# 6. Top 1 영화 지표 카드(Metric) 출력
top_movie = df.iloc[0]

st.subheader(f"🥇 1위: {top_movie['movieNm']}")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="어제 관객수", value=f"{int(top_movie['audiCnt']):,} 명"
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

# 7. 상위 5개 영화 관객수 막대그래프 시각화
st.subheader("📊 관객수 상위 5개 영화")
top5_df = df.head(5).copy()

# 막대그래프에 필요한 컬럼 정리 및 이름 변경
chart_df = top5_df.set_index("movieNm")[["audiCnt"]]
chart_df.columns = ["어제 관객수"]

st.bar_chart(chart_df)

st.divider()

# 8. 전체 순위 데이터 표(Table) 출력
st.subheader("📋 어제 박스오피스 전체 순위")

# 화면에 보여줄 컬럼 선택 및 보기 좋은 컬럼명으로 변경
display_df = df[
    ["rank", "movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]
].copy()
display_df.columns = [
    "순위",
    "영화명",
    "개봉일",
    "관객수(명)",
    "누적관객수(명)",
    "스크린수(개)",
]

# 숫자에 천 단위 쉼표(,) 및 정수 포맷 적용하여 출력
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
