import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Configuration
DATA_PATH = "../../data/nifty50_minute_complete-5min.csv"
OUTPUT_DIR = "../../output/gap_analysis"

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

def run_scenario(df, scenario_name, filter_indices):
    """
    Runs the probability analysis for a specific subset of dates.
    """
    print(f"\n=== Processing Scenario: {scenario_name} ===")
    
    valid_dates = filter_indices
    print(f"Days matching criteria: {len(valid_dates)}")

    if len(valid_dates) == 0:
        print("No days matched the criteria. Skipping.")
        return

    df_filtered = df[df['date_only'].isin(valid_dates)].copy()

    # --- CALCULATE BOTH SCENARIOS ---
    # 1. Exact Match (Offset 0)
    stats_exact = calculate_probabilities(df_filtered, offset=0)
    
    # 2. Near Match (Offset 10)
    OFFSET_VAL = 10
    stats_offset = calculate_probabilities(df_filtered, offset=OFFSET_VAL)

    # --- MERGE ---
    combined_stats = pd.merge(
        stats_exact[['bar_index', 'prob_high_set', 'prob_low_set', 'prob_either_set']],
        stats_offset[['bar_index', 'prob_high_set', 'prob_low_set', 'prob_either_set']],
        on='bar_index',
        suffixes=('_exact', f'_offset_{OFFSET_VAL}')
    )

    # --- SAVE CSV ---
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    csv_filename = f"{scenario_name}.csv"
    csv_path = os.path.join(OUTPUT_DIR, csv_filename)
    print(f"Saving CSV to {csv_path}...")
    
    # Round to 2 decimals
    combined_stats = combined_stats.round(2)
    combined_stats.to_csv(csv_path, index=False)

    # --- PLOT ---
    plot_filename = f"{scenario_name}.png"
    plot_path = os.path.join(OUTPUT_DIR, plot_filename)
    print(f"Generating plot to {plot_path}...")
    
    plt.figure(figsize=(14, 8))
    
    # Limit to standard trading day (75 bars)
    plot_data = combined_stats[combined_stats['bar_index'] <= 75]

    # Plot Exact (Solid Lines)
    plt.plot(plot_data['bar_index'], plot_data['prob_high_set_exact'], label='High Set (Exact)', color='green', linewidth=2, linestyle='-', alpha=0.7)
    plt.plot(plot_data['bar_index'], plot_data['prob_low_set_exact'], label='Low Set (Exact)', color='red', linewidth=2, linestyle='-', alpha=0.7)
    plt.plot(plot_data['bar_index'], plot_data['prob_either_set_exact'], label='Total Prob (Exact)', color='black', linewidth=4, linestyle='-')

    # Plot Offset (Dashed Lines)
    plt.plot(plot_data['bar_index'], plot_data[f'prob_high_set_offset_{OFFSET_VAL}'], label=f'High Set (+/- {OFFSET_VAL})', color='green', linewidth=2, linestyle='--', alpha=0.7)
    plt.plot(plot_data['bar_index'], plot_data[f'prob_low_set_offset_{OFFSET_VAL}'], label=f'Low Set (+/- {OFFSET_VAL})', color='red', linewidth=2, linestyle='--', alpha=0.7)
    plt.plot(plot_data['bar_index'], plot_data[f'prob_either_set_offset_{OFFSET_VAL}'], label=f'Total Prob (+/- {OFFSET_VAL})', color='gray', linewidth=4, linestyle='--')

    plt.title(f'Probabilities: {scenario_name} (N={len(valid_dates)})', fontsize=16)
    plt.xlabel('Bar Index (5-min intervals)', fontsize=12)
    plt.ylabel('Probability (0.0 - 1.0)', fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.xlim(1, 75)
    plt.ylim(0, 1.05)
    
    plt.savefig(plot_path)
    plt.close()

def main():
    if not os.path.exists(DATA_PATH):
        print(f"Error: Data file not found at {DATA_PATH}")
        return

    print("Loading data...")
    try:
        df = pd.read_csv(DATA_PATH)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # 1. Parse Dates
    if 'date' in df.columns:
        dt_col = 'date'
    elif 'datetime' in df.columns:
        dt_col = 'datetime'
    else:
        print(f"Error: Could not find datetime column. Columns: {df.columns}")
        return

    print(f"Parsing datetime column '{dt_col}'...")
    df['datetime'] = pd.to_datetime(df[dt_col])
    df['date_only'] = df['datetime'].dt.date

    # 2. Sort Data
    df = df.sort_values('datetime').reset_index(drop=True)

    print(f"Data loaded. Rows: {len(df)}, Days: {df['date_only'].nunique()}")

    # --- PRE-CALCULATE BASE METRICS ---
    print("Pre-calculating daily metrics...")
    
    df['day_high'] = df.groupby('date_only')['high'].transform('max')
    df['day_low'] = df.groupby('date_only')['low'].transform('min')
    df['high_so_far'] = df.groupby('date_only')['high'].cummax()
    df['low_so_far'] = df.groupby('date_only')['low'].cummin()
    df['bar_index'] = df.groupby('date_only').cumcount() + 1

    # --- PREPARE 1ST BARS FOR FILTERING ---
    df['prev_close'] = df['close'].shift(1)
    
    first_bars = df[df['bar_index'] == 1].copy()

    # Common metrics
    # Gap = Open - Prev Close. Gap Down 50 means Gap <= -50.
    first_bars['gap'] = first_bars['open'] - first_bars['prev_close']
    first_bars['candle_len'] = first_bars['high'] - first_bars['low']
    first_bars['upper_wick'] = first_bars['high'] - first_bars['close']
    first_bars['lower_wick'] = first_bars['close'] - first_bars['low']
    first_bars['is_bull'] = first_bars['close'] > first_bars['open']
    first_bars['is_bear'] = first_bars['close'] < first_bars['open']

    # --- DEFINE SCENARIOS (GAP DOWN >= 50) ---
    GAP_THRESHOLD = -50
    
    # 1. 50-gapdown-bull: Gap <= -50, Bullish, Upper Wick <= 10%
    cond_bull = (
        (first_bars['gap'] <= GAP_THRESHOLD) & 
        (first_bars['is_bull']) & 
        (first_bars['upper_wick'] <= 0.10 * first_bars['candle_len']) & 
        (first_bars['candle_len'] > 0)
    )
    
    # 2. 50-gapdown-bear: Gap <= -50, Bearish, Lower Wick <= 10%
    cond_bear = (
        (first_bars['gap'] <= GAP_THRESHOLD) & 
        (first_bars['is_bear']) & 
        (first_bars['lower_wick'] <= 0.10 * first_bars['candle_len']) & 
        (first_bars['candle_len'] > 0)
    )
    
    # 3. 50-gapdown-any: Gap <= -50 (Any Bar)
    cond_any = (first_bars['gap'] <= GAP_THRESHOLD)

    scenarios = [
        ("50-gapdown-bull", first_bars[cond_bull]['date_only'].unique()),
        ("50-gapdown-bear", first_bars[cond_bear]['date_only'].unique()),
        ("50-gapdown-any", first_bars[cond_any]['date_only'].unique())
    ]

    # --- RUN LOOP ---
    for name, dates in scenarios:
        run_scenario(df, name, dates)

    print("\nAll scenarios completed.")

if __name__ == "__main__":
    main()
