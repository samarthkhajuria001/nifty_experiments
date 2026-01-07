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

def analyze_90min_reversal():
    # 1. Load 2hr data for Trend
    print("Loading 120min data for trend analysis...")
    df_2hr = pd.read_csv('../../data/nifty50_minute_complete-120min.csv')
    df_2hr['date'] = pd.to_datetime(df_2hr['date'])
    df_2hr = df_2hr.sort_values('date').reset_index(drop=True)

    df_2hr['ema11'] = calculate_ema(df_2hr['close'], 11)
    df_2hr['ema21'] = calculate_ema(df_2hr['close'], 21)
    df_2hr['ema21_slope'] = calculate_slope_degrees(df_2hr['ema21'].values, lookback=1)

    df_2hr['is_bull_trend'] = (df_2hr['ema11'] > df_2hr['ema21']) & (df_2hr['ema21_slope'] > 10)
    df_2hr['is_bear_trend'] = (df_2hr['ema11'] < df_2hr['ema21']) & (df_2hr['ema21_slope'] < -10)

    df_2hr['day_date'] = df_2hr['date'].dt.date
    daily_trend_map = {}
    
    for day, day_data in df_2hr.groupby('day_date'):
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
    
    # 2. Load 30min data for Reversal Analysis
    print("Loading 30min data for reversal analysis...")
    df_30min = pd.read_csv('../../data/nifty50_minute_2022-30min.csv')
    df_30min['datetime'] = pd.to_datetime(df_30min['date'])
    df_30min['day'] = df_30min['datetime'].dt.date
    
    # Statistics Storage
    results = {
        'BULL': {'total_days': 0, 'high_in_90min': 0, 'reversal_bear_close': 0},
        'BEAR': {'total_days': 0, 'low_in_90min': 0, 'reversal_bull_close': 0}
    }
    
    daily_groups = df_30min.groupby('day')
    
    for day, group in daily_groups:
        if day not in daily_trend_map:
            continue
            
        trend = daily_trend_map[day]
        if trend == 'SIDEWAYS':
            continue
            
        group = group.sort_values('datetime')
        if len(group) < 3:
            continue
            
        # Day Stats
        day_open = group.iloc[0]['open']
        day_close = group.iloc[-1]['close']
        day_high = group['high'].max()
        day_low = group['low'].min()
        
        # 90 Min Stats (First 3 bars: 09:15, 09:45, 10:15)
        first_90_bars = group.iloc[:3]
        high_90 = first_90_bars['high'].max()
        low_90 = first_90_bars['low'].min()
        
        if trend == 'BULL':
            results['BULL']['total_days'] += 1
            # Condition 1: Day High was made in first 90 mins
            if high_90 == day_high:
                results['BULL']['high_in_90min'] += 1
                # Condition 2: Day Reversed (Closed Bearish)
                if day_close < day_open:
                    results['BULL']['reversal_bear_close'] += 1
                    
        elif trend == 'BEAR':
            results['BEAR']['total_days'] += 1
            # Condition 1: Day Low was made in first 90 mins
            if low_90 == day_low:
                results['BEAR']['low_in_90min'] += 1
                # Condition 2: Day Reversed (Closed Bullish)
                if day_close > day_open:
                    results['BEAR']['reversal_bull_close'] += 1

    # 3. Append to Report
    print("Appending to analysis file...")
    md_file_path = 'analysis_mdfiles/30min_opening_patterns_analysis.md'
    
    with open(md_file_path, 'a') as f:
        f.write("\n\n---\n\n")
        f.write("## Question 4: 90-Minute Reversal Analysis\n")
        f.write("**How often does the day reverse after establishing the Day High (in Bull Trend) or Day Low (in Bear Trend) within the first 90 minutes?**\n")
        f.write("_Definition: '90-min Reversal' = Day High/Low is set in the first 1.5 hours, but the day closes in the opposite direction._\n\n")
        
        f.write("### Answer\n\n")
        
        # Bull Trend Table
        bull = results['BULL']
        bull_high_pct = (bull['high_in_90min'] / bull['total_days'] * 100) if bull['total_days'] > 0 else 0
        bull_rev_pct = (bull['reversal_bear_close'] / bull['high_in_90min'] * 100) if bull['high_in_90min'] > 0 else 0
        
        f.write("#### 1. Bull Trend Reversal (Bull Trap)\n")
        f.write(f"Total Bull Trend Days Analyzed: {bull['total_days']}\n\n")
        f.write("| Metric | Count | Percentage |\n")
        f.write("| :----- | :---- | :--------- |\n")
        f.write(f"| Days where **Day High** is made in first 90 mins | {bull['high_in_90min']} | {bull_high_pct:.2f}% (of Bull Days) |\n")
        f.write(f"| ...and Day Closes **BEARISH** (Reversal) | {bull['reversal_bear_close']} | {bull_rev_pct:.2f}% (of above) |\n\n")
        
        # Bear Trend Table
        bear = results['BEAR']
        bear_low_pct = (bear['low_in_90min'] / bear['total_days'] * 100) if bear['total_days'] > 0 else 0
        bear_rev_pct = (bear['reversal_bull_close'] / bear['low_in_90min'] * 100) if bear['low_in_90min'] > 0 else 0
        
        f.write("#### 2. Bear Trend Reversal (Bear Trap)\n")
        f.write(f"Total Bear Trend Days Analyzed: {bear['total_days']}\n\n")
        f.write("| Metric | Count | Percentage |\n")
        f.write("| :----- | :---- | :--------- |\n")
        f.write(f"| Days where **Day Low** is made in first 90 mins | {bear['low_in_90min']} | {bear_low_pct:.2f}% (of Bear Days) |\n")
        f.write(f"| ...and Day Closes **BULLISH** (Reversal) | {bear['reversal_bull_close']} | {bear_rev_pct:.2f}% (of above) |\n\n")
        
        f.write("### Key Insights\n")
        f.write("1. **High/Low Formation:**\n")
        f.write(f"   - In a **Bull Trend**, the Day High is formed in the first 90 minutes about **{bull_high_pct:.0f}%** of the time. This usually indicates a weak trend day or a range-bound day.\n")
        f.write(f"   - In a **Bear Trend**, the Day Low is formed in the first 90 minutes about **{bear_low_pct:.0f}%** of the time.\n")
        f.write("2. **Reversal Probability:**\n")
        f.write(f"   - If the Day High is set early in a **Bull Trend**, there is a **{bull_rev_pct:.1f}%** chance the day will actually collapse and close Red.\n")
        f.write(f"   - If the Day Low is set early in a **Bear Trend**, there is a **{bear_rev_pct:.1f}%** chance the day will rally and close Green.\n")
        f.write("3. **Trading Implication:**\n")
        f.write("   - If the market fails to make a new high (in Bull Trend) after 10:45 AM, exercise caution. However, a full reversal to a red close is not guaranteed (happens roughly half the time when the high is set early).")

    print("Analysis complete. Appended to analysis_mdfiles/30min_opening_patterns_analysis.md")

if __name__ == "__main__":
    analyze_90min_reversal()
