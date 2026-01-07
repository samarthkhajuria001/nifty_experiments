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

df_2hr['ema11'] = calculate_ema(df_2hr['close'], 11)
df_2hr['ema21'] = calculate_ema(df_2hr['close'], 21)
df_2hr['ema21_slope'] = calculate_slope_degrees(df_2hr['ema21'].values, lookback=1)

df_2hr['is_bull_trend'] = (df_2hr['ema11'] > df_2hr['ema21']) & (df_2hr['ema21_slope'] > 10)
df_2hr['is_bear_trend'] = (df_2hr['ema11'] < df_2hr['ema21']) & (df_2hr['ema21_slope'] < -10)

df_2hr['trading_date'] = df_2hr['date'].dt.date

daily_trend = df_2hr[df_2hr['date'].dt.time == pd.to_datetime('09:15:00').time()][['trading_date', 'is_bull_trend', 'is_bear_trend']].copy()

# Read 5min data
df_5min = pd.read_csv('../../data/nifty50_minute_complete-5min.csv')
df_5min['date'] = pd.to_datetime(df_5min['date'])
df_5min['trading_date'] = df_5min['date'].dt.date
df_5min['time'] = df_5min['date'].dt.time

# Skip first bar (09:15), take next 3 bars (09:20, 09:25, 09:30)
skip_first_3_bar_times = [
    pd.to_datetime('09:20:00').time(),
    pd.to_datetime('09:25:00').time(),
    pd.to_datetime('09:30:00').time(),
]

last_bar_time = pd.to_datetime('15:25:00').time()

# Get previous day close for gap calculation
daily_data = df_5min.groupby('trading_date').agg({
    'open': 'first',
    'close': 'last'
}).reset_index()
daily_data['prev_close'] = daily_data['close'].shift(1)
daily_data['gap_up'] = daily_data['open'] > daily_data['prev_close']
daily_data['gap_down'] = daily_data['open'] < daily_data['prev_close']

results = []

for trading_date, day_data in df_5min.groupby('trading_date'):
    # Get gap info
    gap_info = daily_data[daily_data['trading_date'] == trading_date]
    if len(gap_info) == 0:
        continue

    is_gap_up = gap_info.iloc[0]['gap_up']
    is_gap_down = gap_info.iloc[0]['gap_down']

    # Skip first bar, take next 3 bars (09:20, 09:25, 09:30)
    skip_first_3_bars = day_data[day_data['time'].isin(skip_first_3_bar_times)].copy()
    if len(skip_first_3_bars) == 3:
        skip_first_3_bars['is_bull'] = skip_first_3_bars['close'] > skip_first_3_bars['open']
        skip_first_3_all_bull = skip_first_3_bars['is_bull'].all()
        skip_first_3_all_bear = (~skip_first_3_bars['is_bull']).all()
    else:
        skip_first_3_all_bull = False
        skip_first_3_all_bear = False

    # Day close
    day_open = day_data.iloc[0]['open']
    last_bar = day_data[day_data['time'] == last_bar_time]
    if len(last_bar) == 0:
        day_close = day_data.iloc[-1]['close']
    else:
        day_close = last_bar.iloc[0]['close']

    day_is_bull = day_close > day_open

    # 2hr trend
    trend_info = daily_trend[daily_trend['trading_date'] == trading_date]
    if len(trend_info) == 0:
        continue

    is_2hr_bull = trend_info.iloc[0]['is_bull_trend']
    is_2hr_bear = trend_info.iloc[0]['is_bear_trend']

    results.append({
        'date': trading_date,
        'gap_up': is_gap_up,
        'gap_down': is_gap_down,
        'skip_first_3_all_bull': skip_first_3_all_bull,
        'skip_first_3_all_bear': skip_first_3_all_bear,
        'day_close_bull': day_is_bull,
        '2hr_bull_trend': is_2hr_bull,
        '2hr_bear_trend': is_2hr_bear
    })

results_df = pd.DataFrame(results)

# Analysis: Skip first bar, next 3 bars (09:20-09:30) + Gap
print("=" * 80)
print("SKIP FIRST BAR - Next 3 Bars (09:20-09:30) by 2HR Trend + Gap")
print("=" * 80)
print()

table_data = []

for trend, trend_name in [(True, 'BULL'), (False, 'BEAR')]:
    trend_col = '2hr_bull_trend' if trend else '2hr_bear_trend'

    for gap, gap_name in [(True, 'Gap Up'), (False, 'Gap Down')]:
        gap_col = 'gap_up' if gap else 'gap_down'

        filtered = results_df[(results_df[trend_col] == True) & (results_df[gap_col] == True)]

        # 3 Bull bars
        pattern_data = filtered[filtered['skip_first_3_all_bull'] == True]
        if len(pattern_data) > 0:
            bull_close = len(pattern_data[pattern_data['day_close_bull'] == True]) / len(pattern_data) * 100
            bear_close = len(pattern_data[pattern_data['day_close_bull'] == False]) / len(pattern_data) * 100
            table_data.append([trend_name, gap_name, '3 Bull Bars', f'{bull_close:.2f}%', f'{bear_close:.2f}%'])

        # 3 Bear bars
        pattern_data = filtered[filtered['skip_first_3_all_bear'] == True]
        if len(pattern_data) > 0:
            bull_close = len(pattern_data[pattern_data['day_close_bull'] == True]) / len(pattern_data) * 100
            bear_close = len(pattern_data[pattern_data['day_close_bull'] == False]) / len(pattern_data) * 100
            table_data.append([trend_name, gap_name, '3 Bear Bars', f'{bull_close:.2f}%', f'{bear_close:.2f}%'])

print("| 2HR Trend | Gap       | Pattern (09:20-09:30) | Day Closes BULL | Day Closes BEAR |")
print("|-----------|-----------|------------------------|-----------------|-----------------|")
for row in table_data:
    print(f"| {row[0]:<9} | {row[1]:<9} | {row[2]:<22} | {row[3]:<15} | {row[4]:<15} |")
