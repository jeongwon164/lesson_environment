
import streamlit as st
import pandas as pd
import plotly.express as px

# --------------------------------
# 1. 페이지 설정
# --------------------------------
st.set_page_config(
    page_title="경기도 시군별 온실가스 배출량",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 경기도 시군별 온실가스 배출량")
st.write("2023년 경기도 31개 시군의 온실가스 배출량을 비교합니다.")

# --------------------------------
# 2. 데이터 불러오기
# --------------------------------
파일 = st.file_uploader(
    "CSV 파일을 올려 주세요.",
    type=["csv"]
)

if 파일 is None:
    st.info("경기도시군별온실가스배출량.csv 파일을 업로드해 주세요.")
    st.stop()

try:
    try:
        df = pd.read_csv(파일, encoding="cp949")
    except UnicodeDecodeError:
        파일.seek(0)
        df = pd.read_csv(파일, encoding="utf-8-sig")

except Exception as e:
    st.error(f"파일을 읽을 수 없습니다: {e}")
    st.stop()

# --------------------------------
# 3. 데이터 정리
# --------------------------------

# 완전히 동일한 중복 행 제거
df = df.drop_duplicates().copy()

# 분석에 필요한 열
년도열 = "년도"
시군열 = "시군명"
배출량열 = "온실가스배출량(tonCO2-eq)"
감축률열 = "온실가스감축률(%)"

# 숫자 데이터 변환
df[년도열] = pd.to_numeric(df[년도열], errors="coerce")
df[배출량열] = pd.to_numeric(df[배출량열], errors="coerce")
df[감축률열] = pd.to_numeric(df[감축률열], errors="coerce")

# 2023년 자료만 추출
분석데이터 = df[df[년도열] == 2023].copy()

# 필요한 값이 없는 행 제거
분석데이터 = 분석데이터.dropna(
    subset=[시군열, 배출량열]
)

# 시군별 중복 확인
분석데이터 = 분석데이터.drop_duplicates(
    subset=[시군열]
)

if 분석데이터.empty:
    st.error("2023년 자료를 찾을 수 없습니다.")
    st.stop()

# --------------------------------
# 4. 주요 통계
# --------------------------------

st.subheader("📊 2023년 주요 통계")

가장많이배출 = 분석데이터.loc[
    분석데이터[배출량열].idxmax()
]

가장적게배출 = 분석데이터.loc[
    분석데이터[배출량열].idxmin()
]

col1, col2, col3 = st.columns(3)

col1.metric(
    "분석 시군 수",
    f"{분석데이터[시군열].nunique()}개"
)

col2.metric(
    "온실가스 총배출량",
    f"{분석데이터[배출량열].sum():,.0f} tonCO2-eq"
)

col3.metric(
    "시군별 평균 배출량",
    f"{분석데이터[배출량열].mean():,.1f} tonCO2-eq"
)

st.divider()

# --------------------------------
# 5. 시군별 온실가스 배출량 그래프
# --------------------------------

st.subheader("① 시군별 온실가스 배출량")

# 배출량이 적은 순서로 정렬
그래프데이터 = 분석데이터.sort_values(
    by=배출량열,
    ascending=True
)

fig = px.bar(
    그래프데이터,
    x=배출량열,
    y=시군열,
    orientation="h",
    color=배출량열,
    color_continuous_scale="Oranges",
    text=배출량열,
    hover_data={
        시군열: True,
        배출량열: ":,.0f"
    },
    labels={
        시군열: "시군",
        배출량열: "온실가스 배출량 (tonCO2-eq)"
    },
    title="2023년 경기도 시군별 온실가스 배출량"
)

fig.update_traces(
    texttemplate="%{text:,.0f}",
    textposition="outside"
)

fig.update_layout(
    height=750,
    xaxis_title="온실가스 배출량 (tonCO2-eq)",
    yaxis_title="시군",
    coloraxis_showscale=False,
    showlegend=False
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.markdown(
    "**이 그래프로 알 수 있는 것**"
)

st.write(
    "경기도에서 온실가스를 가장 많이 배출하는 시군과 "
    "가장 적게 배출하는 시군을 비교할 수 있습니다."
)

st.divider()

# --------------------------------
# 6. 가장 많이 배출하는 시군과 적게 배출하는 시군
# --------------------------------

st.subheader("② 배출량 비교")

col1, col2 = st.columns(2)

with col1:
    st.write("🔴 가장 많이 배출하는 시군")
    st.metric(
        가장많이배출[시군열],
        f"{가장많이배출[배출량열]:,.0f} tonCO2-eq"
    )

with col2:
    st.write("🟢 가장 적게 배출하는 시군")
    st.metric(
        가장적게배출[시군열],
        f"{가장적게배출[배출량열]:,.0f} tonCO2-eq"
    )

# --------------------------------
# 7. 데이터 표
# --------------------------------

st.subheader("③ 시군별 데이터")

표시열 = [
    "년도",
    "시군명",
    "기준배출량(tonCO2-eq)",
    "온실가스배출량(tonCO2-eq)",
    "온실가스감축량(tonCO2-eq)",
    "온실가스감축률(%)"
]

st.dataframe(
    분석데이터[표시열].sort_values(
        by=배출량열,
        ascending=False
    ),
    use_container_width=True,
    hide_index=True
)

st.caption("자료 출처: 경기도 데이터드림")
