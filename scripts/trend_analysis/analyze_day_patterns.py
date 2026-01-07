import pandas as pd
import numpy as np
import math

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

def is_strong_bear_candle(candle, max_wick_pct=0.30):
    """Check if candle is strong bear (lower wick < 10% of total candle)"""
    total_range = candle['high'] - candle['low']
    if total_range == 0:
        return False

    # For bear candle: close < open
    # Lower wick = close - low
    is_bear = candle['close'] < candle['open']
    if not is_bear:
        return False

    lower_wick = candle['close'] - candle['low']
    wick_pct = lower_wick / total_range

    return wick_pct <= max_wick_pct

def find_plateau(prices, start_idx, min_bars=6, max_range_pct=0.005):
    """
    Find if there's a plateau (consolidation) after start_idx
    min_bars: minimum bars for plateau (default 6 = 30 min)
    max_range_pct: max range as % of price (default 0.5%)
    """
    if start_idx + min_bars >= len(prices):
        return False, 0, 0

    for length in range(min_bars, min(len(prices) - start_idx, 24)):  # Check up to 2 hours
        segment = prices[start_idx:start_idx + length]
        price_range = segment.max() - segment.min()
        avg_price = segment.mean()
        range_pct = price_range / avg_price

        if range_pct <= max_range_pct:
            return True, start_idx, start_idx + length

    return False, 0, 0

def classify_day_pattern(day_data):
    """
    Classify day into one of 6 patterns:
    1. Early Bounce Fade
    2. Bounce → Plateau → Fall
    3. Grind → Grind → Grind
    4. Delayed Bounce
    5. Deep V Reversal
    6. Opening Drive Rejection
    """
    highs = day_data['high'].values
    lows = day_data['low'].values
    closes = day_data['close'].values

    # Find when high of day is set
    day_high = highs.max()
    high_bar = np.where(highs == day_high)[0][0]

    # Find when low of day is set
    day_low = lows.min()
    low_bar = np.where(lows == day_low)[0][0]

    opening_price = day_data.iloc[0]['open']

    # Case 6: Opening Drive Rejection (high in first 1-2 bars)
    if high_bar <= 2:
        return "Case 6: Opening Drive Rejection", high_bar, low_bar

    # Case 1 or 2: High set in first 10 bars (50 min)
    if high_bar < 10:
        # Check for plateau after high
        has_plateau, plat_start, plat_end = find_plateau(closes, high_bar + 1)

        if has_plateau:
            return "Case 2: Bounce → Plateau → Fall", high_bar, low_bar
        else:
            return "Case 1: Early Bounce Fade", high_bar, low_bar

    # Case 3: Grind (high near opening price, no significant bounce)
    if abs(day_high - opening_price) / opening_price < 0.002:  # Less than 0.2% bounce
        return "Case 3: Grind → Grind → Grind", high_bar, low_bar

    # Case 4: Delayed Bounce (high set around bar 30-50)
    if 25 <= high_bar <= 55:
        return "Case 4: Delayed Bounce", high_bar, low_bar

    # Case 5: Deep V Reversal (high set very late, after bar 50)
    if high_bar > 55:
        return "Case 5: Deep V Reversal", high_bar, low_bar

    # Default: Early Bounce Fade
    return "Case 1: Early Bounce Fade", high_bar, low_bar

# Read 2hr data
df_2hr = pd.read_csv('../../data/nifty50_minute_complete-120min.csv')
df_2hr['date'] = pd.to_datetime(df_2hr['date'])
df_2hr = df_2hr.sort_values('date').reset_index(drop=True)

df_2hr['ema11'] = calculate_ema(df_2hr['close'], 11)
df_2hr['ema21'] = calculate_ema(df_2hr['close'], 21)
df_2hr['ema21_slope'] = calculate_slope_degrees(df_2hr['ema21'].values, lookback=1)

df_2hr['is_bull_trend'] = (df_2hr['ema11'] > df_2hr['ema21']) & (df_2hr['ema21_slope'] > 10)
df_2hr['is_bear_trend'] = (df_2hr['ema11'] < df_2hr['ema21']) & (df_2hr['ema21_slope'] < -10)

df_2hr['trading_date'] = df_2hr['date'].dt.date

daily_trend = df_2hr[df_2hr['date'].dt.time == pd.to_datetime('09:15:00').time()][['trading_date', 'is_bull_trend', 'is_bear_trend']].copy()

# Read 5min data
df_5min = pd.read_csv('../../data/nifty50_minute_complete-5min.csv')
df_5min['date'] = pd.to_datetime(df_5min['date'])
df_5min['trading_date'] = df_5min['date'].dt.date
df_5min['time'] = df_5min['date'].dt.time

# Get previous day close for gap
daily_data = df_5min.groupby('trading_date').agg({
    'open': 'first',
    'close': 'last'
}).reset_index()
daily_data['prev_close'] = daily_data['close'].shift(1)
daily_data['gap_down'] = daily_data['open'] < daily_data['prev_close']

results = []
debug_counts = {'total': 0, 'bear_trend': 0, 'gap_down': 0, 'strong_bear': 0}

for trading_date, day_data in df_5min.groupby('trading_date'):
    debug_counts['total'] += 1

    # Get gap info
    gap_info = daily_data[daily_data['trading_date'] == trading_date]
    if len(gap_info) == 0 or pd.isna(gap_info.iloc[0]['prev_close']):
        continue

    is_gap_down = gap_info.iloc[0]['gap_down']

    # Get 2hr trend
    trend_info = daily_trend[daily_trend['trading_date'] == trading_date]
    if len(trend_info) == 0:
        continue

    is_2hr_bear = trend_info.iloc[0]['is_bear_trend']

    if is_2hr_bear:
        debug_counts['bear_trend'] += 1

    if is_gap_down:
        debug_counts['gap_down'] += 1

    # Filter: Only bear trend + gap down
    if not (is_2hr_bear and is_gap_down):
        continue

    # Check first bar is strong bear
    first_bar = day_data.iloc[0]
    if not is_strong_bear_candle(first_bar):
        continue

    debug_counts['strong_bear'] += 1

    # Classify the day pattern
    pattern, high_bar, low_bar = classify_day_pattern(day_data.reset_index(drop=True))

    # Calculate stats
    day_high = day_data['high'].max()
    day_low = day_data['low'].min()
    day_open = day_data.iloc[0]['open']
    day_close = day_data.iloc[-1]['close']
    day_range = day_high - day_low

    results.append({
        'date': trading_date,
        'pattern': pattern,
        'high_bar': high_bar,
        'low_bar': low_bar,
        'day_open': day_open,
        'day_high': day_high,
        'day_low': day_low,
        'day_close': day_close,
        'day_range': day_range,
        'high_from_open_pct': (day_high - day_open) / day_open * 100,
        'close_from_open_pct': (day_close - day_open) / day_open * 100
    })

results_df = pd.DataFrame(results)

print("=" * 100)
print("DAY PATTERN ANALYSIS: BEAR TREND + GAP DOWN + STRONG BEAR FIRST BAR")
print("=" * 100)
print(f"\nDEBUG FILTER COUNTS:")
print(f"Total days: {debug_counts['total']}")
print(f"Bear trend days: {debug_counts['bear_trend']}")
print(f"Gap down days: {debug_counts['gap_down']}")
print(f"Strong bear first bar days: {debug_counts['strong_bear']}")
print(f"\nTotal qualifying days: {len(results_df)}")
print()

if len(results_df) == 0:
    print("No qualifying days found. Filters may be too strict.")
    print("Try loosening the 'strong bear' criteria or checking data quality.")
    exit()

# Count each pattern
pattern_counts = results_df['pattern'].value_counts().sort_index()

print("PATTERN BREAKDOWN:")
print("-" * 100)
for pattern, count in pattern_counts.items():
    pct = count / len(results_df) * 100
    print(f"{pattern:<40} {count:3d} days ({pct:5.2f}%)")

print()
print("=" * 100)
print("DETAILED STATISTICS BY PATTERN")
print("=" * 100)

for pattern in sorted(pattern_counts.index):
    pattern_data = results_df[results_df['pattern'] == pattern]

    print(f"\n{pattern}")
    print("-" * 100)
    print(f"Count: {len(pattern_data)} days")
    print(f"Avg High Bar: {pattern_data['high_bar'].mean():.1f} (Bar {pattern_data['high_bar'].median():.0f} median)")
    print(f"Avg Low Bar: {pattern_data['low_bar'].mean():.1f} (Bar {pattern_data['low_bar'].median():.0f} median)")
    print(f"Avg Bounce from Open: {pattern_data['high_from_open_pct'].mean():+.3f}%")
    print(f"Avg Day Return: {pattern_data['close_from_open_pct'].mean():+.3f}%")
    print(f"Avg Day Range: {pattern_data['day_range'].mean():.2f} points")

print()
print("=" * 100)
print("KEY INSIGHTS")
print("=" * 100)

# Most common pattern
most_common = pattern_counts.idxmax()
most_common_pct = pattern_counts.max() / len(results_df) * 100
print(f"\n1. Most Common Pattern: {most_common}")
print(f"   Occurs {pattern_counts.max()} times ({most_common_pct:.1f}% of days)")

# Pattern with plateau
plateau_pattern = results_df[results_df['pattern'] == 'Case 2: Bounce → Plateau → Fall']
if len(plateau_pattern) > 0:
    print(f"\n2. Bounce → Plateau → Fall Pattern:")
    print(f"   Occurs {len(plateau_pattern)} times ({len(plateau_pattern)/len(results_df)*100:.1f}% of days)")
    print(f"   Avg High Bar: {plateau_pattern['high_bar'].mean():.1f}")
    print(f"   These are the days that bounce early, consolidate, then fall")

# Early vs Late high
early_high = results_df[results_df['high_bar'] < 10]
late_high = results_df[results_df['high_bar'] >= 10]
print(f"\n3. Early High (< 50 min): {len(early_high)} days ({len(early_high)/len(results_df)*100:.1f}%)")
print(f"   Late High (>= 50 min): {len(late_high)} days ({len(late_high)/len(results_df)*100:.1f}%)")

# Grind days
grind_days = results_df[results_df['pattern'] == 'Case 3: Grind → Grind → Grind']
if len(grind_days) > 0:
    print(f"\n4. Pure Grind Days: {len(grind_days)} ({len(grind_days)/len(results_df)*100:.1f}%)")
    print(f"   Avg Return: {grind_days['close_from_open_pct'].mean():+.3f}%")
    print(f"   These are the most bearish - no bounce at all")

print()
print("=" * 100)
