# Trend Analysis Rules

These rules define how uptrends and downtrends are identified in this project, specifically based on the analysis in `trading_analysis_qa.md` and the implementation in `trend_analysis_methods.py`.

## Trend Definitions

Trends are determined using the **120-minute (2-hour)** timeframe data (`nifty50_minute_complete-120min.csv`).

### Uptrend (Bullish Trend)
A market is considered to be in an uptrend if **both** of the following conditions are met:
1.  **EMA Crossover:** The 11-period Exponential Moving Average (EMA) is **greater than** the 21-period EMA.
    *   `EMA(11) > EMA(21)`
2.  **EMA Slope:** The slope of the 21-period EMA is **greater than 10 degrees**.
    *   `Slope(EMA(21)) > 10°`

### Downtrend (Bearish Trend)
A market is considered to be in a downtrend if **both** of the following conditions are met:
1.  **EMA Crossover:** The 11-period EMA is **less than** the 21-period EMA.
    *   `EMA(11) < EMA(21)`
2.  **EMA Slope:** The slope of the 21-period EMA is **less than -10 degrees**.
    *   `Slope(EMA(21)) < -10°`

## Calculation Details

*   **EMA (Exponential Moving Average):** Standard calculation based on the `close` price.
*   **Slope:** Calculated based on the angle of the EMA 21 line over a 1-period lookback.
