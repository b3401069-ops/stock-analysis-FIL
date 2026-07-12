"""
股票追蹤與決策輔助系統 V1.1 - 5+2 投資研究框架頁
Stock Tracking & Decision Support System V1.1 - 5+2 Research Framework Page

整合 5+2 分析法的完整研究頁面
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from modules.database import get_enabled_stocks
from modules.industry_analysis import get_industry_analysis_manager
from modules.business_model import get_business_model_manager
from modules.management_analysis import get_management_analysis_manager
from modules.financial_analysis import get_financial_analysis_manager
from modules.valuation import get_valuation_analysis_manager
from modules.investment_thesis import get_investment_thesis_manager
from modules.risk_analysis import get_risk_analysis_manager
from modules.research_5plus2 import get_research_5plus2_manager

# 設定頁面配置
st.set_page_config(
    page_title="5+2 投資研究框架 - 股票追蹤系統",
    page_icon="📋",
    layout="wide"
)

from modules.ui import apply_style
apply_style()

# 頁面標題
st.title("📋 5+2 投資研究框架")
st.markdown("""
**5+2 投資研究框架**是一套系統化的投資分析方法：

**前五個步驟：**
1. 行業分析
2. 商業模式分析
3. 經營管理層分析
4. 財報分析
5. 公司估值分析

**後兩個步驟：**
1. 投資邏輯：正向假設
2. 分析風險：反向風險
""")
st.markdown("---")

# 取得自選股清單
try:
    stocks = get_enabled_stocks()

    if stocks.empty:
        st.warning("⚠️ 沒有自選股資料，請先執行 `python scripts/init_db.py`")
    else:
        # 股票選擇器
        stock_options = {f"{row['stock_id']} {row['name']}": row['stock_id'] for _, row in stocks.iterrows()}
        selected_stock_label = st.selectbox(
            "選擇股票",
            options=list(stock_options.keys()),
            index=0
        )
        selected_stock_id = stock_options[selected_stock_label]

        # 初始化管理器
        industry_manager = get_industry_analysis_manager()
        business_manager = get_business_model_manager()
        management_manager = get_management_analysis_manager()
        financial_manager = get_financial_analysis_manager()
        valuation_manager = get_valuation_analysis_manager()
        thesis_manager = get_investment_thesis_manager()
        risk_manager = get_risk_analysis_manager()
        research_manager = get_research_5plus2_manager()

        # 取得分析資料
        industry_analysis = industry_manager.get_industry_analysis(selected_stock_id)
        business_analysis = business_manager.get_business_model(selected_stock_id)
        management_analysis = management_manager.get_management_analysis(selected_stock_id)
        financial_analysis = financial_manager.get_financial_analysis(selected_stock_id)
        valuation_analysis = valuation_manager.get_valuation_analysis(selected_stock_id)
        thesis_analysis = thesis_manager.get_investment_thesis(selected_stock_id)
        risk_analysis = risk_manager.get_risk_analysis(selected_stock_id)

        # 顯示 5+2 綜合評估
        st.subheader(f"📊 {selected_stock_id} - 5+2 綜合評估")

        research_data = research_manager.get_latest_research(selected_stock_id)
        if research_data:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("總評分", f"{research_data.get('total_score', 0):.1f}")
            with col2:
                st.metric("投資邏輯", research_data.get('investment_logic', 'N/A'))
            with col3:
                st.metric("關鍵優勢", research_data.get('key_strengths', 'N/A')[:20] + "...")
            with col4:
                st.metric("關鍵弱點", research_data.get('key_weaknesses', 'N/A')[:20] + "...")
        else:
            st.info("ℹ️ 尚無 5+2 綜合評估資料")

        st.markdown("---")

        # 顯示各分析模組
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "1️⃣ 行業分析", "2️⃣ 商業模式", "3️⃣ 管理層", "4️⃣ 財報分析",
            "5️⃣ 估值分析", "6️⃣ 投資邏輯", "7️⃣ 風險分析"
        ])

        with tab1:
            st.subheader("🏭 行業分析")
            if industry_analysis:
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**行業名稱：** {industry_analysis.get('industry_name', 'N/A')}")
                    st.write(f"**市場規模：** {industry_analysis.get('market_size', 'N/A')}")
                    st.write(f"**成長率：** {industry_analysis.get('growth_rate', 'N/A')}%")
                    st.write(f"**競爭程度：** {industry_analysis.get('competition_level', 'N/A')}")
                    st.write(f"**進入障礙：** {industry_analysis.get('entry_barriers', 'N/A')}")
                with col2:
                    st.write(f"**行業趨勢：** {industry_analysis.get('industry_trends', 'N/A')}")
                    st.write(f"**關鍵驅動力：** {industry_analysis.get('key_drivers', 'N/A')}")
                    st.write(f"**威脅：** {industry_analysis.get('threats', 'N/A')}")
                    st.write(f"**展望：** {industry_analysis.get('outlook', 'N/A')}")
                    score = industry_analysis.get('score')
                    if score:
                        st.metric("行業評分", f"{score:.1f}")
            else:
                st.warning("⚠️ 尚無行業分析資料")

        with tab2:
            st.subheader("💼 商業模式分析")
            if business_analysis:
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**商業模式類型：** {business_analysis.get('business_model_type', 'N/A')}")
                    st.write(f"**收入來源：** {business_analysis.get('revenue_streams', 'N/A')}")
                    st.write(f"**價值主張：** {business_analysis.get('value_proposition', 'N/A')}")
                    st.write(f"**競爭優勢：** {business_analysis.get('competitive_advantage', 'N/A')}")
                with col2:
                    st.write(f"**客戶群體：** {business_analysis.get('customer_segments', 'N/A')}")
                    st.write(f"**成本結構：** {business_analysis.get('cost_structure', 'N/A')}")
                    st.write(f"**可擴展性：** {business_analysis.get('scalability', 'N/A')}")
                    st.write(f"**永續性：** {business_analysis.get('sustainability', 'N/A')}")
                    score = business_analysis.get('score')
                    if score:
                        st.metric("商業模式評分", f"{score:.1f}")
            else:
                st.warning("⚠️ 尚無商業模式分析資料")

        with tab3:
            st.subheader("👥 經營管理層分析")
            if management_analysis:
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**執行長：** {management_analysis.get('ceo_name', 'N/A')}")
                    st.write(f"**執行長背景：** {management_analysis.get('ceo_background', 'N/A')}")
                    st.write(f"**管理團隊規模：** {management_analysis.get('management_team_size', 'N/A')}")
                    st.write(f"**平均任期：** {management_analysis.get('avg_tenure_years', 'N/A')} 年")
                    st.write(f"**內部持股：** {management_analysis.get('insider_ownership', 'N/A')}%")
                with col2:
                    st.write(f"**主要股東：** {management_analysis.get('major_shareholders', 'N/A')}")
                    st.write(f"**公司治理：** {management_analysis.get('corporate_governance', 'N/A')}")
                    st.write(f"**薪酬結構：** {management_analysis.get('compensation_structure', 'N/A')}")
                    st.write(f"**過去績效：** {management_analysis.get('track_record', 'N/A')}")
                    st.write(f"**策略願景：** {management_analysis.get('strategic_vision', 'N/A')}")
                    score = management_analysis.get('score')
                    if score:
                        st.metric("管理層評分", f"{score:.1f}")
            else:
                st.warning("⚠️ 尚無經營管理層分析資料")

        with tab4:
            st.subheader("📊 財報分析")
            if financial_analysis:
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**報告期間：** {financial_analysis.get('report_period', 'N/A')}")
                    st.write(f"**營收：** {financial_analysis.get('revenue', 'N/A'):,.0f}")
                    st.write(f"**營收成長：** {financial_analysis.get('revenue_growth', 'N/A')}%")
                    st.write(f"**毛利率：** {financial_analysis.get('gross_margin', 'N/A')}%")
                    st.write(f"**營業利益率：** {financial_analysis.get('operating_margin', 'N/A')}%")
                    st.write(f"**淨利率：** {financial_analysis.get('net_margin', 'N/A')}%")
                with col2:
                    st.write(f"**ROE：** {financial_analysis.get('roe', 'N/A')}%")
                    st.write(f"**ROA：** {financial_analysis.get('roa', 'N/A')}%")
                    st.write(f"**負債比率：** {financial_analysis.get('debt_to_equity', 'N/A')}")
                    st.write(f"**流動比率：** {financial_analysis.get('current_ratio', 'N/A')}")
                    st.write(f"**自由現金流：** {financial_analysis.get('free_cash_flow', 'N/A'):,.0f}")
                    score = financial_analysis.get('score')
                    if score:
                        st.metric("財報評分", f"{score:.1f}")
            else:
                st.warning("⚠️ 尚無財報分析資料")

        with tab5:
            st.subheader("💰 估值分析")
            if valuation_analysis:
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**目前股價：** {valuation_analysis.get('current_price', 'N/A')}")
                    st.write(f"**本益比：** {valuation_analysis.get('pe_ratio', 'N/A')}")
                    st.write(f"**股價淨值比：** {valuation_analysis.get('pb_ratio', 'N/A')}")
                    st.write(f"**股價營收比：** {valuation_analysis.get('ps_ratio', 'N/A')}")
                    st.write(f"**殖利率：** {valuation_analysis.get('dividend_yield', 'N/A')}%")
                with col2:
                    st.write(f"**DCF 價值：** {valuation_analysis.get('dcf_value', 'N/A')}")
                    st.write(f"**安全邊際：** {valuation_analysis.get('margin_of_safety', 'N/A')}%")
                    st.write(f"**估值評級：** {valuation_analysis.get('valuation_rating', 'N/A')}")
                    st.write(f"**歷史平均本益比：** {valuation_analysis.get('historical_avg_pe', 'N/A')}")
                    st.write(f"**產業平均本益比：** {valuation_analysis.get('industry_avg_pe', 'N/A')}")
                    score = valuation_analysis.get('score')
                    if score:
                        st.metric("估值評分", f"{score:.1f}")
            else:
                st.warning("⚠️ 尚無估值分析資料")

        with tab6:
            st.subheader("🎯 投資邏輯")
            if thesis_analysis:
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**投資邏輯摘要：** {thesis_analysis.get('thesis_summary', 'N/A')}")
                    st.write(f"**觀察理由：** {thesis_analysis.get('buy_reasons', 'N/A')}")
                    st.write(f"**催化劑：** {thesis_analysis.get('catalysts', 'N/A')}")
                    st.write(f"**目標價：** {thesis_analysis.get('target_price', 'N/A')}")
                with col2:
                    st.write(f"**投資期間：** {thesis_analysis.get('investment_horizon', 'N/A')}")
                    st.write(f"**部位規模：** {thesis_analysis.get('position_sizing', 'N/A')}")
                    st.write(f"**情境假設：** {thesis_analysis.get('entry_strategy', 'N/A')}")
                    st.write(f"**退出條件：** {thesis_analysis.get('exit_strategy', 'N/A')}")
                    st.write(f"**邏輯狀態：** {thesis_analysis.get('thesis_status', 'N/A')}")
                    st.write(f"**信心水準：** {thesis_analysis.get('confidence_level', 'N/A')}")
                    score = thesis_analysis.get('score')
                    if score:
                        st.metric("投資邏輯評分", f"{score:.1f}")
            else:
                st.warning("⚠️ 尚無投資邏輯資料")

        with tab7:
            st.subheader("⚠️ 風險分析")
            if risk_analysis:
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**業務風險：** {risk_analysis.get('business_risks', 'N/A')}")
                    st.write(f"**財務風險：** {risk_analysis.get('financial_risks', 'N/A')}")
                    st.write(f"**市場風險：** {risk_analysis.get('market_risks', 'N/A')}")
                    st.write(f"**監管風險：** {risk_analysis.get('regulatory_risks', 'N/A')}")
                    st.write(f"**競爭風險：** {risk_analysis.get('competitive_risks', 'N/A')}")
                with col2:
                    st.write(f"**管理層風險：** {risk_analysis.get('management_risks', 'N/A')}")
                    st.write(f"**流動性風險：** {risk_analysis.get('liquidity_risks', 'N/A')}")
                    st.write(f"**匯率風險：** {risk_analysis.get('currency_risks', 'N/A')}")
                    st.write(f"**地緣政治風險：** {risk_analysis.get('geopolitical_risks', 'N/A')}")
                    st.write(f"**黑天鵝風險：** {risk_analysis.get('black_swan_risks', 'N/A')}")
                    st.write(f"**整體風險等級：** {risk_analysis.get('overall_risk_level', 'N/A')}")
                    score = risk_analysis.get('score')
                    if score:
                        st.metric("風險評分", f"{score:.1f}")
            else:
                st.warning("⚠️ 尚無風險分析資料")

        # 顯示分析歷史
        st.markdown("---")
        st.subheader("📅 分析歷史")

        research_history = research_manager.get_research_history(selected_stock_id)
        if not research_history.empty:
            st.dataframe(
                research_history[['analysis_date', 'total_score', 'overall_rating', 'investment_logic']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("ℹ️ 尚無分析歷史資料")

except Exception as e:
    st.error(f"❌ 載入資料時發生錯誤: {e}")
    st.exception(e)

# 側邊欄
with st.sidebar:
    st.header("📋 5+2 研究框架")
    st.markdown("""
    **前五個步驟：**
    1. 行業分析
    2. 商業模式分析
    3. 經營管理層分析
    4. 財報分析
    5. 公司估值分析

    **後兩個步驟：**
    1. 投資邏輯：正向假設
    2. 分析風險：反向風險
    """)

    st.markdown("---")
    st.markdown("### 📊 評級說明")
    st.markdown("""
    - **投資邏輯成立**：80分以上
    - **投資邏輯部分成立**：60-79分
    - **投資邏輯待確認**：40-59分
    - **投資邏輯轉弱**：40分以下
    """)

    st.markdown("---")
    st.markdown("### ⚙️ 免責聲明")
    st.markdown("""
    本系統僅供學習與研究用途，不構成任何投資建議。
    所有評級僅供技術分析參考，投資有風險，請謹慎評估。
    """)

# 頁面底部
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>5+2 投資研究框架 | 僅供學習研究使用</p>
</div>
""", unsafe_allow_html=True)

# ---------- 記錄管理（新增 / 刪除） ----------
from modules.research_forms import render_research_5plus2_forms
render_research_5plus2_forms()
