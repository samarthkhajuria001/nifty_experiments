# Nifty 50 Opening Pattern Analysis (30-Minute Timeframe)

This document consolidates statistical analysis regarding the opening 1 hour of trading (first two 30-minute bars) and its relationship with the daily closing direction, filtered by the prevailing 2-hour trend.

---

## Question 1: Frequency of Opening Patterns by Trend
In the 30-minute timeframe, what are the days where the first 2 bars are bullish, first 2 bars are bearish, and opposite (bull/bear or bear/bull)? Analyze this separately for Bull Trends and Bear Trends (defined on 2-hour timeframe).

### Answer

Based on the analysis of 1,967 trading days, we categorized the opening 1 hour (09:15-10:15) into three patterns:
1.  2 Bull Bars: Both 09:15 and 09:45 bars are bullish.
2.  2 Bear Bars: Both 09:15 and 09:45 bars are bearish.
3.  Opposite: Mixed signals (one bull, one bear).

#### Detailed Breakdown by 2-Hour Trend

1. Bull Trend Days (Total: 1,023)

| Opening Pattern (First 1 Hour) | Days Count | Percentage | Insight |
| :----------------------------- | :--------- | :--------- | :----------------------------------------------------------------- |
| 2 Bull Bars                | 300    | 29.33% | Bullish Momentum: Strong opening aligned with trend.           |
| 2 Bear Bars                | 219        | 21.41%     | Counter-Trend Start: Potential dip buying opportunity or warning. |
| Opposite                   | 501        | 48.97%     | Mixed/Choppy: No clear immediate direction.                    |

2. Bear Trend Days (Total: 599)

| Opening Pattern (First 1 Hour) | Days Count | Percentage | Insight |
| :----------------------------- | :--------- | :--------- | :------------------------------------------------------------- |
| 2 Bull Bars                | 76         | 12.69%     | Counter-Trend Start: Rare. Potential short squeeze or failed breakdown. |
| 2 Bear Bars                | 214    | 35.73% | Bearish Momentum: Very strong confirmation of downtrend.   |
| Opposite                   | 306        | 51.09%     | Mixed/Choppy: No clear immediate direction.                |

#### Summary Table (Question 1)

| Pattern         | All Days | Bull Trend | Bear Trend |
| :-------------- | :------- | :--------- | :--------- |
| 2 Bull Bars | 23.49%   | 29.33% | 12.69%     |
| 2 Bear Bars | 27.66%   | 21.41%     | 35.73% |
| Opposite    | 48.50%   | 48.97%     | 51.09%     |

---

## Question 2: Day Close Probability by Pattern & Trend
In a Bull Trend, if both first bars are bull, what is the probability the day closes Bull or Bear? Similarly for Bear Trend and mixed patterns (Bull-Bear, Bear-Bull).

### Answer

This analysis looks at the predictive power of the first two 30-minute bars for the rest of the day.

#### 1. Bull Trend Context
*When the 2-hour trend is UP:*

| Pattern (Bar 1 - Bar 2) | Occurrences | Day Closes BULL | Day Closes BEAR |
| :---------------------- | :---------- | :-------------- | :-------------- |
| Bull-Bull           | 300         | 76.00%      | 24.00%          |
| Bear-Bear           | 219         | 24.20%          | 75.80%      |
| Bull-Bear           | 214         | 52.80%      | 47.20%          |
| Bear-Bull           | 287         | 44.25%          | 55.75%      |

Insight:
*   Bull-Bull is a high-probability continuation signal (76% win rate).
*   Bear-Bear is a high-probability reversal signal. If a Bull Trend starts with 2 Bear bars, it has a 75.8% chance of failing and closing Red.

#### 2. Bear Trend Context
*When the 2-hour trend is DOWN:*

| Pattern (Bar 1 - Bar 2) | Occurrences | Day Closes BULL | Day Closes BEAR |
| :---------------------- | :---------- | :-------------- | :-------------- |
| Bull-Bull           | 76          | 73.68%      | 26.32%          |
| Bear-Bear           | 214         | 23.83%          | 76.17%      |
| Bull-Bear           | 116         | 55.17%      | 44.83%          |
| Bear-Bull           | 190         | 36.84%          | 63.16%      |

Insight:
*   Bear-Bear is a high-probability continuation signal (76% win rate).
*   Bull-Bull is a high-probability reversal signal. If a Bear Trend starts with 2 Bull bars, it has a 73.7% chance of failing and closing Green.

#### Summary Table (Question 2)

| Opening Pattern | Bull Trend Win Rate (Bull Close) | Bear Trend Win Rate (Bear Close) |
| :-------------- | :------------------------------- | :------------------------------- |
| Bull-Bull   | 76.00% (Strong Continuation) | 26.32% (Trend Fails)             |
| Bear-Bear   | 24.20% (Trend Fails)             | 76.17% (Strong Continuation) |
| Bull-Bear   | 52.80% (Neutral/Coin Flip)       | 44.83% (Neutral)                 |
| Bear-Bull   | 44.25% (Slight Bearish Bias)     | 63.16% (Moderate Bias)       |

### Key Takeaway
Intraday Momentum Trumps Higher Timeframe Trend.
Regardless of the 2-hour trend, if the first hour (2 bars) is strongly one-sided (Bull-Bull or Bear-Bear), the day has a ~75% chance of closing in that same direction, even if it means reversing the major trend.


---

## Question 3: 3-Bar Pattern Analysis (First 1.5 Hours)
Probability of Day Close Direction based on first 3 bars (09:15, 09:45, 10:15) in Bull and Bear Trends.

### Answer

#### BULL Trend Context

| Pattern (Bar 1-2-3) | Occurrences | Day Closes BULL | Day Closes BEAR |
| :------------------ | :---------- | :-------------- | :-------------- |
| Bear-Bull-Bull      | 152         |  52.63%          |  47.37%          |
| Bull-Bull-Bull      | 151         |  79.47%          |  20.53%          |
| Bull-Bull-Bear      | 148         |  72.30%          |  27.70%          |
| Bear-Bull-Bear      | 134         |  34.33%          |  65.67%          |
| Bear-Bear-Bull      | 113         |  27.43%          |  72.57%          |
| Bull-Bear-Bull      | 108         |  61.11%          |  38.89%          |
| Bull-Bear-Bear      | 105         |  43.81%          |  56.19%          |
| Bear-Bear-Bear      | 105         |  20.95%          |  79.05%          |

#### BEAR Trend Context

| Pattern (Bar 1-2-3) | Occurrences | Day Closes BULL | Day Closes BEAR |
| :------------------ | :---------- | :-------------- | :-------------- |
| Bear-Bull-Bear      | 111         |  29.73%          |  70.27%          |
| Bear-Bear-Bear      | 110         |  15.45%          |  84.55%          |
| Bear-Bear-Bull      | 104         |  32.69%          |  67.31%          |
| Bear-Bull-Bull      | 77          |  48.05%          |  51.95%          |
| Bull-Bear-Bear      | 59          |  45.76%          |  54.24%          |
| Bull-Bear-Bull      | 57          |  64.91%          |  35.09%          |
| Bull-Bull-Bear      | 45          |  66.67%          |  33.33%          |
| Bull-Bull-Bull      | 30          |  83.33%          |  16.67%          |

### Key Insights (3-Bar Patterns)
1. Strongest Continuation Signals:
   - Bull Trend: Bull-Bull-Bull -> 79.5% Bullish Close.
   - Bear Trend: Bear-Bear-Bear -> 84.5% Bearish Close.
2. Strongest Reversal Signals:
   - Bull Trend: Bear-Bear-Bear -> 79.0% Bearish Close (Trend Failure).
   - Bear Trend: Bull-Bull-Bull -> 83.3% Bullish Close (Trend Failure).


---

## Question 4: First 30-Minute High/Low Reversal Analysis
**How often does the day reverse after establishing the Day High (in Bull Trend) or Day Low (in Bear Trend) specifically within the FIRST 30-minute bar (09:15-09:45)?**

### Answer

#### 1. Bull Trend Reversal (Bull Trap)
Total Bull Trend Days Analyzed: 1023

| Metric | Count | Percentage |
| :----- | :---- | :--------- |
| Days where **Day High** is made in 1st 30-min Bar | 302 | 29.52% (of Bull Days) |
| ...and Day Closes **BEARISH** (Reversal) | 282 | 93.38% (of above) |

#### 2. Bear Trend Reversal (Bear Trap)
Total Bear Trend Days Analyzed: 599

| Metric | Count | Percentage |
| :----- | :---- | :--------- |
| Days where **Day Low** is made in 1st 30-min Bar | 126 | 21.04% (of Bear Days) |
| ...and Day Closes **BULLISH** (Reversal) | 113 | 89.68% (of above) |

### Key Insights
1. **Trend Weakness Indication:**
   - In a **Bull Trend**, if the High is set in the first 30 minutes (happens ~30% of time), it's a major warning sign. The market cannot push higher for the remaining 6 hours.
   - In a **Bear Trend**, if the Low is set in the first 30 minutes (happens ~21% of time), selling pressure has exhausted early.
2. **Reversal Probability:**
   - **Bull Trend:** If Day High = First 30-min High, there is an **93.4%** probability the day closes Red.
   - **Bear Trend:** If Day Low = First 30-min Low, there is an **89.7%** probability the day closes Green.
3. **Trading Rule:**
   - If the first 30-minute range is not broken in the direction of the trend (i.e., new high in bull trend) by 10:15 or 10:45, the probability of a trend continuation day drops significantly, and a reversal/range day becomes the dominant scenario.

---

## Question 5: Mid-Morning High/Low Analysis (Bars 15-19)
What happens when the Day High (in Bull Trend) or Day Low (in Bear Trend) is established exactly between the 15th and 19th 5-minute bars (approx. 10:25 AM - 10:50 AM)?

### Answer

#### 1. Bull Trend Context
Total Bull Trend Days: 1287

| Metric | Count | Percentage |
| :----- | :---- | :--------- |
| Days High set between Bars 15-19 | 62 | 4.82% |
| ...and Day Closes BEARISH | 37 | 59.68% |

#### 2. Bear Trend Context
Total Bear Trend Days: 765

| Metric | Count | Percentage |
| :----- | :---- | :--------- |
| Days Low set between Bars 15-19 | 34 | 4.44% |
| ...and Day Closes BULLISH | 22 | 64.71% |

### Key Insights
1. Rarity: This specific timing for a Day High/Low is relatively rare (~3-4% of days).
2. Reversal Potential:
   - Bull Trend: If the high is set in this window (10:25-10:50 AM), there is a 59.7% chance of a reversal red close.
   - Bear Trend: If the low is set in this window, there is a 64.7% chance of a reversal green close.
