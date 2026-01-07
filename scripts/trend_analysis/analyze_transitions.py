import pandas as pd
import itertools

# Load the file
df = pd.read_csv('../../data/nifty50_minute_complete-120min.csv')

# map boolean columns to a single state integer
# 1 = Uptrend, -1 = Downtrend, 0 = Neutral (False/False)
def get_state(row):
    if row['uptrend']:
        return 1
    elif row['downtrend']:
        return -1
    else:
        return 0

df['state'] = df.apply(get_state, axis=1)

# Compress the dataframe into a list of "Trend Segments"
# Example: [(-1, 5 bars), (0, 3 bars), (1, 10 bars)]
trend_segments = []
for state, group in itertools.groupby(df['state']):
    segment_len = len(list(group))
    trend_segments.append({'state': state, 'length': segment_len})

# Analyze Transitions
# We specifically look for transitions starting from a Trend (1 or -1) -> Neutral (0) -> Next State
transitions = {
    'From_Down': {'Total': 0, 'To_Up (Reversal)': 0, 'To_Down (Continuation)': 0},
    'From_Up':   {'Total': 0, 'To_Down (Reversal)': 0, 'To_Up (Continuation)': 0}
}

neutral_durations = []

# Iterate through segments (stop before the last one to avoid index error)
for i in range(len(trend_segments) - 2):
    prev_seg = trend_segments[i]
    curr_seg = trend_segments[i+1]
    next_seg = trend_segments[i+2]
    
    # We only care if the current segment is Neutral (0)
    if curr_seg['state'] == 0:
        neutral_durations.append(curr_seg['length'])
        
        # Case 1: Coming from Downtrend
        if prev_seg['state'] == -1:
            transitions['From_Down']['Total'] += 1
            if next_seg['state'] == 1:
                transitions['From_Down']['To_Up (Reversal)'] += 1
            elif next_seg['state'] == -1:
                transitions['From_Down']['To_Down (Continuation)'] += 1
                
        # Case 2: Coming from Uptrend
        elif prev_seg['state'] == 1:
            transitions['From_Up']['Total'] += 1
            if next_seg['state'] == -1:
                transitions['From_Up']['To_Down (Reversal)'] += 1
            elif next_seg['state'] == 1:
                transitions['From_Up']['To_Up (Continuation)'] += 1

# Output Analysis
avg_neutral = sum(neutral_durations)/len(neutral_durations) if neutral_durations else 0

print("--- ANALYSIS OF FALSE/FALSE (NEUTRAL) ZONES ---")
print(f"Total Neutral Zones Analyzed: {len(neutral_durations)}")
print(f"Average Duration of Neutral Zone: {avg_neutral:.2f} bars (approx {avg_neutral * 2:.1f} hours)\n")

print("1. WHEN MARKET IS IN DOWNTREND (-1) AND GOES NEUTRAL (0):")
d_total = transitions['From_Down']['Total']
d_rev = transitions['From_Down']['To_Up (Reversal)']
d_cont = transitions['From_Down']['To_Down (Continuation)']
print(f"   - It Reversed to UPTREND: {d_rev} times ({d_rev/d_total*100:.2f}%)")
print(f"   - It Continued DOWNTREND: {d_cont} times ({d_cont/d_total*100:.2f}%)")

print("\n2. WHEN MARKET IS IN UPTREND (1) AND GOES NEUTRAL (0):")
u_total = transitions['From_Up']['Total']
u_rev = transitions['From_Up']['To_Down (Reversal)']
u_cont = transitions['From_Up']['To_Up (Continuation)']
print(f"   - It Reversed to DOWNTREND: {u_rev} times ({u_rev/u_total*100:.2f}%)")
print(f"   - It Continued UPTREND: {u_cont} times ({u_cont/u_total*100:.2f}%)")