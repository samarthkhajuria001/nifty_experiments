import pandas as pd
import numpy as np
import math

# Re-implement helper functions to avoid importing main execution block
def calculate_ema(data, period):
    """Calculate Exponential Moving Average"""
    return data.ewm(span=period, adjust=False).mean()

def calculate_slope_degrees(values, lookback=1):
    """Calculate slope in degrees"""
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

# Calculate Slope of EMA21
# Default lookback=1 as per trend_analysis_methods usage
df['ema21_slope'] = calculate_slope_degrees(df['ema21'].values, lookback=1)

# Determine Trend Status for each row
# Uptrend: EMA11 > EMA21 AND Slope > 10
df['is_uptrend'] = (df['ema11'] > df['ema21']) & (df['ema21_slope'] > 10)

# Downtrend: EMA11 < EMA21 AND Slope < -10
df['is_downtrend'] = (df['ema11'] < df['ema21']) & (df['ema21_slope'] < -10)

# We want to know: "In uptrend... probability a bar is bull".
# This means if the trend *leading into* the bar is Up, what does the bar do?
# So we use the trend status of the *previous* bar to classify the *current* bar.
df['prev_uptrend'] = df['is_uptrend'].shift(1)
df['prev_downtrend'] = df['is_downtrend'].shift(1)

# Identify bars to exclude (15min bars at end of day)
# Timestamps: 09:15, 11:15, 13:15, 15:15. 
# 15:15 is the start of the 15min bar.
df['time_str'] = df['date'].dt.time.astype(str)
df_clean = df[df['time_str'] != '15:15:00'].copy()

# Determine Bull/Bear status of the bar itself
# Bull: Close > Open
# Bear: Close < Open
df_clean['is_bull'] = df_clean['close'] > df_clean['open']
df_clean['is_bear'] = df_clean['close'] < df_clean['open']

# --- Analysis ---

# Uptrend Group
up_bars = df_clean[df_clean['prev_uptrend'] == True]
up_total = len(up_bars)
up_bull = up_bars['is_bull'].sum()
up_bear = up_bars['is_bear'].sum()

# Downtrend Group
down_bars = df_clean[df_clean['prev_downtrend'] == True]
down_total = len(down_bars)
down_bull = down_bars['is_bull'].sum()
down_bear = down_bars['is_bear'].sum()

# Calculate Probabilities
def calc_prob(count, total):
    if total == 0: return 0.0
    return (count / total) * 100

up_bull_prob = calc_prob(up_bull, up_total)
up_bear_prob = calc_prob(up_bear, up_total)

down_bull_prob = calc_prob(down_bull, down_total)
down_bear_prob = calc_prob(down_bear, down_total)

# Create Output Table
output = "# 2Hr Bar Probability by Trend\n\n"
output += "Analysis of 2-hour bars (excluding 15-min end-of-day bars).\n\n"
output += "| Trend | Total Bars | Bull Bars | Bear Bars | Bull Prob (%) | Bear Prob (%) |\n"
output += "|---|---|---|---|---|---|\n"
output += f"| Uptrend | {up_total} | {up_bull} | {up_bear} | {up_bull_prob:.2f}% | {up_bear_prob:.2f}% |\n"
output += f"| Downtrend | {down_total} | {down_bull} | {down_bear} | {down_bull_prob:.2f}% | {down_bear_prob:.2f}% |\n"

print(output)

with open('2hr_bar_analysis.md', 'w') as f:
    f.write(output)
