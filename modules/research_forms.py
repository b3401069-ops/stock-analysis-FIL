"""
股票追蹤與決策輔助系統 - 研究筆記輸入表單
Stock Tracking & Decision Support System - Research Note Entry Forms

供財報電話會議、投行觀點、5+2 研究三個頁面共用的
新增 / 刪除紀錄 UI 區塊。
"""

import streamlit as st
from datetime import date
from modules.database import get_enabled_stocks


def _stock_options():
    """回傳 {顯示名稱: stock_id}，無自選股時回傳 None 並顯示提示"""
    stocks = get_enabled_stocks()
    if stocks.empty:
        st.info("ℹ️ 尚無自選股，請先到「自選股管理」新增")
        return None
    return {f"{r['stock_id']} {r['name']}": r['stock_id']
            for _, r in stocks.iterrows()}


def render_earnings_call_forms():
    """財報與電話會議頁的記錄管理區塊"""
    from modules.earnings_call import get_earnings_call_manager
    mgr = get_earnings_call_manager()

    st.markdown("---")
    st.subheader("✍️ 記錄管理")
    opts = _stock_options()
    if opts is None:
        return

    with st.expander("➕ 新增電話會議紀錄"):
        with st.form("add_earnings_call_form"):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                label = st.selectbox("股票", list(opts.keys()))
            with c2:
                call_date = st.date_input("會議日期", value=date.today())
            with c3:
                quarter = st.selectbox("季度", ["Q1", "Q2", "Q3", "Q4"])
            with c4:
                fiscal_year = st.text_input("年度", value=str(date.today().year))

            sentiment = st.selectbox("整體情緒", ["正面", "中性", "負面"])
            key_highlights = st.text_area("關鍵重點", placeholder="本季重要訊息、數字...")
            management_guidance = st.text_area("管理層指引",
                                               placeholder="營收/毛利/資本支出展望...")
            outlook_summary = st.text_area("展望摘要")
            notes = st.text_input("備註")

            if st.form_submit_button("💾 儲存", type="primary"):
                ok = mgr.add_earnings_call({
                    'stock_id': opts[label],
                    'call_date': str(call_date),
                    'quarter': quarter,
                    'fiscal_year': fiscal_year,
                    'sentiment': sentiment,
                    'key_highlights': key_highlights,
                    'management_guidance': management_guidance,
                    'outlook_summary': outlook_summary,
                    'notes': notes,
                    'source': '人工記錄',
                    'data_as_of': str(call_date),
                })
                if ok:
                    st.success("✅ 已儲存")
                    st.rerun()
                else:
                    st.error("❌ 儲存失敗")

    with st.expander("🗑️ 刪除紀錄"):
        del_label = st.selectbox("股票 ", list(opts.keys()), key="ec_del_stock")
        records = mgr.get_earnings_calls(stock_id=opts[del_label])
        if records.empty:
            st.caption("此股票沒有紀錄")
        else:
            rec_opts = {f"{r['call_date']}（{r['quarter']} {r['fiscal_year']}）":
                        (r['call_date'], r['quarter'])
                        for _, r in records.iterrows()}
            picked = st.selectbox("選擇紀錄", list(rec_opts.keys()), key="ec_del_rec")
            if st.button("刪除此紀錄", key="ec_del_btn"):
                cdate, q = rec_opts[picked]
                if mgr.delete_earnings_call(opts[del_label], cdate, q):
                    st.success("✅ 已刪除")
                    st.rerun()


def render_analyst_view_forms():
    """投行觀點頁的記錄管理區塊"""
    from modules.analyst_views import get_analyst_views_manager
    mgr = get_analyst_views_manager()

    st.markdown("---")
    st.subheader("✍️ 記錄管理")
    opts = _stock_options()
    if opts is None:
        return

    with st.expander("➕ 新增投行觀點"):
        with st.form("add_analyst_view_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                label = st.selectbox("股票", list(opts.keys()))
            with c2:
                report_date = st.date_input("報告日期", value=date.today())
            with c3:
                analyst_firm = st.text_input("投行名稱", placeholder="例如：Morgan Stanley")

            c4, c5, c6 = st.columns(3)
            with c4:
                rating = st.selectbox("評等", ["買進", "增持", "中立", "減持", "賣出"])
            with c5:
                target_price = st.number_input("目標價", min_value=0.0, step=1.0)
            with c6:
                previous_target = st.number_input("前次目標價（0 = 不填）",
                                                  min_value=0.0, step=1.0)

            key_findings = st.text_area("重點看法")
            report_summary = st.text_area("報告摘要")

            if st.form_submit_button("💾 儲存", type="primary"):
                if not analyst_firm.strip():
                    st.error("❌ 請填寫投行名稱")
                else:
                    ok = mgr.add_analyst_view({
                        'stock_id': opts[label],
                        'report_date': str(report_date),
                        'analyst_firm': analyst_firm.strip(),
                        'rating': rating,
                        'target_price': target_price or None,
                        'previous_target': previous_target or None,
                        'key_findings': key_findings,
                        'report_summary': report_summary,
                        'data_as_of': str(report_date),
                    })
                    if ok:
                        st.success("✅ 已儲存")
                        st.rerun()
                    else:
                        st.error("❌ 儲存失敗")

    with st.expander("🗑️ 刪除紀錄"):
        del_label = st.selectbox("股票 ", list(opts.keys()), key="av_del_stock")
        records = mgr.get_analyst_views(stock_id=opts[del_label])
        if records.empty:
            st.caption("此股票沒有紀錄")
        else:
            rec_opts = {f"{r['report_date']} {r['analyst_firm']}":
                        (r['report_date'], r['analyst_firm'])
                        for _, r in records.iterrows()}
            picked = st.selectbox("選擇紀錄", list(rec_opts.keys()), key="av_del_rec")
            if st.button("刪除此紀錄", key="av_del_btn"):
                rdate, firm = rec_opts[picked]
                if mgr.delete_analyst_view(opts[del_label], rdate, firm):
                    st.success("✅ 已刪除")
                    st.rerun()


def render_research_5plus2_forms():
    """5+2 投資研究頁的記錄管理區塊"""
    from modules.research_5plus2 import get_research_5plus2_manager
    from modules.config import get_config
    mgr = get_research_5plus2_manager()
    config = get_config()

    st.markdown("---")
    st.subheader("✍️ 記錄管理")
    opts = _stock_options()
    if opts is None:
        return

    with st.expander("➕ 新增 5+2 綜合評估"):
        with st.form("add_research_form"):
            c1, c2 = st.columns(2)
            with c1:
                label = st.selectbox("股票", list(opts.keys()))
            with c2:
                analysis_date = st.date_input("分析日期", value=date.today())

            st.caption("五大分析 + 投資邏輯與風險（0-100 分）")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                industry = st.slider("行業分析", 0, 100, 60)
                financial = st.slider("財報分析", 0, 100, 60)
            with c2:
                business = st.slider("商業模式", 0, 100, 60)
                valuation = st.slider("估值分析", 0, 100, 60)
            with c3:
                management = st.slider("管理層", 0, 100, 60)
                thesis = st.slider("投資邏輯", 0, 100, 60)
            with c4:
                risk = st.slider("風險分析", 0, 100, 60)

            investment_logic = st.text_area("投資邏輯：為什麼要買")
            key_weaknesses = st.text_area("分析風險：為什麼不買")
            key_strengths = st.text_area("關鍵優勢")

            if st.form_submit_button("💾 儲存", type="primary"):
                w = config.RESEARCH_5PLUS2_WEIGHTS
                pairs = [
                    (industry, w.get('industry_analysis', 0.15)),
                    (business, w.get('business_model', 0.15)),
                    (management, w.get('management_analysis', 0.15)),
                    (financial, w.get('financial_analysis', 0.15)),
                    (valuation, w.get('valuation', 0.15)),
                    (thesis, w.get('investment_thesis', 0.15)),
                    (risk, w.get('risk_analysis', 0.10)),
                ]
                total = sum(s * wt for s, wt in pairs) / sum(wt for _, wt in pairs)
                th = config.RESEARCH_5PLUS2_THRESHOLDS
                if total >= th.get('investment_logic_established', 80):
                    overall = '投資邏輯成立'
                elif total >= th.get('investment_logic_partial', 60):
                    overall = '投資邏輯部分成立'
                elif total >= th.get('investment_logic_pending', 40):
                    overall = '投資邏輯待確認'
                else:
                    overall = '投資邏輯轉弱'

                ok = mgr.add_research({
                    'stock_id': opts[label],
                    'analysis_date': str(analysis_date),
                    'industry_score': industry,
                    'business_model_score': business,
                    'management_score': management,
                    'financial_score': financial,
                    'valuation_score': valuation,
                    'investment_thesis_score': thesis,
                    'risk_score': risk,
                    'total_score': round(total, 1),
                    'overall_rating': overall,
                    'investment_logic': investment_logic,
                    'key_strengths': key_strengths,
                    'key_weaknesses': key_weaknesses,
                })
                if ok:
                    st.success(f"✅ 已儲存（總分 {total:.1f}，{overall}）")
                    st.rerun()
                else:
                    st.error("❌ 儲存失敗")

    with st.expander("🗑️ 刪除紀錄"):
        del_label = st.selectbox("股票 ", list(opts.keys()), key="r52_del_stock")
        records = mgr.get_research_history(opts[del_label])
        if records.empty:
            st.caption("此股票沒有紀錄")
        else:
            rec_opts = {f"{r['analysis_date']}（總分 {r['total_score']}）":
                        r['analysis_date'] for _, r in records.iterrows()}
            picked = st.selectbox("選擇紀錄", list(rec_opts.keys()), key="r52_del_rec")
            if st.button("刪除此紀錄", key="r52_del_btn"):
                if mgr.delete_research(opts[del_label], rec_opts[picked]):
                    st.success("✅ 已刪除")
                    st.rerun()
