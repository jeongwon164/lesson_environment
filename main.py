import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.title("📊 시군별 온실가스 배출량과 감축률의 관계")

# 데이터 불러오기
df = pd.read_csv(
    "https://raw.githubusercontent.com/사용자아이디/저장소/main/파일이름.csv",
    encoding="cp949"
)

# 2023년 데이터만 선택
분석데이터 = df[df["년도"] == 2023].copy()

# 필요한 열의 결측치 제거
분석데이터 = 분석데이터.dropna(
    subset=[
        "온실가스배출량(tonCO2-eq)",
        "온실가스감축률(%)"
    ]
)

# x축과 y축 데이터
x = 분석데이터["온실가스배출량(tonCO2-eq)"].to_numpy()
y = 분석데이터["온실가스감축률(%)"].to_numpy()

# 상관계수 계산
상관계수 = np.corrcoef(x, y)[0, 1]

# 회귀 직선 계산
기울기, 절편 = np.polyfit(x, y, 1)

x_직선 = np.linspace(x.min(), x.max(), 100)
y_직선 = 기울기 * x_직선 + 절편

# 산점도 그리기
fig = px.scatter(
    분석데이터,
    x="온실가스배출량(tonCO2-eq)",
    y="온실가스감축률(%)",
    text="시군명",
    hover_name="시군명",
    title="시군별 온실가스 배출량과 감축률의 관계",
    labels={
        "온실가스배출량(tonCO2-eq)": "온실가스 배출량 (tonCO2-eq)",
        "온실가스감축률(%)": "온실가스 감축률 (%)"
    }
)

# 회귀 직선 추가
fig.add_trace(
    go.Scatter(
        x=x_직선,
        y=y_직선,
        mode="lines",
        name="회귀 직선"
    )
)

# 그래프 꾸미기
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

# 상관계수 표시
st.metric("온실가스 배출량과 감축률의 상관계수", f"{상관계수:.3f}")

st.write(
    "상관계수는 두 변수 사이의 선형적인 관계를 나타냅니다. "
    "0에 가까우면 선형 관계가 약하고, "
    "1에 가까우면 양의 관계, -1에 가까우면 음의 관계입니다."
)
