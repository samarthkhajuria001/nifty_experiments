import pandas as pd
import numpy as np
import math

def calculate_ema(data, period):
    return data.ewm(span=period, adjust=False).mean()

def calculate_slope_degrees(values, lookback=1):
    slopes = []
    for i in range(len(values)):
        if i < lookback:
            slopes.append(0)
        else:
            y_diff = values[i] - values[i - lookback]
            x_diff = lookback
            angle = math.degrees(math.atan2(y_diff, x_diff))
            slopes.append(angle)
    return slopes

# Read 2hr data for trend
df_2hr = pd.read_csv('../../data/nifty50_minute_complete-120min.csv')
df_2hr['date'] = pd.to_datetime(df_2hr['date'])
df_2hr = df_2hr.sort_values('date').reset_index(drop=True)

# Calculate EMAs and slope on 2hr
df_2hr['ema11'] = calculate_ema(df_2hr['close'], 11)
df_2hr['ema21'] = calculate_ema(df_2hr['close'], 21)
df_2hr['ema21_slope'] = calculate_slope_degrees(df_2hr['ema21'].values, lookback=1)

# Determine trend
df_2hr['is_bull_trend'] = (df_2hr['ema11'] > df_2hr['ema21']) & (df_2hr['ema21_slope'] > 10)
df_2hr['is_bear_trend'] = (df_2hr['ema11'] < df_2hr['ema21']) & (df_2hr['ema21_slope'] < -10)

# Extract trading date
df_2hr['trading_date'] = df_2hr['date'].dt.date

# Get trend for each day (use 09:15 bar)
daily_trend = df_2hr[df_2hr['date'].dt.time == pd.to_datetime('09:15:00').time()][['trading_date', 'is_bull_trend', 'is_bear_trend']].copy()

# Read 5min data
df_5min = pd.read_csv('../../data/nifty50_minute_complete-5min.csv')
df_5min['date'] = pd.to_datetime(df_5min['date'])
df_5min['trading_date'] = df_5min['date'].dt.date
df_5min['time'] = df_5min['date'].dt.time

# First 6 bars (1 hour) times
first_6_bar_times = [
    pd.to_datetime('09:15:00').time(),
    pd.to_datetime('09:20:00').time(),
    pd.to_datetime('09:25:00').time(),
    pd.to_datetime('09:30:00').time(),
    pd.to_datetime('09:35:00').time(),
    pd.to_datetime('09:40:00').time(),
]

last_bar_time = pd.to_datetime('15:25:00').time()

results = []

for trading_date, day_data in df_5min.groupby('trading_date'):
    first_6_bars = day_data[day_data['time'].isin(first_6_bar_times)].copy()

    if len(first_6_bars) != 6:
        continue

    first_6_bars['is_bull'] = first_6_bars['close'] > first_6_bars['open']

    all_bull = first_6_bars['is_bull'].all()
    all_bear = (~first_6_bars['is_bull']).all()

    day_open = day_data.iloc[0]['open']
    last_bar = day_data[day_data['time'] == last_bar_time]

    if len(last_bar) == 0:
        day_close = day_data.iloc[-1]['close']
    else:
        day_close = last_bar.iloc[0]['close']

    day_is_bull = day_close > day_open

    # Check if first bar low/high holds for rest of day
    first_bar = first_6_bars.iloc[0]
    rest_of_day = day_data[day_data['time'] > first_6_bars.iloc[5]['time']]  # After first 6 bars

    first_bull_low_is_lowest = False
    first_bear_high_is_highest = False

    if len(rest_of_day) > 0:
        rest_of_day_low = rest_of_day['low'].min()
        rest_of_day_high = rest_of_day['high'].max()

        if all_bull:
            first_bull_low_is_lowest = first_bar['low'] <= rest_of_day_low

        if all_bear:
            first_bear_high_is_highest = first_bar['high'] >= rest_of_day_high

    # Get 2hr trend
    trend_info = daily_trend[daily_trend['trading_date'] == trading_date]
    if len(trend_info) == 0:
        continue

    is_2hr_bull = trend_info.iloc[0]['is_bull_trend']
    is_2hr_bear = trend_info.iloc[0]['is_bear_trend']

    results.append({
        'date': trading_date,
        'first_6_all_bull': all_bull,
        'first_6_all_bear': all_bear,
        'day_close_bull': day_is_bull,
        'first_bull_low_is_lowest': first_bull_low_is_lowest,
        'first_bear_high_is_highest': first_bear_high_is_highest,
        '2hr_bull_trend': is_2hr_bull,
        '2hr_bear_trend': is_2hr_bear
    })

results_df = pd.DataFrame(results)

# Prepare data for table
table_data = []

# BULL TREND
bull_trend_days = results_df[results_df['2hr_bull_trend'] == True]

bull_first6_bull = bull_trend_days[bull_trend_days['first_6_all_bull'] == True]
if len(bull_first6_bull) > 0:
    closes_bull_pct = len(bull_first6_bull[bull_first6_bull['day_close_bull'] == True]) / len(bull_first6_bull) * 100
    closes_bear_pct = len(bull_first6_bull[bull_first6_bull['day_close_bull'] == False]) / len(bull_first6_bull) * 100
    low_holds_pct = len(bull_first6_bull[bull_first6_bull['first_bull_low_is_lowest'] == True]) / len(bull_first6_bull) * 100
    table_data.append(['BULL', '6 Bull Bars', f'{closes_bull_pct:.2f}%', f'{closes_bear_pct:.2f}%', f'{low_holds_pct:.2f}%', '-'])

bull_first6_bear = bull_trend_days[bull_trend_days['first_6_all_bear'] == True]
if len(bull_first6_bear) > 0:
    closes_bull_pct = len(bull_first6_bear[bull_first6_bear['day_close_bull'] == True]) / len(bull_first6_bear) * 100
    closes_bear_pct = len(bull_first6_bear[bull_first6_bear['day_close_bull'] == False]) / len(bull_first6_bear) * 100
    high_holds_pct = len(bull_first6_bear[bull_first6_bear['first_bear_high_is_highest'] == True]) / len(bull_first6_bear) * 100
    table_data.append(['BULL', '6 Bear Bars', f'{closes_bull_pct:.2f}%', f'{closes_bear_pct:.2f}%', '-', f'{high_holds_pct:.2f}%'])

# BEAR TREND
bear_trend_days = results_df[results_df['2hr_bear_trend'] == True]

bear_first6_bull = bear_trend_days[bear_trend_days['first_6_all_bull'] == True]
if len(bear_first6_bull) > 0:
    closes_bull_pct = len(bear_first6_bull[bear_first6_bull['day_close_bull'] == True]) / len(bear_first6_bull) * 100
    closes_bear_pct = len(bear_first6_bull[bear_first6_bull['day_close_bull'] == False]) / len(bear_first6_bull) * 100
    low_holds_pct = len(bear_first6_bull[bear_first6_bull['first_bull_low_is_lowest'] == True]) / len(bear_first6_bull) * 100
    table_data.append(['BEAR', '6 Bull Bars', f'{closes_bull_pct:.2f}%', f'{closes_bear_pct:.2f}%', f'{low_holds_pct:.2f}%', '-'])

bear_first6_bear = bear_trend_days[bear_trend_days['first_6_all_bear'] == True]
if len(bear_first6_bear) > 0:
    closes_bull_pct = len(bear_first6_bear[bear_first6_bear['day_close_bull'] == True]) / len(bear_first6_bear) * 100
    closes_bear_pct = len(bear_first6_bear[bear_first6_bear['day_close_bull'] == False]) / len(bear_first6_bear) * 100
    high_holds_pct = len(bear_first6_bear[bear_first6_bear['first_bear_high_is_highest'] == True]) / len(bear_first6_bear) * 100
    table_data.append(['BEAR', '6 Bear Bars', f'{closes_bull_pct:.2f}%', f'{closes_bear_pct:.2f}%', '-', f'{high_holds_pct:.2f}%'])

# Print table
print("FIRST 6 BARS (1 HOUR)")
print()
print(f"{'2HR Trend':<12} {'First 1hr':<15} {'Day Close BULL':<16} {'Day Close BEAR':<16} {'1st Bull Low Holds':<20} {'1st Bear High Holds':<20}")
print("-" * 120)
for row in table_data:
    print(f"{row[0]:<12} {row[1]:<15} {row[2]:<16} {row[3]:<16} {row[4]:<20} {row[5]:<20}")
print()

# Output for markdown
for row in table_data:
    print(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} |")
