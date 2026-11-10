
import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# --------------------------------------------------
# 1. 페이지 설정
# --------------------------------------------------

st.set_page_config(
    page_title="경기도 온실가스 배출량 순위",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 경기도 시군별 온실가스 배출량 순위")

st.write(
    "경기도 31개 시군 중 온실가스 배출량이 "
    "가장 많은 지역과 가장 적은 지역을 알아봅니다."
)

st.divider()


# --------------------------------------------------
# 2. CSV 파일 업로드
# --------------------------------------------------

st.subheader("📁 데이터 불러오기")

uploaded_file = st.file_uploader(
    "경기도 시군별 온실가스 배출량 CSV 파일을 올려주세요.",
    type=["csv"]
)

if uploaded_file is None:
    st.info("분석할 CSV 파일을 업로드해 주세요.")
    st.stop()


# --------------------------------------------------
# 3. CSV 인코딩 자동 확인
# --------------------------------------------------

파일내용 = uploaded_file.getvalue()
df = None

for 인코딩 in ["utf-8-sig", "utf-8", "cp949", "euc-kr"]:
    try:
        df = pd.read_csv(
            BytesIO(파일내용),
            encoding=인코딩
        )
        break
    except UnicodeDecodeError:
        continue
    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
        st.stop()

if df is None:
    st.error("CSV 파일의 인코딩을 확인할 수 없습니다.")
    st.stop()

st.success("데이터를 성공적으로 불러왔습니다.")


# --------------------------------------------------
# 4. 필요한 열 확인
# --------------------------------------------------

필요한열 = [
    "년도",
    "시군명",
    "온실가스배출량(tonCO2-eq)"
]

없는열 = [
    열 for 열 in 필요한열
    if 열 not in df.columns
]

if 없는열:
    st.error(f"CSV 파일에 필요한 열이 없습니다: {없는열}")
    st.write("현재 파일의 열 이름:", df.columns.tolist())
    st.stop()


# --------------------------------------------------
# 5. 데이터 정리
# --------------------------------------------------

df = df.drop_duplicates().copy()

df["년도"] = pd.to_numeric(
    df["년도"],
    errors="coerce"
)

df["온실가스배출량(tonCO2-eq)"] = pd.to_numeric(
    df["온실가스배출량(tonCO2-eq)"].astype(str).str.replace(
        ",", "", regex=False
    ),
    errors="coerce"
)

df = df.dropna(
    subset=필요한열
)

# --------------------------------------------------
# 6. 분석 연도 선택
# --------------------------------------------------

st.subheader("📅 분석할 연도 선택")

연도목록 = sorted(
    df["년도"].astype(int).unique().tolist()
)

if not 연도목록:
    st.error("분석할 연도 데이터가 없습니다.")
    st.stop()

기본연도 = 2023 if 2023 in 연도목록 else 연도목록[-1]

선택연도 = st.selectbox(
    "연도를 선택하세요.",
    연도목록,
    index=연도목록.index(기본연도)
)

분석데이터 = df[
    df["년도"] == 선택연도
].copy()

# 시군별 중복 데이터 확인
분석데이터 = 분석데이터.drop_duplicates(
    subset=["시군명"],
    keep="first"
)

if 분석데이터.empty:
    st.error("선택한 연도에 분석할 데이터가 없습니다.")
    st.stop()


# --------------------------------------------------
# 7. 배출량 순위 계산
# --------------------------------------------------

분석데이터 = 분석데이터.sort_values(
    by="온실가스배출량(tonCO2-eq)",
    ascending=False
).reset_index(drop=True)

분석데이터["순위"] = range(
    1, len(분석데이터) + 1
)

최다지역 = 분석데이터.iloc[0]
최소지역 = 분석데이터.iloc[-1]

최다배출량 = 최다지역["온실가스배출량(tonCO2-eq)"]
최소배출량 = 최소지역["온실가스배출량(tonCO2-eq)"]


# --------------------------------------------------
# 8. 가장 많이 배출한 지역 표시
# --------------------------------------------------

st.subheader(f"🏆 {선택연도}년 온실가스 배출량 1위")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "배출량 1위 지역",
        str(최다지역["시군명"])
    )

with col2:
    st.metric(
        "배출량",
        f"{최다배출량:,.0f} tonCO2-eq"
    )

with col3:
    st.metric(
        "배출량 최하위 지역",
        str(최소지역["시군명"])
    )

st.success(
    f"{선택연도}년 온실가스 배출량이 가장 많은 지역은 "
    f"**{최다지역['시군명']}**입니다."
)

st.divider()


# --------------------------------------------------
# 9. 시군별 배출량 순위 그래프
# --------------------------------------------------

st.subheader("📊 시군별 온실가스 배출량 순위")

그래프 = px.bar(
    분석데이터,
    x="온실가스배출량(tonCO2-eq)",
    y="시군명",
    orientation="h",
    text="온실가스배출량(tonCO2-eq)",
    hover_data={
        "순위": True,
        "온실가스배출량(tonCO2-eq)": ":,.0f"
    },
    title=f"{선택연도}년 경기도 시군별 온실가스 배출량",
    labels={
        "온실가스배출량(tonCO2-eq)": "온실가스 배출량 (tonCO2-eq)",
        "시군명": "시군"
    }
)

# 배출량이 많은 지역을 위쪽에 표시
그래프.update_yaxes(
    categoryorder="total ascending"
)

그래프.update_traces(
    texttemplate="%{x:,.0f}",
    textposition="outside"
)

그래프.update_layout(
    height=850,
    xaxis_title="온실가스 배출량 (tonCO2-eq)",
    yaxis_title="시군명",
    showlegend=False
)

st.plotly_chart(
    그래프,
    use_container_width=True
)


# --------------------------------------------------
# 10. 전체 순위표
# --------------------------------------------------

st.subheader("📋 시군별 온실가스 배출량 순위표")

표시데이터 = 분석데이터[
    ["순위", "시군명", "온실가스배출량(tonCO2-eq)"]
].copy()

표시데이터.columns = [
    "순위",
    "시군명",
    "온실가스 배출량 (tonCO2-eq)"
]

st.dataframe(
    표시데이터,
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# 11. 그래프에서 알 수 있는 것
# --------------------------------------------------

st.divider()

st.subheader("💡 이 그래프로 알 수 있는 것")

st.write(
    f"{선택연도}년 경기도에서 온실가스 배출량이 가장 많은 지역은 "
    f"{최다지역['시군명']}이며, "
    f"배출량이 가장 적은 지역은 {최소지역['시군명']}이다. "
    "지역에 따라 온실가스 배출량에 어떤 차이가 있는지 비교할 수 있다."
)
