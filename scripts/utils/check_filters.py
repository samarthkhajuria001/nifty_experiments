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

df_2hr['is_bear_trend'] = (df_2hr['ema11'] < df_2hr['ema21']) & (df_2hr['ema21_slope'] < -10)

df_2hr['trading_date'] = df_2hr['date'].dt.date

daily_trend = df_2hr[df_2hr['date'].dt.time == pd.to_datetime('09:15:00').time()][['trading_date', 'is_bear_trend']].copy()

# Read 5min data
df_5min = pd.read_csv('../../data/nifty50_minute_complete-5min.csv')
df_5min['date'] = pd.to_datetime(df_5min['date'])
df_5min['trading_date'] = df_5min['date'].dt.date

# Get previous day close for gap
daily_data = df_5min.groupby('trading_date').agg({
    'open': 'first',
    'close': 'last'
}).reset_index()
daily_data['prev_close'] = daily_data['close'].shift(1)
daily_data['gap_down'] = daily_data['open'] < daily_data['prev_close']

# Check filters step by step
bear_and_gap = 0
first_bar_stats = []

for trading_date, day_data in df_5min.groupby('trading_date'):
    # Get gap info
    gap_info = daily_data[daily_data['trading_date'] == trading_date]
    if len(gap_info) == 0 or pd.isna(gap_info.iloc[0]['prev_close']):
        continue

    is_gap_down = gap_info.iloc[0]['gap_down']

    # Get 2hr trend
    trend_info = daily_trend[daily_trend['trading_date'] == trading_date]
    if len(trend_info) == 0:
        continue

    is_2hr_bear = trend_info.iloc[0]['is_bear_trend']

    # Count bear trend + gap down
    if is_2hr_bear and is_gap_down:
        bear_and_gap += 1

        # Analyze first bar
        first_bar = day_data.iloc[0]
        total_range = first_bar['high'] - first_bar['low']
        is_bear_candle = first_bar['close'] < first_bar['open']

        if total_range > 0 and is_bear_candle:
            lower_wick = first_bar['close'] - first_bar['low']
            wick_pct = lower_wick / total_range

            first_bar_stats.append({
                'date': trading_date,
                'lower_wick_pct': wick_pct * 100,
                'is_strong_bear_10pct': wick_pct <= 0.10,
                'is_strong_bear_20pct': wick_pct <= 0.20,
                'is_strong_bear_30pct': wick_pct <= 0.30
            })

first_bar_df = pd.DataFrame(first_bar_stats)

print("=" * 80)
print("FILTER ANALYSIS")
print("=" * 80)
print(f"\nTotal days in dataset: {len(df_5min.groupby('trading_date'))}")
print(f"Bear trend days: {daily_trend['is_bear_trend'].sum()}")
print(f"Gap down days: {daily_data['gap_down'].sum()}")
print(f"\n⭐ Bear trend + Gap down: {bear_and_gap}")
print()

if len(first_bar_df) > 0:
    print("FIRST BAR ANALYSIS (of bear trend + gap down days):")
    print("-" * 80)
    print(f"Days with strong bear candle (wick <= 10%): {first_bar_df['is_strong_bear_10pct'].sum()}")
    print(f"Days with strong bear candle (wick <= 20%): {first_bar_df['is_strong_bear_20pct'].sum()}")
    print(f"Days with strong bear candle (wick <= 30%): {first_bar_df['is_strong_bear_30pct'].sum()}")
    print()
    print(f"Average lower wick %: {first_bar_df['lower_wick_pct'].mean():.2f}%")
    print(f"Median lower wick %: {first_bar_df['lower_wick_pct'].median():.2f}%")
    print()
    print("Distribution of lower wick %:")
    print(first_bar_df['lower_wick_pct'].describe())
