import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from datetime import datetime
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.analysis import QuantAnalyzer


@pytest.fixture
def analyzer():
    """Create a QuantAnalyzer instance"""
    return QuantAnalyzer()


def create_bloomberg_csv(dates, open_prices, high_prices, low_prices, close_prices, pct_changes):
    """Helper function to create Bloomberg-style CSV with given data"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
    
    # Write Bloomberg header rows (6 rows)
    temp_file.write('Security,SPX Index,,,,,,,,,,,\n')
    temp_file.write('Start Date,01/01/24 0:00,,,,,,,,,,,\n')
    temp_file.write('End Date,12/31/24 0:00,,,,,,,,,,,\n')
    temp_file.write('Period,D,,,,,,,,,,,\n')
    temp_file.write('Currency,USD,,,,,,,,,,,\n')
    temp_file.write(',,,,,,,,,,,,\n')
    
    # Write column header (row 6)
    temp_file.write('Date,PX_LAST,Change,% Change,PX_OPEN,Change,% Change,PX_HIGH,Change,% Change,PX_LOW,Change,% Change\n')
    
    # Write data rows
    for i in range(len(dates)):
        date_str = dates[i].strftime('%m/%d/%y') if isinstance(dates[i], pd.Timestamp) else dates[i]
        temp_file.write(f'{date_str},{close_prices[i]},0,{pct_changes[i]},{open_prices[i]},0,0,{high_prices[i]},0,0,{low_prices[i]},0,0\n')
    
    temp_file.close()
    return temp_file.name


@pytest.fixture
def bloomberg_csv_file():
    """Create a temporary Bloomberg-style CSV file with test data"""
    dates = pd.date_range(start='2024-01-01', periods=10, freq='B')
    open_prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109]
    high_prices = [101, 103, 102, 104, 106, 105, 107, 109, 108, 110]
    low_prices = [99, 101, 100, 102, 104, 103, 105, 107, 106, 108]
    close_prices = [100.5, 102.5, 101.5, 103.5, 105.5, 104.5, 106.5, 108.5, 107.5, 109.5]
    pct_changes = [0.5, 1.99, -0.98, 1.97, 1.93, -0.95, 1.91, 1.88, -0.92, 1.86]
    
    filepath = create_bloomberg_csv(dates, open_prices, high_prices, low_prices, close_prices, pct_changes)
    
    yield filepath
    
    # Cleanup
    if os.path.exists(filepath):
        os.unlink(filepath)


def test_init(analyzer):
    """Test QuantAnalyzer initialization"""
    assert analyzer.df is None
    assert analyzer.data_loaded is False


def test_load_data_success(analyzer, bloomberg_csv_file):
    """Test successful data loading from Bloomberg CSV"""
    result = analyzer.load_data(bloomberg_csv_file)
    
    assert result is True
    assert analyzer.data_loaded is True
    assert analyzer.df is not None
    assert len(analyzer.df) == 10
    assert 'Date' in analyzer.df.columns
    assert 'Open' in analyzer.df.columns
    assert 'High' in analyzer.df.columns
    assert 'Low' in analyzer.df.columns
    assert 'Close' in analyzer.df.columns
    assert 'Close_Pct_Change' in analyzer.df.columns
    assert 'Open_Pct_Change' in analyzer.df.columns
    assert 'High_Pct_Change' in analyzer.df.columns
    assert 'Low_Pct_Change' in analyzer.df.columns
    assert 'Close_Change' in analyzer.df.columns
    assert 'Open_Change' in analyzer.df.columns
    assert 'High_Change' in analyzer.df.columns
    assert 'Low_Change' in analyzer.df.columns
    assert 'DayOfWeek' in analyzer.df.columns

    assert True == False


def test_load_data_with_percent_change(analyzer, bloomberg_csv_file):
    """Test that existing % Change columns from Bloomberg are used"""
    analyzer.load_data(bloomberg_csv_file)
    
    # Check that all Pct_Change columns exist and have values
    for price_type in ['Close', 'Open', 'High', 'Low']:
        col = f'{price_type}_Pct_Change'
        assert col in analyzer.df.columns
        # First row will be NaN since no previous close, rest should have values
        assert not analyzer.df[col].iloc[1:].isna().all()
    
    # Check that we have the expected number of rows
    assert len(analyzer.df) == 10


def test_load_bloomberg_column_mapping(analyzer, bloomberg_csv_file):
    """Test that Bloomberg columns are properly mapped to OHLC"""
    analyzer.load_data(bloomberg_csv_file)
    
    # Verify all OHLC columns exist
    assert 'Open' in analyzer.df.columns
    assert 'High' in analyzer.df.columns
    assert 'Low' in analyzer.df.columns
    assert 'Close' in analyzer.df.columns
    
    # Verify Bloomberg columns are renamed
    assert 'PX_OPEN' not in analyzer.df.columns
    assert 'PX_HIGH' not in analyzer.df.columns
    assert 'PX_LOW' not in analyzer.df.columns
    assert 'PX_LAST' not in analyzer.df.columns


def test_load_data_without_percent_change(analyzer):
    """Test data loading when Change/% Change columns are missing raises error"""
    # Create Bloomberg CSV without Change and % Change columns
    dates = pd.date_range(start='2024-01-01', periods=5, freq='B')
    
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
    temp_file.write('Security,SPX Index,,,,,,,,,,,\n')
    temp_file.write('Start Date,01/01/24 0:00,,,,,,,,,,,\n')
    temp_file.write('End Date,01/05/24 0:00,,,,,,,,,,,\n')
    temp_file.write('Period,D,,,,,,,,,,,\n')
    temp_file.write('Currency,USD,,,,,,,,,,,\n')
    temp_file.write(',,,,,,,,,,,,\n')
    temp_file.write('Date,PX_LAST,PX_OPEN,PX_HIGH,PX_LOW\n')
    for i, date in enumerate(dates):
        temp_file.write(f'{date.strftime("%m/%d/%y")},{100+i},{100+i},{101+i},{99+i}\n')
    temp_file.close()
    
    try:
        with pytest.raises(Exception) as exc_info:
            analyzer.load_data(temp_file.name)
        
        # Should fail because Change and Pct_Change columns are required
        assert 'Missing required columns' in str(exc_info.value)
    finally:
        os.unlink(temp_file.name)


def test_load_data_missing_columns(analyzer):
    """Test loading Bloomberg CSV with missing required columns"""
    # Create Bloomberg CSV with missing columns
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
    temp_file.write('Security,SPX Index,,,,,,,,,,,\n')
    temp_file.write('Start Date,01/01/24 0:00,,,,,,,,,,,\n')
    temp_file.write('End Date,01/10/24 0:00,,,,,,,,,,,\n')
    temp_file.write('Period,D,,,,,,,,,,,\n')
    temp_file.write('Currency,USD,,,,,,,,,,,\n')
    temp_file.write(',,,,,,,,,,,,\n')
    # Missing PX_HIGH, PX_LOW columns
    temp_file.write('Date,PX_LAST,Change,% Change,PX_OPEN,Change,% Change\n')
    temp_file.write('01/10/24,109.5,0,0.5,109,0,0\n')
    temp_file.close()
    
    try:
        with pytest.raises(Exception) as exc_info:
            analyzer.load_data(temp_file.name)
        
        assert 'Missing required columns' in str(exc_info.value)
    finally:
        os.unlink(temp_file.name)


def test_load_data_invalid_file(analyzer):
    """Test loading invalid file"""
    with pytest.raises(Exception) as exc_info:
        analyzer.load_data('nonexistent_file.csv')
    
    assert 'Error loading data' in str(exc_info.value)


def test_best_day_of_week_no_data(analyzer):
    """Test best_day_of_week without loading data first"""
    with pytest.raises(Exception) as exc_info:
        analyzer.best_day_of_week()
    
    assert 'No data loaded' in str(exc_info.value)


def test_best_day_of_week_full_range(analyzer, bloomberg_csv_file):
    """Test best_day_of_week analysis on full data range"""
    analyzer.load_data(bloomberg_csv_file)
    result = analyzer.best_day_of_week()
    
    # Check result structure
    assert 'best_day' in result
    assert 'period' in result
    assert 'statistics' in result
    
    # Check period info
    assert 'start' in result['period']
    assert 'end' in result['period']
    assert 'total_days' in result['period']
    assert result['period']['total_days'] == 10
    
    # Check statistics
    assert isinstance(result['statistics'], dict)
    
    # Check that best_day is one of the weekdays
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    assert result['best_day'] in weekdays
    
    # Check that each day has proper statistics
    for day, stats in result['statistics'].items():
        assert 'avg_return' in stats
        assert 'median_return' in stats
        assert 'std_return' in stats
        assert 'positive_days' in stats
        assert 'negative_days' in stats
        assert 'total_days' in stats
        assert 'win_rate' in stats


def test_best_day_of_week_with_date_range(analyzer, bloomberg_csv_file):
    """Test best_day_of_week analysis with date filtering"""
    analyzer.load_data(bloomberg_csv_file)
    
    start_date = '2024-01-03'
    end_date = '2024-01-08'
    
    result = analyzer.best_day_of_week(start_date=start_date, end_date=end_date)
    
    # Check that the period is filtered
    result_start = pd.to_datetime(result['period']['start'])
    result_end = pd.to_datetime(result['period']['end'])
    
    assert result_start >= pd.to_datetime(start_date)
    assert result_end <= pd.to_datetime(end_date)
    assert result['period']['total_days'] < 10


def test_best_day_of_week_invalid_date_range(analyzer, bloomberg_csv_file):
    """Test best_day_of_week with date range that has no data"""
    analyzer.load_data(bloomberg_csv_file)
    
    with pytest.raises(Exception) as exc_info:
        analyzer.best_day_of_week(start_date='2025-01-01', end_date='2025-01-31')
    
    assert 'No data available' in str(exc_info.value)


def test_day_of_week_calculation(analyzer, bloomberg_csv_file):
    """Test that day of week is correctly calculated"""
    analyzer.load_data(bloomberg_csv_file)
    
    # Check that DayOfWeek column exists and has valid values
    assert 'DayOfWeek' in analyzer.df.columns
    
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    for day in analyzer.df['DayOfWeek']:
        assert day in weekdays


def test_data_sorting(analyzer, bloomberg_csv_file):
    """Test that data is sorted by date"""
    analyzer.load_data(bloomberg_csv_file)
    
    dates = analyzer.df['Date'].values
    # Check if dates are sorted
    assert all(dates[i] <= dates[i+1] for i in range(len(dates)-1))


def test_numeric_conversion(analyzer, bloomberg_csv_file):
    """Test that OHLC columns are converted to numeric"""
    analyzer.load_data(bloomberg_csv_file)
    
    for col in ['Open', 'High', 'Low', 'Close']:
        assert pd.api.types.is_numeric_dtype(analyzer.df[col])


def test_bloomberg_date_parsing(analyzer, bloomberg_csv_file):
    """Test that Bloomberg dates are correctly parsed"""
    analyzer.load_data(bloomberg_csv_file)
    
    # Check that Date column is datetime type
    assert pd.api.types.is_datetime64_any_dtype(analyzer.df['Date'])
    
    # Check that dates are in expected range
    assert analyzer.df['Date'].min() >= pd.Timestamp('2024-01-01')
    assert analyzer.df['Date'].max() <= pd.Timestamp('2024-12-31')


def test_low_volatility_streaks_basic(analyzer, bloomberg_csv_file):
    """Test basic low volatility windows functionality"""
    analyzer.load_data(bloomberg_csv_file)
    
    result = analyzer.low_volatility_streaks(consecutive_days=3, volatility_threshold=2.0)
    
    # Check result structure
    assert 'parameters' in result
    assert 'period' in result
    assert 'summary' in result
    assert 'windows' in result
    
    # Check parameters
    assert result['parameters']['window_size'] == 3
    assert result['parameters']['volatility_threshold'] == 2.0
    
    # Check summary
    assert 'matching_windows' in result['summary']
    assert 'total_possible_windows' in result['summary']
    assert 'match_percentage' in result['summary']


def test_low_volatility_streaks_with_date_range(analyzer, bloomberg_csv_file):
    """Test low volatility windows with date filtering"""
    analyzer.load_data(bloomberg_csv_file)
    
    start_date = '2024-01-03'
    end_date = '2024-01-08'
    
    result = analyzer.low_volatility_streaks(
        consecutive_days=2,
        volatility_threshold=1.5,
        start_date=start_date,
        end_date=end_date
    )
    
    # Check that period is filtered
    result_start = pd.to_datetime(result['period']['start'])
    result_end = pd.to_datetime(result['period']['end'])
    
    assert result_start >= pd.to_datetime(start_date)
    assert result_end <= pd.to_datetime(end_date)


def test_low_volatility_streaks_window_open_mode(analyzer, bloomberg_csv_file):
    """Test low volatility windows with window_open reference price"""
    analyzer.load_data(bloomberg_csv_file)
    
    result = analyzer.low_volatility_streaks(
        consecutive_days=2,
        volatility_threshold=2.0,
        reference_price='window_open'
    )
    
    # Check parameters
    assert result['parameters']['reference_price'] == 'window_open'
    
    # Check that windows use correct reference
    if result['summary']['matching_windows'] > 0:
        window = result['windows'][0]
        assert window['reference_type'] == 'Window Open'
        # Reference date should be same as window start for window_open mode
        assert window['reference_date'] == window['window_start']


def test_low_volatility_streaks_no_data(analyzer):
    """Test low volatility windows without loading data first"""
    with pytest.raises(Exception) as exc_info:
        analyzer.low_volatility_streaks()
    
    assert 'No data loaded' in str(exc_info.value)


def test_low_volatility_streaks_insufficient_data(analyzer):
    """Test low volatility windows with insufficient data"""
    # Create CSV with only 2 days of data
    dates = pd.date_range(start='2024-01-01', periods=2, freq='B')
    open_prices = [100, 102]
    high_prices = [101, 103]
    low_prices = [99, 101]
    close_prices = [100.5, 102.5]
    pct_changes = [0.5, 1.99]
    
    filepath = create_bloomberg_csv(dates, open_prices, high_prices, low_prices, close_prices, pct_changes)
    
    try:
        analyzer.load_data(filepath)
        
        with pytest.raises(Exception) as exc_info:
            analyzer.low_volatility_streaks(consecutive_days=5)
        
        assert 'Not enough data' in str(exc_info.value)
    finally:
        os.unlink(filepath)


def test_low_volatility_streaks_details(analyzer, bloomberg_csv_file):
    """Test that window details are correctly calculated"""
    analyzer.load_data(bloomberg_csv_file)
    
    result = analyzer.low_volatility_streaks(consecutive_days=2, volatility_threshold=3.0)
    
    # Check window structure if any windows found
    if result['summary']['matching_windows'] > 0:
        window = result['windows'][0]
        assert 'reference_date' in window
        assert 'reference_price' in window
        assert 'reference_type' in window
        assert 'window_start' in window
        assert 'window_end' in window
        assert 'window_end_close' in window
        assert 'price_change_pct' in window
        assert 'window_high' in window
        assert 'window_low' in window
        assert 'window_volatility_pct' in window
        
        # Verify price change is within threshold
        assert window['price_change_pct'] <= 3.0
        
        # Verify volatility is calculated correctly
        assert window['window_volatility_pct'] >= 0
        
        # Verify reference type for default mode
        assert window['reference_type'] == 'Previous Close'


def test_low_volatility_streaks_invalid_reference(analyzer, bloomberg_csv_file):
    """Test low volatility windows with invalid reference_price"""
    analyzer.load_data(bloomberg_csv_file)
    
    with pytest.raises(Exception) as exc_info:
        analyzer.low_volatility_streaks(
            consecutive_days=2,
            volatility_threshold=1.0,
            reference_price='invalid_option'
        )
    
    assert 'Invalid reference_price' in str(exc_info.value)
