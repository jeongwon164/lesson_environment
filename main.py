
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
from io import BytesIO

# -----------------------------------------
# 1. 페이지 설정
# -----------------------------------------
st.set_page_config(
    page_title="경기도 시군별 온실가스 배출량",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 경기도 시군별 온실가스 배출량")
st.markdown("""
경기도 31개 시군의 온실가스 배출 현황을 살펴보는 데이터 분석 실습실입니다.

**분석 기준: 2023년**
""")

# -----------------------------------------
# 2. 데이터 불러오기
# -----------------------------------------
DATA_URL = (
    "https://data.gg.go.kr/portal/data/sheet/"
    "downloadSheetData.do"
    "?downloadType=C"
    "&infId=VJWZJK4EHADPZ7C4J5LB31529041"
    "&infSeq=1"
)


@st.cache_data
def load_data():
    response = requests.get(DATA_URL, timeout=30)
    response.raise_for_status()

    file_data = response.content

    if file_data[:100].lstrip().lower().startswith(
        (b"<!doctype html", b"<html")
    ):
        raise ValueError(
            "CSV 다운로드 주소에서 HTML 페이지가 반환되었습니다."
        )

    errors = []

    for encoding in ["utf-8-sig", "cp949", "euc-kr"]:
        try:
            df = pd.read_csv(
                BytesIO(file_data),
                encoding=encoding,
                sep=None,
                engine="python"
            )
            if len(df.columns) > 1:
                return df
        except Exception as e:
            errors.append(str(e))

    raise ValueError("CSV 파일을 읽지 못했습니다.")


uploaded_file = st.file_uploader(
    "CSV 파일을 직접 업로드할 수도 있습니다.",
    type=["csv"]
)

try:
    if uploaded_file is not None:
        df = pd.read_csv(
            uploaded_file,
            encoding="utf-8-sig",
            sep=None,
            engine="python"
        )
    else:
        df = load_data()

except Exception as e:
    st.error(f"데이터를 불러오지 못했습니다: {e}")
    st.info(
        "경기데이터드림에서 CSV 파일을 내려받아 "
        "위 업로드 칸에 올려 주세요."
    )
    st.stop()


# -----------------------------------------
# 3. 데이터 정리
# -----------------------------------------

# 열 이름 앞뒤 공백 제거
df.columns = df.columns.astype(str).str.strip()

필수열 = [
    "년도",
    "위치",
    "온실가스 배출량",
    "온실가스 감축률"
]

없는열 = [col for col in 필수열 if col not in df.columns]

if 없는열:
    st.error(f"데이터에 필요한 열이 없습니다: {없는열}")
    st.write("현재 데이터의 열 이름:", list(df.columns))
    st.stop()


# 숫자로 변환하는 함수
def 숫자변환(series):
    return pd.to_numeric(
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.strip(),
        errors="coerce"
    )


df["년도"] = 숫자변환(df["년도"])
df["온실가스 배출량"] = 숫자변환(df["온실가스 배출량"])
df["온실가스 감축률"] = 숫자변환(df["온실가스 감축률"])

df["위치"] = df["위치"].astype(str).str.strip()

# 2023년 자료만 사용
df = df[df["년도"] == 2023].copy()

# 분석에 필요한 값이 없는 행 제외
df = df.dropna(
    subset=[
        "위치",
        "온실가스 배출량",
        "온실가스 감축률"
    ]
)

if df.empty:
    st.error("2023년 분석에 사용할 데이터가 없습니다.")
    st.stop()

# 같은 시군이 여러 번 나오는 경우 확인
if df["위치"].duplicated().any():
    st.warning(
        "같은 시군이 여러 번 나타납니다. "
        "원본 데이터의 중복 여부를 확인해 주세요."
    )

# -----------------------------------------
# 4. 주요 통계
# -----------------------------------------

총시군수 = df["위치"].nunique()
총배출량 = df["온실가스 배출량"].sum()
평균배출량 = df["온실가스 배출량"].mean()
평균감축률 = df["온실가스 감축률"].mean()

st.subheader("📊 2023년 주요 통계")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "분석 시군 수",
    f"{총시군수}개"
)

col2.metric(
    "온실가스 총배출량",
    f"{총배출량:,.2f}"
)

col3.metric(
    "시군별 평균 배출량",
    f"{평균배출량:,.2f}"
)

col4.metric(
    "평균 감축률",
    f"{평균감축률:,.2f}%"
)

st.caption(
    "※ 배출량의 단위는 원본 데이터의 단위를 따릅니다. "
    "감축률은 원본 데이터의 수치를 사용합니다."
)

st.divider()


# -----------------------------------------
# 5. 시군별 온실가스 배출량
# -----------------------------------------

st.subheader("① 시군별 온실가스 배출량")

배출량순 = df.sort_values(
    "온실가스 배출량",
    ascending=True
)

fig1 = px.bar(
    배출량순,
    x="온실가스 배출량",
    y="위치",
    orientation="h",
    color="온실가스 배출량",
    color_continuous_scale="Oranges",
    hover_data={
        "위치": True,
        "온실가스 배출량": ":,.2f",
        "온실가스 감축률": ":.2f"
    },
    labels={
        "위치": "시군",
        "온실가스 배출량": "온실가스 배출량"
    }
)

fig1.update_layout(
    height=750,
    xaxis_title="온실가스 배출량",
    yaxis_title="시군",
    coloraxis_showscale=False
)

st.plotly_chart(fig1, use_container_width=True)

st.markdown(
    "**이 그래프로 알 수 있는 것**  \n"
    "경기도에서 온실가스를 많이 배출하는 시군과 "
    "적게 배출하는 시군을 비교할 수 있습니다."
)

st.divider()


# -----------------------------------------
# 6. 시군별 온실가스 감축률
# -----------------------------------------

st.subheader("② 시군별 온실가스 감축률")

감축률순 = df.sort_values(
    "온실가스 감축률",
    ascending=True
)

fig2 = px.bar(
    감축률순,
    x="온실가스 감축률",
    y="위치",
    orientation="h",
    color="온실가스 감축률",
    color_continuous_scale="Greens",
    hover_data={
        "위치": True,
        "온실가스 감축률": ":.2f",
        "온실가스 배출량": ":,.2f"
    },
    labels={
        "위치": "시군",
        "온실가스 감축률": "온실가스 감축률"
    }
)

fig2.update_layout(
    height=750,
    xaxis_title="온실가스 감축률",
    yaxis_title="시군",
    coloraxis_showscale=False
)

st.plotly_chart(fig2, use_container_width=True)

st.markdown(
    "**이 그래프로 알 수 있는 것**  \n"
    "시군별 온실가스 감축률을 비교하여 "
    "감축률이 높은 지역과 낮은 지역을 찾을 수 있습니다."
)

st.divider()


# -----------------------------------------
# 7. 산점도와 상관계수
# -----------------------------------------

st.subheader("③ 온실가스 배출량과 감축률의 관계")

st.markdown("""
- 가로축(X): 온실가스 배출량
- 세로축(Y): 온실가스 감축률
- 점 하나: 경기도의 한 시군
""")

상관데이터 = df[
    ["온실가스 배출량", "온실가스 감축률"]
].dropna()

if len(상관데이터) >= 2:

    상관계수 = 상관데이터[
        "온실가스 배출량"
    ].corr(
        상관데이터["온실가스 감축률"]
    )

    st.metric(
        "배출량과 감축률의 상관계수",
        f"{상관계수:.3f}"
    )

    # 상관계수 해석
    if pd.isna(상관계수):
        st.warning(
            "상관계수를 계산할 수 없습니다. "
            "데이터의 값이 모두 같은지 확인해 주세요."
        )
    elif 상관계수 > 0:
        st.info(
            "양의 상관관계입니다. "
            "배출량이 큰 시군일수록 감축률도 높은 경향이 있습니다."
        )
    elif 상관계수 < 0:
        st.info(
            "음의 상관관계입니다. "
            "배출량이 큰 시군일수록 감축률은 낮은 경향이 있습니다."
        )
    else:
        st.info(
            "선형 상관관계가 거의 없습니다."
        )

    # -------------------------------------
    # 회귀 직선 계산
    # -------------------------------------

    x = 상관데이터["온실가스 배출량"].to_numpy()
    y = 상관데이터["온실가스 감축률"].to_numpy()

    fig3 = go.Figure()

    # 산점도
    fig3.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="markers",
            name="시군별 자료",
            text=df.loc[
                상관데이터.index, "위치"
            ],
            hovertemplate=(
                "시군: %{text}<br>"
                "배출량: %{x:,.2f}<br>"
                "감축률: %{y:.2f}<extra></extra>"
            ),
            marker=dict(
                size=12,
                opacity=0.8
            )
        )
    )

    # 회귀 직선
    if len(x) >= 2 and np.unique(x).size >= 2:

        기울기, 절편 = np.polyfit(x, y, 1)

        x선 = np.linspace(
            x.min(),
            x.max(),
            100
        )

        y선 = 기울기 * x선 + 절편

        fig3.add_trace(
            go.Scatter(
                x=x선,
                y=y선,
                mode="lines",
                name="회귀 직선",
                line=dict(
                    width=3,
                    dash="dash"
                )
            )
        )

        st.write(
            f"**회귀 직선의 식**: "
            f"감축률 = {기울기:.6f} × 배출량 "
            f"+ {절편:.4f}"
        )

    else:
        st.warning(
            "배출량 값이 모두 같아 회귀 직선을 만들 수 없습니다."
        )

    fig3.update_layout(
        height=600,
        xaxis_title="온실가스 배출량",
        yaxis_title="온실가스 감축률",
        hovermode="closest",
        legend_title="범례"
    )

    st.plotly_chart(
        fig3,
        use_container_width=True
    )

    st.markdown(
        "**이 그래프로 알 수 있는 것**  \n"
        "온실가스 배출량이 많은 시군이 감축률도 높은지, "
        "또는 낮은지 관계를 살펴볼 수 있습니다."
    )

else:
    st.warning(
        "상관관계 분석을 위한 데이터가 부족합니다."
    )

st.divider()


# -----------------------------------------
# 8. 원본 데이터 확인
# -----------------------------------------

st.subheader("④ 2023년 시군별 원본 데이터")

표시데이터 = df[
    [
        "년도",
        "위치",
        "온실가스 배출량",
        "온실가스 감축률"
    ]
].sort_values(
    "온실가스 배출량",
    ascending=False
)

st.dataframe(
    표시데이터,
    use_container_width=True,
    hide_index=True
)

st.caption(
    f"총 {len(표시데이터)}개 행"
)

# -----------------------------------------
# 9. 데이터 출처
# -----------------------------------------

st.divider()

st.subheader("📚 데이터 출처")

st.markdown("""
- 제공 기관: 경기도
- 데이터명: 경기도 시군별 온실가스 배출량
- 분석 기준: 2023년
- 원본 데이터: [경기데이터드림](https://data.gg.go.kr/portal/data/service/selectServicePage.do?infId=VJWZJK4EHADPZ7C4J5LB31529041&infSeq=1)
""")
