"""
股票追蹤與決策輔助系統 V1 - 訊號配置
Stock Tracking & Decision Support System V1 - Signals Configuration
"""

# 訊號類型配置
SIGNAL_TYPES = {
    '技術面': {
        'weight': 1.0,
        'description': '技術指標產生的訊號'
    },
    '成交量': {
        'weight': 0.8,
        'description': '成交量異常產生的訊號'
    },
    '價格': {
        'weight': 0.9,
        'description': '價格變動產生的訊號'
    }
}

# RSI 訊號配置
RSI_SIGNALS = {
    '超買': {
        'threshold': 70,
        'severity': '警告',
        'description': 'RSI 高於 {threshold}，可能超買'
    },
    '超賣': {
        'threshold': 30,
        'severity': '機會',
        'description': 'RSI 低於 {threshold}，可能超賣'
    }
}

# MACD 訊號配置
MACD_SIGNALS = {
    '黃金交叉': {
        'condition': 'macd > macd_signal',
        'severity': '偏多',
        'description': 'MACD 線向上突破訊號線，為偏多技術訊號'
    },
    '死亡交叉': {
        'condition': 'macd < macd_signal',
        'severity': '偏空',
        'description': 'MACD 線向下跌破訊號線，為偏空技術訊號'
    }
}

# 移動平均線訊號配置
MA_SIGNALS = {
    '突破 MA20': {
        'condition': 'close > ma20 and prev_close < ma20',
        'severity': '偏多',
        'description': '股價突破 20 日均線，可能開始上漲趨勢'
    },
    '跌破 MA20': {
        'condition': 'close < ma20 and prev_close > ma20',
        'severity': '偏空',
        'description': '股價跌破 20 日均線，可能開始下跌趨勢'
    },
    '多頭排列': {
        'condition': 'close > ma5 > ma20',
        'severity': '偏多',
        'description': '股價 > MA5 > MA20，為多頭排列'
    },
    '空頭排列': {
        'condition': 'close < ma5 < ma20',
        'severity': '偏空',
        'description': '股價 < MA5 < MA20，為空頭排列'
    }
}

# 成交量訊號配置
VOLUME_SIGNALS = {
    '異常放量': {
        'threshold': 2.0,
        'severity': '警告',
        'description': '成交量為 20 日均量的 {ratio:.1f} 倍，需關注'
    },
    '放量上漲': {
        'threshold': 1.5,
        'severity': '偏多',
        'description': '成交量為 20 日均量的 {ratio:.1f} 倍，配合上漲為偏多觀察'
    }
}

# 價格變動訊號配置
PRICE_SIGNALS = {
    '大幅上漲': {
        'threshold': 5.0,
        'severity': '警告',
        'description': '單日上漲 {change:.1f}%，需注意追高風險'
    },
    '大幅下跌': {
        'threshold': -5.0,
        'severity': '警告',
        'description': '單日下跌 {change:.1f}%，需關注是否止跌'
    }
}

# 嚴重度圖示配置
SEVERITY_ICONS = {
    '偏多': '🟢',
    '偏空': '🔴',
    '警告': '🟡',
    '機會': '🔵',
    '資訊': '⚪'
}