# Nifty 50 Trading Pattern Analysis - Q&A

## Question 1: Opening 30-Minute Pattern and Day Close Direction

**Question:** If there are 3 consecutive bull bars in the first 30 minutes of trading, what are the chances that the day will close bullish? Similarly, if there are 3 consecutive bear bars in the first 30 minutes, what are the chances that the day will close bearish?

---

### Analysis Overview

This analysis examines Nifty 50 5-minute candle data to determine the correlation between the direction of the first 3 consecutive bars (first 30 minutes: 09:15, 09:20, 09:25) and the day's closing direction.

### Dataset
- **Source:** nifty50_minute_complete-5min.csv
- **Total Trading Days Analyzed:** 2,486 days
- **Time Period:** 2015-01-09 onwards
- **Candle Timeframe:** 5 minutes

---

### Key Findings

#### Scenario 1: Three Consecutive BULL Bars (First 30 Minutes)

**Occurrences:** 267 days (10.74% of all trading days)

| Outcome            | Count | Probability |
|--------------------|-------|-------------|
| Day closes BULLISH | 184   | **68.91%**  |
| Day closes BEARISH | 83    | 31.09%      |

**Average Day Change:** +44.03 points

**Interpretation:** When the first 3 consecutive bars are bullish, there is a **68.91% probability** that the day will close above its opening price. This indicates a strong positive correlation between an aggressive bullish opening and an overall bullish day.

---

#### Scenario 2: Three Consecutive BEAR Bars (First 30 Minutes)

**Occurrences:** 323 days (12.99% of all trading days)

| Outcome            | Count | Probability |
|--------------------|-------|-------------|
| Day closes BEARISH | 239   | **73.99%**  |
| Day closes BULLISH | 84    | 26.01%      |

**Average Day Change:** -59.87 points

**Interpretation:** When the first 3 consecutive bars are bearish, there is a **73.99% probability** that the day will close below its opening price. This shows an even stronger correlation on the bearish side - a weak opening tends to persist throughout the day.

---

#### Scenario 3: Mixed Bars (First 30 Minutes)

**Occurrences:** 1,896 days (76.27% of all trading days)

| Outcome            | Count | Probability |
|--------------------|-------|-------------|
| Day closes BULLISH | 892   | 47.05%      |
| Day closes BEARISH | 1,004 | 52.95%      |

**Interpretation:** When the first 3 bars show mixed signals (neither all bullish nor all bearish), the day's direction is essentially a coin flip with a slight bearish bias (52.95%).

---

### Trading Insights

1. **Strong Correlation:** The first 30 minutes of trading provides a statistically significant edge in predicting the day's closing direction.

2. **Bearish Opening More Reliable:** A bearish opening (3 consecutive bear bars) has a 73.99% success rate in predicting a bearish close, which is stronger than the bullish equivalent (68.91%).

3. **Risk/Reward:** On average, bearish opening days close -59.87 points down, while bullish opening days close +44.03 points up. The bearish days show larger average moves.

4. **Majority Are Mixed:** 76.27% of trading days have mixed bars in the first 30 minutes, making clear directional openings relatively rare but valuable when they occur.

5. **Failed Patterns:**
   - 31.09% of bullish openings reverse to close bearish
   - 26.01% of bearish openings reverse to close bullish
   - These failed patterns could be trading opportunities for reversal strategies

---

### Conclusion

The first 30 minutes of trading in Nifty 50 carries significant predictive value. When 3 consecutive bars move in the same direction:
- **Bullish opening → ~69% chance of bullish close**
- **Bearish opening → ~74% chance of bearish close**

This pattern can be used as a confirmation signal for intraday trend-following strategies or to set directional bias for the trading day.

---

## Question 3: Opening Pattern by 2HR Trend (First 3 Bars - 30 Minutes)

**Question:** When the 2HR trend is bullish or bearish (using EMA 11 > 21 + slope > 10°), what are the probabilities of day close direction when first 3 bars in 5-min are all bull or all bear?

### Results (Without Gap Filter)

| 2HR Trend | First 30min Pattern | Day Closes BULL | Day Closes BEAR | 1st Bull Bar Low Holds | 1st Bear Bar High Holds |
|-----------|---------------------|-----------------|-----------------|------------------------|-------------------------|
| BULL      | 3 Bull Bars         | 71.93%          | 28.07%          | 49.71%                 | -                       |
| BULL      | 3 Bear Bars         | 26.15%          | 73.85%          | -                      | 50.00%                  |
| BEAR      | 3 Bull Bars         | 63.64%          | 36.36%          | 30.91%                 | -                       |
| BEAR      | 3 Bear Bars         | 25.74%          | 74.26%          | -                      | 61.76%                  |

### Results (With Gap Filter)

| 2HR Trend | Gap       | First 30min Pattern | Day Closes BULL | Day Closes BEAR |
|-----------|-----------|---------------------|-----------------|-----------------|
| BULL      | Gap Up    | 3 Bull Bars         | 71.90%          | 28.10%          |
| BULL      | Gap Up    | 3 Bear Bars         | 23.15%          | 76.85%          |
| BULL      | Gap Down  | 3 Bull Bars         | 72.00%          | 28.00%          |
| BULL      | Gap Down  | 3 Bear Bars         | 40.91%          | 59.09%          |
| BEAR      | Gap Up    | 3 Bull Bars         | 53.85%          | 46.15%          |
| BEAR      | Gap Up    | 3 Bear Bars         | 23.75%          | 76.25%          |
| BEAR      | Gap Down  | 3 Bull Bars         | 72.41%          | 27.59%          |
| BEAR      | Gap Down  | 3 Bear Bars         | 28.57%          | 71.43%          |

### Comparison: Skip First Bar (09:20-09:30)

| 2HR Trend | Gap       | Pattern (09:20-09:30) | Day Closes BULL | Day Closes BEAR |
|-----------|-----------|------------------------|-----------------|-----------------|
| BULL      | Gap Up    | 3 Bull Bars            | 69.67%          | 30.33%          |
| BULL      | Gap Up    | 3 Bear Bars            | 28.21%          | 71.79%          |
| BULL      | Gap Down  | 3 Bull Bars            | 65.91%          | 34.09%          |
| BULL      | Gap Down  | 3 Bear Bars            | 48.28%          | 51.72%          |
| BEAR      | Gap Up    | 3 Bull Bars            | 50.00%          | 50.00%          |
| BEAR      | Gap Up    | 3 Bear Bars            | 27.78%          | 72.22%          |
| BEAR      | Gap Down  | 3 Bull Bars            | 43.75%          | 56.25%          |
| BEAR      | Gap Down  | 3 Bear Bars            | 32.14%          | 67.86%          |

---

## Question 4: Opening Pattern by 2HR Trend (First 6 Bars - 1 Hour)

**Question:** When the 2HR trend is bullish or bearish, what are the probabilities when first 6 bars (1 hour) are all bull or all bear?

### Results (Without Gap Filter)

| 2HR Trend | First 1hr Pattern | Day Closes BULL | Day Closes BEAR | 1st Bull Bar Low Holds | 1st Bear Bar High Holds |
|-----------|-------------------|-----------------|-----------------|------------------------|-------------------------|
| BULL      | 6 Bull Bars       | 76.47%          | 23.53%          | 64.71%                 | -                       |
| BULL      | 6 Bear Bars       | 23.08%          | 76.92%          | -                      | 53.85%                  |
| BEAR      | 6 Bull Bars       | 50.00%          | 50.00%          | 33.33%                 | -                       |
| BEAR      | 6 Bear Bars       | 44.44%          | 55.56%          | -                      | 50.00%                  |

### Results (With Gap Filter)

| 2HR Trend | Gap       | First 1hr Pattern | Day Closes BULL | Day Closes BEAR |
|-----------|-----------|-------------------|-----------------|-----------------|
| BULL      | Gap Up    | 6 Bull Bars       | 75.00%          | 25.00%          |
| BULL      | Gap Up    | 6 Bear Bars       | 27.27%          | 72.73%          |
| BULL      | Gap Down  | 6 Bull Bars       | 80.00%          | 20.00%          |
| BULL      | Gap Down  | 6 Bear Bars       | 0.00%           | 100.00%         |
| BEAR      | Gap Up    | 6 Bull Bars       | 33.33%          | 66.67%          |
| BEAR      | Gap Up    | 6 Bear Bars       | 50.00%          | 50.00%          |
| BEAR      | Gap Down  | 6 Bull Bars       | 66.67%          | 33.33%          |
| BEAR      | Gap Down  | 6 Bear Bars       | 37.50%          | 62.50%          |

---

## Question 5: Day Close Direction by 2HR Trend

**Question:** In bull and bear trends (2hr), what percentage of days close bullish vs bearish?

### Results (Without Gap Filter)

| 2HR Trend | Day Closes BULL | Day Closes BEAR |
|-----------|-----------------|-----------------|
| BULL      | 51.20%          | 48.80%          |
| BEAR      | 40.34%          | 59.66%          |

### Results (With Gap Filter)

| 2HR Trend | Gap       | Day Closes BULL | Day Closes BEAR |
|-----------|-----------|-----------------|-----------------|
| BULL      | Gap Up    | 48.79%          | 51.21%          |
| BULL      | Gap Down  | 59.32%          | 40.68%          |
| BEAR      | Gap Up    | 39.32%          | 60.68%          |
| BEAR      | Gap Down  | 41.72%          | 58.28%          |

---