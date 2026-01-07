import pandas as pd
import numpy as np
import math

# Re-implement helper functions
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

# Load data
df = pd.read_csv('../../data/nifty50_minute_complete-120min.csv')
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

# Calculate EMAs
df['ema11'] = calculate_ema(df['close'], 11)
df['ema21'] = calculate_ema(df['close'], 21)

# Calculate Slope
df['ema21_slope'] = calculate_slope_degrees(df['ema21'].values, lookback=1)

# Determine Trend
df['is_uptrend'] = (df['ema11'] > df['ema21']) & (df['ema21_slope'] > 10)
df['is_downtrend'] = (df['ema11'] < df['ema21']) & (df['ema21_slope'] < -10)

# Filter for the specific date range
start_date = '2022-11-23'
end_date = '2022-12-02'
mask = (df['date'] >= start_date) & (df['date'] <= f"{end_date} 23:59:59")
df_range = df.loc[mask].copy()

# Output columns
cols = ['date', 'close', 'ema11', 'ema21', 'ema21_slope', 'is_uptrend', 'is_downtrend']
print(df_range[cols].to_string(index=False))
