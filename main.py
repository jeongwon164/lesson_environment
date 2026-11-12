
import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# --------------------------------------------------
# 1. 페이지 설정
# --------------------------------------------------

st.set_page_config(
    page_title="경기도 온실가스 배출량 감소 분석",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 경기도 시군별 온실가스 배출량 감소 분석")

st.write(
    "연도별 온실가스 배출량을 비교하여 "
    "배출량이 가장 많이 감소한 지역을 찾아봅니다."
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
    st.info("먼저 CSV 파일을 업로드해 주세요.")
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
    st.write("현재 CSV 파일의 열 이름:")
    st.write(df.columns.tolist())
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
    df["온실가스배출량(tonCO2-eq)"]
    .astype(str)
    .str.replace(",", "", regex=False),
    errors="coerce"
)

df = df.dropna(subset=필요한열)

df["년도"] = df["년도"].astype(int)


# --------------------------------------------------
# 6. 비교할 연도 선택
# --------------------------------------------------

st.subheader("📅 비교할 연도 선택")

연도목록 = sorted(df["년도"].unique().tolist())

if len(연도목록) < 2:
    st.error("비교하려면 최소 2개 연도의 데이터가 필요합니다.")
    st.stop()

기준연도 = st.selectbox(
    "기준 연도",
    연도목록,
    index=0
)

비교연도 = st.selectbox(
    "비교 연도",
    연도목록,
    index=len(연도목록) - 1
)

if 기준연도 >= 비교연도:
    st.warning("비교 연도는 기준 연도보다 뒤의 연도를 선택해 주세요.")
    st.stop()


# --------------------------------------------------
# 7. 연도별 시군 배출량 정리
# --------------------------------------------------

분석데이터 = df[
    df["년도"].isin([기준연도, 비교연도])
].copy()

# 시군별, 연도별 배출량 합계
연도별데이터 = (
    분석데이터
    .groupby(["시군명", "년도"])["온실가스배출량(tonCO2-eq)"]
    .sum()
    .reset_index()
)

# 시군별로 연도 데이터를 나란히 배치
비교표 = 연도별데이터.pivot(
    index="시군명",
    columns="년도",
    values="온실가스배출량(tonCO2-eq)"
).reset_index()

# 두 연도 모두 자료가 있는 시군만 분석
비교표 = 비교표.dropna(
    subset=[기준연도, 비교연도]
).copy()

if 비교표.empty:
    st.error("두 연도에 모두 존재하는 시군 데이터가 없습니다.")
    st.stop()


# --------------------------------------------------
# 8. 배출량 감소량과 감소율 계산
# --------------------------------------------------

비교표["배출량 감소량"] = (
    비교표[기준연도] - 비교표[비교연도]
)

비교표["배출량 감소율(%)"] = (
    비교표["배출량 감소량"]
    / 비교표[기준연도]
    .replace(0, float("nan"))
    * 100
)

# 감소량이 큰 순서로 정렬
비교표 = 비교표.sort_values(
    "배출량 감소량",
    ascending=False
).reset_index(drop=True)

비교표["순위"] = range(1, len(비교표) + 1)


# --------------------------------------------------
# 9. 가장 많이 감소한 지역 표시
# --------------------------------------------------

st.divider()

st.subheader(
    f"🏆 {기준연도}년~{비교연도}년 배출량 감소 1위"
)

최다감소지역 = 비교표.iloc[0]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "배출량이 가장 많이 감소한 지역",
        str(최다감소지역["시군명"])
    )

with col2:
    st.metric(
        "배출량 감소량",
        f"{최다감소지역['배출량 감소량']:,.0f} tonCO2-eq"
    )

with col3:
    감소율 = 최다감소지역["배출량 감소율(%)"]

    if pd.notna(감소율):
        st.metric(
            "배출량 감소율",
            f"{감소율:.2f}%"
        )
    else:
        st.metric("배출량 감소율", "계산 불가")

if 최다감소지역["배출량 감소량"] > 0:
    st.success(
        f"**{최다감소지역['시군명']}**의 온실가스 배출량이 "
        f"가장 많이 감소했습니다."
    )
else:
    st.warning(
        "비교한 시군 중 배출량이 감소한 지역이 없습니다."
    )


# --------------------------------------------------
# 10. 배출량 감소 상위 10개 지역 그래프
# --------------------------------------------------

st.divider()

st.subheader("📊 온실가스 배출량 감소 상위 10개 지역")

상위10개 = 비교표.head(10).copy()

그래프 = px.bar(
    상위10개,
    x="배출량 감소량",
    y="시군명",
    orientation="h",
    text="배출량 감소량",
    hover_data={
        "순위": True,
        "배출량 감소량": ":,.0f",
        "배출량 감소율(%)": ":.2f"
    },
    title=f"{기준연도}년 대비 {비교연도}년 배출량 감소량",
    labels={
        "배출량 감소량": "배출량 감소량 (tonCO2-eq)",
        "시군명": "시군명"
    }
)

그래프.update_yaxes(
    categoryorder="total ascending"
)

그래프.update_traces(
    texttemplate="%{x:,.0f}",
    textposition="outside"
)

그래프.update_layout(
    height=550,
    xaxis_title="배출량 감소량 (tonCO2-eq)",
    yaxis_title="시군명",
    showlegend=False
)

st.plotly_chart(
    그래프,
    use_container_width=True
)


# --------------------------------------------------
# 11. 전체 시군 비교표
# --------------------------------------------------

st.divider()

st.subheader("📋 시군별 배출량 변화 순위")

표시데이터 = 비교표[
    [
        "순위",
        "시군명",
        기준연도,
        비교연도,
        "배출량 감소량",
        "배출량 감소율(%)"
    ]
].copy()

표시데이터.columns = [
    "순위",
    "시군명",
    f"{기준연도}년 배출량",
    f"{비교연도}년 배출량",
    "배출량 감소량",
    "배출량 감소율(%)"
]

st.dataframe(
    표시데이터,
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# 12. 결과 해석
# --------------------------------------------------

st.divider()

st.subheader("💡 이 그래프로 알 수 있는 것")

st.write(
    f"{기준연도}년과 {비교연도를} 비교했을 때 "
    f"온실가스 배출량이 가장 많이 감소한 지역은 "
    f"{최다감소지역['시군명']}이다. "
    f"배출량 감소량은 "
    f"{최다감소지역['배출량 감소량']:,.0f} tonCO2-eq이다."
)

st.caption(
    "※ 감소량이 양수이면 배출량이 감소한 것이고, "
    "음수이면 배출량이 증가한 것입니다. "
    "감소량은 실제 배출량의 두 연도 간 차이로 계산했습니다."
)
