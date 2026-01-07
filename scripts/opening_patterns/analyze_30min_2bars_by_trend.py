import pandas as pd
import numpy as np
import math
import os

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

def analyze_trend_patterns():
    # 1. Load and process 2hr data for Trend
    print("Loading 120min data for trend analysis...")
    df_2hr = pd.read_csv('../../data/nifty50_minute_complete-120min.csv')
    df_2hr['date'] = pd.to_datetime(df_2hr['date'])
    df_2hr = df_2hr.sort_values('date').reset_index(drop=True)

    # Calculate Indicators
    df_2hr['ema11'] = calculate_ema(df_2hr['close'], 11)
    df_2hr['ema21'] = calculate_ema(df_2hr['close'], 21)
    df_2hr['ema21_slope'] = calculate_slope_degrees(df_2hr['ema21'].values, lookback=1)

    # Determine Trend
    df_2hr['is_bull_trend'] = (df_2hr['ema11'] > df_2hr['ema21']) & (df_2hr['ema21_slope'] > 10)
    df_2hr['is_bear_trend'] = (df_2hr['ema11'] < df_2hr['ema21']) & (df_2hr['ema21_slope'] < -10)

    # Map Date -> Trend
    # We use the trend status at 9:15 of the day (start of day)
    # The 120min data timestamps usually represent the END of the bar or START. 
    # Let's check typical timestamps. Usually 09:15, 11:15, 13:15, 15:15.
    # We will use the trend value at 09:15 for that day.
    
    df_2hr['day_date'] = df_2hr['date'].dt.date
    daily_trend_map = {}
    
    # Iterate through days
    for day, day_data in df_2hr.groupby('day_date'):
        # Get the first bar of the day (09:15)
        # Note: If 09:15 row has the trend, it means the trend was calculated using THAT bar?
        # Actually, EMAs are lagging. If we use 09:15 bar's EMA, it includes the 09:15-11:15 price action if timestamps are start time.
        # Ideally, we want "Trend Entering the Day" (yesterday's close).
        # However, standard practice in this codebase (as seen in analyze_opening_with_trend.py)
        # uses the 09:15 row's calculated trend values.
        # "daily_trend = df_2hr[df_2hr['date'].dt.time == pd.to_datetime('09:15:00').time()]"
        # We will follow this convention.
        
        start_bar = day_data[day_data['date'].dt.time == pd.to_datetime('09:15:00').time()]
        
        if not start_bar.empty:
            is_bull = start_bar.iloc[0]['is_bull_trend']
            is_bear = start_bar.iloc[0]['is_bear_trend']
            
            if is_bull:
                daily_trend_map[day] = 'BULL'
            elif is_bear:
                daily_trend_map[day] = 'BEAR'
            else:
                daily_trend_map[day] = 'SIDEWAYS'
    
    # 2. Load and process 30min data for Patterns
    print("Loading 30min data for pattern analysis...")
    df_30min = pd.read_csv('../../data/nifty50_minute_2022-30min.csv')
    df_30min['datetime'] = pd.to_datetime(df_30min['date'])
    df_30min['day'] = df_30min['datetime'].dt.date
    
    # Results Storage
    results = {
        'BULL': {'2_bulls': [], '2_bears': [], 'opposite': [], 'total': 0},
        'BEAR': {'2_bulls': [], '2_bears': [], 'opposite': [], 'total': 0},
        'SIDEWAYS': {'2_bulls': [], '2_bears': [], 'opposite': [], 'total': 0} # Optional
    }
    
    # Iterate Days
    daily_groups = df_30min.groupby('day')
    
    for day, group in daily_groups:
        if day not in daily_trend_map:
            continue
            
        trend = daily_trend_map[day]
        # We only care about BULL and BEAR trends as per request
        if trend == 'SIDEWAYS':
            continue
            
        group = group.sort_values('datetime')
        if len(group) < 2:
            continue
            
        bar1 = group.iloc[0]
        bar2 = group.iloc[1]
        
        b1_bull = bar1['close'] > bar1['open']
        b1_bear = bar1['close'] < bar1['open']
        b2_bull = bar2['close'] > bar2['open']
        b2_bear = bar2['close'] < bar2['open']
        
        day_str = str(day)
        results[trend]['total'] += 1
        
        if b1_bull and b2_bull:
            results[trend]['2_bulls'].append(day_str)
        elif b1_bear and b2_bear:
            results[trend]['2_bears'].append(day_str)
        elif (b1_bull and b2_bear) or (b1_bear and b2_bull):
            results[trend]['opposite'].append(day_str)
            
    # 3. Output Results
    print("\n" + "="*60)
    print("ANALYSIS RESULTS: FIRST 2 BARS (30MIN) BY 2HR TREND")
    print("="*60)
    
    for trend in ['BULL', 'BEAR']:
        data = results[trend]
        total = data['total']
        if total == 0:
            print(f"\n{trend} TREND: No days found (check data alignment)")
            continue
            
        n_2bulls = len(data['2_bulls'])
        n_2bears = len(data['2_bears'])
        n_opp = len(data['opposite'])
        
        print(f"\n{trend} TREND (Total Days: {total})")
        print(f"  2 Bull Bars: {n_2bulls:4d} ({n_2bulls/total:.2%})")
        print(f"  2 Bear Bars: {n_2bears:4d} ({n_2bears/total:.2%})")
        print(f"  Opposite:    {n_opp:4d} ({n_opp/total:.2%})")
        
        # Save to CSV
        os.makedirs(f'output/trend_{trend.lower()}', exist_ok=True)
        pd.DataFrame({'date': data['2_bulls']}).to_csv(f'output/trend_{trend.lower()}/2bulls.csv', index=False)
        pd.DataFrame({'date': data['2_bears']}).to_csv(f'output/trend_{trend.lower()}/2bears.csv', index=False)
        pd.DataFrame({'date': data['opposite']}).to_csv(f'output/trend_{trend.lower()}/opposite.csv', index=False)

if __name__ == "__main__":
    analyze_trend_patterns()
