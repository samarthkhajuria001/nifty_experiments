import pandas as pd
import numpy as np
import math

def calculate_ema(data, period):
    return data.ewm(span=period, adjust=False).mean()

def calculate_slope_degrees(values, lookback=1):
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

# Load data
df = pd.read_csv('../../data/nifty50_minute_complete-120min.csv')
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

# Calculate EMAs
df['ema11'] = calculate_ema(df['close'], 11)
df['ema21'] = calculate_ema(df['close'], 21)

# Calculate Slope
df['ema21_slope'] = calculate_slope_degrees(df['ema21'].values, lookback=1)

# Define conditions
df['ema_condition'] = np.where(df['ema11'] > df['ema21'], 'EMA11 > EMA21 (Bull)', 'EMA11 < EMA21 (Bear)')
df['slope_condition'] = df['ema21_slope']

# Filter for the specific time
target_date = '2019-01-22 09:15:00'
row = df[df['date'] == target_date]

if not row.empty:
    print(f"Data for {target_date}:")
    print(f"Close: {row['close'].values[0]}")
    print(f"EMA11: {row['ema11'].values[0]:.4f}")
    print(f"EMA21: {row['ema21'].values[0]:.4f}")
    print(f"EMA Relation: {row['ema_condition'].values[0]}")
    print(f"EMA21 Slope: {row['ema21_slope'].values[0]:.4f} degrees")
    
    ema11 = row['ema11'].values[0]
    ema21 = row['ema21'].values[0]
    slope = row['ema21_slope'].values[0]
    
    print("\nCheck Rules:")
    print(f"1. Uptrend Rule (EMA11 > EMA21 AND Slope > 10):")
    print(f"   - {ema11:.2f} > {ema21:.2f}? {ema11 > ema21}")
    print(f"   - {slope:.2f} > 10? {slope > 10}")
    print(f"   - Result: {(ema11 > ema21) and (slope > 10)}")
    
    print(f"\n2. Downtrend Rule (EMA11 < EMA21 AND Slope < -10):")
    print(f"   - {ema11:.2f} < {ema21:.2f}? {ema11 < ema21}")
    print(f"   - {slope:.2f} < -10? {slope < -10}")
    print(f"   - Result: {(ema11 < ema21) and (slope < -10)}")
else:
    print("Date not found.")
