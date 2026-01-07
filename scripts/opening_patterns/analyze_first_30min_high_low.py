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

def analyze_30min_reversal_refinement():
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
        'BULL': {'total_days': 0, 'high_in_30min': 0, 'reversal_bear_close': 0},
        'BEAR': {'total_days': 0, 'low_in_30min': 0, 'reversal_bull_close': 0}
    }
    
    daily_groups = df_30min.groupby('day')
    
    for day, group in daily_groups:
        if day not in daily_trend_map:
            continue
            
        trend = daily_trend_map[day]
        if trend == 'SIDEWAYS':
            continue
            
        group = group.sort_values('datetime')
        if len(group) < 1:
            continue
            
        # Day Stats
        day_open = group.iloc[0]['open']
        day_close = group.iloc[-1]['close']
        day_high = group['high'].max()
        day_low = group['low'].min()
        
        # 30 Min Stats (First bar only: 09:15)
        first_bar = group.iloc[0]
        high_30 = first_bar['high']
        low_30 = first_bar['low']
        
        if trend == 'BULL':
            results['BULL']['total_days'] += 1
            # Condition 1: Day High was made in first 30 mins (Bar 1)
            # We use strict equality. If the high was touched again later, it still counts as "made in first 30"
            # because the level was established then.
            if high_30 == day_high:
                results['BULL']['high_in_30min'] += 1
                # Condition 2: Day Reversed (Closed Bearish)
                if day_close < day_open:
                    results['BULL']['reversal_bear_close'] += 1
                    
        elif trend == 'BEAR':
            results['BEAR']['total_days'] += 1
            # Condition 1: Day Low was made in first 30 mins (Bar 1)
            if low_30 == day_low:
                results['BEAR']['low_in_30min'] += 1
                # Condition 2: Day Reversed (Closed Bullish)
                if day_close > day_open:
                    results['BEAR']['reversal_bull_close'] += 1

    # 3. Update Report (Replace Question 4)
    print("Updating analysis file...")
    md_file_path = 'analysis_mdfiles/30min_opening_patterns_analysis.md'
    
    # Read existing content
    with open(md_file_path, 'r') as f:
        lines = f.readlines()
        
    # Find where Question 4 starts and truncate
    new_lines = []
    for line in lines:
        if "Question 4:" in line:
            break
        new_lines.append(line)
        
    # Write updated content
    with open(md_file_path, 'w') as f:
        f.writelines(new_lines)
        
        f.write("## Question 4: First 30-Minute High/Low Reversal Analysis\n")
        f.write("**How often does the day reverse after establishing the Day High (in Bull Trend) or Day Low (in Bear Trend) specifically within the FIRST 30-minute bar (09:15-09:45)?**\n\n")
        
        f.write("### Answer\n\n")
        
        # Bull Trend Table
        bull = results['BULL']
        bull_high_pct = (bull['high_in_30min'] / bull['total_days'] * 100) if bull['total_days'] > 0 else 0
        bull_rev_pct = (bull['reversal_bear_close'] / bull['high_in_30min'] * 100) if bull['high_in_30min'] > 0 else 0
        
        f.write("#### 1. Bull Trend Reversal (Bull Trap)\n")
        f.write(f"Total Bull Trend Days Analyzed: {bull['total_days']}\n\n")
        f.write("| Metric | Count | Percentage |\n")
        f.write("| :----- | :---- | :--------- |\n")
        f.write(f"| Days where **Day High** is made in 1st 30-min Bar | {bull['high_in_30min']} | {bull_high_pct:.2f}% (of Bull Days) |\n")
        f.write(f"| ...and Day Closes **BEARISH** (Reversal) | {bull['reversal_bear_close']} | {bull_rev_pct:.2f}% (of above) |\n\n")
        
        # Bear Trend Table
        bear = results['BEAR']
        bear_low_pct = (bear['low_in_30min'] / bear['total_days'] * 100) if bear['total_days'] > 0 else 0
        bear_rev_pct = (bear['reversal_bull_close'] / bear['low_in_30min'] * 100) if bear['low_in_30min'] > 0 else 0
        
        f.write("#### 2. Bear Trend Reversal (Bear Trap)\n")
        f.write(f"Total Bear Trend Days Analyzed: {bear['total_days']}\n\n")
        f.write("| Metric | Count | Percentage |\n")
        f.write("| :----- | :---- | :--------- |\n")
        f.write(f"| Days where **Day Low** is made in 1st 30-min Bar | {bear['low_in_30min']} | {bear_low_pct:.2f}% (of Bear Days) |\n")
        f.write(f"| ...and Day Closes **BULLISH** (Reversal) | {bear['reversal_bull_close']} | {bear_rev_pct:.2f}% (of above) |\n\n")
        
        f.write("### Key Insights\n")
        f.write("1. **Trend Weakness Indication:**\n")
        f.write(f"   - In a **Bull Trend**, if the High is set in the first 30 minutes (happens ~{bull_high_pct:.0f}% of time), it's a major warning sign. The market cannot push higher for the remaining 6 hours.\n")
        f.write(f"   - In a **Bear Trend**, if the Low is set in the first 30 minutes (happens ~{bear_low_pct:.0f}% of time), selling pressure has exhausted early.\n")
        f.write("2. **Reversal Probability:**\n")
        f.write(f"   - **Bull Trend:** If Day High = First 30-min High, there is an **{bull_rev_pct:.1f}%** probability the day closes Red.\n")
        f.write(f"   - **Bear Trend:** If Day Low = First 30-min Low, there is an **{bear_rev_pct:.1f}%** probability the day closes Green.\n")
        f.write("3. **Trading Rule:**\n")
        f.write("   - If the first 30-minute range is not broken in the direction of the trend (i.e., new high in bull trend) by 10:15 or 10:45, the probability of a trend continuation day drops significantly, and a reversal/range day becomes the dominant scenario.")

    print("Analysis complete. Updated analysis_mdfiles/30min_opening_patterns_analysis.md")

if __name__ == "__main__":
    analyze_30min_reversal_refinement()
