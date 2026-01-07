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

def analyze_patterns_and_outcomes():
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
    
    # 2. Load and process 30min data
    print("Loading 30min data for pattern analysis...")
    df_30min = pd.read_csv('../../data/nifty50_minute_2022-30min.csv')
    df_30min['datetime'] = pd.to_datetime(df_30min['date'])
    df_30min['day'] = df_30min['datetime'].dt.date
    
    # Storage for analysis
    # Structure: Trend -> Pattern -> {Total, DayBull, DayBear}
    stats = {
        'BULL': {
            'Bull-Bull': {'total': 0, 'bull_close': 0, 'bear_close': 0},
            'Bear-Bear': {'total': 0, 'bull_close': 0, 'bear_close': 0},
            'Bull-Bear': {'total': 0, 'bull_close': 0, 'bear_close': 0},
            'Bear-Bull': {'total': 0, 'bull_close': 0, 'bear_close': 0},
        },
        'BEAR': {
            'Bull-Bull': {'total': 0, 'bull_close': 0, 'bear_close': 0},
            'Bear-Bear': {'total': 0, 'bull_close': 0, 'bear_close': 0},
            'Bull-Bear': {'total': 0, 'bull_close': 0, 'bear_close': 0},
            'Bear-Bull': {'total': 0, 'bull_close': 0, 'bear_close': 0},
        }
    }
    
    daily_groups = df_30min.groupby('day')
    
    for day, group in daily_groups:
        if day not in daily_trend_map:
            continue
            
        trend = daily_trend_map[day]
        if trend == 'SIDEWAYS':
            continue
            
        group = group.sort_values('datetime')
        if len(group) < 2:
            continue
            
        # Determine Opening Pattern
        bar1 = group.iloc[0]
        bar2 = group.iloc[1]
        
        b1_bull = bar1['close'] > bar1['open']
        b1_bear = bar1['close'] < bar1['open']
        b2_bull = bar2['close'] > bar2['open']
        b2_bear = bar2['close'] < bar2['open']
        
        pattern = None
        if b1_bull and b2_bull:
            pattern = 'Bull-Bull'
        elif b1_bear and b2_bear:
            pattern = 'Bear-Bear'
        elif b1_bull and b2_bear:
            pattern = 'Bull-Bear'
        elif b1_bear and b2_bull:
            pattern = 'Bear-Bull'
        
        if pattern is None:
            continue # Doji/Flat involved
            
        # Determine Day Outcome
        day_open = group.iloc[0]['open']
        day_close = group.iloc[-1]['close']
        
        day_is_bull = day_close > day_open
        day_is_bear = day_close < day_open
        
        stats[trend][pattern]['total'] += 1
        if day_is_bull:
            stats[trend][pattern]['bull_close'] += 1
        elif day_is_bear:
            stats[trend][pattern]['bear_close'] += 1
            
    # 3. Generate Markdown Report
    print("Generating report...")
    
    md_lines = []
    md_lines.append("# 30-Minute Pattern Outcome Analysis")
    md_lines.append("")
    md_lines.append("This analysis breaks down the day's closing direction probability based on the specific sequence of the first two 30-minute bars (09:15 and 09:45) within established 2-hour trends.")
    md_lines.append("")
    
    # Detailed Tables
    for trend in ['BULL', 'BEAR']:
        md_lines.append(f"## {trend} Trend Context")
        md_lines.append(f"| Pattern (Bar 1 - Bar 2) | Occurrences | Day Closes BULL | Day Closes BEAR |")
        md_lines.append(f"| :---------------------- | :---------- | :-------------- | :-------------- |")
        
        trend_stats = stats[trend]
        # Sort for consistent order
        patterns = ['Bull-Bull', 'Bear-Bear', 'Bull-Bear', 'Bear-Bull']
        
        for pat in patterns:
            data = trend_stats[pat]
            total = data['total']
            if total == 0:
                md_lines.append(f"| {pat:<23} | 0           | 0.00%           | 0.00%           |")
                continue
                
            bull_pct = (data['bull_close'] / total) * 100
            bear_pct = (data['bear_close'] / total) * 100
            
            md_lines.append(f"| {pat:<23} | {total:<11} | **{bull_pct:6.2f}%**      | **{bear_pct:6.2f}%**      |")
        md_lines.append("")
        
    # Summary Table
    md_lines.append("## Summary Comparison")
    md_lines.append("")
    md_lines.append("| Pattern | Bull Trend Win Rate (Bull Close) | Bear Trend Win Rate (Bear Close) |")
    md_lines.append("| :------ | :------------------------------- | :------------------------------- |")
    
    patterns = ['Bull-Bull', 'Bear-Bear', 'Bull-Bear', 'Bear-Bull']
    for pat in patterns:
        # Bull Trend Stats
        bull_data = stats['BULL'][pat]
        bull_total = bull_data['total']
        bull_win_rate = (bull_data['bull_close'] / bull_total * 100) if bull_total > 0 else 0
        
        # Bear Trend Stats
        bear_data = stats['BEAR'][pat]
        bear_total = bear_data['total']
        bear_win_rate = (bear_data['bear_close'] / bear_total * 100) if bear_total > 0 else 0
        
        md_lines.append(f"| {pat:<9} | {bull_win_rate:6.2f}% ({bull_total} days)            | {bear_win_rate:6.2f}% ({bear_total} days)            |")
        
    md_lines.append("")
    md_lines.append("### Key Insights")
    md_lines.append("1. **Trend Continuation:**")
    md_lines.append("   - In a **Bull Trend**, a **Bull-Bull** start has the highest probability of a Bull Close.")
    md_lines.append("   - In a **Bear Trend**, a **Bear-Bear** start has the highest probability of a Bear Close.")
    md_lines.append("2. **Reversals:**")
    md_lines.append("   - Look at **Bear-Bear** in a Bull Trend vs **Bull-Bull** in a Bear Trend to see which is more likely to reverse the day.")
    
    with open('30min_pattern_outcomes.md', 'w') as f:
        f.write('\n'.join(md_lines))
        
    print("Analysis complete. Saved to 30min_pattern_outcomes.md")

if __name__ == "__main__":
    analyze_patterns_and_outcomes()
