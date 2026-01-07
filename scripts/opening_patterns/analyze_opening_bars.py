import pandas as pd
import numpy as np

# Read the CSV file
df = pd.read_csv('../../data/nifty50_minute_complete-5min.csv')
df['date'] = pd.to_datetime(df['date'])

# Extract date and time components
df['trading_date'] = df['date'].dt.date
df['time'] = df['date'].dt.time

# Get first 30 minutes (6 bars) for each day
# First 30 minutes: 09:15, 09:20, 09:25, 09:30, 09:35, 09:40
first_30_min_times = [
    pd.to_datetime('09:15:00').time(),
    pd.to_datetime('09:20:00').time(),
    pd.to_datetime('09:25:00').time(),
    pd.to_datetime('09:30:00').time(),
    pd.to_datetime('09:35:00').time(),
    pd.to_datetime('09:40:00').time()
]

# Get last bar of each day (15:25:00 typically)
last_bar_time = pd.to_datetime('15:25:00').time()

# Group by trading date
results = []

for trading_date, day_data in df.groupby('trading_date'):
    # Get first 30 minutes data
    first_30_min = day_data[day_data['time'].isin(first_30_min_times)].copy()

    # Skip if we don't have exactly 6 bars
    if len(first_30_min) != 6:
        continue

    # Determine if each bar is bullish or bearish
    first_30_min['is_bull'] = first_30_min['close'] > first_30_min['open']

    # Get first 3 bars (09:15, 09:20, 09:25)
    first_3_bars = first_30_min.iloc[:3]

    # Check if all 3 consecutive bars are bull or bear
    all_bull = first_3_bars['is_bull'].all()
    all_bear = (~first_3_bars['is_bull']).all()

    # Get day's open and close
    day_open = day_data.iloc[0]['open']
    last_bar = day_data[day_data['time'] == last_bar_time]

    if len(last_bar) == 0:
        # If no 15:25 bar, use the last available bar
        day_close = day_data.iloc[-1]['close']
    else:
        day_close = last_bar.iloc[0]['close']

    day_is_bull = day_close > day_open

    results.append({
        'date': trading_date,
        'first_3_all_bull': all_bull,
        'first_3_all_bear': all_bear,
        'day_close_bull': day_is_bull,
        'day_open': day_open,
        'day_close': day_close,
        'day_change': day_close - day_open
    })

results_df = pd.DataFrame(results)

# Calculate probabilities
print("=" * 80)
print("ANALYSIS: 3 CONSECUTIVE BULL/BEAR BARS IN FIRST 30 MINUTES")
print("=" * 80)
print()

# When first 3 bars are all BULL
bull_days = results_df[results_df['first_3_all_bull'] == True]
print(f"Days with 3 consecutive BULL bars in first 30 min: {len(bull_days)}")
if len(bull_days) > 0:
    bull_day_closes_bull = bull_days[bull_days['day_close_bull'] == True]
    bull_day_closes_bear = bull_days[bull_days['day_close_bull'] == False]

    prob_bull_close = len(bull_day_closes_bull) / len(bull_days) * 100
    prob_bear_close = len(bull_day_closes_bear) / len(bull_days) * 100

    print(f"  → Day closes BULL: {len(bull_day_closes_bull)} ({prob_bull_close:.2f}%)")
    print(f"  → Day closes BEAR: {len(bull_day_closes_bear)} ({prob_bear_close:.2f}%)")
    print()

# When first 3 bars are all BEAR
bear_days = results_df[results_df['first_3_all_bear'] == True]
print(f"Days with 3 consecutive BEAR bars in first 30 min: {len(bear_days)}")
if len(bear_days) > 0:
    bear_day_closes_bull = bear_days[bear_days['day_close_bull'] == True]
    bear_day_closes_bear = bear_days[bear_days['day_close_bull'] == False]

    prob_bull_close = len(bear_day_closes_bull) / len(bear_days) * 100
    prob_bear_close = len(bear_day_closes_bear) / len(bear_days) * 100

    print(f"  → Day closes BULL: {len(bear_day_closes_bull)} ({prob_bull_close:.2f}%)")
    print(f"  → Day closes BEAR: {len(bear_day_closes_bear)} ({prob_bear_close:.2f}%)")
    print()

# Mixed bars (neither all bull nor all bear)
mixed_days = results_df[(results_df['first_3_all_bull'] == False) &
                        (results_df['first_3_all_bear'] == False)]
print(f"Days with MIXED bars in first 30 min: {len(mixed_days)}")
if len(mixed_days) > 0:
    mixed_day_closes_bull = mixed_days[mixed_days['day_close_bull'] == True]
    mixed_day_closes_bear = mixed_days[mixed_days['day_close_bull'] == False]

    prob_bull_close = len(mixed_day_closes_bull) / len(mixed_days) * 100
    prob_bear_close = len(mixed_day_closes_bear) / len(mixed_days) * 100

    print(f"  → Day closes BULL: {len(mixed_day_closes_bull)} ({prob_bull_close:.2f}%)")
    print(f"  → Day closes BEAR: {len(mixed_day_closes_bear)} ({prob_bear_close:.2f}%)")
    print()

print("=" * 80)
print(f"Total trading days analyzed: {len(results_df)}")
print("=" * 80)

# Additional statistics
print("\nAVERAGE DAY CHANGES:")
if len(bull_days) > 0:
    avg_change_bull = bull_days['day_change'].mean()
    print(f"When first 3 bars are BULL: Avg day change = {avg_change_bull:.2f}")

if len(bear_days) > 0:
    avg_change_bear = bear_days['day_change'].mean()
    print(f"When first 3 bars are BEAR: Avg day change = {avg_change_bear:.2f}")
