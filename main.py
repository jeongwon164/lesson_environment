
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

# --------------------------------------------------
# 1. 페이지 설정
# --------------------------------------------------

st.set_page_config(
    page_title="경기도 온실가스 배출량 분석",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 경기도 시군별 온실가스 배출량과 감축률의 관계")

st.write(
    "경기도 각 시군의 온실가스 배출량과 감축률 사이에 "
    "어떤 관계가 있는지 산점도로 알아봅니다."
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
사용인코딩 = None

for 인코딩 in ["utf-8-sig", "utf-8", "cp949", "euc-kr"]:
    try:
        df = pd.read_csv(
            BytesIO(파일내용),
            encoding=인코딩
        )
        사용인코딩 = 인코딩
        break

    except UnicodeDecodeError:
        continue

    except Exception as e:
        st.error(f"CSV 파일을 읽는 중 문제가 발생했습니다: {e}")
        st.stop()

if df is None:
    st.error(
        "CSV 파일의 인코딩을 확인할 수 없습니다. "
        "UTF-8 또는 CP949 형식으로 저장한 파일인지 확인해 주세요."
    )
    st.stop()

st.success(f"데이터를 불러왔습니다. (인코딩: {사용인코딩})")


# --------------------------------------------------
# 4. 데이터 확인 및 정리
# --------------------------------------------------

필요한열 = [
    "년도",
    "시군명",
    "온실가스배출량(tonCO2-eq)",
    "온실가스감축률(%)"
]

없는열 = [열 for 열 in 필요한열 if 열 not in df.columns]

if 없는열:
    st.error(
        "CSV 파일에 필요한 열이 없습니다: "
        + ", ".join(없는열)
    )
    st.write("현재 CSV 파일의 열 이름:")
    st.write(df.columns.tolist())
    st.stop()

# 중복 데이터 제거
df = df.drop_duplicates().copy()

# 숫자 데이터로 변환
숫자열 = [
    "년도",
    "온실가스배출량(tonCO2-eq)",
    "온실가스감축률(%)"
]

for 열 in 숫자열:
    df[열] = pd.to_numeric(
        df[열].astype(str).str.replace(",", "", regex=False),
        errors="coerce"
    )

# 필요한 값이 없는 행 제거
df = df.dropna(subset=필요한열)


# --------------------------------------------------
# 5. 분석 연도 선택
# --------------------------------------------------

st.subheader("📅 분석할 연도 선택")

연도목록 = sorted(
    df["년도"].astype(int).unique().tolist()
)

if not 연도목록:
    st.error("분석할 수 있는 연도 데이터가 없습니다.")
    st.stop()

기본연도 = 2023 if 2023 in 연도목록 else 연도목록[-1]

선택연도 = st.selectbox(
    "분석할 연도를 선택하세요.",
    options=연도목록,
    index=연도목록.index(기본연도)
)

분석데이터 = df[
    df["년도"] == 선택연도
].copy()

if len(분석데이터) < 2:
    st.error("산점도를 그리려면 최소 2개 이상의 시군 데이터가 필요합니다.")
    st.stop()

st.write(f"**분석 대상: {선택연도}년 경기도 {len(분석데이터)}개 시군**")


# --------------------------------------------------
# 6. 산점도에 사용할 데이터 준비
# --------------------------------------------------

x = 분석데이터[
    "온실가스배출량(tonCO2-eq)"
].to_numpy()

y = 분석데이터[
    "온실가스감축률(%)"
].to_numpy()

# 상관계수 계산
if np.std(x) == 0 or np.std(y) == 0:
    상관계수 = np.nan
else:
    상관계수 = np.corrcoef(x, y)[0, 1]


# --------------------------------------------------
# 7. 산점도 작성
# --------------------------------------------------

fig = px.scatter(
    분석데이터,
    x="온실가스배출량(tonCO2-eq)",
    y="온실가스감축률(%)",
    text="시군명",
    hover_name="시군명",
    title=f"{선택연도}년 경기도 시군별 온실가스 배출량과 감축률",
    labels={
        "온실가스배출량(tonCO2-eq)": "온실가스 배출량 (tonCO2-eq)",
        "온실가스감축률(%)": "온실가스 감축률 (%)"
    }
)

# 점 모양과 글자 설정
fig.update_traces(
    marker=dict(size=11),
    textposition="top center"
)

# --------------------------------------------------
# 8. 회귀 직선 추가
# --------------------------------------------------

if np.std(x) > 0:
    기울기, 절편 = np.polyfit(x, y, 1)

    x_직선 = np.linspace(
        x.min(),
        x.max(),
        100
    )

    y_직선 = 기울기 * x_직선 + 절편

    fig.add_trace(
        go.Scatter(
            x=x_직선,
            y=y_직선,
            mode="lines",
            name="회귀 직선"
        )
    )

# 그래프 꾸미기
fig.update_layout(
    height=650,
    font=dict(size=13),
    xaxis_title="온실가스 배출량 (tonCO2-eq)",
    yaxis_title="온실가스 감축률 (%)",
    legend_title="범례"
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# --------------------------------------------------
# 9. 상관관계 분석 결과
# --------------------------------------------------

st.subheader("📈 상관관계 분석 결과")

if np.isnan(상관계수):
    st.warning("상관계수를 계산할 수 없습니다.")
else:
    st.metric(
        label="온실가스 배출량과 감축률의 상관계수",
        value=f"{상관계수:.3f}"
    )

    if 상관계수 >= 0.7:
        st.info("강한 양의 상관관계가 있습니다.")
    elif 상관계수 >= 0.3:
        st.info("약한 양의 상관관계가 있습니다.")
    elif 상관계수 > -0.3:
        st.info("선형 상관관계가 약합니다.")
    elif 상관계수 > -0.7:
        st.info("약한 음의 상관관계가 있습니다.")
    else:
        st.info("강한 음의 상관관계가 있습니다.")

st.caption(
    "※ 상관관계는 두 변수의 관계를 나타내며, "
    "한 변수가 다른 변수의 원인이라는 뜻은 아닙니다."
)


# --------------------------------------------------
# 10. 분석 데이터 확인
# --------------------------------------------------

with st.expander("📋 산점도에 사용한 데이터 확인하기"):
    st.dataframe(
        분석데이터[필요한열].sort_values(
            "온실가스배출량(tonCO2-eq)",
            ascending=False
        ),
        use_container_width=True,
        hide_index=True
    )

st.divider()

st.caption("경기도 시군별 온실가스 배출량 데이터 분석 실습")
