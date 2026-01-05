import pandas as pd

class QuantAnalyzer:
    """Quantitative analysis engine for OHLC data"""
    
    def __init__(self):
        self.df = None
        self.data_loaded = False
    
    def load_data(self, filepath):
        """Load OHLC data from Bloomberg CSV file
        
        Bloomberg CSV format has 6 header rows before the data:
        Row 0: Security information
        Row 1: Start Date
        Row 2: End Date
        Row 3: Period
        Row 4: Currency
        Row 5: Empty row
        Row 6: Column headers (Date,PX_LAST,Change,% Change,PX_OPEN,Change,% Change,PX_HIGH,Change,% Change,PX_LOW,Change,% Change)
        Row 7+: Data rows
        
        Each OHLC price has:
        - Price value (PX_LAST, PX_OPEN, PX_HIGH, PX_LOW)
        - Change: absolute price change vs previous close
        - % Change: percentage change vs previous close
        """
        try:
            # Read Bloomberg CSV format - skip first 6 rows, use row 6 as header
            df = pd.read_csv(filepath, skiprows=6, header=0)
            
            # Bloomberg CSV has duplicate column names (Change, % Change appear 4 times)
            # Pandas automatically appends .1, .2, .3 to duplicates
            # We need to rename them based on their position relative to price columns
            
            # Map to new column names
            column_mapping = {
                'Date': 'Date',
                'PX_LAST': 'Close',
                'Change': 'Close_Change',
                '% Change': 'Close_Pct_Change',
                'PX_OPEN': 'Open',
                'Change.1': 'Open_Change',
                '% Change.1': 'Open_Pct_Change',
                'PX_HIGH': 'High',
                'Change.2': 'High_Change',
                '% Change.2': 'High_Pct_Change',
                'PX_LOW': 'Low',
                'Change.3': 'Low_Change',
                '% Change.3': 'Low_Pct_Change'
            }
            
            # Rename columns
            df = df.rename(columns=column_mapping)
            
            # Parse date column (Bloomberg format: MM/DD/YY)
            df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%y')
            
            # Ensure we have all required columns (OHLC + Change + % Change for each)
            required_cols = [
                'Date', 'Open', 'High', 'Low', 'Close',
                'Close_Change', 'Close_Pct_Change',
                'Open_Change', 'Open_Pct_Change',
                'High_Change', 'High_Pct_Change',
                'Low_Change', 'Low_Pct_Change'
            ]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")
            
            # Convert all numeric columns to numeric type
            numeric_cols = ['Open', 'High', 'Low', 'Close', 
                          'Close_Change', 'Close_Pct_Change',
                          'Open_Change', 'Open_Pct_Change',
                          'High_Change', 'High_Pct_Change',
                          'Low_Change', 'Low_Pct_Change']
            
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Check for any missing values in required columns after conversion
            cols_with_missing = []
            for col in required_cols:
                if df[col].isna().any():
                    cols_with_missing.append(col)
            
            if cols_with_missing:
                raise ValueError(f"Found missing values in columns: {', '.join(cols_with_missing)}")
            
            # Sort by date (ascending)
            df = df.sort_values('Date').reset_index(drop=True)
            
            # Add day of week
            df['DayOfWeek'] = df['Date'].dt.day_name()

            print(df)
            
            self.df = df
            self.data_loaded = True
            
            return True
        except Exception as e:
            raise Exception(f"Error loading data: {str(e)}")
    
    def best_day_of_week(self, start_date=None, end_date=None):
        """Calculate the best day of week based on average returns
        
        Uses Close_Pct_Change as the return metric (percentage change from previous close)
        """
        if not self.data_loaded or self.df is None:
            raise Exception("No data loaded")
        
        # Filter by date range
        df = self.df.copy()
        
        if start_date:
            start_date = pd.to_datetime(start_date)
            df = df[df['Date'] >= start_date]
        
        if end_date:
            end_date = pd.to_datetime(end_date)
            df = df[df['Date'] <= end_date]
        
        if len(df) == 0:
            raise Exception("No data available for the specified date range")
        
        # Use Close_Pct_Change as the return metric
        return_col = 'Close_Pct_Change'
        if return_col not in df.columns:
            raise Exception("Close_Pct_Change column not found in data")
        
        # Calculate statistics by day of week
        day_stats = df.groupby('DayOfWeek')[return_col].agg([
            ('avg_return', 'mean'),
            ('median_return', 'median'),
            ('std_return', 'std'),
            ('positive_days', lambda x: (x > 0).sum()),
            ('negative_days', lambda x: (x < 0).sum()),
            ('total_days', 'count')
        ]).round(4)
        
        # Calculate win rate
        day_stats['win_rate'] = (day_stats['positive_days'] / day_stats['total_days'] * 100).round(2)
        
        # Sort days in proper order
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_stats = day_stats.reindex([day for day in day_order if day in day_stats.index])
        
        # Find best day
        best_day = day_stats['avg_return'].idxmax()
        
        # Prepare result
        result = {
            'best_day': best_day,
            'period': {
                'start': df['Date'].min().strftime('%Y-%m-%d'),
                'end': df['Date'].max().strftime('%Y-%m-%d'),
                'total_days': len(df)
            },
            'statistics': day_stats.to_dict('index')
        }
        
        return result
    
    def low_volatility_streaks(self, consecutive_days=5, volatility_threshold=1.0, start_date=None, end_date=None):
        """Find all X-day windows where price change is within Y% threshold
        
        For each X-day window, checks if the closing price at the end of the window
        is within Y% of the closing price on the day BEFORE the window starts.
        
        Example: X=4, Y=1
        Window: 1998-01-06 to 1998-01-09 (4 days)
        Compare: Close on 1998-01-09 vs Close on 1998-01-05
        Match if: abs((Close_1998-01-09 - Close_1998-01-05) / Close_1998-01-05 * 100) <= 1%
        
        Args:
            consecutive_days (int): Window size in days (X)
            volatility_threshold (float): Maximum price change threshold in % (Y)
            start_date (str): Optional start date for filtering
            end_date (str): Optional end date for filtering
        
        Returns:
            dict: Analysis results including all matching windows
        """
        if not self.data_loaded or self.df is None:
            raise Exception("No data loaded")
        
        # Filter by date range
        df = self.df.copy()
        
        if start_date:
            start_date = pd.to_datetime(start_date)
            df = df[df['Date'] >= start_date]
        
        if end_date:
            end_date = pd.to_datetime(end_date)
            df = df[df['Date'] <= end_date]
        
        if len(df) <= consecutive_days:
            raise Exception(f"Not enough data. Need at least {consecutive_days + 1} days, but only have {len(df)} days")
        
        # Find all X-day windows where price change is within Y%
        windows = []
        
        # Iterate through all possible windows
        # Start from index consecutive_days (need previous day for comparison)
        for i in range(consecutive_days, len(df)):
            # Window end date is at index i
            window_end_idx = i
            # Window start date is at index i - consecutive_days + 1
            window_start_idx = i - consecutive_days + 1
            # Reference date (day before window) is at index i - consecutive_days
            reference_idx = i - consecutive_days
            
            # Get closing prices
            reference_close = df.iloc[reference_idx]['Close']
            window_end_close = df.iloc[window_end_idx]['Close']
            
            # Calculate percentage change
            pct_change = abs((window_end_close - reference_close) / reference_close * 100)
            
            # Check if within threshold
            if pct_change <= volatility_threshold:
                window_data = df.iloc[window_start_idx:window_end_idx+1]
                
                window_high = window_data['High'].max()
                window_low = window_data['Low'].min()
                volatility_pct = ((window_high - window_low) / reference_close) * 100
                
                windows.append({
                    'reference_date': df.iloc[reference_idx]['Date'].strftime('%Y-%m-%d'),
                    'reference_close': round(reference_close, 2),
                    'window_start': df.iloc[window_start_idx]['Date'].strftime('%Y-%m-%d'),
                    'window_end': df.iloc[window_end_idx]['Date'].strftime('%Y-%m-%d'),
                    'window_end_close': round(window_end_close, 2),
                    'price_change_pct': round(pct_change, 4),
                    'window_high': round(window_high, 2),
                    'window_low': round(window_low, 2),
                    'window_volatility_pct': round(volatility_pct, 4)
                })
        
        result = {
            'parameters': {
                'window_size': consecutive_days,
                'volatility_threshold': volatility_threshold
            },
            'period': {
                'start': df['Date'].min().strftime('%Y-%m-%d'),
                'end': df['Date'].max().strftime('%Y-%m-%d'),
                'total_days': len(df)
            },
            'summary': {
                'matching_windows': len(windows),
                'total_possible_windows': len(df) - consecutive_days,
                'match_percentage': round((len(windows) / (len(df) - consecutive_days)) * 100, 2) if len(df) > consecutive_days else 0
            },
            'windows': windows
        }
        
        return result
