import pandas as pd
import numpy as np
import math

def calculate_ema(data, period):
    """Calculate Exponential Moving Average"""
    return data.ewm(span=period, adjust=False).mean()

def calculate_slope_degrees(values, lookback=1):
    """Calculate slope in degrees"""
    slopes = []
    for i in range(len(values)):
        if i < lookback:
            slopes.append(0.0)
        else:
            y_diff = values[i] - values[i - lookback]
            x_diff = lookback
            angle = math.degrees(math.atan2(y_diff, x_diff))
            slopes.append(angle)
    return slopes

# Load the CSV file
file_path = '../../data/nifty50_minute_complete-120min.csv'
df = pd.read_csv(file_path)

# Ensure date is datetime (though not strictly needed for calc, good practice)
# We won't sort unless necessary to preserve original order if it wasn't sorted, 
# but EMAs depend on order. The file seems sorted.
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

# Calculate EMAs
df['ema11'] = calculate_ema(df['close'], 11)
df['ema21'] = calculate_ema(df['close'], 21)

# Calculate Slope of EMA21
df['ema21_slope'] = calculate_slope_degrees(df['ema21'].values, lookback=1)

# Define Trend Rules
# Uptrend: EMA11 > EMA21 AND Slope > 10
df['uptrend'] = (df['ema11'] > df['ema21']) & (df['ema21_slope'] > 10)

# Downtrend: EMA11 < EMA21 AND Slope < -10
df['downtrend'] = (df['ema11'] < df['ema21']) & (df['ema21_slope'] < -10)

# Drop intermediate calculation columns if you only want the keys 'uptrend', 'downtrend'
# keeping them allows verifying logic, but user only asked for "extra columns ... with keys uptrend , downtrend"
# I will drop the helper columns ema11, ema21, ema21_slope to keep it clean, 
# unless the user wants them. The request implies adding trend columns.
# I'll keep them as they are useful context, but maybe I should just keep the requested ones.
# "add extra columns ... called trend , with keys uptrend , downtrend"
# I will keep just the requested columns to modify the file as little as possible regarding schema clutter.
df.drop(columns=['ema11', 'ema21', 'ema21_slope'], inplace=True)

# Save back to CSV
df.to_csv(file_path, index=False)
print(f"Updated {file_path} with 'uptrend' and 'downtrend' columns.")
