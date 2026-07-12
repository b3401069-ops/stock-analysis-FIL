"""
股票追蹤與決策輔助系統 V1 - 警報模組測試
Stock Tracking & Decision Support System V1 - Alerts Module Tests
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# 確保專案根目錄在 Python 路徑中
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_telegram_alert_initialization():
    """測試 Telegram 警報初始化"""
    from modules.alerts import TelegramAlert
    
    # 測試自訂參數（不依賴環境變數）
    alert = TelegramAlert(bot_token='test_token', chat_id='test_chat')
    assert alert.enabled is True
    
    # 測試未設定參數
    alert = TelegramAlert(bot_token=None, chat_id=None)
    assert alert.enabled is False


def test_telegram_alert_custom_params():
    """測試 Telegram 警報自訂參數"""
    from modules.alerts import TelegramAlert
    
    alert = TelegramAlert(bot_token='custom_token', chat_id='custom_chat')
    assert alert.enabled is True
    assert alert.bot_token == 'custom_token'
    assert alert.chat_id == 'custom_chat'


def test_telegram_alert_disabled():
    """測試 Telegram 警報禁用"""
    from modules.alerts import TelegramAlert
    
    alert = TelegramAlert(bot_token=None, chat_id=None)
    assert alert.enabled is False
    
    # 嘗試發送訊息
    result = alert.send_message("測試訊息")
    assert result is False


@patch('modules.alerts.requests.post')
def test_telegram_alert_send_message(mock_post):
    """測試 Telegram 警報發送訊息"""
    from modules.alerts import TelegramAlert
    
    # 模擬成功回應
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    
    alert = TelegramAlert(bot_token='test_token', chat_id='test_chat')
    result = alert.send_message("測試訊息")
    
    assert result is True
    mock_post.assert_called_once()


@patch('modules.alerts.requests.post')
def test_telegram_alert_send_message_failure(mock_post):
    """測試 Telegram 警報發送訊息失敗"""
    from modules.alerts import TelegramAlert
    
    # 模擬失敗回應
    mock_post.side_effect = Exception("Network error")
    
    alert = TelegramAlert(bot_token='test_token', chat_id='test_chat')
    result = alert.send_message("測試訊息")
    
    assert result is False


def test_telegram_alert_token_masking():
    """測試 Telegram token 掩碼功能"""
    from modules.alerts import TelegramAlert
    
    alert = TelegramAlert(bot_token='test_token_123456789', chat_id='test_chat')
    
    # 測試掩碼功能
    masked = alert._mask_token('test_token_123456789')
    assert '123456789' not in masked  # 原始 token 不應出現
    assert 'test_tok' in masked  # 前 8 字元應出現
    assert '6789' in masked  # 後 4 字元應出現
    
    # 測試短 token
    masked_short = alert._mask_token('short')
    assert masked_short == '***'


@patch('modules.alerts.requests.post')
def test_telegram_alert_error_no_raw_token(mock_post, capsys):
    """
    測試 Telegram 例外訊息不得包含 raw token
    確認錯誤日誌不會洩漏完整 token
    """
    from modules.alerts import TelegramAlert
    
    # 使用一個真實的 token 格式
    real_token = 'ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh'
    
    # 模擬失敗回應
    mock_post.side_effect = Exception("Network error")
    
    alert = TelegramAlert(bot_token=real_token, chat_id='test_chat')
    result = alert.send_message("測試訊息")
    
    assert result is False
    
    # 檢查輸出不包含完整 token
    captured = capsys.readouterr()
    assert real_token not in captured.out, "錯誤訊息不應包含完整 token"
    
    # 檢查輸出包含掩碼後的 token
    masked_token = alert._mask_token(real_token)
    assert masked_token in captured.out, "錯誤訊息應包含掩碼後的 token"


@patch('modules.alerts.requests.post')
def test_telegram_alert_error_scrub_url(mock_post, capsys):
    """
    測試 Telegram 例外訊息中的 URL 會被 scrub
    確認 exception message 中的 Telegram API URL 不會洩漏 token
    """
    from modules.alerts import TelegramAlert
    
    # 使用一個真實的 token
    real_token = '1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh'
    
    # 模擬包含 Telegram API URL 的 exception
    error_msg = f"401 Client Error: Unauthorized for url: https://api.telegram.org/bot{real_token}/sendMessage"
    mock_post.side_effect = Exception(error_msg)
    
    alert = TelegramAlert(bot_token=real_token, chat_id='test_chat')
    result = alert.send_message("測試訊息")
    
    assert result is False
    
    # 檢查輸出不包含完整 token
    captured = capsys.readouterr()
    assert real_token not in captured.out, "錯誤訊息不應包含完整 token"
    assert 'bot***' in captured.out, "錯誤訊息應包含 scrub 後的 token"
    # 確認 URL 中的 token 被替換
    assert f'bot{real_token}' not in captured.out, "錯誤訊息不應包含完整 bot token"


def test_telegram_alert_scrub_exception():
    """測試 _scrub_exception 方法"""
    from modules.alerts import TelegramAlert
    
    alert = TelegramAlert(bot_token='test_token', chat_id='test_chat')
    
    # 測試 Telegram URL scrub
    error_with_url = "Error: https://api.telegram.org/bot1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ/sendMessage"
    scrubbed = alert._scrub_exception(error_with_url)
    assert '1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ' not in scrubbed
    assert 'bot***' in scrubbed
    
    # 測試一般錯誤訊息
    error_normal = "Network error"
    scrubbed = alert._scrub_exception(error_normal)
    assert scrubbed == "Network error"


def test_telegram_alert_severity_icon():
    """測試嚴重度圖示"""
    from modules.alerts import TelegramAlert
    
    alert = TelegramAlert()
    
    assert alert._get_severity_icon('偏多') == '🟢'


@patch('modules.alerts.requests.post')
def test_telegram_alert_no_emoji_crash_in_cp950(mock_post, capsys):
    """
    測試 Telegram 錯誤處理在 CP950 環境下不會因 emoji 崩潰
    確認錯誤日誌在 Windows CP950 環境下可以正常輸出
    """
    from modules.alerts import TelegramAlert
    
    # 模擬 CP950 環境
    with patch('sys.stdout') as mock_stdout:
        mock_stdout.encoding = 'cp950'
        mock_stdout.write = MagicMock()
        
        # 模擬失敗回應
        mock_post.side_effect = Exception("Network error")
        
        alert = TelegramAlert(bot_token='test_token', chat_id='test_chat')
        
        # 應該不會崩潰
        result = alert.send_message("測試訊息")
        assert result is False


@patch('modules.alerts.requests.post')
def test_telegram_alert_send_daily_summary(mock_post):
    """測試 Telegram 警報發送每日摘要"""
    from modules.alerts import TelegramAlert
    
    # 模擬成功回應
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    
    alert = TelegramAlert(bot_token='test_token', chat_id='test_chat')
    
    signals = [
        {'stock_name': '台積電', 'signal_name': 'RSI 超買', 'severity': '警告'},
        {'stock_name': '鴻海', 'signal_name': 'MACD 黃金交叉', 'severity': '買入'}
    ]
    
    scores = [
        {'stock_name': '台積電', 'rating': '持有', 'total_score': 65.0},
        {'stock_name': '鴻海', 'rating': '買入', 'total_score': 72.0}
    ]
    
    result = alert.send_daily_summary(signals, scores)
    
    assert result is True
    mock_post.assert_called_once()


@patch('modules.alerts.requests.post')
def test_telegram_alert_send_alert(mock_post):
    """測試 Telegram 警報發送單一警報"""
    from modules.alerts import TelegramAlert
    
    # 模擬成功回應
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    
    alert = TelegramAlert(bot_token='test_token', chat_id='test_chat')
    
    result = alert.send_alert('台積電', 'RSI 超買', '警告', 'RSI = 75，處於超買區域')
    
    assert result is True
    mock_post.assert_called_once()


def test_create_telegram_alert():
    """測試建立 Telegram 警報實例"""
    from modules.alerts import create_telegram_alert
    
    alert = create_telegram_alert()
    assert alert is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])