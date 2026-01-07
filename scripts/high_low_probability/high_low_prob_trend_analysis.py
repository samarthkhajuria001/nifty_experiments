import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Configuration
DATA_PATH_5MIN = "../../data/nifty50_minute_complete-5min.csv"
DATA_PATH_120MIN = "../../data/nifty50_minute_complete-120min.csv"

DIR_BULL_TREND = "../../output/trend_patterns/bull"
DIR_BEAR_TREND = "../../output/trend_patterns/bear"

def calculate_probabilities(df, offset=0):
    """
    Calculates the probability of having seen the day's high or low 
    by a specific bar, given a noise offset.
    """
    calc_df = df.copy()

    # Determine if the High/Low has been established (with offset)
    calc_df['is_day_high_set'] = (calc_df['high_so_far'] + offset >= calc_df['day_high'])
    calc_df['is_day_low_set'] = (calc_df['low_so_far'] - offset <= calc_df['day_low'])
    calc_df['is_either_set'] = calc_df['is_day_high_set'] | calc_df['is_day_low_set']

    # Aggregation
    stats = calc_df.groupby('bar_index').agg(
        high_set_count=('is_day_high_set', 'sum'),
        low_set_count=('is_day_low_set', 'sum'),
        either_set_count=('is_either_set', 'sum'),
        total_days=('date_only', 'nunique')
    ).reset_index()

    # Calculate Probabilities
    stats['prob_high_set'] = stats['high_set_count'] / stats['total_days']
    stats['prob_low_set'] = stats['low_set_count'] / stats['total_days']
    stats['prob_either_set'] = stats['either_set_count'] / stats['total_days']
    
    return stats

def run_analysis_and_save(df, scenario_name, valid_dates, trend_type, output_dir):
    """
    Runs the probability analysis for a specific list of dates and saves to the specified folder.
    """
    if len(valid_dates) == 0:
        print(f"  [Skipping] No days found for {scenario_name} in {trend_type} trend.")
        return

    print(f"  Processing {scenario_name} ({trend_type} Trend) - Days: {len(valid_dates)}")
    
    df_filtered = df[df['date_only'].isin(valid_dates)].copy()

    # Calculate with Offset 0 (Exact)
    stats_exact = calculate_probabilities(df_filtered, offset=0)
    
    # Calculate with Offset 10 (Near Match)
    OFFSET_VAL = 10
    stats_offset = calculate_probabilities(df_filtered, offset=OFFSET_VAL)

    # Merge
    combined_stats = pd.merge(
        stats_exact[['bar_index', 'prob_high_set', 'prob_low_set', 'prob_either_set']],
        stats_offset[['bar_index', 'prob_high_set', 'prob_low_set', 'prob_either_set']],
        on='bar_index',
        suffixes=('_exact', f'_offset_{OFFSET_VAL}')
    )

    # Save CSV
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    csv_filename = f"{scenario_name}.csv"
    csv_path = os.path.join(output_dir, csv_filename)
    
    combined_stats = combined_stats.round(2)
    
    # Create CSV version with count row
    csv_df = combined_stats.copy()
    count_row = pd.DataFrame([['total_days', len(valid_dates)] + [None]*(len(combined_stats.columns)-2)], columns=combined_stats.columns)
    csv_df = pd.concat([csv_df, count_row], ignore_index=True)
    
    csv_df.to_csv(csv_path, index=False)
    
    # Plot (use original numeric combined_stats)
    plot_filename = f"{scenario_name}.png"
    plot_path = os.path.join(output_dir, plot_filename)
    
    plt.figure(figsize=(14, 8))
    plot_data = combined_stats[combined_stats['bar_index'] <= 75]

    plt.plot(plot_data['bar_index'], plot_data['prob_high_set_exact'], label='High Set (Exact)', color='green', linewidth=2, linestyle='-', alpha=0.7)
    plt.plot(plot_data['bar_index'], plot_data['prob_low_set_exact'], label='Low Set (Exact)', color='red', linewidth=2, linestyle='-', alpha=0.7)
    plt.plot(plot_data['bar_index'], plot_data[f'prob_high_set_offset_{OFFSET_VAL}'], label=f'High Set (+/- {OFFSET_VAL})', color='green', linewidth=2, linestyle='--', alpha=0.7)
    plt.plot(plot_data['bar_index'], plot_data[f'prob_low_set_offset_{OFFSET_VAL}'], label=f'Low Set (+/- {OFFSET_VAL})', color='red', linewidth=2, linestyle='--', alpha=0.7)

    plt.title(f'{scenario_name} ({trend_type} Trend) N={len(valid_dates)}', fontsize=16)
    plt.xlabel('Bar Index (5-min intervals)', fontsize=12)
    plt.ylabel('Probability', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xlim(1, 75)
    plt.ylim(0, 1.05)
    
    plt.savefig(plot_path)
    plt.close()

def get_trend_map():
    """
    Generates a dictionary {date: 'UP'/'DOWN'} based on 120min EMA 11/21 crossover.
    Uses PREVIOUS DAY's close to determine TODAY's trend.
    """
    print("Calculating Trends from 120min data...")
    try:
        df_trend = pd.read_csv(DATA_PATH_120MIN)
        # Handle different column name possibilities if needed, but assuming standard format
        if 'datetime' not in df_trend.columns and 'date' in df_trend.columns:
            df_trend.rename(columns={'date': 'datetime'}, inplace=True)
            
        df_trend['datetime'] = pd.to_datetime(df_trend['datetime'])
        df_trend['date_only'] = df_trend['datetime'].dt.date
        df_trend = df_trend.sort_values('datetime')
    except Exception as e:
        print(f"Error loading 120min data: {e}")
        return {}

    # Calculate EMAs
    df_trend['ema_11'] = df_trend['close'].ewm(span=11, adjust=False).mean()
    df_trend['ema_21'] = df_trend['close'].ewm(span=21, adjust=False).mean()

    # Get the LAST row for each date to define "End of Day Status"
    daily_status = df_trend.groupby('date_only').last().reset_index()
    
    # Define Trend Status for that day
    # Simple Logic: 11 > 21 = UP, else DOWN
    daily_status['trend_status'] = np.where(daily_status['ema_11'] > daily_status['ema_21'], 'UP', 'DOWN')
    
    # SHIFT: The trend status at close of Day T applies to Day T+1
    daily_status['trading_trend'] = daily_status['trend_status'].shift(1)
    
    # Drop NaN (first day)
    daily_status = daily_status.dropna(subset=['trading_trend'])
    
    # Create Dictionary
    trend_map = dict(zip(daily_status['date_only'], daily_status['trading_trend']))
    return trend_map

def main():
    # 1. Get Trend Map
    trend_map = get_trend_map()
    if not trend_map:
        print("Failed to generate trend map. Exiting.")
        return

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

    # 3. Apply Trend to Data
    print("Applying trend map to data...")
    df['market_trend'] = df['date_only'].map(trend_map)
    # Filter out days where we don't have trend info (e.g., first day of dataset)
    df = df.dropna(subset=['market_trend'])

    # 4. Pre-calculate Metrics
    print("Pre-calculating metrics...")
    df['day_high'] = df.groupby('date_only')['high'].transform('max')
    df['day_low'] = df.groupby('date_only')['low'].transform('min')
    df['high_so_far'] = df.groupby('date_only')['high'].cummax()
    df['low_so_far'] = df.groupby('date_only')['low'].cummin()
    df['bar_index'] = df.groupby('date_only').cumcount() + 1
    
    # 5. Define Scenarios (Gap Logic)
    df['prev_close'] = df['close'].shift(1)
    first_bars = df[df['bar_index'] == 1].copy()
    
    first_bars['gap'] = first_bars['open'] - first_bars['prev_close']
    first_bars['candle_len'] = first_bars['high'] - first_bars['low']
    first_bars['upper_wick'] = first_bars['high'] - first_bars['close']
    first_bars['lower_wick'] = first_bars['close'] - first_bars['low']
    first_bars['is_bull'] = first_bars['close'] > first_bars['open']
    first_bars['is_bear'] = first_bars['close'] < first_bars['open']

    # --- SCENARIO DEFINITIONS ---
    GAP_THRESHOLD = 50
    
    # Gap Up Scenarios
    gu_bull = (first_bars['gap'] >= GAP_THRESHOLD) & first_bars['is_bull'] & (first_bars['upper_wick'] <= 0.10 * first_bars['candle_len'])
    gu_bear = (first_bars['gap'] >= GAP_THRESHOLD) & first_bars['is_bear'] & (first_bars['lower_wick'] <= 0.10 * first_bars['candle_len'])
    gu_any = (first_bars['gap'] >= GAP_THRESHOLD)
    
    # New Scenarios (Simple Bull/Bear - No Wick Restriction)
    gu_bull_simple = (first_bars['gap'] >= GAP_THRESHOLD) & first_bars['is_bull']
    gu_bear_simple = (first_bars['gap'] >= GAP_THRESHOLD) & first_bars['is_bear']
    
    # Gap Down Scenarios
    gd_bull = (first_bars['gap'] <= -GAP_THRESHOLD) & first_bars['is_bull'] & (first_bars['upper_wick'] <= 0.10 * first_bars['candle_len'])
    gd_bear = (first_bars['gap'] <= -GAP_THRESHOLD) & first_bars['is_bear'] & (first_bars['lower_wick'] <= 0.10 * first_bars['candle_len'])
    gd_any = (first_bars['gap'] <= -GAP_THRESHOLD)

    scenarios = [
        ("50-gapup-bull", gu_bull),
        ("50-gapup-bear", gu_bear),
        ("50-gapup-bull-simple", gu_bull_simple),
        ("50-gapup-bear-simple", gu_bear_simple),
        ("50-gapup-any", gu_any),
        ("50-gapdown-bull", gd_bull),
        ("50-gapdown-bear", gd_bear),
        ("50-gapdown-any", gd_any)
    ]

    # 6. Execute Split Analysis
    print("\n--- Starting Analysis ---")
    
    for name, condition in scenarios:
        # Get dates for this scenario
        matching_rows = first_bars[condition]
        
        # Split by Trend
        dates_uptrend = matching_rows[matching_rows['market_trend'] == 'UP']['date_only'].unique()
        dates_downtrend = matching_rows[matching_rows['market_trend'] == 'DOWN']['date_only'].unique()
        
        # Run and Save for Uptrend Folder
        run_analysis_and_save(df, name, dates_uptrend, "UP", DIR_BULL_TREND)
        
        # Run and Save for Downtrend Folder
        run_analysis_and_save(df, name, dates_downtrend, "DOWN", DIR_BEAR_TREND)

    print("\nDone. Files saved in:")
    print(f" - {DIR_BULL_TREND}")
    print(f" - {DIR_BEAR_TREND}")

if __name__ == "__main__":
    main()
