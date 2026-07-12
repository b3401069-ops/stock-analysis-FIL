"""
股票追蹤與決策輔助系統 V1 - CSV 驗證測試
Stock Tracking & Decision Support System V1 - CSV Validation Tests
"""

import pytest
import tempfile
import pandas as pd
from pathlib import Path


@pytest.fixture
def valid_stocks_csv(tmp_path):
    """有效的股票 CSV 檔案"""
    csv_path = tmp_path / "stocks.csv"
    df = pd.DataFrame({
        'stock_id': ['2330', '2317'],
        'name': ['台積電', '鴻海'],
        'market': ['上市', '上市'],
        'industry': ['半導體', '電子'],
        'enabled': [1, 1]
    })
    df.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def valid_prices_csv(tmp_path):
    """有效的價格 CSV 檔案"""
    csv_path = tmp_path / "prices.csv"
    df = pd.DataFrame({
        'stock_id': ['2330', '2330'],
        'date': ['2024-01-01', '2024-01-02'],
        'open': [600.0, 610.0],
        'high': [620.0, 630.0],
        'low': [590.0, 600.0],
        'close': [615.0, 625.0],
        'volume': [1000000, 1200000]
    })
    df.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def invalid_csv_missing_columns(tmp_path):
    """缺少欄位的 CSV 檔案"""
    csv_path = tmp_path / "invalid.csv"
    df = pd.DataFrame({
        'stock_id': ['2330'],
        'name': ['台積電']
        # 缺少 market, industry, enabled
    })
    df.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def invalid_csv_empty_values(tmp_path):
    """包含空值的 CSV 檔案"""
    csv_path = tmp_path / "empty_values.csv"
    df = pd.DataFrame({
        'stock_id': ['2330', '2317'],
        'name': ['台積電', ''],
        'market': ['上市', '上市'],
        'industry': ['半導體', '電子'],
        'enabled': [1, 1]
    })
    df.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def invalid_csv_wrong_types(tmp_path):
    """類型錯誤的 CSV 檔案"""
    csv_path = tmp_path / "wrong_types.csv"
    df = pd.DataFrame({
        'stock_id': ['2330', '2317'],
        'name': ['台積電', '鴻海'],
        'market': ['上市', '上市'],
        'industry': ['半導體', '電子'],
        'enabled': ['abc', 1]  # 第一筆 enabled 是字串
    })
    df.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def invalid_csv_duplicates(tmp_path):
    """重複資料的 CSV 檔案"""
    csv_path = tmp_path / "duplicates.csv"
    df = pd.DataFrame({
        'stock_id': ['2330', '2330'],  # 重複的 stock_id
        'name': ['台積電', '台積電'],
        'market': ['上市', '上市'],
        'industry': ['半導體', '半導體'],
        'enabled': [1, 1]
    })
    df.to_csv(csv_path, index=False)
    return csv_path


def test_csv_validator_valid_stocks(valid_stocks_csv):
    """測試有效的股票 CSV"""
    from modules.csv_validator import CSVValidator
    
    result = CSVValidator.validate_csv(valid_stocks_csv, 'stocks')
    
    assert result.is_valid is True
    assert result.errors == []
    assert result.row_count == 2
    assert result.valid_rows == 2


def test_csv_validator_valid_prices(valid_prices_csv):
    """測試有效的價格 CSV"""
    from modules.csv_validator import CSVValidator
    
    result = CSVValidator.validate_csv(valid_prices_csv, 'prices')
    
    assert result.is_valid is True
    assert result.errors == []
    assert result.row_count == 2
    assert result.valid_rows == 2


def test_csv_validator_missing_columns(invalid_csv_missing_columns):
    """測試缺少欄位的 CSV"""
    from modules.csv_validator import CSVValidator
    
    result = CSVValidator.validate_csv(invalid_csv_missing_columns, 'stocks')
    
    assert result.is_valid is False
    assert len(result.errors) > 0
    assert '缺少必要欄位' in result.errors[0]


def test_csv_validator_empty_values(invalid_csv_empty_values):
    """測試包含空值的 CSV"""
    from modules.csv_validator import CSVValidator
    
    result = CSVValidator.validate_csv(invalid_csv_empty_values, 'stocks')
    
    assert result.is_valid is False
    assert len(result.errors) > 0
    assert any('為空值' in error for error in result.errors)


def test_csv_validator_wrong_types(invalid_csv_wrong_types):
    """測試類型錯誤的 CSV"""
    from modules.csv_validator import CSVValidator
    
    result = CSVValidator.validate_csv(invalid_csv_wrong_types, 'stocks')
    
    assert result.is_valid is False
    assert len(result.errors) > 0
    assert any('類型錯誤' in error for error in result.errors)


def test_csv_validator_duplicates(invalid_csv_duplicates):
    """測試重複資料的 CSV"""
    from modules.csv_validator import CSVValidator
    
    result = CSVValidator.validate_csv(invalid_csv_duplicates, 'stocks')
    
    # 重複資料是警告，不是錯誤
    assert len(result.warnings) > 0
    assert any('重複' in warning for warning in result.warnings)


def test_csv_validator_nonexistent_file():
    """測試不存在的檔案"""
    from modules.csv_validator import CSVValidator
    
    result = CSVValidator.validate_csv(Path("nonexistent.csv"), 'stocks')
    
    assert result.is_valid is False
    assert len(result.errors) > 0
    assert '檔案不存在' in result.errors[0]


def test_csv_validator_unsupported_type():
    """測試不支援的類型"""
    from modules.csv_validator import CSVValidator
    
    # 建立一個臨時檔案
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("test\n")
        tmp_path = Path(f.name)
    
    try:
        result = CSVValidator.validate_csv(tmp_path, 'unsupported')
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert '不支援的 CSV 類型' in result.errors[0]
    finally:
        tmp_path.unlink()


def test_csv_validator_invalid_date():
    """測試無效日期格式"""
    from modules.csv_validator import CSVValidator
    
    # 建立包含無效日期的 CSV
    import tempfile
    csv_path = Path(tempfile.mktemp(suffix='.csv'))
    
    df = pd.DataFrame({
        'stock_id': ['2330'],
        'date': ['invalid-date'],
        'open': [600.0],
        'high': [620.0],
        'low': [590.0],
        'close': [615.0],
        'volume': [1000000]
    })
    df.to_csv(csv_path, index=False)
    
    try:
        result = CSVValidator.validate_csv(csv_path, 'prices')
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any('日期格式錯誤' in error for error in result.errors)
    finally:
        csv_path.unlink()


def test_csv_validator_negative_prices():
    """測試負數價格"""
    from modules.csv_validator import CSVValidator
    
    # 建立包含負數價格的 CSV
    import tempfile
    csv_path = Path(tempfile.mktemp(suffix='.csv'))
    
    df = pd.DataFrame({
        'stock_id': ['2330'],
        'date': ['2024-01-01'],
        'open': [-600.0],  # 負數價格
        'high': [620.0],
        'low': [590.0],
        'close': [615.0],
        'volume': [1000000]
    })
    df.to_csv(csv_path, index=False)
    
    try:
        result = CSVValidator.validate_csv(csv_path, 'prices')
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any('價格不能為負數或零' in error for error in result.errors)
    finally:
        csv_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])