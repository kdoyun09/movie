import datetime
import requests
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
# 🎨 마인크래프트 커스텀 CSS (문법 에러 방지를 위한 정돈된 스타일)
# ---------------------------------------------------------
css_code = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Noto+Sans+KR:wght@700;900&display=swap');

/* 전체 배경 설정 */
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

/* 상단 메인 헤더 배너 */
.mc-header-container {
    background: linear-gradient(180deg, rgba(35, 25, 15, 0.95) 0%, rgba(15, 15, 15, 0.98) 100%);
    border: 4px solid #5c3818;
    box-shadow: inset -4px -4px 0px #2a180b, inset 4px 4px 0px #8f5828, 0px 8px 16px rgba(0,0,0,0.8);
    padding: 25px;
    border-radius: 4px;
    text-align: center;
    margin-bottom: 25px;
}

/* 마인크래프트 타이틀 폰트 */
.mc-title {
    font-family: 'Press Start 2P', cursive;
    color: #55FF55;
    text-shadow: 3px 3px 0px #00AA00, 5px 5px 0px #000000;
    font-size: 1.8rem;
    margin-bottom: 15px;
}

/* 캐릭터 픽셀 배너 아이콘 */
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

/* 데이터 지표 카드 및 표 가독성 패널 (HUD UI 스타일) */
div[data-testid="stMetric"], div.stDataFrame {
    background: rgba(18, 18, 18, 0.92) !important;
    border: 3px solid #4a4a4a !important;
    box-shadow: inset -3px -3px 0px #111111, inset 3px 3px 0px #666666, 0 4px 12px rgba(0,0,0,0.8) !important;
    padding: 15px !important;
    border-radius: 2px !important;
}

/* 카드 텍스트 색상 고대비 설정 */
[data-testid="stMetricLabel"] {
    color: #FFFF55 !important;
    font-weight: bold !important;
    font-size: 1.05rem !important;
}
[data-testid="stMetricValue"] {
    color: #FFFFFF !important;
    font-weight: 900 !important;
}

/* 제목 텍스트 색상 */
h2, h3 {
    color: #FFAA00 !important;
    text-shadow: 2px 2px 0px #000000;
    font-weight: 900 !important;
}

/* 구분선 */
hr {
    border-top: 3px dashed #55FF55 !important;
}
</style>
"""
st.markdown(css_code, unsafe_allow_html=True)


# ---------------------------------------------------------
# ⛏️ 헤더 구성
# ---------------------------------------------------------
header_html = """
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
"""
st.markdown(header_html, unsafe_allow_html=True)


# 1. secrets에서 API 키 가져오기
def get_api_key():
    try:
        return st.secrets["KOBIS_KEY"]
    except Exception:
        return None


# 2. 한국 시간(KST) 기준 어제 날짜 구하기
def get_yesterday_kst():
    tz_kst = pytz.timezone("Asia/Seoul")
    now_kst = datetime.datetime.now(tz_kst)
    return now_kst.date() - datetime.timedelta(days=1)


api_key = get_api_key()
max_selectable_date = get_yesterday_kst()

# 3. 달력 선택 UI
selected_date = st.date_input(
    label="📅 탐험할 날짜 선택 (최대 어제까지 가능)",
    value=max_selectable_date,
    max_value=max_selectable_date,
    min_value=datetime.date(2004, 1, 1),
)

target_date = selected_date.strftime("%Y%m%d")
st.caption(
    f"🧱 현재 세계 시각: {selected_date.strftime('%Y-%m-%d')} (한국 표준
