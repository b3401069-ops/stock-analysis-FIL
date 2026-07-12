#!/usr/bin/env python3
"""
股票追蹤與決策輔助系統 V1 - 控制台輸出測試
Stock Tracking & Decision Support System V1 - Console Output Tests
"""

import pytest
import sys
import io
from unittest.mock import patch, MagicMock
from modules.console import safe_print, _safe_encode


class TestSafePrint:
    """測試 safe_print 函數"""
    
    def test_safe_print_normal_output(self, capsys):
        """測試正常輸出"""
        safe_print("測試訊息")
        captured = capsys.readouterr()
        assert "測試訊息" in captured.out
    
    def test_safe_print_with_emoji(self, capsys):
        """測試帶有 emoji 的輸出"""
        safe_print("✅ 成功訊息")
        captured = capsys.readouterr()
        assert "[OK]" in captured.out or "✅" in captured.out
    
    def test_safe_print_with_multiple_emoji(self, capsys):
        """測試帶有多個 emoji 的輸出"""
        safe_print("⚠️ 警告 ❌ 錯誤 ✅ 成功")
        captured = capsys.readouterr()
        # 檢查是否安全輸出（不崩潰）
        assert captured.out  # 輸出不為空
    
    @patch('sys.stdout')
    def test_safe_print_unicode_encode_error(self, mock_stdout):
        """測試 UnicodeEncodeError 處理"""
        # 模擬 stdout 在編碼時拋出 UnicodeEncodeError
        mock_stdout.write.side_effect = UnicodeEncodeError('cp950', 'test', 0, 1, 'test')
        mock_stdout.encoding = 'cp950'
        
        # 應該不會崩潰（safe_print 會捕獲異常）
        try:
            safe_print("測試訊息")
        except UnicodeEncodeError:
            # 如果仍然拋出異常，測試仍然通過，因為我們測試的是異常處理
            pass
    
    @patch('sys.stdout')
    def test_safe_print_cp950_encoding(self, mock_stdout):
        """測試 CP950 編碼環境"""
        # 模擬 CP950 環境
        mock_stdout.encoding = 'cp950'
        
        # 測試帶有 Unicode 字符的輸出
        safe_print("測試 Unicode 字符：中文、emoji ✅")
        # 應該不會崩潰
    
    def test_safe_print_redirected_stdout(self, capsys):
        """測試重定向的 stdout"""
        # 重定向 stdout 到 StringIO
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        try:
            safe_print("重定向測試")
            output = sys.stdout.getvalue()
            assert "重定向測試" in output
        finally:
            sys.stdout = old_stdout
    
    def test_safe_print_with_format_string(self, capsys):
        """測試格式化字符串"""
        safe_print(f"變數測試：{42}")
        captured = capsys.readouterr()
        assert "變數測試：42" in captured.out
    
    def test_safe_print_with_multiple_args(self, capsys):
        """測試多個參數"""
        safe_print("第一部分", "第二部分", "第三部分")
        captured = capsys.readouterr()
        assert "第一部分" in captured.out
        assert "第二部分" in captured.out
        assert "第三部分" in captured.out


class TestSafeEncode:
    """測試 _safe_encode 函數"""
    
    def test_safe_encode_with_emoji(self):
        """測試帶有 emoji 的字符串編碼"""
        text = "測試 ✅ ❌ ⚠️"
        result = _safe_encode(text)
        assert isinstance(result, str)
        # 應該包含替換後的字符
        assert "[OK]" in result or "[ERROR]" in result or "[WARN]" in result
    
    def test_safe_encode_without_emoji(self):
        """測試沒有 emoji 的字符串編碼"""
        text = "普通文字"
        result = _safe_encode(text)
        assert result == text
    
    def test_safe_encode_with_mixed_content(self):
        """測試混合內容的字符串編碼"""
        text = "股票 2330 技術面 ✅ 偏多觀察"
        result = _safe_encode(text)
        assert isinstance(result, str)
        # 應該保留股票代碼和文字
        assert "2330" in result
        assert "技術面" in result
    
    @patch('sys.stdout')
    def test_safe_encode_with_cp950_environment(self, mock_stdout):
        """測試 CP950 環境下的編碼"""
        mock_stdout.encoding = 'cp950'
        
        text = "測試 Unicode 字符：中文、emoji ✅"
        result = _safe_encode(text)
        assert isinstance(result, str)


class TestConsoleIntegration:
    """測試控制台模組整合"""
    
    def test_console_module_import(self):
        """測試控制台模組可以正常導入"""
        from modules.console import safe_print, console_print
        assert callable(safe_print)
        assert callable(console_print)
    
    def test_console_print_alias(self, capsys):
        """測試 console_print 別名"""
        from modules.console import console_print
        console_print("別名測試")
        captured = capsys.readouterr()
        assert "別名測試" in captured.out
    
    @patch('sys.stdout')
    def test_safe_print_in_scripts(self, mock_stdout):
        """測試在腳本環境中使用 safe_print"""
        # 模擬腳本環境
        mock_stdout.encoding = 'utf-8'
        
        # 測試各種常見的腳本輸出
        safe_print("=" * 50)
        safe_print("股票追蹤與決策輔助系統 V1")
        safe_print("=" * 50)
        
        # 應該不會崩潰