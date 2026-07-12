"""
股票追蹤與決策輔助系統 V1 - 警報模組
Stock Tracking & Decision Support System V1 - Alerts Module
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime
from modules.config import get_config
from modules.console import safe_print


class TelegramAlert:
    """Telegram 警報類別"""
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """
        初始化 Telegram 警報
        
        Args:
            bot_token: Telegram Bot Token
            chat_id: Telegram Chat ID
        """
        config = get_config()
        self.bot_token = bot_token or config.TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or config.TELEGRAM_CHAT_ID
        self.enabled = bool(self.bot_token and self.chat_id)
    
    def _mask_token(self, token: str) -> str:
        """掩碼 token，只顯示前 8 字元和後 4 字元"""
        if not token or len(token) < 12:
            return "***"
        return f"{token[:8]}...{token[-4:]}"
    
    def _scrub_exception(self, error_msg: str) -> str:
        """
        清理 exception message 中的敏感資訊
        移除 Telegram API URL 中的 bot token
        """
        import re
        # 移除 Telegram API URL 中的 bot token
        # 模式：https://api.telegram.org/bot{token}/
        scrubbed = re.sub(
            r'https://api\.telegram\.org/bot[^/]+/',
            'https://api.telegram.org/bot***/',
            str(error_msg)
        )
        # 移除任何看起來像 token 的字串
        scrubbed = re.sub(r'bot\d+:[A-Za-z0-9_-]+', 'bot***:***', scrubbed)
        return scrubbed
    
    def send_message(self, message: str, parse_mode: str = 'Markdown') -> bool:
        """
        發送訊息到 Telegram
        
        Args:
            message: 訊息內容
            parse_mode: 解析模式 (Markdown 或 HTML)
            
        Returns:
            是否成功
        """
        if not self.enabled:
            safe_print("⚠️  Telegram 未設定，跳過發送")
            return False
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': parse_mode
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            safe_print(f"✅ Telegram 訊息發送成功")
            return True
        except Exception as e:
            # 掩碼 token 後再記錄錯誤
            masked_token = self._mask_token(self.bot_token)
            scrubbed_error = self._scrub_exception(str(e))
            safe_print(f"❌ Telegram 訊息發送失敗 (token: {masked_token}): {scrubbed_error}")
            return False
    
    def send_daily_summary(self, signals: List[Dict], scores: List[Dict]) -> bool:
        """
        發送每日摘要
        
        Args:
            signals: 訊號列表
            scores: 評分列表
            
        Returns:
            是否成功
        """
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        message = f"📊 *股票追蹤系統 - 每日摘要*\n"
        message += f"📅 {now}\n\n"
        
        # 訊號摘要
        if signals:
            message += f"🔔 *今日訊號 ({len(signals)} 個)*\n"
            for signal in signals[:5]:  # 最多顯示 5 個
                icon = self._get_severity_icon(signal.get('severity', ''))
                message += f"{icon} {signal.get('stock_name', '')} - {signal.get('signal_name', '')}\n"
            if len(signals) > 5:
                message += f"... 還有 {len(signals) - 5} 個訊號\n"
            message += "\n"
        else:
            message += "ℹ️ 今日沒有訊號\n\n"
        
        # 評分摘要
        if scores:
            message += f"⭐ *股票評分*\n"
            for score in scores[:5]:  # 最多顯示 5 個
                rating = score.get('rating', '')
                total_score = score.get('total_score', 0)
                message += f"📈 {score.get('stock_name', '')} - {rating} ({total_score:.1f}分)\n"
            if len(scores) > 5:
                message += f"... 還有 {len(scores) - 5} 檔股票\n"
        
        message += "\n_由股票追蹤系統自動產生_"
        
        return self.send_message(message)
    
    def send_alert(self, stock_name: str, signal_name: str, severity: str, description: str) -> bool:
        """
        發送單一警報
        
        Args:
            stock_name: 股票名稱
            signal_name: 訊號名稱
            severity: 嚴重度
            description: 描述
            
        Returns:
            是否成功
        """
        icon = self._get_severity_icon(severity)
        
        message = f"{icon} *{stock_name}* - {signal_name}\n"
        message += f"{description}\n\n"
        message += f"_嚴重度: {severity}_"
        
        return self.send_message(message)
    
    def _get_severity_icon(self, severity: str) -> str:
        """取得嚴重度圖示"""
        icons = {
            '偏多': '🟢',
            '偏空': '🔴',
            '警告': '🟡',
            '機會': '🔵',
            '資訊': '⚪'
        }
        return icons.get(severity, '⚪')


def create_telegram_alert() -> TelegramAlert:
    """建立 Telegram 警報實例"""
    return TelegramAlert()


def send_daily_alerts():
    """發送每日警報"""
    from modules.database import get_latest_signals, get_scores

    alert = create_telegram_alert()

    if not alert.enabled:
        safe_print("⚠️  Telegram 未設定，無法發送警報")
        safe_print("請設定環境變數 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID")
        return False

    # 取得最新一批訊號
    signals_df = get_latest_signals()
    signals = signals_df.to_dict('records') if not signals_df.empty else []
    
    # 取得評分
    scores_df = get_scores()
    scores = scores_df.to_dict('records') if not scores_df.empty else []
    
    # 發送摘要
    success = alert.send_daily_summary(signals, scores)
    
    return success