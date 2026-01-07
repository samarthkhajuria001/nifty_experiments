# Nifty 50 Trading Analysis Summary

Complete Q&A summary of all findings from this project (2,500+ trading days analyzed).

---

## PROBABILITY: High or Low Seen by Bar (Key Reference)

### Overall Market (All Days)

| Bar | High Set | Low Set | Either Set |
|-----|----------|---------|------------|
| 1 | 23% | 17% | 40% |
| 6 | 35% | 30% | 63% |
| 12 | 41% | 37% | 74% |
| 20 | 47% | 43% | 83% |
| 30 | 51% | 48% | 88% |
| 50 | 59% | 61% | 96% |
| 75 | 100% | 100% | 100% |

### Gap Up ≥50 + Bear Bar (Strongest Short Signal)

| Bar | High Set | Low Set | Either Set |
|-----|----------|---------|------------|
| 1 | 43% | 3% | 46% |
| 6 | 46% | 25% | 68% |
| 12 | 50% | 37% | 80% |
| 20 | 57% | 45% | 88% |
| 30 | 59% | 51% | 94% |

### Small Gap Scenarios (from output/small_gap/)

**UPTREND + Small Gap Down + Strong Bear Bar:**
| Bar | High Set | Low Set | Either Set |
|-----|----------|---------|------------|
| 1 | 48% | 0% | 48% |
| 6 | 48% | 18% | 61% |
| 12 | 55% | 21% | 70% |

**UPTREND + Small Gap Up + Strong Bull Bar:**
| Bar | High Set | Low Set | Either Set |
|-----|----------|---------|------------|
| 1 | 25% | 17% | 42% |
| 6 | 36% | 28% | 64% |
| 12 | 43% | 36% | 75% |

**DOWNTREND + Small Gap Down + Strong Bull Bar:**
| Bar | High Set | Low Set | Either Set |
|-----|----------|---------|------------|
| 1 | 0% | 41% | 41% |
| 6 | 19% | 48% | 67% |
| 12 | 26% | 48% | 74% |

**UPTREND + Small Gap Down + Bull Bar:**
| Bar | High Set | Low Set | Either Set |
|-----|----------|---------|------------|
| 1 | 7% | 33% | 40% |
| 6 | 25% | 40% | 65% |
| 12 | 33% | 43% | 74% |

---

## PROBABILITY: Day Close Direction

### Q1: 3 consecutive bars (5-min) in first 30 min → day close?

| First 30 Min | Days | Day Closes Same Direction |
|--------------|------|---------------------------|
| 3 Bull Bars | 267 (10.7%) | 68.9% Bull Close |
| 3 Bear Bars | 323 (13.0%) | 74.0% Bear Close |
| Mixed | 1,896 (76.3%) | ~50/50 |

### Q2: First 2 bars (30-min) same direction → day close?

| 2HR Trend | Pattern | BULL Close | BEAR Close |
|-----------|---------|------------|------------|
| BULL | Bull-Bull | 76.0% | 24.0% |
| BULL | Bear-Bear | 24.2% | 75.8% |
| BEAR | Bull-Bull | 73.7% | 26.3% |
| BEAR | Bear-Bear | 23.8% | 76.2% |

### Q3: 3-bar patterns (30-min bars) → day close?

| Context | Pattern | Day Close |
|---------|---------|-----------|
| Bull Trend | Bull-Bull-Bull | 79.5% Bull |
| Bull Trend | Bear-Bear-Bear | 79.0% Bear |
| Bear Trend | Bear-Bear-Bear | 84.5% Bear |
| Bear Trend | Bull-Bull-Bull | 83.3% Bull |

### Q4: Day close by 2HR trend alone?

| 2HR Trend | BULL Close | BEAR Close |
|-----------|------------|------------|
| BULL | 51.2% | 48.8% |
| BEAR | 40.3% | 59.7% |

---

## PROBABILITY: High/Low Timing Traps

### Q5: When high/low set in first 30 min → reversal?

| Trend | Event | Occurrence | Reversal Prob |
|-------|-------|------------|---------------|
| Bull | High in 1st 30 min | 29.5% | 93.4% Bear close |
| Bear | Low in 1st 30 min | 21.0% | 89.7% Bull close |

---

## PROBABILITY: Bar 1 Master Table

| Trend | Gap | First Bar | High% | Low% | Either% |
|-------|-----|-----------|-------|------|---------|
| Up | SmGapUp | Bull | 9% | 31% | 40% |
| Up | SmGapUp | Bear | 37% | 7% | 43% |
| Up | SmGapUp | Strong Bull | 1% | 42% | 43% |
| Up | SmGapUp | Strong Bear | 45% | 1% | 46% |
| Up | SmGapDn | Bull | 7% | 33% | 40% |
| Up | SmGapDn | Bear | 28% | 10% | 38% |
| Up | SmGapDn | Strong Bear | 48% | 0% | 48% |
| Dn | SmGapUp | Bull | 9% | 27% | 36% |
| Dn | SmGapUp | Bear | 33% | 5% | 39% |
| Dn | SmGapUp | Strong Bull | 0% | 33% | 33% |
| Dn | SmGapUp | Strong Bear | 39% | 0% | 39% |
| Dn | SmGapDn | Strong Bull | 0% | 41% | 41% |
| Bear | GapUp≥50 | Bull | 0% | 38% | 38% |
| Bear | GapUp≥50 | Bear | 46% | 2% | 48% |
| Bull | GapUp≥50 | Bull | 0% | 42% | 42% |
| Bull | GapUp≥50 | Bear | 41% | 4% | 44% |
| Bull | GapDn≥50 | Bull | 3% | 44% | 47% |

---

## PROBABILITY: +10 Point Tolerance

| Scenario | Exact High | +10pt High | Exact Low | +10pt Low |
|----------|------------|------------|-----------|-----------|
| Up+SmGapUp+StrongBear | 45% | 54% | 1% | 13% |
| Up+SmGapUp+StrongBull | 1% | 15% | 42% | 51% |
| Bear+GapUp≥50+Bear | 46% | 52% | 2% | 8% |
| Bull+GapUp≥50+Bull | 0% | 6% | 42% | 52% |

---

## PROBABILITY: First Bar Reversal

| First Bar | Predicts | Probability |
|-----------|----------|-------------|
| Bullish | Day's LOW is set | 27-44% |
| Bearish | Day's HIGH is set | 28-46% |
| Strong Bullish | Day's LOW is set | 29-42% |
| Strong Bearish | Day's HIGH is set | 39-48% |

---

## PROBABILITY: Strong Bar Amplification

| Scenario | Regular | Strong | Boost |
|----------|---------|--------|-------|
| Up+SmGapUp: Low in Bar 1 | 31% | 42% | +11% |
| Up+SmGapDn: High in Bar 1 | 28% | 48% | +20% |
| Dn+SmGapUp: Low in Bar 1 | 27% | 33% | +6% |
| Up+SmGapUp: High in Bar 1 | 37% | 45% | +8% |

---

## TRADING STRATEGIES

| Strategy | Trigger | Action | Win Rate |
|----------|---------|--------|----------|
| Strong Bear Fade | Uptrend + SmGapUp + Strong Bear | Short at bar 1 high | 54% |
| Bear Gap Trap | Bear Trend + GapUp≥50 + Bear | Short at bar 1 high | 52% |
| Bull Continuation | Bull Trend + GapDn≥50 + Bull | Long at bar 1 low | ~55% |
| Large Gap Bull Long | Any + GapUp≥50 + Bull | Long at bar 1 low | ~52% |

---

## KEY PATTERNS

1. **Inverted First Bar:** Bull bar = low set, Bear bar = high set
2. **Gap Amplification:** Larger gaps = stronger reversal signals
3. **Trend Counter-Move:** Gap against trend = strongest setups
4. **Time Concentration:** 40-50% of extremes in bar 1, 85% by bar 20
5. **Strong Bar Superiority:** +6-20% probability boost

---

## DEFINITIONS

| Term | Definition |
|------|------------|
| Bull Trend | EMA(11) > EMA(21) AND Slope(EMA21) > 10° on 2HR |
| Bear Trend | EMA(11) < EMA(21) AND Slope(EMA21) < -10° on 2HR |
| Strong Bar | Body > 90% of candle range |
| Small Gap | < 50 points |
| Large Gap | ≥ 50 points |
