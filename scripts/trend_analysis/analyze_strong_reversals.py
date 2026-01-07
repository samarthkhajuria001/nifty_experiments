import pandas as pd
import itertools

# Load the file
df = pd.read_csv('../../data/nifty50_minute_complete-120min.csv')

def get_state(row):
    if row['uptrend']:
        return 1
    elif row['downtrend']:
        return -1
    else:
        return 0

df['state'] = df.apply(get_state, axis=1)

# Compress into segments
trend_segments = []
for state, group in itertools.groupby(df['state']):
    segment_len = len(list(group))
    trend_segments.append({'state': state, 'length': segment_len})

# Define "Strong Trend" threshold (5 days * 4 bars/day = 20 bars)
STRONG_TREND_LEN = 20

transitions = {
    'From_Strong_Down': {'Total': 0, 'To_Up (Reversal)': 0, 'To_Down (Continuation)': 0},
    'From_Strong_Up':   {'Total': 0, 'To_Down (Reversal)': 0, 'To_Up (Continuation)': 0}
}

filtered_neutral_durations = []

for i in range(len(trend_segments) - 2):
    prev_seg = trend_segments[i]
    curr_seg = trend_segments[i+1]
    next_seg = trend_segments[i+2]
    
    # We only analyze if we are in a Neutral Zone
    if curr_seg['state'] == 0:
        
        # Check if the PREVIOUS trend was "Strong"
        if prev_seg['length'] >= STRONG_TREND_LEN:
            filtered_neutral_durations.append(curr_seg['length'])
            
            # Case 1: Strong Downtrend -> Neutral -> ?
            if prev_seg['state'] == -1:
                transitions['From_Strong_Down']['Total'] += 1
                if next_seg['state'] == 1:
                    transitions['From_Strong_Down']['To_Up (Reversal)'] += 1
                elif next_seg['state'] == -1:
                    transitions['From_Strong_Down']['To_Down (Continuation)'] += 1
            
            # Case 2: Strong Uptrend -> Neutral -> ?
            elif prev_seg['state'] == 1:
                transitions['From_Strong_Up']['Total'] += 1
                if next_seg['state'] == -1:
                    transitions['From_Strong_Up']['To_Down (Reversal)'] += 1
                elif next_seg['state'] == 1:
                    transitions['From_Strong_Up']['To_Up (Continuation)'] += 1

# Output
print(f"--- ANALYSIS OF NEUTRAL ZONES AFTER STRONG TRENDS (> {STRONG_TREND_LEN} bars / 5 days) ---")
avg_dur = sum(filtered_neutral_durations)/len(filtered_neutral_durations) if filtered_neutral_durations else 0
print(f"Count of such events: {len(filtered_neutral_durations)}")
print(f"Average Neutral Duration: {avg_dur:.2f} bars\n")

print("1. AFTER STRONG DOWNTREND -> NEUTRAL:")
sd_total = transitions['From_Strong_Down']['Total']
if sd_total > 0:
    sd_rev = transitions['From_Strong_Down']['To_Up (Reversal)']
    sd_cont = transitions['From_Strong_Down']['To_Down (Continuation)']
    print(f"   - Reversal to UPTREND: {sd_rev} ({sd_rev/sd_total*100:.2f}%)")
    print(f"   - Continuation of DOWN: {sd_cont} ({sd_cont/sd_total*100:.2f}%)")
else:
    print("   - No events found.")

print("\n2. AFTER STRONG UPTREND -> NEUTRAL:")
su_total = transitions['From_Strong_Up']['Total']
if su_total > 0:
    su_rev = transitions['From_Strong_Up']['To_Down (Reversal)']
    su_cont = transitions['From_Strong_Up']['To_Up (Continuation)']
    print(f"   - Reversal to DOWNTREND: {su_rev} ({su_rev/su_total*100:.2f}%)")
    print(f"   - Continuation of UP: {su_cont} ({su_cont/su_total*100:.2f}%)")
else:
    print("   - No events found.")
