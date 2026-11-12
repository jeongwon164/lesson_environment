
import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# --------------------------------------------------
# 1. 페이지 설정
# --------------------------------------------------

st.set_page_config(
    page_title="경기도 전체 온실가스 배출량 변화",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 경기도 전체 온실가스 배출량은 매년 감소하고 있을까?")

st.write(
    "2018년부터 2023년까지 경기도 31개 시군의 "
    "온실가스 배출량을 합산하여 연도별 변화를 알아봅니다."
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
    df["온실가스배출량(tonCO2-eq)"]
    .astype(str)
    .str.replace(",", "", regex=False),
    errors="coerce"
)

df = df.dropna(subset=필요한열)

df["년도"] = df["년도"].astype(int)

# 같은 연도에 같은 시군이 여러 번 있는지 확인
중복자료 = df.duplicated(
    subset=["년도", "시군명"],
    keep=False
)

if 중복자료.any():
    st.error(
        "같은 연도와 시군이 중복되어 있습니다. "
        "중복 자료를 확인한 후 다시 업로드해 주세요."
    )
    st.dataframe(
        df.loc[중복자료].sort_values(["년도", "시군명"]),
        use_container_width=True
    )
    st.stop()


# --------------------------------------------------
# 6. 연도별 경기도 전체 배출량 계산
# --------------------------------------------------

연도별합계 = (
    df.groupby("년도")["온실가스배출량(tonCO2-eq)"]
    .sum()
    .reset_index()
)

연도별합계 = 연도별합계.sort_values("년도")

# 연도별 데이터가 2개 이상인지 확인
if len(연도별합계) < 2:
    st.error("연도별 변화를 비교할 데이터가 부족합니다.")
    st.stop()

# 연도별 시군 수 확인
시군수 = df.groupby("년도")["시군명"].nunique()

if 시군수.nunique() > 1:
    st.warning(
        "연도별 시군 수가 서로 다릅니다. "
        "일부 연도의 자료가 누락되었을 수 있으므로 비교에 주의하세요."
    )

# --------------------------------------------------
# 7. 전년도 대비 증감량과 증감률 계산
# --------------------------------------------------

연도별합계["전년 대비 증감량"] = (
    연도별합계["온실가스배출량(tonCO2-eq)"].diff()
)

연도별합계["전년 대비 증감률(%)"] = (
    연도별합계["온실가스배출량(tonCO2-eq)"]
    .pct_change() * 100
)


# --------------------------------------------------
# 8. 경기도 전체 배출량 요약
# --------------------------------------------------

st.divider()

st.subheader("📊 경기도 전체 온실가스 배출량")

첫해 = 연도별합계.iloc[0]
마지막해 = 연도별합계.iloc[-1]

전체변화량 = (
    마지막해["온실가스배출량(tonCO2-eq)"]
    - 첫해["온실가스배출량(tonCO2-eq)"]
)

전체변화율 = (
    전체변화량
    / 첫해["온실가스배출량(tonCO2-eq)"]
    * 100
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        f"{int(첫해['년도'])}년 전체 배출량",
        f"{첫해['온실가스배출량(tonCO2-eq)']:,.0f}"
    )

with col2:
    st.metric(
        f"{int(마지막해['년도'])}년 전체 배출량",
        f"{마지막해['온실가스배출량(tonCO2-eq)']:,.0f}"
    )

with col3:
    st.metric(
        "전체 기간 증감률",
        f"{전체변화율:+.2f}%",
        delta=f"{전체변화율:+.2f}%"
    )

st.caption("단위: tonCO2-eq")


# --------------------------------------------------
# 9. 연도별 배출량 꺾은선그래프
# --------------------------------------------------

st.divider()

st.subheader("📈 연도별 경기도 전체 온실가스 배출량")

그래프 = px.line(
    연도별합계,
    x="년도",
    y="온실가스배출량(tonCO2-eq)",
    markers=True,
    text="온실가스배출량(tonCO2-eq)",
    title="경기도 전체 온실가스 배출량 변화",
    labels={
        "년도": "연도",
        "온실가스배출량(tonCO2-eq)": "온실가스 배출량 (tonCO2-eq)"
    }
)

그래프.update_traces(
    texttemplate="%{y:,.0f}",
    textposition="top center",
    line=dict(width=3),
    marker=dict(size=10)
)

그래프.update_layout(
    height=550,
    xaxis_title="연도",
    yaxis_title="온실가스 배출량 (tonCO2-eq)",
    xaxis=dict(
        tickmode="linear",
        dtick=1
    )
)

st.plotly_chart(
    그래프,
    use_container_width=True
)

st.caption(
    "이 그래프는 경기도 31개 시군의 온실가스 배출량을 "
    "연도별로 합산하여 나타낸 것입니다."
)


# --------------------------------------------------
# 10. 매년 감소했는지 확인
# --------------------------------------------------

st.divider()

st.subheader("🔍 경기도 전체 배출량은 매년 감소했을까?")

증감량 = 연도별합계["전년 대비 증감량"].dropna()

감소횟수 = int((증감량 < 0).sum())
증가횟수 = int((증감량 > 0).sum())
동일횟수 = int((증감량 == 0).sum())

if 감소횟수 == len(증감량):
    st.success(
        "경기도 전체 온실가스 배출량은 "
        "비교한 모든 해에 전년보다 감소했습니다."
    )

elif 증가횟수 == len(증감량):
    st.warning(
        "경기도 전체 온실가스 배출량은 "
        "비교한 모든 해에 전년보다 증가했습니다."
    )

else:
    st.info(
        "경기도 전체 온실가스 배출량은 "
        "매년 꾸준히 감소하지는 않았습니다. "
        "연도에 따라 증가하거나 감소했습니다."
    )

col1, col2, col3 = st.columns(3)

col1.metric("배출량 감소 횟수", f"{감소횟수}회")
col2.metric("배출량 증가 횟수", f"{증가횟수}회")
col3.metric("변화 없음", f"{동일횟수}회")


# --------------------------------------------------
# 11. 연도별 증감량 표
# --------------------------------------------------

st.divider()

st.subheader("📋 연도별 배출량 변화표")

표시데이터 = 연도별합계.copy()

표시데이터["년도"] = 표시데이터["년도"].astype(str) + "년"

표시데이터 = 표시데이터.rename(
    columns={
        "년도": "연도",
        "온실가스배출량(tonCO2-eq)": "전체 배출량 (tonCO2-eq)",
        "전년 대비 증감량": "전년 대비 증감량 (tonCO2-eq)",
        "전년 대비 증감률(%)": "전년 대비 증감률 (%)"
    }
)

st.dataframe(
    표시데이터,
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# 12. 그래프로 알 수 있는 것
# --------------------------------------------------

st.divider()

st.subheader("💡 이 그래프로 알 수 있는 것")

if 전체변화량 < 0:
    해석 = (
        f"전체 분석 기간 동안 경기도의 온실가스 배출량은 "
        f"{abs(전체변화량):,.0f} tonCO2-eq 감소했습니다."
    )
elif 전체변화량 > 0:
    해석 = (
        f"전체 분석 기간 동안 경기도의 온실가스 배출량은 "
        f"{전체변화량:,.0f} tonCO2-eq 증가했습니다."
    )
else:
    해석 = "전체 분석 기간 동안 경기도의 온실가스 배출량은 변하지 않았습니다."

st.write(
    f"{int(첫해['년도'])}년부터 {int(마지막해['년도'])}년까지 "
    f"경기도 전체 배출량을 비교한 결과, {해석}"
)

st.caption(
    "※ 연도별 합계는 각 시군의 온실가스 배출량을 더한 값입니다. "
    "연도별 자료 범위와 시군 수가 같은지 확인한 뒤 해석해야 합니다."
)
