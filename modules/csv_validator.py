"""
股票追蹤與決策輔助系統 V1 - CSV 驗證模組
Stock Tracking & Decision Support System V1 - CSV Validation Module
"""

import csv
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """驗證結果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    row_count: int
    valid_rows: int
    
    def __str__(self):
        status = "✅ 有效" if self.is_valid else "❌ 無效"
        result = f"{status} ({self.valid_rows}/{self.row_count} 筆資料有效)"
        
        if self.errors:
            result += "\n錯誤:\n" + "\n".join(f"  - {e}" for e in self.errors)
        
        if self.warnings:
            result += "\n警告:\n" + "\n".join(f"  - {w}" for w in self.warnings)
        
        return result


class CSVValidator:
    """CSV 驗證器"""
    
    # 定義每個 CSV 檔案的必要欄位
    REQUIRED_COLUMNS = {
        'stocks': ['stock_id', 'name', 'market', 'industry', 'enabled'],
        'prices': ['stock_id', 'date', 'open', 'high', 'low', 'close', 'volume'],
        'fundamentals': ['stock_id', 'date', 'pe_ratio', 'pb_ratio', 'dividend_yield', 'market_cap', 'revenue', 'net_income', 'eps', 'roe']
    }
    
    # 定義欄位類型
    COLUMN_TYPES = {
        'stocks': {
            'stock_id': str,
            'name': str,
            'market': str,
            'industry': str,
            'enabled': int
        },
        'prices': {
            'stock_id': str,
            'date': str,  # 日期格式稍後驗證
            'open': float,
            'high': float,
            'low': float,
            'close': float,
            'volume': int
        },
        'fundamentals': {
            'stock_id': str,
            'date': str,
            'pe_ratio': float,
            'pb_ratio': float,
            'dividend_yield': float,
            'market_cap': float,
            'revenue': float,
            'net_income': float,
            'eps': float,
            'roe': float
        }
    }
    
    @classmethod
    def validate_csv(cls, file_path: Path, csv_type: str) -> ValidationResult:
        """
        驗證 CSV 檔案
        
        Args:
            file_path: CSV 檔案路徑
            csv_type: CSV 類型 ('stocks', 'prices', 'fundamentals')
            
        Returns:
            驗證結果
        """
        errors = []
        warnings = []
        
        # 檢查檔案是否存在
        if not file_path.exists():
            return ValidationResult(
                is_valid=False,
                errors=[f"檔案不存在: {file_path}"],
                warnings=[],
                row_count=0,
                valid_rows=0
            )
        
        # 檢查 CSV 類型是否支援
        if csv_type not in cls.REQUIRED_COLUMNS:
            return ValidationResult(
                is_valid=False,
                errors=[f"不支援的 CSV 類型: {csv_type}"],
                warnings=[],
                row_count=0,
                valid_rows=0
            )
        
        try:
            # 讀取 CSV
            df = pd.read_csv(file_path, encoding='utf-8')
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"讀取 CSV 失敗: {e}"],
                warnings=[],
                row_count=0,
                valid_rows=0
            )
        
        row_count = len(df)
        
        # 檢查必要欄位
        required_cols = cls.REQUIRED_COLUMNS[csv_type]
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            errors.append(f"缺少必要欄位: {', '.join(missing_cols)}")
        
        # 如果缺少欄位，無法繼續驗證
        if errors:
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                row_count=row_count,
                valid_rows=0
            )
        
        # 驗證每一行
        valid_rows = 0
        duplicate_rows = []
        
        for idx, row in df.iterrows():
            row_errors = cls._validate_row(row, csv_type, idx)
            
            if row_errors:
                for error in row_errors:
                    errors.append(f"第 {idx + 2} 行: {error}")
            else:
                valid_rows += 1
        
        # 檢查重複資料
        if csv_type == 'stocks':
            duplicates = df[df.duplicated(subset=['stock_id'], keep=False)]
            if not duplicates.empty:
                duplicate_ids = duplicates['stock_id'].unique().tolist()
                warnings.append(f"發現重複 stock_id: {duplicate_ids}")
        
        elif csv_type == 'prices':
            duplicates = df[df.duplicated(subset=['stock_id', 'date'], keep=False)]
            if not duplicates.empty:
                duplicate_count = len(duplicates) // 2
                warnings.append(f"發現 {duplicate_count} 筆重複價格記錄")
        
        elif csv_type == 'fundamentals':
            duplicates = df[df.duplicated(subset=['stock_id', 'date'], keep=False)]
            if not duplicates.empty:
                duplicate_count = len(duplicates) // 2
                warnings.append(f"發現 {duplicate_count} 筆重複基本面記錄")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            row_count=row_count,
            valid_rows=valid_rows
        )
    
    @classmethod
    def _validate_row(cls, row: pd.Series, csv_type: str, row_idx: int) -> List[str]:
        """驗證單行資料"""
        errors = []
        column_types = cls.COLUMN_TYPES[csv_type]
        
        for column, expected_type in column_types.items():
            if column not in row.index:
                continue
            
            value = row[column]
            
            # 檢查空值
            if pd.isna(value) or (isinstance(value, str) and value.strip() == ''):
                errors.append(f"欄位 '{column}' 為空值")
                continue
            
            # 檢查類型
            try:
                if expected_type == int:
                    int(value)
                elif expected_type == float:
                    float(value)
                elif expected_type == str:
                    str(value)
            except (ValueError, TypeError):
                errors.append(f"欄位 '{column}' 類型錯誤: 期望 {expected_type.__name__}，實際 {type(value).__name__}")
        
        # 額外驗證
        if csv_type == 'prices':
            # 驗證日期格式
            try:
                pd.to_datetime(row['date'])
            except:
                errors.append(f"日期格式錯誤: {row['date']}")
            
            # 驗證價格合理性
            if 'open' in row and 'close' in row:
                if float(row['open']) <= 0 or float(row['close']) <= 0:
                    errors.append("價格不能為負數或零")
        
        return errors
    
    @classmethod
    def validate_and_report(cls, file_path: Path, csv_type: str, verbose: bool = True) -> ValidationResult:
        """驗證並報告結果"""
        result = cls.validate_csv(file_path, csv_type)
        
        if verbose:
            print(f"\n{'='*50}")
            print(f"CSV 驗證報告: {file_path.name}")
            print(f"{'='*50}")
            print(result)
        
        return result