import pandas as pd
import numpy as np
import math

# Read the 2-hour CSV file
df = pd.read_csv('../../data/nifty50_minute_complete-120min.csv')
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_ema(data, period):
    """Calculate Exponential Moving Average"""
    return data.ewm(span=period, adjust=False).mean()

def calculate_slope_degrees(values, lookback=1):
    """Calculate slope in degrees"""
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

def calculate_atr(df, period=14):
    """Calculate Average True Range"""
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())

    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

def calculate_adx(df, period=14):
    """Calculate ADX (Average Directional Index)"""
    # Calculate +DM and -DM
    high_diff = df['high'].diff()
    low_diff = -df['low'].diff()

    plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
    minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)

    # Calculate ATR
    atr = calculate_atr(df, period)

    # Calculate +DI and -DI
    plus_di = 100 * pd.Series(plus_dm).ewm(span=period, adjust=False).mean() / atr
    minus_di = 100 * pd.Series(minus_dm).ewm(span=period, adjust=False).mean() / atr

    # Calculate DX and ADX
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.ewm(span=period, adjust=False).mean()

    return adx, plus_di, minus_di

# ============================================================================
# CALCULATE INDICATORS
# ============================================================================

# EMAs
df['ema11'] = calculate_ema(df['close'], 11)
df['ema21'] = calculate_ema(df['close'], 21)
df['ema50'] = calculate_ema(df['close'], 50)

# EMA 21 slope
df['ema21_slope'] = calculate_slope_degrees(df['ema21'].values, lookback=1)

# ADX
df['adx'], df['plus_di'], df['minus_di'] = calculate_adx(df, period=14)

# Higher Highs and Higher Lows (lookback 5 bars)
df['hh'] = df['high'] > df['high'].shift(5)
df['hl'] = df['low'] > df['low'].shift(5)
df['lh'] = df['high'] < df['high'].shift(5)
df['ll'] = df['low'] < df['low'].shift(5)

# ============================================================================
# TREND IDENTIFICATION METHODS
# ============================================================================

# Method 1: Your Proposed Method - EMA 11 > 21 + Slope > 10 degrees
df['method1_bull'] = (df['ema11'] > df['ema21']) & (df['ema21_slope'] > 10)
df['method1_bear'] = (df['ema11'] < df['ema21']) & (df['ema21_slope'] < -10)

# Method 2: Simple EMA Crossover (11 > 21 for bull, 11 < 21 for bear)
df['method2_bull'] = df['ema11'] > df['ema21']
df['method2_bear'] = df['ema11'] < df['ema21']

# Method 3: Price vs EMA 21 + EMA 21 > EMA 50
df['method3_bull'] = (df['close'] > df['ema21']) & (df['ema21'] > df['ema50'])
df['method3_bear'] = (df['close'] < df['ema21']) & (df['ema21'] < df['ema50'])

# Method 4: ADX Based (ADX > 25 indicates strong trend)
df['method4_bull'] = (df['plus_di'] > df['minus_di']) & (df['adx'] > 25)
df['method4_bear'] = (df['minus_di'] > df['plus_di']) & (df['adx'] > 25)

# Method 5: Higher Highs & Higher Lows
df['method5_bull'] = df['hh'] & df['hl']
df['method5_bear'] = df['lh'] & df['ll']

# Method 6: Combination - EMA + ADX
df['method6_bull'] = (df['ema11'] > df['ema21']) & (df['adx'] > 20) & (df['plus_di'] > df['minus_di'])
df['method6_bear'] = (df['ema11'] < df['ema21']) & (df['adx'] > 20) & (df['minus_di'] > df['plus_di'])

# ============================================================================
# EVALUATE EFFECTIVENESS
# ============================================================================

def evaluate_trend_method(df, bull_col, bear_col, method_name, forward_bars=3):
    """
    Evaluate how well a trend identification method predicts future price movement
    """
    results = {
        'method': method_name,
        'bull_signals': 0,
        'bull_correct': 0,
        'bull_accuracy': 0,
        'bull_avg_return': 0,
        'bear_signals': 0,
        'bear_correct': 0,
        'bear_accuracy': 0,
        'bear_avg_return': 0,
        'total_signals': 0,
        'overall_accuracy': 0
    }

    bull_returns = []
    bear_returns = []

    for i in range(len(df) - forward_bars):
        current_price = df.iloc[i]['close']
        future_price = df.iloc[i + forward_bars]['close']
        price_change_pct = ((future_price - current_price) / current_price) * 100

        # Bull signal
        if df.iloc[i][bull_col]:
            results['bull_signals'] += 1
            bull_returns.append(price_change_pct)
            if price_change_pct > 0:
                results['bull_correct'] += 1

        # Bear signal
        if df.iloc[i][bear_col]:
            results['bear_signals'] += 1
            bear_returns.append(price_change_pct)
            if price_change_pct < 0:
                results['bear_correct'] += 1

    # Calculate statistics
    if results['bull_signals'] > 0:
        results['bull_accuracy'] = (results['bull_correct'] / results['bull_signals']) * 100
        results['bull_avg_return'] = np.mean(bull_returns)

    if results['bear_signals'] > 0:
        results['bear_accuracy'] = (results['bear_correct'] / results['bear_signals']) * 100
        results['bear_avg_return'] = np.mean(bear_returns)

    total_signals = results['bull_signals'] + results['bear_signals']
    total_correct = results['bull_correct'] + results['bear_correct']

    if total_signals > 0:
        results['total_signals'] = total_signals
        results['overall_accuracy'] = (total_correct / total_signals) * 100

    return results

# ============================================================================
# RUN EVALUATION
# ============================================================================

print("=" * 100)
print("TREND IDENTIFICATION METHODS COMPARISON")
print("=" * 100)
print("Forward lookback: 12 bars (24 hours)")
print()

methods = [
    ('method1', 'Your Method: EMA11>21 + Slope>10°'),
    ('method2', 'Simple EMA Crossover (11/21)'),
    ('method3', 'Price vs EMA21 + EMA21>50'),
    ('method4', 'ADX Based (ADX>25)'),
    ('method5', 'Higher Highs & Higher Lows'),
    ('method6', 'Combined: EMA + ADX>20')
]

all_results = []

for method_prefix, method_name in methods:
    bull_col = f'{method_prefix}_bull'
    bear_col = f'{method_prefix}_bear'

    results = evaluate_trend_method(df, bull_col, bear_col, method_name, forward_bars=12)
    all_results.append(results)

    print(f"\n{method_name}")
    print("-" * 100)
    print(f"BULLISH Signals: {results['bull_signals']:4d} | Accuracy: {results['bull_accuracy']:6.2f}% | Avg Return: {results['bull_avg_return']:+6.2f}%")
    print(f"BEARISH Signals: {results['bear_signals']:4d} | Accuracy: {results['bear_accuracy']:6.2f}% | Avg Return: {results['bear_avg_return']:+6.2f}%")
    print(f"OVERALL        : {results['total_signals']:4d} | Accuracy: {results['overall_accuracy']:6.2f}%")

# ============================================================================
# RANKING
# ============================================================================

print("\n" + "=" * 100)
print("RANKING BY OVERALL ACCURACY")
print("=" * 100)

sorted_results = sorted(all_results, key=lambda x: x['overall_accuracy'], reverse=True)

print(f"{'Rank':<6} {'Method':<50} {'Accuracy':<12} {'Signals':<10}")
print("-" * 100)
for i, result in enumerate(sorted_results, 1):
    print(f"{i:<6} {result['method']:<50} {result['overall_accuracy']:6.2f}%     {result['total_signals']:<10}")

print("\n" + "=" * 100)
print("RANKING BY BULL SIGNAL ACCURACY")
print("=" * 100)

sorted_bull = sorted(all_results, key=lambda x: x['bull_accuracy'], reverse=True)

print(f"{'Rank':<6} {'Method':<50} {'Accuracy':<12} {'Avg Return':<12}")
print("-" * 100)
for i, result in enumerate(sorted_bull, 1):
    if result['bull_signals'] > 0:
        print(f"{i:<6} {result['method']:<50} {result['bull_accuracy']:6.2f}%     {result['bull_avg_return']:+6.2f}%")

print("\n" + "=" * 100)
print("RANKING BY BEAR SIGNAL ACCURACY")
print("=" * 100)

sorted_bear = sorted(all_results, key=lambda x: x['bear_accuracy'], reverse=True)

print(f"{'Rank':<6} {'Method':<50} {'Accuracy':<12} {'Avg Return':<12}")
print("-" * 100)
for i, result in enumerate(sorted_bear, 1):
    if result['bear_signals'] > 0:
        print(f"{i:<6} {result['method']:<50} {result['bear_accuracy']:6.2f}%     {result['bear_avg_return']:+6.2f}%")

# ============================================================================
# DETAILED INSIGHTS
# ============================================================================

print("\n" + "=" * 100)
print("KEY INSIGHTS")
print("=" * 100)

best_overall = sorted_results[0]
print(f"\n1. BEST OVERALL METHOD: {best_overall['method']}")
print(f"   - Accuracy: {best_overall['overall_accuracy']:.2f}%")
print(f"   - Total Signals: {best_overall['total_signals']}")

best_bull = sorted_bull[0]
print(f"\n2. BEST FOR BULL TRENDS: {best_bull['method']}")
print(f"   - Accuracy: {best_bull['bull_accuracy']:.2f}%")
print(f"   - Avg Return: {best_bull['bull_avg_return']:+.2f}%")
print(f"   - Signals: {best_bull['bull_signals']}")

best_bear = sorted_bear[0]
print(f"\n3. BEST FOR BEAR TRENDS: {best_bear['method']}")
print(f"   - Accuracy: {best_bear['bear_accuracy']:.2f}%")
print(f"   - Avg Return: {best_bear['bear_avg_return']:+.2f}%")
print(f"   - Signals: {best_bear['bear_signals']}")

print("\n" + "=" * 100)
