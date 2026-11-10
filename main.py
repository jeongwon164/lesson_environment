import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(
    page_title="경기도 시군별 온실가스 배출량 분석",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 경기도 시군별 온실가스 배출량과 감축률의 관계")

# 1. 데이터 불러오기
데이터주소 = (
    "https://data.gg.go.kr/portal/data/sheet/downloadSheetData.do"
    "?downloadType=C&infId=VJWZJK4EHADPZ7C4J5LB31529041&infSeq=1"
)

try:
    df = pd.read_csv(데이터주소, encoding="cp949")
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# 2. 중복 데이터 제거
df = df.drop_duplicates()

# 3. 2023년 데이터만 선택
분석데이터 = df[df["년도"] == 2023].copy()

# 4. 필요한 열의 결측치 제거
분석데이터 = 분석데이터.dropna(
    subset=[
        "온실가스배출량(tonCO2-eq)",
        "온실가스감축률(%)"
    ]
)

if len(분석데이터) < 2:
    st.error("산점도를 그리기에 데이터가 부족합니다.")
    st.stop()

# 5. 상관계수 계산
x = 분석데이터["온실가스배출량(tonCO2-eq)"].to_numpy()
y = 분석데이터["온실가스감축률(%)"].to_numpy()

상관계수 = np.corrcoef(x, y)[0, 1]

# 6. 회귀 직선 계산
기울기, 절편 = np.polyfit(x, y, 1)

x_직선 = np.linspace(x.min(), x.max(), 100)
y_직선 = 기울기 * x_직선 + 절편

# 7. 산점도 작성
fig = px.scatter(
    분석데이터,
    x="온실가스배출량(tonCO2-eq)",
    y="온실가스감축률(%)",
    hover_name="시군명",
    text="시군명",
    title="시군별 온실가스 배출량과 감축률의 관계",
    labels={
        "온실가스배출량(tonCO2-eq)": "온실가스 배출량 (tonCO2-eq)",
        "온실가스감축률(%)": "온실가스 감축률 (%)"
    }
)

# 8. 회귀 직선 추가
fig.add_trace(
    go.Scatter(
        x=x_직선,
        y=y_직선,
        mode="lines",
        name="회귀 직선"
    )
)

# 9. 그래프 꾸미기
fig.update_traces(
    selector=dict(mode="markers+text"),
    textposition="top center",
    marker=dict(size=10)
)

fig.update_layout(
    height=600,
    xaxis_title="온실가스 배출량 (tonCO2-eq)",
    yaxis_title="온실가스 감축률 (%)"
)

st.plotly_chart(fig, use_container_width=True)

# 10. 상관계수 표시
st.metric(
    "온실가스 배출량과 감축률의 상관계수",
    f"{상관계수:.3f}"
)

st.write(
    "상관계수가 0보다 작으면 음의 상관관계, "
    "0보다 크면 양의 상관관계를 의미합니다."
)
