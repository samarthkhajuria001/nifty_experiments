import pandas as pd
import numpy as np
import os

# Configuration
DATA_PATH_5MIN = "../../data/nifty50_minute_complete-5min.csv"
DATA_PATH_120MIN = "../../data/nifty50_minute_complete-120min.csv"

def get_trend_map():
    print("Calculating Trends from 120min data...")
    try:
        df_trend = pd.read_csv(DATA_PATH_120MIN)
        if 'datetime' not in df_trend.columns and 'date' in df_trend.columns:
            df_trend.rename(columns={'date': 'datetime'}, inplace=True)
        df_trend['datetime'] = pd.to_datetime(df_trend['datetime'])
        df_trend['date_only'] = df_trend['datetime'].dt.date
        df_trend = df_trend.sort_values('datetime')
    except Exception as e:
        print(f"Error loading 120min data: {e}")
        return {}

    df_trend['ema_11'] = df_trend['close'].ewm(span=11, adjust=False).mean()
    df_trend['ema_21'] = df_trend['close'].ewm(span=21, adjust=False).mean()

    # Get Last Row of each day
    daily_status = df_trend.groupby('date_only').last().reset_index()
    
    # Define Trend
    daily_status['trend_status'] = np.where(daily_status['ema_11'] > daily_status['ema_21'], 'UP', 'DOWN')
    
    # Shift to apply to NEXT day
    daily_status['trading_trend'] = daily_status['trend_status'].shift(1)
    daily_status = daily_status.dropna(subset=['trading_trend'])
    
    return dict(zip(daily_status['date_only'], daily_status['trading_trend']))

def main():
    # 1. Load Trend
    trend_map = get_trend_map()
    if not trend_map: return

    # 2. Load 5-min Data
    print("Loading 5-min data...")
    try:
        df = pd.read_csv(DATA_PATH_5MIN)
    except Exception as e:
        print(f"Error reading 5min CSV: {e}")
        return

    if 'date' in df.columns: df.rename(columns={'date': 'datetime'}, inplace=True)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['date_only'] = df['datetime'].dt.date
    df = df.sort_values('datetime').reset_index(drop=True)

    # 3. Apply Trend
    df['market_trend'] = df['date_only'].map(trend_map)
    # Important: Drop days where we don't have trend info (e.g. Day 1)
    df = df.dropna(subset=['market_trend'])

    # 4. Filter for First Bar of Every Day
    df['bar_index'] = df.groupby('date_only').cumcount() + 1
    df['prev_close'] = df['close'].shift(1)
    
    first_bars = df[df['bar_index'] == 1].copy()
    
    # Filter out the very first row of dataset (NaN prev_close)
    first_bars = first_bars.dropna(subset=['prev_close'])

    # 5. Metrics Calculation
    first_bars['gap'] = first_bars['open'] - first_bars['prev_close']
    first_bars['candle_len'] = first_bars['high'] - first_bars['low']
    first_bars['upper_wick'] = first_bars['high'] - first_bars['close']
    first_bars['lower_wick'] = first_bars['close'] - first_bars['low']
    first_bars['is_bull'] = first_bars['close'] > first_bars['open']
    first_bars['is_bear'] = first_bars['close'] < first_bars['open']
    
    # Strong Condition (Wick <= 10% of Length)
    # Avoid division by zero
    first_bars['is_strong_bull'] = (
        first_bars['is_bull'] & 
        (first_bars['candle_len'] > 0) & 
        (first_bars['upper_wick'] <= 0.10 * first_bars['candle_len'])
    )
    
    first_bars['is_strong_bear'] = (
        first_bars['is_bear'] & 
        (first_bars['candle_len'] > 0) & 
        (first_bars['lower_wick'] <= 0.10 * first_bars['candle_len'])
    )

    # 6. Tree Construction
    total_days = len(first_bars)
    
    # Trend Split
    days_up = first_bars[first_bars['market_trend'] == 'UP']
    days_down = first_bars[first_bars['market_trend'] == 'DOWN']
    
    # Helper to print stats
    def print_node(label, df_subset, parent_count, indent_level=0):
        count = len(df_subset)
        pct = (count / parent_count * 100) if parent_count > 0 else 0
        indent = "    " * indent_level
        print(f"{indent}|-- {label}: {count} ({pct:.1f}%)")
        return count

    print(f"\n=== DATA TREE SUMMARY (Total Days Analyzed: {total_days}) ===")
    
    for trend_label, df_trend in [("UP TREND", days_up), ("DOWN TREND", days_down)]:
        c_trend = print_node(trend_label, df_trend, total_days, 0)
        if c_trend == 0: continue

        # Gap Categories
        # 1. Large Gap Up (> 50)
        gap_up_50 = df_trend[df_trend['gap'] >= 50]
        # 2. Small Gap Up (0 < Gap < 50)
        gap_up_small = df_trend[(df_trend['gap'] > 0) & (df_trend['gap'] < 50)]
        # 3. Small Gap Down (-50 < Gap <= 0)
        gap_down_small = df_trend[(df_trend['gap'] <= 0) & (df_trend['gap'] > -50)]
        # 4. Large Gap Down (Gap <= -50)
        gap_down_50 = df_trend[df_trend['gap'] <= -50]

        categories = [
            ("Gap Up >= 50", gap_up_50),
            ("Gap Up (0 to 50)", gap_up_small),
            ("Gap Down (0 to -50)", gap_down_small),
            ("Gap Down <= -50", gap_down_50)
        ]

        for gap_label, df_gap in categories:
            c_gap = print_node(gap_label, df_gap, c_trend, 1)
            if c_gap == 0: continue

            # Bar Types
            strong_bull = df_gap[df_gap['is_strong_bull']]
            bull = df_gap[df_gap['is_bull']]
            strong_bear = df_gap[df_gap['is_strong_bear']]
            bear = df_gap[df_gap['is_bear']]
            
            # Note: "Any" is just c_gap, so we list subtypes
            print_node("Strong Bull", strong_bull, c_gap, 2)
            print_node("Bull (Any)", bull, c_gap, 2)
            print_node("Strong Bear", strong_bear, c_gap, 2)
            print_node("Bear (Any)", bear, c_gap, 2)

if __name__ == "__main__":
    main()
