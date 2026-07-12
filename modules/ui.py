"""
股票追蹤與決策輔助系統 - 共用 UI 樣式模組
Stock Tracking & Decision Support System - Shared UI Styles

各頁面在 st.set_page_config() 之後呼叫 apply_style() 套用統一外觀。
"""

import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap');

html, body, [class*="st-"], [class*="css"] {
    font-family: 'Noto Sans TC', 'Microsoft JhengHei', sans-serif;
}

/* 還原 Streamlit 圖示字型（否則 expander 箭頭等圖示會變成文字） */
[data-testid="stIconMaterial"],
span[translate="no"],
[class*="material-symbols"],
[class*="st-emotion"] i {
    font-family: 'Material Symbols Rounded', 'Material Symbols Outlined',
                 'Material Icons' !important;
}

/* 隱藏 Streamlit 預設雜訊 */
#MainMenu, footer { visibility: hidden; }
.stDeployButton, [data-testid="stToolbar"] { display: none; }

/* 頁面標題 */
h1 {
    font-weight: 700;
    letter-spacing: 0.5px;
    padding-bottom: 0.4rem;
    border-bottom: 3px solid #D64545;
}
h2, h3 { font-weight: 600; }

/* 指標卡片（st.metric） */
div[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E6E8EF;
    border-radius: 12px;
    padding: 14px 18px;
    box-shadow: 0 1px 3px rgba(16, 24, 40, 0.06);
}
div[data-testid="stMetric"] label { color: #667085; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] { font-weight: 700; }

/* 深色側邊欄 */
section[data-testid="stSidebar"] {
    background: #101828;
}
section[data-testid="stSidebar"] * {
    color: #E4E7EC !important;
}
section[data-testid="stSidebar"] a:hover {
    color: #FFFFFF !important;
}

/* 按鈕 */
.stButton > button {
    border-radius: 8px;
    font-weight: 600;
}

/* 表格 */
div[data-testid="stDataFrame"] {
    border: 1px solid #E6E8EF;
    border-radius: 10px;
    overflow: hidden;
}

/* 首頁橫幅 */
.app-hero {
    background: linear-gradient(120deg, #101828 0%, #1D2939 55%, #3E1C24 100%);
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 8px;
}
.app-hero h1 {
    color: #FFFFFF;
    border: none;
    margin: 0 0 6px 0;
    padding: 0;
}
.app-hero p {
    color: #98A2B3;
    margin: 0;
    font-size: 0.95rem;
}
</style>
"""


def apply_style():
    """套用全站共用樣式（在 st.set_page_config 之後呼叫）"""
    st.markdown(_CSS, unsafe_allow_html=True)


def color_change(val):
    """漲跌欄位著色（台股慣例：紅漲綠跌），供 DataFrame Styler 使用"""
    if isinstance(val, str):
        if val.startswith('+') and not val.startswith('+0.00'):
            return 'color: #D64545; font-weight: 600'
        if val.startswith('-'):
            return 'color: #12876F; font-weight: 600'
    return ''
