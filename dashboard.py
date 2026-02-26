"""
Health Trend Dashboard V3
네이버 자동완성 기반 건강 키워드 트렌드 시각화
실행: streamlit run dashboard.py
"""

import glob
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ──────────────────────────────────────────────
# 페이지 설정
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Health Trend Dashboard V3",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = "data"

# ──────────────────────────────────────────────
# 커스텀 CSS
# ──────────────────────────────────────────────
st.markdown(
    """
    <style>
    .metric-card {
        background: #f0f4ff;
        border-radius: 10px;
        padding: 14px 18px;
        border-left: 4px solid #4A7BF7;
    }
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 4px;
    }
    div[data-testid="stTabs"] button {
        font-size: 1rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# 데이터 로드 (캐시 5분)
# ──────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_top20() -> pd.DataFrame:
    files = sorted(glob.glob(os.path.join(DATA_DIR, "top20_*.csv")))
    if not files:
        return pd.DataFrame()
    dfs = []
    for f in files:
        try:
            dfs.append(pd.read_csv(f))
        except Exception:
            pass
    if not dfs:
        return pd.DataFrame()
    df = pd.concat(dfs, ignore_index=True)
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    return df


@st.cache_data(ttl=300)
def load_related() -> pd.DataFrame:
    files = sorted(glob.glob(os.path.join(DATA_DIR, "related_*.csv")))
    if not files:
        return pd.DataFrame()
    dfs = []
    for f in files:
        try:
            dfs.append(pd.read_csv(f))
        except Exception:
            pass
    if not dfs:
        return pd.DataFrame()
    df = pd.concat(dfs, ignore_index=True)
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    return df


# ──────────────────────────────────────────────
# 헤더
# ──────────────────────────────────────────────
st.markdown("# 🏥 Health Trend Dashboard V3")
st.markdown(
    "**네이버 자동완성** 기반으로 사람들이 실제로 검색하는 건강 키워드 트렌드를 매일 분석합니다."
)
st.divider()

# ──────────────────────────────────────────────
# 데이터 로드
# ──────────────────────────────────────────────
top20_df = load_top20()
related_df = load_related()

if top20_df.empty:
    st.warning(
        "📭 수집된 데이터가 없습니다.  \n"
        "아래 명령어로 데이터를 먼저 수집해 주세요:\n\n"
        "```bash\npython src/collect.py\n```"
    )
    st.stop()

# ──────────────────────────────────────────────
# 사이드바
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ 필터")
    available_dates = sorted(top20_df["date"].unique(), reverse=True)
    selected_date = st.selectbox(
        "📅 날짜 선택",
        available_dates,
        index=0,
        help="분석할 날짜를 선택하세요",
    )

    st.divider()
    st.markdown("### 📊 데이터 현황")

    col_a, col_b = st.columns(2)
    col_a.metric("수집 일수", f"{len(available_dates)}일")
    col_b.metric("최근 수집일", available_dates[0] if available_dates else "-")

    total_keywords = len(top20_df["keyword"].unique()) if not top20_df.empty else 0
    st.metric("고유 연관 키워드", f"{total_keywords:,}개")

    if not related_df.empty:
        total_records = len(related_df)
        st.metric("총 연관어 수집 건수", f"{total_records:,}건")

    st.divider()
    if st.button("🔄 데이터 새로고침", width="stretch"):
        st.cache_data.clear()
        st.rerun()

    st.markdown(
        "<br><small>📌 GitHub Actions가 매일 오전 9시(KST)에 자동 수집합니다.</small>",
        unsafe_allow_html=True,
    )

# ──────────────────────────────────────────────
# 선택 날짜 데이터 필터
# ──────────────────────────────────────────────
day_top20 = top20_df[top20_df["date"] == selected_date].sort_values("rank").reset_index(drop=True)
day_related = (
    related_df[related_df["date"] == selected_date].reset_index(drop=True)
    if not related_df.empty
    else pd.DataFrame()
)

# ──────────────────────────────────────────────
# 탭
# ──────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(
    ["📊 TOP 20 트렌드", "🔍 씨앗 키워드별 연관어", "📈 키워드 시계열"]
)

# ═══════════════════════════════════════════════
# TAB 1: TOP 20 트렌드
# ═══════════════════════════════════════════════
with tab1:
    st.markdown(f"### 📊 {selected_date} — 가장 많이 등장한 연관 검색어 TOP 20")
    st.caption("120개 씨앗 키워드의 자동완성 결과에서 등장 빈도를 집계한 순위입니다.")

    if day_top20.empty:
        st.info("선택한 날짜의 TOP 20 데이터가 없습니다.")
    else:
        # 차트
        fig = px.bar(
            day_top20.sort_values("count", ascending=True),
            x="count",
            y="keyword",
            orientation="h",
            color="count",
            color_continuous_scale="Blues",
            text="count",
            labels={"count": "등장 횟수", "keyword": "키워드"},
        )
        fig.update_traces(
            texttemplate="%{text:,}회",
            textposition="outside",
        )
        fig.update_layout(
            height=580,
            showlegend=False,
            coloraxis_showscale=False,
            margin=dict(l=10, r=80, t=20, b=20),
            yaxis=dict(tickfont=dict(size=13)),
            xaxis_title="등장 횟수",
            yaxis_title="",
        )
        st.plotly_chart(fig, width="stretch")

        # 테이블
        st.markdown("#### 순위표")
        display_df = day_top20[["rank", "keyword", "count"]].rename(
            columns={"rank": "순위", "keyword": "키워드", "count": "등장 횟수"}
        )
        st.dataframe(
            display_df,
            hide_index=True,
            width="stretch",
        )

# ═══════════════════════════════════════════════
# TAB 2: 씨앗 키워드별 연관어
# ═══════════════════════════════════════════════
with tab2:
    st.markdown(f"### 🔍 {selected_date} — 씨앗 키워드별 연관 검색어")
    st.caption("씨앗 키워드를 선택하면 해당 날짜의 자동완성 연관 검색어를 확인할 수 있습니다.")

    if day_related.empty:
        st.info("선택한 날짜의 연관 검색어 데이터가 없습니다.")
    else:
        seed_keywords_available = sorted(day_related["seed_keyword"].unique())
        selected_seed = st.selectbox(
            "🌱 씨앗 키워드 선택",
            seed_keywords_available,
            help="연관 검색어를 확인할 씨앗 키워드를 선택하세요",
        )

        seed_data = (
            day_related[day_related["seed_keyword"] == selected_seed]
            .sort_values("position")
            .reset_index(drop=True)
        )

        if seed_data.empty:
            st.warning(f"'{selected_seed}'의 연관 검색어 데이터가 없습니다.")
        else:
            col1, col2 = st.columns([1, 1], gap="large")

            with col1:
                st.markdown(f"**'{selected_seed}' 자동완성 결과 ({len(seed_data)}개)**")
                display_seed = seed_data[["position", "related_keyword"]].rename(
                    columns={"position": "순서", "related_keyword": "연관 검색어"}
                )
                st.dataframe(
                    display_seed,
                    hide_index=True,
                    width="stretch",
                    height=400,
                )

            with col2:
                fig2 = px.bar(
                    seed_data,
                    x="related_keyword",
                    y="position",
                    color="position",
                    color_continuous_scale="Blues_r",
                    labels={
                        "related_keyword": "연관 검색어",
                        "position": "자동완성 순위",
                    },
                    title=f"'{selected_seed}' 연관 검색어 자동완성 순위",
                )
                fig2.update_yaxes(autorange="reversed", title="순위 (낮을수록 상위)")
                fig2.update_layout(
                    xaxis_tickangle=-35,
                    coloraxis_showscale=False,
                    height=420,
                    margin=dict(t=50, b=80),
                )
                st.plotly_chart(fig2, width="stretch")

        # 모든 씨앗 키워드 수집 현황 요약
        st.divider()
        st.markdown("#### 전체 씨앗 키워드 수집 현황")
        summary = (
            day_related.groupby("seed_keyword")["related_keyword"]
            .count()
            .reset_index()
            .rename(columns={"seed_keyword": "씨앗 키워드", "related_keyword": "연관어 수집 수"})
            .sort_values("연관어 수집 수", ascending=False)
        )
        st.dataframe(summary, hide_index=True, width="stretch", height=300)

# ═══════════════════════════════════════════════
# TAB 3: 키워드 시계열
# ═══════════════════════════════════════════════
with tab3:
    st.markdown("### 📈 키워드 등장 횟수 시계열 트렌드")
    st.caption("여러 날짜에 걸쳐 특정 키워드가 얼마나 자주 등장했는지 추이를 확인합니다.")

    if len(available_dates) < 2:
        st.info(
            "📅 시계열 분석을 위해 **2일 이상**의 데이터가 필요합니다.  \n"
            "데이터 수집 후 다시 확인해 주세요."
        )
    else:
        # 날짜 범위 필터
        col_start, col_end = st.columns(2)
        all_dates_sorted = sorted(available_dates)
        with col_start:
            date_from = st.selectbox(
                "시작 날짜",
                all_dates_sorted,
                index=0,
                key="date_from",
            )
        with col_end:
            date_to = st.selectbox(
                "종료 날짜",
                all_dates_sorted,
                index=len(all_dates_sorted) - 1,
                key="date_to",
            )

        # 선택 기간 데이터
        mask = (top20_df["date"] >= date_from) & (top20_df["date"] <= date_to)
        period_df = top20_df[mask]

        if period_df.empty:
            st.warning("선택한 기간에 데이터가 없습니다.")
        else:
            all_kws = sorted(period_df["keyword"].unique())
            default_kws = all_kws[:5] if len(all_kws) >= 5 else all_kws

            selected_kws = st.multiselect(
                "📌 키워드 선택 (복수 선택 가능)",
                all_kws,
                default=default_kws,
                help="최대 10개를 권장합니다",
            )

            if not selected_kws:
                st.info("키워드를 하나 이상 선택해 주세요.")
            else:
                trend_df = period_df[period_df["keyword"].isin(selected_kws)]

                fig3 = px.line(
                    trend_df,
                    x="date",
                    y="count",
                    color="keyword",
                    markers=True,
                    labels={
                        "date": "날짜",
                        "count": "등장 횟수",
                        "keyword": "키워드",
                    },
                    title=f"기간별 키워드 등장 횟수 추이 ({date_from} ~ {date_to})",
                )
                fig3.update_layout(
                    height=500,
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )
                st.plotly_chart(fig3, width="stretch")

                # 순위 변화 히트맵
                st.markdown("#### 날짜별 TOP 키워드 등장 횟수 (히트맵)")
                pivot = trend_df.pivot_table(
                    index="keyword", columns="date", values="count", fill_value=0
                )
                fig4 = go.Figure(
                    data=go.Heatmap(
                        z=pivot.values,
                        x=pivot.columns.tolist(),
                        y=pivot.index.tolist(),
                        colorscale="Blues",
                        hoverongaps=False,
                        text=pivot.values,
                        texttemplate="%{text}",
                    )
                )
                fig4.update_layout(
                    height=max(300, len(pivot) * 35 + 100),
                    margin=dict(l=120, r=20, t=20, b=60),
                    xaxis_title="날짜",
                    yaxis_title="키워드",
                )
                st.plotly_chart(fig4, width="stretch")
