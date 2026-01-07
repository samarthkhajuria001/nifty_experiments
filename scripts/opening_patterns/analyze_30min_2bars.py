import pandas as pd
import os

def analyze_30min_patterns():
    # Load the data
    file_path = '../../data/nifty50_minute_2022-30min.csv'
    df = pd.read_csv(file_path)
    
    # Parse date column
    df['datetime'] = pd.to_datetime(df['date'])
    df['day'] = df['datetime'].dt.date
    
    # Group by day
    daily_groups = df.groupby('day')
    
    two_bulls = []
    two_bears = []
    opposite = []
    other = [] # For cases where one might be flat/doji
    
    for day, group in daily_groups:
        # Sort by time just in case
        group = group.sort_values('datetime')
        
        # We need at least 2 bars
        if len(group) < 2:
            continue
            
        bar1 = group.iloc[0]
        bar2 = group.iloc[1]
        
        # Define bullish/bearish
        # Using strict inequality, so flat is treated as neither (will go to 'opposite' logic check or 'other')
        b1_bull = bar1['close'] > bar1['open']
        b1_bear = bar1['close'] < bar1['open']
        
        b2_bull = bar2['close'] > bar2['open']
        b2_bear = bar2['close'] < bar2['open']
        
        date_str = str(day)
        
        if b1_bull and b2_bull:
            two_bulls.append(date_str)
        elif b1_bear and b2_bear:
            two_bears.append(date_str)
        elif (b1_bull and b2_bear) or (b1_bear and b2_bull):
            opposite.append(date_str)
        else:
            # Contains a flat/doji bar
            other.append(date_str)
            
    # Output results
    print(f"Total Days Analyzed: {len(daily_groups)}")
    print("-" * 30)
    print(f"2 Bull Bars: {len(two_bulls)} days ({len(two_bulls)/len(daily_groups):.2%})")
    print(f"2 Bear Bars: {len(two_bears)} days ({len(two_bears)/len(daily_groups):.2%})")
    print(f"Opposite:    {len(opposite)} days ({len(opposite)/len(daily_groups):.2%})")
    print(f"Other (Doji): {len(other)} days ({len(other)/len(daily_groups):.2%})")
    
    # Save lists to files for inspection
    os.makedirs('output', exist_ok=True)
    
    pd.DataFrame({'date': two_bulls}).to_csv('output/30min_2bulls.csv', index=False)
    pd.DataFrame({'date': two_bears}).to_csv('output/30min_2bears.csv', index=False)
    pd.DataFrame({'date': opposite}).to_csv('output/30min_opposite.csv', index=False)

if __name__ == "__main__":
    analyze_30min_patterns()
