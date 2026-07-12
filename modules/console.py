"""
股票追蹤與決策輔助系統 V1 - 安全控制台輸出模組
Stock Tracking & Decision Support System V1 - Safe Console Output Module

提供安全的控制台輸出功能，避免 Windows CP950 等編碼環境下的 UnicodeEncodeError
"""

import sys
import io


def safe_print(*args, **kwargs):
    """
    安全的 print 函數，處理 Unicode 編碼問題
    
    在 Windows CP950 等環境下，自動將無法編碼的字符替換為安全字符
    """
    try:
        # 先嘗試正常輸出
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # 如果遇到編碼錯誤，將輸出轉為安全字符串
        safe_args = []
        for arg in args:
            safe_arg = _safe_encode(str(arg))
            safe_args.append(safe_arg)
        
        # 重新嘗試輸出
        try:
            print(*safe_args, **kwargs)
        except UnicodeEncodeError:
            # 如果還是失敗，使用 ASCII 安全模式
            ascii_args = []
            for arg in args:
                ascii_arg = str(arg).encode('ascii', 'replace').decode('ascii')
                ascii_args.append(ascii_arg)
            print(*ascii_args, **kwargs)


def _safe_encode(text: str) -> str:
    """
    安全編碼字符串，替換無法在當前環境編碼的字符
    
    Args:
        text: 輸入字符串
        
    Returns:
        安全編碼後的字符串
    """
    # 取得當前 stdout 編碼，預設為 utf-8
    encoding = sys.stdout.encoding or "utf-8"
    
    # 常見的 Unicode 字符映射到 ASCII 安全字符
    char_map = {
        '✅': '[OK]',
        '❌': '[ERROR]',
        '⚠️': '[WARN]',
        '📦': '[DATA]',
        '📊': '[CHART]',
        '⭐': '[STAR]',
        '🔔': '[BELL]',
        '📈': '[UP]',
        '🗑️': '[DELETE]',
        '🔄': '[SYNC]',
        '🚀': '[START]',
        '💡': '[TIP]',
        '🔍': '[SEARCH]',
        '📝': '[NOTE]',
        '🔧': '[FIX]',
        '🟢': '[GREEN]',
        '🔴': '[RED]',
        '🟡': '[YELLOW]',
        '🔵': '[BLUE]',
        '⚪': '[WHITE]',
    }
    
    result = text
    for emoji, replacement in char_map.items():
        result = result.replace(emoji, replacement)
    
    # 嘗試編碼，如果還是失敗則替換為問號
    try:
        result.encode(encoding)
    except UnicodeEncodeError:
        # 替換所有非 ASCII 字符
        result = result.encode(encoding, errors='replace').decode(encoding)
    
    return result


def console_print(*args, **kwargs):
    """
    控制台輸出函數，別名為 safe_print
    """
    safe_print(*args, **kwargs)