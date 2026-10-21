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
# 🎨 마인크래프트 스타일 CSS 커스텀 디자인 주입
# ---------------------------------------------------------
st.markdown("""
    <style>
    /* 마인크래프트 공식 느낌의 픽셀 폰트 로드 */
    @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Noto+Sans+KR:wght@700;900&display=swap');

    /* 전체 배경: 마인크래프트 흙 블록(Dirt) 패턴 및 게임 분위기 설정 */
    .stApp {
        background-color: #1e1e1e;
        background-image: 
            radial-gradient(circle at 50% 50%, rgba(0, 0, 0, 0.4) 0%, rgba(0, 0, 0, 0.85) 100%),
            url('https://images.unsplash.com/photo-1627856013091-fed6e4e30025?q=80&w=1000&auto=format&fit=crop'); /* 마인크래프트 픽셀 스타일 패턴 배경 */
        background-attachment: fixed;
        background-size: cover;
        font-family: 'Noto Sans KR', sans-serif;
        color: #ffffff;
    }

    /* 마인크래프트 상단 헤더 배너 (공식 캐릭터 배치: 스티브, 알렉스, 크리퍼, 엔더맨, 돼지) */
    .mc-header-container {
        background: linear-gradient(180deg, rgba(30, 20, 10, 0.9) 0%, rgba(10, 10, 10, 0.95) 100%);
        border: 4px solid #5c3818;
        box-shadow: inset -4px -4px 0px #2a180b, inset 4px 4px 0px #8f5828, 0px 8px 16px rgba(0,0,0,0.8);
        padding: 20px;
        border-radius: 4px;
        text-align: center;
        margin-bottom: 25px;
        position: relative;
    }

    /* 타이틀 폰트 (마인크래프트 픽셀 폰트) */
    .mc-title {
        font-family: 'Press Start 2P', cursive;
        color: #55FF55; /* 마인크래프트 라임 그린 색상 */
        text-shadow: 3px 3px 0px #00AA00, 5px 5px 0px #000000;
        font-size: 2rem;
        margin-bottom: 10px;
    }

    /* 마인크래프트 HUD 패널 (글씨 가독성을 높이기 위한 반투명 상자) */
    div[data-testid="stMetric"], div.stDataFrame, div[data-testid="stForm"] {
        background: rgba(20, 20, 20, 0.85) !important;
        border: 4px solid #3c3c3c !important;
        border-image: initial;
        box-shadow: inset -4px -4px 0px #1e1e1e, inset 4px 4px 0px #626262, 0 4px 10px rgba(0,0,0,0.7) !important;
        padding: 15px !important;
        border-radius: 2px !important;
    }

    /* 지표 카드(Metric) 글자 색상 및 가독성 조정 */
    [data-testid="stMetricLabel"] {
        color: #
