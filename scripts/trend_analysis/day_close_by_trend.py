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

# Read 2hr data
df_2hr = pd.read_csv('../../data/nifty50_minute_complete-120min.csv')
df_2hr['date'] = pd.to_datetime(df_2hr['date'])
df_2hr = df_2hr.sort_values('date').reset_index(drop=True)

# Calculate EMAs and slope
df_2hr['ema11'] = calculate_ema(df_2hr['close'], 11)
df_2hr['ema21'] = calculate_ema(df_2hr['close'], 21)
df_2hr['ema21_slope'] = calculate_slope_degrees(df_2hr['ema21'].values, lookback=1)

# Determine trend
df_2hr['is_bull_trend'] = (df_2hr['ema11'] > df_2hr['ema21']) & (df_2hr['ema21_slope'] > 10)
df_2hr['is_bear_trend'] = (df_2hr['ema11'] < df_2hr['ema21']) & (df_2hr['ema21_slope'] < -10)

df_2hr['trading_date'] = df_2hr['date'].dt.date

# Get trend for each day
daily_trend = df_2hr[df_2hr['date'].dt.time == pd.to_datetime('09:15:00').time()][['trading_date', 'is_bull_trend', 'is_bear_trend']].copy()

# Read 5min data
df_5min = pd.read_csv('../../data/nifty50_minute_complete-5min.csv')
df_5min['date'] = pd.to_datetime(df_5min['date'])
df_5min['trading_date'] = df_5min['date'].dt.date
df_5min['time'] = df_5min['date'].dt.time

last_bar_time = pd.to_datetime('15:25:00').time()

results = []

for trading_date, day_data in df_5min.groupby('trading_date'):
    day_open = day_data.iloc[0]['open']
    last_bar = day_data[day_data['time'] == last_bar_time]

    if len(last_bar) == 0:
        day_close = day_data.iloc[-1]['close']
    else:
        day_close = last_bar.iloc[0]['close']

    day_is_bull = day_close > day_open

    trend_info = daily_trend[daily_trend['trading_date'] == trading_date]
    if len(trend_info) == 0:
        continue

    is_2hr_bull = trend_info.iloc[0]['is_bull_trend']
    is_2hr_bear = trend_info.iloc[0]['is_bear_trend']

    results.append({
        'date': trading_date,
        'day_close_bull': day_is_bull,
        '2hr_bull_trend': is_2hr_bull,
        '2hr_bear_trend': is_2hr_bear
    })

results_df = pd.DataFrame(results)

# BULL TREND
bull_trend_days = results_df[results_df['2hr_bull_trend'] == True]
bull_closes_bull = len(bull_trend_days[bull_trend_days['day_close_bull'] == True])
bull_closes_bear = len(bull_trend_days[bull_trend_days['day_close_bull'] == False])
bull_total = len(bull_trend_days)

bull_closes_bull_pct = (bull_closes_bull / bull_total * 100) if bull_total > 0 else 0
bull_closes_bear_pct = (bull_closes_bear / bull_total * 100) if bull_total > 0 else 0

# BEAR TREND
bear_trend_days = results_df[results_df['2hr_bear_trend'] == True]
bear_closes_bull = len(bear_trend_days[bear_trend_days['day_close_bull'] == True])
bear_closes_bear = len(bear_trend_days[bear_trend_days['day_close_bull'] == False])
bear_total = len(bear_trend_days)

bear_closes_bull_pct = (bear_closes_bull / bear_total * 100) if bear_total > 0 else 0
bear_closes_bear_pct = (bear_closes_bear / bear_total * 100) if bear_total > 0 else 0

print("Day Close Direction by 2HR Trend")
print()
print("| 2HR Trend | Day Closes BULL | Day Closes BEAR |")
print("|-----------|-----------------|-----------------|")
print(f"| BULL      | {bull_closes_bull_pct:.2f}%          | {bull_closes_bear_pct:.2f}%          |")
print(f"| BEAR      | {bear_closes_bull_pct:.2f}%          | {bear_closes_bear_pct:.2f}%          |")
