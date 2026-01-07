import pandas as pd
import os

def analyze_market_data(file_path):
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        return f"Error reading CSV: {e}"

    # Clean column names
    df.columns = [c.strip() for c in df.columns]
    
    # Combine Date and Time if strictly needed, but 'date' column seems to have both.
    # Format is 2015-01-09 09:15:00
    try:
        df['datetime'] = pd.to_datetime(df['date'])
    except Exception as e:
        return f"Error parsing dates: {e}"

    df['date_only'] = df['datetime'].dt.date
    df['time_only'] = df['datetime'].dt.time

    results = {
        '3_bull_start': {'total': 0, 'day_bull': 0, 'day_bear': 0},
        '3_bear_start': {'total': 0, 'day_bull': 0, 'day_bear': 0}
    }

    # Group by day
    grouped = df.groupby('date_only')

    for date, group in grouped:
        group = group.sort_values('datetime')
        
        if len(group) < 5: # Skip days with barely any data
            continue

        # Get first 3 bars
        # Assuming 5 min intervals: 09:15, 09:20, 09:25
        # We take the first 3 records regardless of exact time to be robust against missing timestamps,
        # but strictly they should be the opening bars.
        
        first_3_bars = group.iloc[:3]
        
        # Check if they are consecutive (optional, but good for data integrity)
        # For this logic, we just check if they are Bull or Bear.
        
        is_3_bull = all(bar['close'] > bar['open'] for _, bar in first_3_bars.iterrows())
        is_3_bear = all(bar['close'] < bar['open'] for _, bar in first_3_bars.iterrows())

        if not (is_3_bull or is_3_bear):
            continue

        # Determine Day Result
        day_open = group.iloc[0]['open']
        day_close = group.iloc[-1]['close']
        
        day_is_bull = day_close > day_open
        day_is_bear = day_close < day_open # Strictly less

        if is_3_bull:
            results['3_bull_start']['total'] += 1
            if day_is_bull:
                results['3_bull_start']['day_bull'] += 1
            else:
                results['3_bull_start']['day_bear'] += 1
        
        if is_3_bear:
            results['3_bear_start']['total'] += 1
            if day_is_bear:
                results['3_bear_start']['day_bear'] += 1
            else:
                results['3_bear_start']['day_bull'] += 1

    return results

def write_markdown_report(results, output_file):
    
    # Calculate Probabilities
    bull_stats = results['3_bull_start']
    bear_stats = results['3_bear_start']

    prob_bull_after_3bull = (bull_stats['day_bull'] / bull_stats['total'] * 100) if bull_stats['total'] > 0 else 0
    prob_bear_after_3bear = (bear_stats['day_bear'] / bear_stats['total'] * 100) if bear_stats['total'] > 0 else 0

    md_content = f"""# Market Probability Analysis

## Question
**If there are 3 consecutive bull bars in the first 30 minutes (specifically the first 3 bars: 09:15, 09:20, 09:25), what are the chances that the day will close bull? Similarly, if the first 3 bars are bear, what are the chances the day will close bear?**

## Answer

Based on the analysis of the provided data (`../../data/nifty50_minute_complete-5min.csv`):

### Scenario 1: 3 Consecutive Bull Bars at Open
*   **Total Occurrences:** {bull_stats['total']}
*   **Days Closed Bull:** {bull_stats['day_bull']}
*   **Days Closed Bear:** {bull_stats['day_bear']}
*   **Probability of Bull Close:** **{prob_bull_after_3bull:.2f}%**

### Scenario 2: 3 Consecutive Bear Bars at Open
*   **Total Occurrences:** {bear_stats['total']}
*   **Days Closed Bear:** {bear_stats['day_bear']}
*   **Days Closed Bull:** {bear_stats['day_bull']}
*   **Probability of Bear Close:** **{prob_bear_after_3bear:.2f}%**

_Note: The "Day Close" is determined by comparing the opening price of the first bar (09:15) with the closing price of the last available bar of the day._
"""
    
    with open(output_file, 'w') as f:
        f.write(md_content)
    
    print(f"Report generated at {output_file}")
    print(f"Bull Prob: {prob_bull_after_3bull:.2f}%")
    print(f"Bear Prob: {prob_bear_after_3bear:.2f}%")

if __name__ == "__main__":
    file_path = "../../data/nifty50_minute_complete-5min.csv"
    output_path = "gemini_analysis.md"
    
    if os.path.exists(file_path):
        stats = analyze_market_data(file_path)
        if isinstance(stats, dict):
            write_markdown_report(stats, output_path)
        else:
            print(stats)
    else:
        print(f"File not found: {file_path}")
