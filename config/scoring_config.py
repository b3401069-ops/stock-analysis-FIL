"""
股票追蹤與決策輔助系統 V1 - 評分配置
Stock Tracking & Decision Support System V1 - Scoring Configuration
"""

# 評分權重配置
SCORING_WEIGHTS = {
    'technical': 0.4,  # 技術面權重
    'fundamental': 0.3,  # 基本面權重
    'risk': 0.3  # 風險權重
}

# 評級觀察詞配置
RATING_THRESHOLDS = {
    '強勢追蹤': 80,
    '偏多觀察': 70,
    '普通觀察': 60,
    '風險留意': 50,
    '風險升高': 40,
    '暫不追蹤': 0
}

# 技術面評分配置
TECHNICAL_SCORE_CONFIG = {
    'rsi': {
        'weight': 0.3,
        'oversold': 30,
        'overbought': 70,
        'optimal_low': 40,
        'optimal_high': 60
    },
    'macd': {
        'weight': 0.3,
        'bullish_threshold': 0,
        'bearish_threshold': 0
    },
    'ma': {
        'weight': 0.4,
        'short_period': 5,
        'long_period': 20
    }
}

# 基本面評分配置
FUNDAMENTAL_SCORE_CONFIG = {
    'pe_ratio': {
        'weight': 0.3,
        'optimal_low': 10,
        'optimal_high': 20,
        'max_value': 100
    },
    'pb_ratio': {
        'weight': 0.2,
        'optimal_low': 1,
        'optimal_high': 3,
        'max_value': 10
    },
    'dividend_yield': {
        'weight': 0.2,
        'optimal_low': 2.0,    # 百分比形式，例如 2%
        'optimal_high': 5.0,   # 百分比形式，例如 5%
        'max_value': 10.0      # 百分比形式，例如 10%
    },
    'market_cap': {
        'weight': 0.3,
        'optimal_low': 100,  # 億
        'optimal_high': 1000,  # 億
        'max_value': 10000  # 億
    }
}

# 風險評分配置
RISK_SCORE_CONFIG = {
    'volatility': {
        'weight': 0.4,
        'low_threshold': 0.20,   # 年化波动率 20% 为低波动
        'high_threshold': 0.50   # 年化波动率 50% 为高波动
    },
    'drawdown': {
        'weight': 0.3,
        'low_threshold': -0.1,
        'high_threshold': -0.2
    },
    'volume_change': {
        'weight': 0.3,
        'low_threshold': 0.5,
        'high_threshold': 2.0
    }
}