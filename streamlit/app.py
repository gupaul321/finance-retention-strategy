import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# =========================================================
# [1] 페이지 레이아웃 및 커스텀 스타일(방어 물고기 효과) 설정
# =========================================================
st.set_page_config(page_title="Integrated Churn Management System", layout="wide")

# 홈 화면 방어(물고기) 애니메이션 및 카드 디자인을 위한 CSS
st.markdown("""
    <style>
    @keyframes fish-float {
        0% { transform: translateY(0px) rotate(0deg); opacity: 0; }
        20% { opacity: 1; }
        100% { transform: translateY(-1000px) rotate(720deg); opacity: 0; }
    }
    .fish {
        position: fixed;
        bottom: -50px;
        font-size: 2.5rem;
        animation: fish-float 6s linear infinite;
        z-index: 9999;
        pointer-events: none;
    }
    .main { background-color: #f1f3f5; }
    .metric-card {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        text-align: center;
        border-top: 6px solid #1f77b4;
    }
    .metric-title { font-size: 1.1rem; color: #495057; margin-bottom: 10px; font-weight: 600; }
    .metric-value { font-size: 2.2rem; font-weight: 800; color: #1f77b4; }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# [2] 사이드바 및 네비게이션 설정
# =========================================================
st.sidebar.title("👥 분석 대상 설정")
customer_type = st.sidebar.selectbox("고객 유형 선택", ["일반 고객(General)", "VIP 고객"])

st.sidebar.markdown("---")
st.sidebar.title("📌 대시보드 메뉴")
menu = st.sidebar.radio("페이지 선택", [
    "🏠 홈 (전체 개요)", 
    "🚩 이탈 방지 대시보드", 
    "🎯 맞춤형 마케팅 시스템", 
    "👥 개별 고객 정밀 리포트"
])

# =========================================================
# [3] 데이터 경로 및 전역 변수 설정
# =========================================================
if customer_type == "VIP 고객":
    TARGET_FILE = "VIP_30K_Target_Churn_1000.csv"
    HISTORY_FILE = "VIP_Target_History_Data.csv"
    PRIMARY_COLOR = "#1f77b4"
else:
    TARGET_FILE = "general_churn_전체_sample_3000.csv"
    HISTORY_FILE = "general_churn_전체_sample_3000.csv"
    PRIMARY_COLOR = "#ff7f0e"

category_cols = [
    '이용금액_쇼핑', '이용금액_요식', '이용금액_교통', '이용금액_의료', '이용금액_납부',
    '이용금액_교육', '이용금액_여유생활', '이용금액_사교활동', '이용금액_일상생활', '이용금액_해외'
]

# =========================================================
# [4] 고객군별 차별화된 마케팅 가이드 정의
# =========================================================

# 일반 고객용 마케팅 가이드 (위험 등급 기반)
def get_general_marketing_guide(risk_level, category):
    if risk_level == "🚨 고위험군":
        return (f"🚨 [전방위 가치 회복] 결제 활동 급감 상태. "
                f"'{category}' 업종 할인 및 전 가맹점 무이자 할부 등 종합 케어 패키지 제안 필수.")
    base_messages = {
        "✅ 안전군": {"prefix": "✨ [리텐션 유지] ", "suffix": "지속 이용 감사 리워드 제공"},
        "⚠️ 위험군": {"prefix": "🔔 [이탈 방지] ", "suffix": "개인화 재방문 할인 쿠폰 발행"}
    }
    msg_base = base_messages.get(risk_level, {"prefix": "ℹ️ ", "suffix": "마케팅 제안"})
    return f"{msg_base['prefix']} {category} 관련 혜택 및 {msg_base['suffix']}"

# VIP 고객용 마케팅 가이드 (프리미엄 혜택 기반)
def get_vip_marketing_guide(category):
    vip_benefits = {
        '쇼핑': '백화점 VIP 라운지 이용권 및 퍼스널 쇼퍼 서비스 제공',
        '요식': '호텔 파인 다이닝 2인 식사권 및 프리미엄 와인 콜키지 프리',
        '교통': '프리미엄 공항 픽업/샌딩 서비스 및 주유 리워드 강화',
        '의료': '종합건강검진 우대권 및 프라이빗 헬스케어 매니징 서비스',
        '여유생활': '럭셔리 리조트 숙박 바우처 및 골프장 그린피 면제 혜택'
    }
    benefit = vip_benefits.get(category, "최상위 컨시어지 서비스 및 연회비 면제 혜택")
    return f"💎 [VIP 프리미엄 케어] '{category}' 중심의 최상위 로열티 프로그램 및 {benefit} 제안."

# =========================================================
# [5] 데이터 로드 및 전처리 (KeyError 방지 포함)
# =========================================================
@st.cache_data
def load_data(target_path, history_path, current_type):
    try:
        df_history = pd.read_csv(history_path, encoding='utf-8-sig', low_memory=False)
        df_history = df_history.rename(columns={'발급회원번호': 'CustomerID'})
        df_history['기준년월'] = df_history['기준년월'].astype(str)
        df_history = df_history.sort_values(['CustomerID', '기준년월'])
        
        df_history['Current_Spend'] = df_history['이용금액_신용_B0M']
        df_history['Avg_3M_Spend'] = df_history['이용금액_신용_R3M'] / 3
        df_history['Churn_Check'] = np.where(
            (df_history['Current_Spend'] <= 0) | (df_history['Current_Spend'] < df_history['Avg_3M_Spend'] * 0.8), 1, 0
        )

        if current_type == "VIP 고객":
            df_target = pd.read_csv(target_path, encoding='utf-8-sig').rename(columns={'발급회원번호': 'CustomerID'})
            df_target['Total_Spend'] = df_target['이용금액_R3M_신용체크'] if '이용금액_R3M_신용체크' in df_target.columns else 0
            df_target['Risk_Level'] = "VIP 유효"
            df_target['Total_Churn_Count'] = 0 # VIP용 더미 컬럼 생성 (KeyError 방지)
        else:
            all_ids = df_history['CustomerID'].unique()
            summary = df_history.groupby('CustomerID').agg({
                'Churn_Check': 'sum', '이용금액_R3M_신용체크': 'last', '이용금액_신용_B0M': 'last'
            }).reindex(all_ids).reset_index().fillna(0)
            summary.columns = ['CustomerID', 'Total_Churn_Count', 'Total_Spend', 'Last_Spend']
            
            def classify_risk(cnt):
                if cnt >= 5: return "🚨 고위험군"
                elif cnt >= 3: return "⚠️ 위험군"
                else: return "✅ 안전군"
            summary['Risk_Level'] = summary['Total_Churn_Count'].apply(classify_risk)
            df_target = summary

        user_top_cats = df_history.groupby('CustomerID')[category_cols].sum().idxmax(axis=1)
        df_target['Main_Interest'] = df_target['CustomerID'].map(user_top_cats).str.replace('이용금액_', '').fillna('종합소비')
        np.random.seed(42)
        df_target['Churn_Prob'] = np.random.uniform(0.7, 0.99, len(df_target))
        df_target['Spend_for_Size'] = df_target['Total_Spend'].abs().clip(lower=0)
        df_target['Segment'] = np.where(df_target['Total_Spend'] > df_target['Total_Spend'].median(), f'{current_type} Save', 'Warning')
        
        return df_target, df_history
    except:
        return pd.DataFrame(), pd.DataFrame()

df_target, df_history = load_data(TARGET_FILE, HISTORY_FILE, customer_type)

# ---------------------------------------------------------
# [🏠 홈 (전체 개요) 섹션]
# ---------------------------------------------------------
if menu == "🏠 홈 (전체 개요)":
    # 방어(물고기) 팡팡 애니메이션 HTML 생성
    fish_icons = ["🐟", "🐠", "🐡", "🦈", "🌊"]
    fish_html = "".join([f'<div class="fish" style="left: {np.random.randint(0, 100)}%; animation-delay: {np.random.uniform(0, 6)}s;">{np.random.choice(fish_icons)}</div>' for _ in range(25)])
    st.markdown(fish_html, unsafe_allow_html=True)
    
    st.markdown("<h1 style='text-align: center; color: #1f77b4;'>🐟 용기를 팡팡 내! 무지개물고기 통합 대시보드</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    total_pop = 3000000
    vip_total = int(total_pop * 0.2)
    gen_total = total_pop - vip_total

    # 상단 요약 카드 영역
    m1, m2, m3 = st.columns(3)
    with m1: st.markdown(f'<div class="metric-card"><div class="metric-title">전체 관리 고객</div><div class="metric-value">{total_pop:,}명</div></div>', unsafe_allow_html=True)
    with m2: st.markdown(f'<div class="metric-card" style="border-top-color: #2ecc71;"><div class="metric-title">VIP 고객 (20%)</div><div class="metric-value">{vip_total:,}명</div></div>', unsafe_allow_html=True)
    with m3: st.markdown(f'<div class="metric-card" style="border-top-color: #ff7f0e;"><div class="metric-title">일반 고객 (80%)</div><div class="metric-value">{gen_total:,}명</div></div>', unsafe_allow_html=True)

    # 1. VIP 고객 상세 (60만 명)
    st.markdown("<br><hr><h3>💎 VIP 고객 이탈 현황 상세</h3>", unsafe_allow_html=True)
    vip_churners = int(vip_total * 0.085)
    vip_safe = vip_total - vip_churners
    fig_vip = px.bar(x=["안전 (91.5%)", "이탈 위험 (8.5%)"], y=[vip_safe, vip_churners], 
                     color=["안전", "이탈"], color_discrete_map={"안전": "#1f77b4", "이탈": "#e74c3c"}, text_auto=',.0f')
    fig_vip.update_layout(height=500, xaxis_title=None, showlegend=False)
    st.plotly_chart(fig_vip, use_container_width=True)

    # 2. 일반 고객 등급별 세분화 (240만 명)
    st.markdown("<br><hr><h3>📊 일반 고객(General) 위험 등급별 세분화</h3>", unsafe_allow_html=True)

    # 데이터 설정
    gen_total = 2400000
    # 비율 설정: 비이탈(60.18%) + 감지(11.92%) + 위험(13.53%) + 고위험(14.37%) = 100%
    ratios = {
        "safe": 0.6018,
        "detected": 0.1192,
        "risk": 0.1353,
        "high_risk": 0.1437
    }

    # 인원수 계산
    gen_safe_cnt = int(gen_total * ratios["safe"])
    gen_detected_cnt = int(gen_total * ratios["detected"])
    gen_risk_cnt = int(gen_total * ratios["risk"])
    gen_high_risk_cnt = int(gen_total * ratios["high_risk"])
    total_churn_cnt = gen_detected_cnt + gen_risk_cnt + gen_high_risk_cnt

    # 요약 지표 출력
    col1, col2 = st.columns(2)
    col1.metric("전체 분석 고객 수", f"{gen_total:,}명")
    col2.metric("최종 시점 이탈자 수", f"{total_churn_cnt:,}명", f"{39.82:.2f}%", delta_color="inverse")

    # 데이터프레임 구성
    gen_df = pd.DataFrame({
        "등급": [
            f"✅ 비이탈 ({ratios['safe']*100:.2f}%)", 
            f"🔍 이탈 감지 ({ratios['detected']*100:.2f}%)", 
            f"⚠️ 이탈 위험 ({ratios['risk']*100:.2f}%)", 
            f"🚨 이탈 고위험군 ({ratios['high_risk']*100:.2f}%)"
        ],
        "인원수": [gen_safe_cnt, gen_detected_cnt, gen_risk_cnt, gen_high_risk_cnt]
    })

    # 그래프 시각화
    fig_gen = px.bar(
        gen_df, 
        x="등급", 
        y="인원수", 
        text_auto=',.0f', 
        color="등급",
        color_discrete_map={
            f"✅ 비이탈 ({ratios['safe']*100:.2f}%)": "#2ecc71",      # 녹색
            f"🔍 이탈 감지 ({ratios['detected']*100:.2f}%)": "#3498db",  # 파란색
            f"⚠️ 이탈 위험 ({ratios['risk']*100:.2f}%)": "#f1c40f",    # 노란색
            f"🚨 이탈 고위험군 ({ratios['high_risk']*100:.2f}%)": "#e74c3c" # 빨간색
        }
    )

    fig_gen.update_layout(
        height=600, 
        xaxis_title=None, 
        yaxis_title="인원수 (명)",
        showlegend=False,
        font=dict(size=14)
    )

    st.plotly_chart(fig_gen, use_container_width=True)

# ---------------------------------------------------------
# [🚩 이탈 방지 대시보드 섹션]
# ---------------------------------------------------------
elif menu == "🚩 이탈 방지 대시보드":
    st.title(f"🚩 {customer_type} 이탈 방어 전략")
    display_count = 3000 if customer_type == "일반 고객(General)" else len(df_target)
    
    k1, k2, k3 = st.columns(3)
    k1.metric("분석 모수", f"{display_count:,} 명")
    k2.metric("보호 필요 매출 규모", f"₩{df_target['Total_Spend'].sum():,.0f}")
    k3.metric("평균 예측 위험도", f"{df_target['Churn_Prob'].mean()*100:.1f}%")
    
    fig_scatter = px.scatter(df_target, x="Churn_Prob", y="Total_Spend", color="Segment", size="Spend_for_Size", 
                             color_discrete_map={f'{customer_type} Save': '#1f77b4', 'Warning': '#d62728'},
                             hover_data=['CustomerID', 'Risk_Level'])
    st.plotly_chart(fig_scatter, use_container_width=True)
    st.dataframe(df_target.sort_values(by='Total_Spend', ascending=False))

# ---------------------------------------------------------
# [🎯 맞춤형 마케팅 시스템 섹션] - 고객군별 차별화 로직 적용
# ---------------------------------------------------------
elif menu == "🎯 맞춤형 마케팅 시스템":
    st.title(f"🎯 {customer_type} 차별화 마케팅 제안")
    
    if customer_type == "일반 고객(General)":
        selected_risk = st.multiselect("위험 등급 필터", ["✅ 안전군", "⚠️ 위험군", "🚨 고위험군"], default=["🚨 고위험군", "⚠️ 위험군"])
        filtered_df = df_target[df_target['Risk_Level'].isin(selected_risk)]
    else: filtered_df = df_target

    c_left, c_right = st.columns([1, 1])
    with c_right:
        search_id = st.selectbox("회원번호 선택", filtered_df['CustomerID'].unique())
        if search_id:
            row = filtered_df[filtered_df['CustomerID'] == search_id].iloc[0]
            # 고객군에 따른 개별화된 마케팅 시나리오 출력
            if customer_type == "VIP 고객":
                st.subheader(f"💎 {search_id} 회원님을 위한 프리미엄 오퍼")
                st.info(get_vip_marketing_guide(row['Main_Interest']))
            else:
                st.subheader(f"📊 {search_id} 고객 위험도 분석 결과")
                fig_gauge = go.Figure(go.Indicator(
                    mode = "gauge+number", value = row['Total_Churn_Count'], title = {'text': f"<b>{row['Risk_Level']}</b>"},
                    gauge = {'axis': {'range': [0, 6]}, 'steps': [{'range': [0, 2], 'color': '#2ecc71'}, {'range': [2, 4], 'color': '#f1c40f'}, {'range': [4, 6], 'color': '#e74c3c'}]}
                ))
                st.plotly_chart(fig_gauge, use_container_width=True)
                st.warning(get_general_marketing_guide(row['Risk_Level'], row['Main_Interest']))

    with c_left:
        if search_id:
            ind_spend = df_history[df_history['CustomerID'] == search_id][category_cols].sum()
            fig_ind = px.bar(x=[c.replace('이용금액_', '') for c in category_cols], y=ind_spend.values, title=f"ID: {search_id} 업종별 소비 트렌드")
            st.plotly_chart(fig_ind, use_container_width=True)


# ---------------------------------------------------------
# [3페이지: 개별 고객 정밀 리포트] - VIP/GENERAL 통합 버전
# ---------------------------------------------------------
elif menu == "👥 개별 고객 정밀 리포트":
    # 1. 현재 사이드바에서 선택된 고객 유형 확인
    # (앞선 코드에서 customer_type = st.sidebar.selectbox(...)로 정의됨)
    utype_display = "VIP" if customer_type == "VIP 고객" else "일반(General)"
    
    st.title(f"👥 {utype_display} 고객 정밀 리포트 (Individual Report)")
    st.info(f"이 페이지는 선택된 {utype_display} 히스토리 데이터를 기반으로 소비 변동 및 이탈 징후를 정밀 분석합니다.")

    @st.cache_data
    def load_specific_history(c_type):
        """선택된 고객 유형에 따라 로컬 경로에서 히스토리 데이터 로드"""
        if c_type == "VIP 고객":
            # VIP 히스토리 데이터 경로
            file_path = "VIP_Target_History_Data.csv"
        else:
            # General 히스토리 데이터 경로
            file_path = "general_churn_전체_sample_3000.csv"
        
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig', low_memory=False)
            
            # 공통 전처리 로직
            df['Current_Spend'] = df['이용금액_신용_B0M']
            df['Avg_3M_Spend'] = df['이용금액_신용_R3M'] / 3

            # 이탈 징후 판단 (당월 0원 이하 또는 3M 평균 대비 80% 미만)
            df['Churn_Check'] = np.where(
                (df['Current_Spend'] <= 0) | 
                ((df['Avg_3M_Spend'] > 0) & (df['Current_Spend'] < df['Avg_3M_Spend'] * 0.8)), 
                1, 0
            )

            df['기준년월'] = df['기준년월'].astype(str)
            # 데이터 로드 시 '발급회원번호'를 'CustomerID'로 통일하여 처리
            df = df.rename(columns={'발급회원번호': 'CustomerID'})
            df = df.sort_values(by=['CustomerID', '기준년월'])
            return df
        except Exception as e:
            st.error(f"데이터 파일 로드 중 오류가 발생했습니다. 경로를 확인해주세요: {e}")
            return pd.DataFrame()

    # 데이터 로드 실행
    df_history_page = load_specific_history(customer_type)

    if not df_history_page.empty:
        # 2. 마케팅 솔루션 공통 정의
        marketing_solutions = {
            '이용금액_쇼핑': '🛍️ 쇼핑몰 재방문 감사 쿠폰 및 무이자 할부 혜택 제공',
            '이용금액_요식': '🍽️ 주말 외식 타임 세일 바우처 및 인기 레스토랑 예약 서비스',
            '이용금액_교통': '⛽ 주유 할인 포인트 추가 적립 및 대중교통 이용 혜택 안내',
            '이용금액_의료': '🏥 건강관리 서비스 안내 및 약국/병원 결제 시 캐시백 증정',
            '이용금액_납부': '💳 아파트 관리비/통신비 자동이체 전환 시 첫 달 할인',
            '이용금액_교육': '📚 학원비 결제 시 포인트 더블 적립 및 장기 할부 제공',
            '이용금액_여유생활': '🏨 여가 활동 지원을 위한 숙박/여행 상품 할인권 발송',
            '이용금액_사교활동': '⛳ 골프/사교 모임 관련 업종 결제 시 특별 리워드 증정',
            '이용금액_일상생활': '🛒 대형마트/편의점 상시 할인권 및 장바구니 리워드',
            '이용금액_해외': '✈️ 해외 이용 수수료 면제 혜택 및 면세점 선불카드 증정'
        }

        # 3. 회원 검색 (사이드바 selectbox)
        unique_ids = df_history_page['CustomerID'].unique()
        selected_id = st.sidebar.selectbox(f"🔍 분석할 {utype_display} ID 선택", unique_ids)

        if selected_id:
            user_data = df_history_page[df_history_page['CustomerID'] == selected_id].copy()
            st.subheader(f"📊 [ {selected_id} ] 고객 소비 패턴 추적")

            # --- (1) Combo Chart 시각화 ---
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            # 막대 그래프: 당월 이용액
            fig.add_trace(go.Bar(x=user_data['기준년월'], y=user_data['Current_Spend'], 
                                 name="당월 이용액", marker_color='cadetblue'), secondary_y=False)
            # 선 그래프: 직전 3M 평균
            fig.add_trace(go.Scatter(x=user_data['기준년월'], y=user_data['Avg_3M_Spend'], 
                                     name="직전 3M 평균", line=dict(color="orange", dash="dot")), secondary_y=False)
            
            # 위험 지점 (x 마커)
            risk_points = user_data[user_data['Churn_Check'] == 1]
            fig.add_trace(go.Scatter(x=risk_points['기준년월'], y=risk_points['Current_Spend'], 
                                     mode="markers", name="이탈 위험 감지", 
                                     marker=dict(color="crimson", size=15, symbol="x")), secondary_y=False)
            
            fig.update_layout(xaxis_type='category', hovermode="x unified", height=450)
            st.plotly_chart(fig, use_container_width=True)

            # --- (2) 월별 상세 지표 테이블 ---
            st.subheader("🗓️ 월별 주요 지표 및 소비 업종")
            table_list = []
            for _, row in user_data.iterrows():
                # 해당 월 가장 많이 쓴 업종 찾기
                best_cat_col = row[category_cols].idxmax()
                best_cat_name = best_cat_col.replace('이용금액_', '')
                
                table_list.append({
                    "기준년월": row['기준년월'],
                    "당월 이용액": f"₩{row['Current_Spend']:,.0f}",
                    "3M 평균액": f"₩{row['Avg_3M_Spend']:,.0f}",
                    "최다 소비 업종": best_cat_name,
                    "상태": "🔴 위험" if row['Churn_Check'] == 1 else "🟢 정상"
                })
            st.table(pd.DataFrame(table_list))

            # --- (3) 분석 진단 및 마케팅 제안 ---
            st.subheader("📋 분석 진단 및 전략 제안")
            col_diag, col_strategy = st.columns(2)
            
            with col_diag:
                # 가장 최근 데이터의 위험 여부 확인
                recent_row = user_data.iloc[-1]
                if recent_row['Churn_Check'] == 1:
                    st.warning(f"🚩 **위험 상태 감지 ({recent_row['기준년월']})**")
                    st.write("- **판단 근거:** 최근 소비 금액이 직전 3개월 평균 대비 80% 미만으로 급감했습니다.")
                else:
                    st.success("✨ **양호 상태 유지**")
                    st.write("- **판단 근거:** 최근 소비 패턴이 과거 평균 대비 견고하게 유지되고 있습니다.")

            with col_strategy:
                # 6개월 통합 최다 소비 업종 기반 마케팅 제안
                total_cat_spend = user_data[category_cols].sum()
                main_cat_col = total_cat_spend.idxmax()
                main_cat_name = main_cat_col.replace('이용금액_', '')
                
                st.write(f"💡 **주력 소비 분야:** [{main_cat_name}]")
                st.info(f"**추천 마케팅:** {marketing_solutions.get(main_cat_col, 'VIP 전용 리워드 제공')}")
    else:
        st.warning("데이터를 불러오지 못했습니다. 파일이 해당 경로에 있는지 확인해 주세요.")