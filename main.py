import datetime
import math
import pandas as pd
import plotly.graph_objects as go
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

# 3D 입체 회전 황금 트로피 HTML
trophy_3d_html = """
<span style="display: inline-block; perspective: 1000px; vertical-align: middle; margin-left: 8px;">
    <span style="display: inline-block; font-size: 1.6rem; transform-style: preserve-3d; animation: spin3D 2.5s infinite linear; filter: drop-shadow(2px 4px 6px rgba(0,0,0,0.3));">🏆</span>
</span>
<style>
@keyframes spin3D {
    0% { transform: rotateY(0deg) scale3d(1, 1, 1); }
    50% { transform: rotateY(180deg) scale3d(1.15, 1.15, 1.15); }
    100% { transform: rotateY(360deg) scale3d(1, 1, 1); }
}
</style>
"""

# 8. 1위 영화 상단 카드
top_movie = df.iloc[0]
top_trophy = trophy_3d_html if top_movie["audiAcc"] >= 1000000 else ""

st.markdown(
    f"### 🥇 1위: {top_movie['movieNm']}{top_trophy}", unsafe_allow_html=True
)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="당일 관객수", value=f"{int(top_movie['audiCnt']):,} 명")
with col2:
    st.metric(label="누적 관객수", value=f"{int(top_movie['audiAcc']):,} 명")
with col3:
    st.metric(label="상영 스크린수", value=f"{int(top_movie['scrnCnt']):,} 개")

st.divider()

# 9. 상위 5개 영화 3D 입체 원기둥 차트 생성
st.subheader("📊 관객수 상위 5개 영화 (3D 입체 원기둥 차트)")
top5_df = df.head(5).copy()

fig = go.Figure()

# 1위는 황금색(#FFD700), 나머지는 시원한 파란색 계열
colors = ["#FFD700", "#3B82F6", "#60A5FA", "#93C5FD", "#BFDBFE"]


# 3D 원기둥을 그리는 메쉬 생성 함수
def make_cylinder(x_center, radius, height, num_sides=32):
    angles = [
        2 * math.pi * i / num_sides for i in range(num_sides)
    ] + [0]
    # 바닥 원 및 윗면 원의 x, y, z 좌표
    x_bottom = [x_center + radius * math.cos(a) for a in angles]
    y_bottom = [radius * math.sin(a) for a in angles]
    z_bottom = [0] * len(angles)

    x_top = x_bottom
    y_top = y_bottom
    z_top = [height] * len(angles)

    x = x_bottom + x_top
    y = y_bottom + y_top
    z = z_bottom + z_top

    # 메쉬 삼각형 면(Face) 연결
    i, j, k = [], [], []
    n = num_sides + 1
    for idx in range(num_sides):
        # 옆면
        i.extend([idx, idx + 1, idx])
        j.extend([idx + 1, idx + n + 1, idx + n])
        k.extend([idx + n + 1, idx + n, idx + n + 1])

    return x, y, z, i, j, k


# 상위 5개 영화에 대해 3D 원기둥 배치
for idx, row in top5_df.iterrows():
    height = row["audiCnt"]
    movie_name = row["movieNm"]
    color = colors[idx]

    x, y, z, i_idx, j_idx, k_idx = make_cylinder(
        x_center=idx * 2.5, radius=0.8, height=height
    )

    fig.add_trace(
        go.Mesh3d(
            x=x,
            y=y,
            z=z,
            i=i_idx,
            j=j_idx,
            k=k_idx,
            color=color,
            opacity=0.95,
            name=f"{idx+1}위: {movie_name}",
            hovertemplate=f"<b>{int(row['rank'])}위. {movie_name}</b><br>관객수: {int(height):,}명<extra></extra>",
        )
    )

# 3D 축 및 카테고리 레이블 설정
x_ticks = [i * 2.5 for i in range(len(top5_df))]
x_labels = [f"{int(r['rank'])}위<br>{r['movieNm'][:6]}" for _, r in top5_df.iterrows()]

fig.update_layout(
    scene=dict(
        xaxis=dict(
            title="영화명",
            tickmode="array",
            tickvals=x_ticks,
            ticktext=x_labels,
            showgrid=True,
        ),
        yaxis=dict(visible=False),  # 두께(Y축) 숨김
        zaxis=dict(title="당일 관객수(명)", showgrid=True),
        camera=dict(
            eye=dict(x=1.8, y=-1.8, z=1.2)  # 입체감을 잘 보여주는 3D 시점
        ),
    ),
    margin=dict(l=0, r=0, b=0, t=20),
    height=450,
    showlegend=True,
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# 10. 전체 순위 리스트 (3D 회전 트로피 적용)
st.subheader("📋 박스오피스 전체 순위")

for idx, row in df.iterrows():
    is_million = row["audiAcc"] >= 1000000
    trophy_html = (
        f" {trophy_3d_html} <span style='color: #d97706; font-size: 0.85rem; font-weight: bold;'>(100만 돌파!)</span>"
        if is_million
        else ""
    )

    st.markdown(
        f"#### {int(row['rank'])}위. **{row['movieNm']}**{trophy_html}",
        unsafe_allow_html=True,
    )

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
