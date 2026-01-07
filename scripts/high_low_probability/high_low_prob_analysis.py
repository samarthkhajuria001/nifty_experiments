import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Configuration
DATA_PATH = "../../data/nifty50_minute_complete-5min.csv"
OUTPUT_DIR = "../../output/high_low_probability"
OUTPUT_PLOT_PATH = os.path.join(OUTPUT_DIR, "high_low_probability.png")
OUTPUT_CSV_PATH = os.path.join(OUTPUT_DIR, "high_low_probs.csv")

def calculate_probabilities(df, offset=0):
    """
    Calculates the probability of having seen the day's high or low 
    by a specific bar, given a noise offset.
    
    Logic:
    - High is 'seen' if current_high + offset >= day_high
    - Low is 'seen' if current_low - offset <= day_low
    """
    print(f"Calculating probabilities with offset: {offset}")
    
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
    print(f"Range: {df['date_only'].min()} to {df['date_only'].max()}")

    # --- PRE-CALCULATE BASE METRICS ---
    print("Pre-calculating daily metrics...")
    
    df['day_high'] = df.groupby('date_only')['high'].transform('max')
    df['day_low'] = df.groupby('date_only')['low'].transform('min')
    df['high_so_far'] = df.groupby('date_only')['high'].cummax()
    df['low_so_far'] = df.groupby('date_only')['low'].cummin()
    df['bar_index'] = df.groupby('date_only').cumcount() + 1

    # --- CALCULATE BOTH SCENARIOS ---
    
    # 1. Exact Match (Offset 0)
    stats_exact = calculate_probabilities(df, offset=0)
    
    # 2. Near Match (Offset 5)
    OFFSET_VAL = 5
    stats_offset = calculate_probabilities(df, offset=OFFSET_VAL)

    # --- PREPARE COMBINED DATA FOR CSV ---
    
    # Merge on bar_index
    # We rename columns to distinguish them
    combined_stats = pd.merge(
        stats_exact[['bar_index', 'prob_high_set', 'prob_low_set', 'prob_either_set']],
        stats_offset[['bar_index', 'prob_high_set', 'prob_low_set', 'prob_either_set']],
        on='bar_index',
        suffixes=('_exact', f'_offset_{OFFSET_VAL}')
    )
    
    print("\nCombined Probability table (First 10 bars):")
    print(combined_stats.head(10))

    # --- PRINT FULL TABLE (Either Set Probabilities) ---
    print(f"\n--- Total Probability Table (All 75 Bars) [Exact vs Offset {OFFSET_VAL}] ---")
    output_cols = ['bar_index', 'prob_either_set_exact', f'prob_either_set_offset_{OFFSET_VAL}']
    
    # Filter for first 75 bars
    display_df = combined_stats[combined_stats['bar_index'] <= 75][output_cols]
    
    with pd.option_context('display.max_rows', None, 'display.width', 1000):
        print(display_df.to_string(index=False))

    # --- SAVE OUTPUTS ---
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print(f"Saving combined CSV to {OUTPUT_CSV_PATH}...")
    # Saving only the requested columns (bar_index and probs), count columns were already dropped in the merge selection above
    combined_stats.to_csv(OUTPUT_CSV_PATH, index=False)

    # --- VISUALIZATION ---
    print(f"Generating plot to {OUTPUT_PLOT_PATH}...")
    
    plt.figure(figsize=(14, 8)) # Slightly larger for more lines

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

    plt.title(f'Probability Day High/Low is Set: Exact vs Offset {OFFSET_VAL}', fontsize=16)
    plt.xlabel('Bar Index (5-min intervals)', fontsize=12)
    plt.ylabel('Probability (0.0 - 1.0)', fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.xlim(1, 75)
    plt.ylim(0, 1.05)
    
    plt.savefig(OUTPUT_PLOT_PATH)
    print("Done.")

if __name__ == "__main__":
    main()
