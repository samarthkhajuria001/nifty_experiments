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

def analyze_3bar_patterns():
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
    
    # Define all 8 patterns
    patterns = [
        'Bull-Bull-Bull',
        'Bull-Bull-Bear',
        'Bull-Bear-Bull',
        'Bear-Bull-Bull',
        'Bull-Bear-Bear',
        'Bear-Bull-Bear',
        'Bear-Bear-Bull',
        'Bear-Bear-Bear'
    ]
    
    # Storage
    stats = {
        'BULL': {p: {'total': 0, 'bull_close': 0, 'bear_close': 0} for p in patterns},
        'BEAR': {p: {'total': 0, 'bull_close': 0, 'bear_close': 0} for p in patterns}
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
            
        # Get first 3 bars
        bars = [group.iloc[0], group.iloc[1], group.iloc[2]]
        
        # Determine types
        types = []
        for b in bars:
            if b['close'] > b['open']:
                types.append('Bull')
            elif b['close'] < b['open']:
                types.append('Bear')
            else:
                types.append('Flat')
                
        if 'Flat' in types:
            continue
            
        pattern_str = "-".join(types)
        
        # Determine Day Outcome
        day_open = group.iloc[0]['open']
        day_close = group.iloc[-1]['close']
        
        day_is_bull = day_close > day_open
        day_is_bear = day_close < day_open
        
        if pattern_str in stats[trend]:
            stats[trend][pattern_str]['total'] += 1
            if day_is_bull:
                stats[trend][pattern_str]['bull_close'] += 1
            elif day_is_bear:
                stats[trend][pattern_str]['bear_close'] += 1
            
    # 3. Append to existing Markdown Report
    print("Appending to analysis file...")
    
    md_file_path = 'analysis_mdfiles/30min_opening_patterns_analysis.md'
    
    with open(md_file_path, 'a') as f:
        f.write("\n\n---\n\n")
        f.write("## Question 3: 3-Bar Pattern Analysis (First 1.5 Hours)\n")
        f.write("**Probability of Day Close Direction based on first 3 bars (09:15, 09:45, 10:15) in Bull and Bear Trends.**\n\n")
        f.write("### Answer\n\n")
        
        # Detailed Tables for both trends
        for trend in ['BULL', 'BEAR']:
            f.write(f"#### {trend} Trend Context\n\n")
            f.write(f"| Pattern (Bar 1-2-3) | Occurrences | Day Closes BULL | Day Closes BEAR | Win Rate |\n")
            f.write(f"| :------------------ | :---------- | :-------------- | :-------------- | :------- |\n")
            
            trend_stats = stats[trend]
            # Sort by Total Occurrences desc
            sorted_patterns = sorted(trend_stats.keys(), key=lambda x: trend_stats[x]['total'], reverse=True)
            
            for pat in sorted_patterns:
                data = trend_stats[pat]
                total = data['total']
                if total == 0:
                    continue
                    
                bull_pct = (data['bull_close'] / total) * 100
                bear_pct = (data['bear_close'] / total) * 100
                
                # Highlight the "Win" condition based on trend
                win_rate = bull_pct if trend == 'BULL' else bear_pct
                win_str = f"**{win_rate:6.2f}%**" if win_rate > 50 else f"{win_rate:6.2f}%"
                
                f.write(f"| {pat:<19} | {total:<11} | {bull_pct:6.2f}%          | {bear_pct:6.2f}%          | {win_str:<8} |\n")
            f.write("\n")
            
        f.write("### Key Insights (3-Bar Patterns)\n")
        f.write("1. **Strongest Continuation Signals:**\n")
        
        # Calculate max signals
        bull_trend_best = max(stats['BULL'].items(), key=lambda x: x[1]['bull_close']/x[1]['total'] if x[1]['total']>0 else 0)
        bear_trend_best = max(stats['BEAR'].items(), key=lambda x: x[1]['bear_close']/x[1]['total'] if x[1]['total']>0 else 0)
        
        bull_win = (bull_trend_best[1]['bull_close']/bull_trend_best[1]['total']*100)
        bear_win = (bear_trend_best[1]['bear_close']/bear_trend_best[1]['total']*100)
        
        f.write(f"   - **Bull Trend:** {bull_trend_best[0]} -> **{bull_win:.1f}%** Bullish Close.\n")
        f.write(f"   - **Bear Trend:** {bear_trend_best[0]} -> **{bear_win:.1f}%** Bearish Close.\n")
        
        f.write("2. **Strongest Reversal Signals:**\n")
        
        # Calculate max reversals
        bull_trend_rev = max(stats['BULL'].items(), key=lambda x: x[1]['bear_close']/x[1]['total'] if x[1]['total']>0 else 0)
        bear_trend_rev = max(stats['BEAR'].items(), key=lambda x: x[1]['bull_close']/x[1]['total'] if x[1]['total']>0 else 0)
        
        bull_rev_win = (bull_trend_rev[1]['bear_close']/bull_trend_rev[1]['total']*100)
        bear_rev_win = (bear_trend_rev[1]['bull_close']/bear_trend_rev[1]['total']*100)
        
        f.write(f"   - **Bull Trend:** {bull_trend_rev[0]} -> **{bull_rev_win:.1f}%** Bearish Close (Trend Failure).\n")
        f.write(f"   - **Bear Trend:** {bear_trend_rev[0]} -> **{bear_rev_win:.1f}%** Bullish Close (Trend Failure).\n")

    print("Analysis complete. Appended to analysis_mdfiles/30min_opening_patterns_analysis.md")

if __name__ == "__main__":
    analyze_3bar_patterns()
