"""
NIFTY50 First Bar Trade Idea Generator
======================================
Generates 3 complete algorithmic trade ideas based on first bar analysis.

Based on historical probability analysis of 2,500+ trading days showing:
- Bullish first bars tend to mark the day's LOW (continuation higher)
- Bearish first bars tend to mark the day's HIGH (reversal lower)

Trade Ideas Generated:
1. AGGRESSIVE FADE - Immediate entry opposite to first bar direction
2. CONFIRMATION ENTRY - Wait for pullback/confirmation before entry
3. SCALED POSITION - Split entry across multiple price levels/bars
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import os
from pathlib import Path


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class BarType(Enum):
    STRONG_BULL = "strong_bull"
    BULL = "bull"
    NEUTRAL = "neutral"
    BEAR = "bear"
    STRONG_BEAR = "strong_bear"


class TrendType(Enum):
    UPTREND = "uptrend"
    DOWNTREND = "downtrend"
    BULL_TREND = "bull_trend"  # Strong uptrend (for large gap classification)
    BEAR_TREND = "bear_trend"  # Strong downtrend (for large gap classification)


class GapType(Enum):
    LARGE_GAP_UP = "large_gap_up"      # >= 50 points
    SMALL_GAP_UP = "small_gap_up"      # 0 to 50 points
    SMALL_GAP_DOWN = "small_gap_down"  # -50 to 0 points
    LARGE_GAP_DOWN = "large_gap_down"  # <= -50 points


class TradeDirection(Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NO_TRADE = "NO_TRADE"


@dataclass
class FirstBar:
    """First bar of the trading day"""
    open: float
    high: float
    low: float
    close: float
    volume: float = 0

    @property
    def body(self) -> float:
        return self.close - self.open

    @property
    def range(self) -> float:
        return self.high - self.low

    @property
    def body_pct(self) -> float:
        """Body as percentage of total range"""
        if self.range == 0:
            return 0
        return abs(self.body) / self.range

    @property
    def is_bullish(self) -> bool:
        return self.close > self.open

    @property
    def is_bearish(self) -> bool:
        return self.close < self.open

    @property
    def midpoint(self) -> float:
        return (self.high + self.low) / 2


@dataclass
class MarketContext:
    """Complete market context for trade generation"""
    trend: TrendType
    gap_type: GapType
    bar_type: BarType
    gap_points: float
    trend_strength: float  # % distance from MA

    # Probabilities from historical data
    prob_high_bar1: float = 0.0
    prob_low_bar1: float = 0.0
    prob_high_bar1_offset10: float = 0.0
    prob_low_bar1_offset10: float = 0.0
    prob_either_bar1: float = 0.0
    sample_size: int = 0

    # Derived metrics
    high_low_ratio: float = 0.0
    edge_strength: str = "NONE"  # NONE, WEAK, MODERATE, STRONG, EXTREME


@dataclass
class TradeIdea:
    """Complete algorithmic trade idea"""
    name: str
    strategy_type: str  # AGGRESSIVE_FADE, CONFIRMATION, SCALED
    direction: TradeDirection

    # Entry details
    entry_type: str  # IMMEDIATE, LIMIT, STOP, SCALED
    entry_price: float

    # Risk management
    stop_loss: float
    stop_distance: float

    # Targets (multiple for scaling out)
    target_1: float
    target_2: float
    target_3: float

    # Position sizing
    position_size_pct: float  # % of capital to risk
    risk_per_trade: float  # Actual risk in points

    # Probabilities and expected value
    win_probability: float
    risk_reward_ratio: float
    expected_value: float  # Expected return per trade

    # Time management
    max_holding_bars: int

    # Risk assessment
    risk_level: str  # LOW, MODERATE, HIGH
    confidence: str  # LOW, MEDIUM, HIGH (based on sample size)

    # Optional fields with defaults
    entry_zone_high: float = 0.0  # For limit orders
    entry_zone_low: float = 0.0
    target_1_pct: float = 33.0  # % of position to exit
    target_2_pct: float = 33.0
    target_3_pct: float = 34.0
    entry_valid_until_bar: int = 6  # Entry must trigger by this bar
    trigger_condition: str = ""
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'strategy_type': self.strategy_type,
            'direction': self.direction.value,
            'entry_type': self.entry_type,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'stop_distance': self.stop_distance,
            'target_1': self.target_1,
            'target_2': self.target_2,
            'target_3': self.target_3,
            'position_size_pct': self.position_size_pct,
            'win_probability': self.win_probability,
            'risk_reward_ratio': self.risk_reward_ratio,
            'expected_value': self.expected_value,
            'max_holding_bars': self.max_holding_bars,
            'risk_level': self.risk_level,
            'confidence': self.confidence,
            'trigger_condition': self.trigger_condition,
            'notes': self.notes
        }


# =============================================================================
# PROBABILITY LOOKUP TABLE
# =============================================================================

class ProbabilityTable:
    """
    Historical probability lookup based on our analysis.
    Format: (trend, gap_type, bar_type) -> (prob_high, prob_low, prob_high_10, prob_low_10, sample_size)
    """

    def __init__(self):
        # Build lookup table from our analysis
        self.table = self._build_table()

    def _build_table(self) -> Dict:
        """Build probability lookup table from analysis results"""
        table = {}

        # UPTREND + SMALL GAP UP scenarios
        table[('uptrend', 'small_gap_up', 'bull')] = (0.09, 0.31, 0.26, 0.40, 309)
        table[('uptrend', 'small_gap_up', 'bear')] = (0.37, 0.07, 0.52, 0.16, 408)
        table[('uptrend', 'small_gap_up', 'strong_bull')] = (0.01, 0.42, 0.15, 0.51, 96)
        table[('uptrend', 'small_gap_up', 'strong_bear')] = (0.45, 0.01, 0.54, 0.13, 113)
        table[('uptrend', 'small_gap_up', 'neutral')] = (0.25, 0.17, 0.41, 0.26, 718)

        # UPTREND + SMALL GAP DOWN scenarios
        table[('uptrend', 'small_gap_down', 'bull')] = (0.07, 0.33, 0.18, 0.43, 134)
        table[('uptrend', 'small_gap_down', 'bear')] = (0.28, 0.10, 0.38, 0.21, 176)
        table[('uptrend', 'small_gap_down', 'strong_bull')] = (0.05, 0.29, 0.16, 0.37, 62)
        table[('uptrend', 'small_gap_down', 'strong_bear')] = (0.48, 0.00, 0.58, 0.09, 33)
        table[('uptrend', 'small_gap_down', 'neutral')] = (0.19, 0.20, 0.29, 0.30, 310)

        # DOWNTREND + SMALL GAP UP scenarios
        table[('downtrend', 'small_gap_up', 'bull')] = (0.09, 0.27, 0.21, 0.32, 149)
        table[('downtrend', 'small_gap_up', 'bear')] = (0.33, 0.05, 0.43, 0.17, 230)
        table[('downtrend', 'small_gap_up', 'strong_bull')] = (0.00, 0.33, 0.13, 0.35, 54)
        table[('downtrend', 'small_gap_up', 'strong_bear')] = (0.39, 0.00, 0.48, 0.10, 61)
        table[('downtrend', 'small_gap_up', 'neutral')] = (0.24, 0.14, 0.35, 0.23, 379)

        # DOWNTREND + SMALL GAP DOWN scenarios
        table[('downtrend', 'small_gap_down', 'bull')] = (0.13, 0.24, 0.26, 0.30, 76)
        table[('downtrend', 'small_gap_down', 'bear')] = (0.35, 0.07, 0.43, 0.15, 118)
        table[('downtrend', 'small_gap_down', 'strong_bull')] = (0.13, 0.24, 0.26, 0.30, 76)  # Using bull as proxy
        table[('downtrend', 'small_gap_down', 'strong_bear')] = (0.35, 0.07, 0.43, 0.15, 118)  # Using bear as proxy
        table[('downtrend', 'small_gap_down', 'neutral')] = (0.26, 0.13, 0.37, 0.21, 194)

        # BEAR TREND + LARGE GAP UP scenarios (gap >= 50)
        table[('bear_trend', 'large_gap_up', 'bull')] = (0.00, 0.38, 0.05, 0.41, 37)
        table[('bear_trend', 'large_gap_up', 'bear')] = (0.46, 0.02, 0.52, 0.08, 48)
        table[('bear_trend', 'large_gap_up', 'strong_bull')] = (0.00, 0.38, 0.05, 0.41, 37)
        table[('bear_trend', 'large_gap_up', 'strong_bear')] = (0.46, 0.02, 0.52, 0.08, 48)
        table[('bear_trend', 'large_gap_up', 'neutral')] = (0.24, 0.16, 0.29, 0.22, 85)

        # BEAR TREND + LARGE GAP DOWN scenarios
        table[('bear_trend', 'large_gap_down', 'bull')] = (0.05, 0.29, 0.05, 0.29, 21)
        table[('bear_trend', 'large_gap_down', 'bear')] = (0.20, 0.00, 0.33, 0.13, 15)
        table[('bear_trend', 'large_gap_down', 'strong_bull')] = (0.05, 0.29, 0.05, 0.29, 21)
        table[('bear_trend', 'large_gap_down', 'strong_bear')] = (0.20, 0.00, 0.33, 0.13, 15)
        table[('bear_trend', 'large_gap_down', 'neutral')] = (0.12, 0.15, 0.19, 0.21, 36)

        # BULL TREND + LARGE GAP UP scenarios
        table[('bull_trend', 'large_gap_up', 'bull')] = (0.00, 0.42, 0.06, 0.52, 33)
        table[('bull_trend', 'large_gap_up', 'bear')] = (0.41, 0.04, 0.52, 0.20, 54)
        table[('bull_trend', 'large_gap_up', 'strong_bull')] = (0.00, 0.42, 0.06, 0.52, 33)
        table[('bull_trend', 'large_gap_up', 'strong_bear')] = (0.41, 0.04, 0.52, 0.20, 54)
        table[('bull_trend', 'large_gap_up', 'neutral')] = (0.23, 0.17, 0.33, 0.24, 87)

        # BULL TREND + LARGE GAP DOWN scenarios
        table[('bull_trend', 'large_gap_down', 'bull')] = (0.03, 0.44, 0.08, 0.53, 36)
        table[('bull_trend', 'large_gap_down', 'bear')] = (0.33, 0.00, 0.33, 0.11, 9)
        table[('bull_trend', 'large_gap_down', 'strong_bull')] = (0.03, 0.44, 0.08, 0.53, 36)
        table[('bull_trend', 'large_gap_down', 'strong_bear')] = (0.33, 0.00, 0.33, 0.11, 9)
        table[('bull_trend', 'large_gap_down', 'neutral')] = (0.18, 0.22, 0.21, 0.32, 45)

        return table

    def lookup(self, trend: str, gap_type: str, bar_type: str) -> Tuple[float, float, float, float, int]:
        """
        Look up probabilities for given market context.
        Returns: (prob_high, prob_low, prob_high_offset10, prob_low_offset10, sample_size)
        """
        key = (trend, gap_type, bar_type)

        if key in self.table:
            return self.table[key]

        # Fallback to neutral if specific bar type not found
        neutral_key = (trend, gap_type, 'neutral')
        if neutral_key in self.table:
            return self.table[neutral_key]

        # Ultimate fallback - no edge
        return (0.20, 0.20, 0.30, 0.30, 0)


# =============================================================================
# MAIN TRADE GENERATOR CLASS
# =============================================================================

class FirstBarTradeGenerator:
    """
    Generates 3 complete algorithmic trade ideas based on first bar analysis.
    """

    def __init__(self, default_atr: float = 100.0):
        """
        Initialize the trade generator.

        Args:
            default_atr: Default ATR value if not provided (typical NIFTY range ~100-150)
        """
        self.prob_table = ProbabilityTable()
        self.default_atr = default_atr

    # -------------------------------------------------------------------------
    # CLASSIFICATION METHODS
    # -------------------------------------------------------------------------

    def classify_bar(self, bar: FirstBar) -> BarType:
        """
        Classify first bar as bullish, bearish, or neutral with strength.

        Strong: Body > 60% of range
        Regular: Body 30-60% of range
        Neutral: Body < 30% of range
        """
        body_pct = bar.body_pct

        if body_pct < 0.30:
            return BarType.NEUTRAL

        if bar.is_bullish:
            return BarType.STRONG_BULL if body_pct > 0.60 else BarType.BULL
        else:
            return BarType.STRONG_BEAR if body_pct > 0.60 else BarType.BEAR

    def classify_gap(self, prev_close: float, current_open: float) -> Tuple[GapType, float]:
        """
        Classify gap type and return gap in points.

        Returns: (GapType, gap_points)
        """
        gap = current_open - prev_close

        if gap >= 50:
            return GapType.LARGE_GAP_UP, gap
        elif gap > 0:
            return GapType.SMALL_GAP_UP, gap
        elif gap > -50:
            return GapType.SMALL_GAP_DOWN, gap
        else:
            return GapType.LARGE_GAP_DOWN, gap

    def classify_trend(self, current_price: float, ma_50: float,
                       gap_type: GapType) -> Tuple[TrendType, float]:
        """
        Classify trend based on price relative to 50-period MA.
        For large gaps, use bull_trend/bear_trend classification.

        Returns: (TrendType, trend_strength_pct)
        """
        if ma_50 == 0:
            return TrendType.UPTREND, 0.0

        diff_pct = (current_price - ma_50) / ma_50 * 100

        # For large gaps, use stronger trend classification
        is_large_gap = gap_type in [GapType.LARGE_GAP_UP, GapType.LARGE_GAP_DOWN]

        if is_large_gap:
            if diff_pct > 0.3:
                return TrendType.BULL_TREND, diff_pct
            elif diff_pct < -0.3:
                return TrendType.BEAR_TREND, diff_pct
            elif diff_pct > 0:
                return TrendType.BULL_TREND, diff_pct
            else:
                return TrendType.BEAR_TREND, diff_pct
        else:
            if diff_pct > 0:
                return TrendType.UPTREND, diff_pct
            else:
                return TrendType.DOWNTREND, diff_pct

    def _get_gap_type_str(self, gap_type: GapType) -> str:
        """Convert GapType enum to lookup string"""
        mapping = {
            GapType.LARGE_GAP_UP: 'large_gap_up',
            GapType.SMALL_GAP_UP: 'small_gap_up',
            GapType.SMALL_GAP_DOWN: 'small_gap_down',
            GapType.LARGE_GAP_DOWN: 'large_gap_down'
        }
        return mapping[gap_type]

    def _get_trend_str(self, trend: TrendType) -> str:
        """Convert TrendType enum to lookup string"""
        mapping = {
            TrendType.UPTREND: 'uptrend',
            TrendType.DOWNTREND: 'downtrend',
            TrendType.BULL_TREND: 'bull_trend',
            TrendType.BEAR_TREND: 'bear_trend'
        }
        return mapping[trend]

    def _get_bar_type_str(self, bar_type: BarType) -> str:
        """Convert BarType enum to lookup string"""
        mapping = {
            BarType.STRONG_BULL: 'strong_bull',
            BarType.BULL: 'bull',
            BarType.NEUTRAL: 'neutral',
            BarType.BEAR: 'bear',
            BarType.STRONG_BEAR: 'strong_bear'
        }
        return mapping[bar_type]

    # -------------------------------------------------------------------------
    # CONTEXT BUILDING
    # -------------------------------------------------------------------------

    def build_context(self, bar: FirstBar, prev_close: float,
                      ma_50: float) -> MarketContext:
        """
        Build complete market context from first bar data.
        """
        bar_type = self.classify_bar(bar)
        gap_type, gap_points = self.classify_gap(prev_close, bar.open)
        trend, trend_strength = self.classify_trend(bar.close, ma_50, gap_type)

        # Lookup probabilities
        probs = self.prob_table.lookup(
            self._get_trend_str(trend),
            self._get_gap_type_str(gap_type),
            self._get_bar_type_str(bar_type)
        )

        prob_high, prob_low, prob_high_10, prob_low_10, sample_size = probs

        # Calculate edge strength
        if prob_high > 0 and prob_low > 0:
            ratio = max(prob_high / prob_low, prob_low / prob_high)
        else:
            ratio = float('inf') if (prob_high > 0 or prob_low > 0) else 1.0

        if ratio >= 10:
            edge_strength = "EXTREME"
        elif ratio >= 5:
            edge_strength = "STRONG"
        elif ratio >= 2:
            edge_strength = "MODERATE"
        elif ratio >= 1.5:
            edge_strength = "WEAK"
        else:
            edge_strength = "NONE"

        return MarketContext(
            trend=trend,
            gap_type=gap_type,
            bar_type=bar_type,
            gap_points=gap_points,
            trend_strength=trend_strength,
            prob_high_bar1=prob_high,
            prob_low_bar1=prob_low,
            prob_high_bar1_offset10=prob_high_10,
            prob_low_bar1_offset10=prob_low_10,
            prob_either_bar1=prob_high + prob_low,
            sample_size=sample_size,
            high_low_ratio=ratio,
            edge_strength=edge_strength
        )

    # -------------------------------------------------------------------------
    # TRADE IDEA GENERATION
    # -------------------------------------------------------------------------

    def _determine_direction(self, ctx: MarketContext) -> TradeDirection:
        """
        Determine trade direction based on first bar type and probabilities.

        Key insight: First bar direction predicts OPPOSITE extreme
        - Bullish bar -> Low likely set -> Go LONG
        - Bearish bar -> High likely set -> Go SHORT
        """
        # Check if we have an edge
        if ctx.edge_strength == "NONE":
            return TradeDirection.NO_TRADE

        # Bearish bars predict high is set -> SHORT
        if ctx.bar_type in [BarType.BEAR, BarType.STRONG_BEAR]:
            if ctx.prob_high_bar1 >= 0.25:  # Minimum 25% probability
                return TradeDirection.SHORT

        # Bullish bars predict low is set -> LONG
        if ctx.bar_type in [BarType.BULL, BarType.STRONG_BULL]:
            if ctx.prob_low_bar1 >= 0.25:  # Minimum 25% probability
                return TradeDirection.LONG

        # Neutral bars - use probability to decide
        if ctx.bar_type == BarType.NEUTRAL:
            if ctx.prob_high_bar1 > ctx.prob_low_bar1 + 0.10:
                return TradeDirection.SHORT
            elif ctx.prob_low_bar1 > ctx.prob_high_bar1 + 0.10:
                return TradeDirection.LONG

        return TradeDirection.NO_TRADE

    def _calculate_position_size(self, win_prob: float, risk_reward: float,
                                  confidence: str) -> float:
        """
        Calculate position size using modified Kelly Criterion.

        Uses 25% of Kelly for safety, adjusted by confidence level.
        """
        if win_prob <= 0 or risk_reward <= 0:
            return 0.5  # Minimum position

        # Kelly Criterion: (p * b - q) / b
        # where p = win prob, q = loss prob (1-p), b = win/loss ratio
        q = 1 - win_prob
        kelly = (win_prob * risk_reward - q) / risk_reward

        # Use fraction of Kelly based on confidence
        kelly_fraction = {
            'HIGH': 0.30,
            'MEDIUM': 0.20,
            'LOW': 0.10
        }.get(confidence, 0.15)

        safe_kelly = kelly * kelly_fraction

        # Cap between 0.5% and 3%
        return max(0.5, min(3.0, safe_kelly * 100))

    def _get_confidence(self, sample_size: int) -> str:
        """Determine confidence level based on sample size"""
        if sample_size >= 200:
            return "HIGH"
        elif sample_size >= 100:
            return "MEDIUM"
        else:
            return "LOW"

    def _generate_aggressive_fade(self, bar: FirstBar, ctx: MarketContext,
                                   atr: float, direction: TradeDirection) -> TradeIdea:
        """
        STRATEGY 1: AGGRESSIVE FADE

        Enter immediately at bar 1 close, opposite to bar direction.
        Tight stop just beyond bar 1 extreme.
        Multiple targets for scaling out.

        Best for: Strong bars with high probability signals
        Risk: Higher (immediate entry, tight stop)
        Reward: Higher (full move capture potential)
        """
        confidence = self._get_confidence(ctx.sample_size)

        if direction == TradeDirection.SHORT:
            entry_price = bar.close
            stop_loss = bar.high + (atr * 0.15)  # Just above bar 1 high
            stop_distance = stop_loss - entry_price

            # Targets based on ATR multiples
            target_1 = entry_price - (stop_distance * 1.0)   # 1:1 R:R
            target_2 = entry_price - (stop_distance * 2.0)   # 2:1 R:R
            target_3 = entry_price - (stop_distance * 3.0)   # 3:1 R:R

            win_prob = ctx.prob_high_bar1_offset10  # Use offset probability for realistic stop
            trigger = f"Enter SHORT at {entry_price:.0f} immediately after bar 1 close"

        elif direction == TradeDirection.LONG:
            entry_price = bar.close
            stop_loss = bar.low - (atr * 0.15)  # Just below bar 1 low
            stop_distance = entry_price - stop_loss

            target_1 = entry_price + (stop_distance * 1.0)
            target_2 = entry_price + (stop_distance * 2.0)
            target_3 = entry_price + (stop_distance * 3.0)

            win_prob = ctx.prob_low_bar1_offset10
            trigger = f"Enter LONG at {entry_price:.0f} immediately after bar 1 close"

        else:
            # No trade scenario
            return self._create_no_trade_idea("AGGRESSIVE_FADE", ctx)

        # Calculate R:R and expected value
        avg_rr = 2.0  # Average of 1:1, 2:1, 3:1 with 33% each
        expected_value = (win_prob * avg_rr * stop_distance) - ((1 - win_prob) * stop_distance)
        position_size = self._calculate_position_size(win_prob, avg_rr, confidence)

        return TradeIdea(
            name="Aggressive Fade",
            strategy_type="AGGRESSIVE_FADE",
            direction=direction,
            entry_type="IMMEDIATE",
            entry_price=entry_price,
            stop_loss=stop_loss,
            stop_distance=stop_distance,
            target_1=target_1,
            target_2=target_2,
            target_3=target_3,
            position_size_pct=position_size,
            risk_per_trade=stop_distance,
            win_probability=win_prob,
            risk_reward_ratio=avg_rr,
            expected_value=expected_value,
            max_holding_bars=20 if ctx.bar_type in [BarType.STRONG_BEAR, BarType.STRONG_BULL] else 30,
            entry_valid_until_bar=1,
            risk_level="HIGH",
            confidence=confidence,
            trigger_condition=trigger,
            notes=f"Immediate entry opposite to {ctx.bar_type.value} bar. "
                  f"Based on {ctx.prob_high_bar1:.0%}/{ctx.prob_low_bar1:.0%} high/low probability. "
                  f"Sample: {ctx.sample_size} days."
        )

    def _generate_confirmation_entry(self, bar: FirstBar, ctx: MarketContext,
                                      atr: float, direction: TradeDirection) -> TradeIdea:
        """
        STRATEGY 2: CONFIRMATION ENTRY

        Wait for price to pull back toward bar 1 extreme before entry.
        Gives better entry price but may miss some trades.

        Best for: Moderate probability signals, risk-averse traders
        Risk: Medium (better entry, but may not trigger)
        Reward: Higher R:R due to better entry
        """
        confidence = self._get_confidence(ctx.sample_size)

        if direction == TradeDirection.SHORT:
            # Wait for price to rally back toward bar 1 high
            entry_zone_high = bar.high
            entry_zone_low = bar.high - (atr * 0.20)
            entry_price = (entry_zone_high + entry_zone_low) / 2  # Midpoint of zone

            stop_loss = bar.high + (atr * 0.10)  # Tighter stop possible
            stop_distance = stop_loss - entry_price

            target_1 = entry_price - (stop_distance * 1.5)
            target_2 = entry_price - (stop_distance * 2.5)
            target_3 = entry_price - (stop_distance * 4.0)

            # Lower win prob as trade may not trigger
            trigger_prob = 0.65  # Estimated probability of getting filled
            win_prob = ctx.prob_high_bar1_offset10 * trigger_prob

            trigger = f"Enter SHORT if price rallies to {entry_zone_low:.0f}-{entry_zone_high:.0f} zone in bars 2-6"

        elif direction == TradeDirection.LONG:
            entry_zone_low = bar.low
            entry_zone_high = bar.low + (atr * 0.20)
            entry_price = (entry_zone_high + entry_zone_low) / 2

            stop_loss = bar.low - (atr * 0.10)
            stop_distance = entry_price - stop_loss

            target_1 = entry_price + (stop_distance * 1.5)
            target_2 = entry_price + (stop_distance * 2.5)
            target_3 = entry_price + (stop_distance * 4.0)

            trigger_prob = 0.65
            win_prob = ctx.prob_low_bar1_offset10 * trigger_prob

            trigger = f"Enter LONG if price dips to {entry_zone_low:.0f}-{entry_zone_high:.0f} zone in bars 2-6"

        else:
            return self._create_no_trade_idea("CONFIRMATION", ctx)

        avg_rr = 2.67  # Better R:R due to better entry
        expected_value = (win_prob * avg_rr * stop_distance) - ((1 - win_prob) * stop_distance)
        position_size = self._calculate_position_size(win_prob / trigger_prob, avg_rr, confidence)

        return TradeIdea(
            name="Confirmation Entry",
            strategy_type="CONFIRMATION",
            direction=direction,
            entry_type="LIMIT",
            entry_price=entry_price,
            entry_zone_high=entry_zone_high,
            entry_zone_low=entry_zone_low,
            stop_loss=stop_loss,
            stop_distance=stop_distance,
            target_1=target_1,
            target_2=target_2,
            target_3=target_3,
            position_size_pct=position_size,
            risk_per_trade=stop_distance,
            win_probability=win_prob,
            risk_reward_ratio=avg_rr,
            expected_value=expected_value,
            max_holding_bars=25,
            entry_valid_until_bar=6,
            risk_level="MEDIUM",
            confidence=confidence,
            trigger_condition=trigger,
            notes=f"Wait for pullback to bar 1 extreme zone. Better R:R but ~35% chance of no fill. "
                  f"Cancel if not triggered by bar 6."
        )

    def _generate_scaled_entry(self, bar: FirstBar, ctx: MarketContext,
                                atr: float, direction: TradeDirection) -> TradeIdea:
        """
        STRATEGY 3: SCALED POSITION ENTRY

        Split position into 3 tranches:
        - Tranche 1: Immediate entry (33%)
        - Tranche 2: Pullback entry (33%)
        - Tranche 3: Breakout confirmation (33%)

        Best for: All probability levels, position builders
        Risk: Lower (averaged entry, staged risk)
        Reward: Moderate (balanced approach)
        """
        confidence = self._get_confidence(ctx.sample_size)

        if direction == TradeDirection.SHORT:
            # Three entry levels
            entry_1 = bar.close  # Immediate
            entry_2 = bar.high - (atr * 0.05)  # Near high (pullback)
            entry_3 = bar.low - (atr * 0.10)  # Below low (breakdown confirmation)

            avg_entry = (entry_1 + entry_2 + entry_3) / 3

            # Wider stop for scaled position
            stop_loss = bar.high + (atr * 0.25)
            stop_distance = stop_loss - avg_entry

            target_1 = avg_entry - (stop_distance * 1.0)
            target_2 = avg_entry - (stop_distance * 1.75)
            target_3 = avg_entry - (stop_distance * 2.5)

            # Higher win prob due to averaging
            win_prob = min(0.65, ctx.prob_high_bar1_offset10 + 0.08)

            trigger = (f"Scale into SHORT: "
                      f"T1={entry_1:.0f} (now), "
                      f"T2={entry_2:.0f} (pullback), "
                      f"T3={entry_3:.0f} (breakdown)")

        elif direction == TradeDirection.LONG:
            entry_1 = bar.close
            entry_2 = bar.low + (atr * 0.05)
            entry_3 = bar.high + (atr * 0.10)

            avg_entry = (entry_1 + entry_2 + entry_3) / 3

            stop_loss = bar.low - (atr * 0.25)
            stop_distance = avg_entry - stop_loss

            target_1 = avg_entry + (stop_distance * 1.0)
            target_2 = avg_entry + (stop_distance * 1.75)
            target_3 = avg_entry + (stop_distance * 2.5)

            win_prob = min(0.65, ctx.prob_low_bar1_offset10 + 0.08)

            trigger = (f"Scale into LONG: "
                      f"T1={entry_1:.0f} (now), "
                      f"T2={entry_2:.0f} (dip), "
                      f"T3={entry_3:.0f} (breakout)")

        else:
            return self._create_no_trade_idea("SCALED", ctx)

        avg_rr = 1.75
        expected_value = (win_prob * avg_rr * stop_distance) - ((1 - win_prob) * stop_distance)
        # Smaller per-tranche size
        position_size = self._calculate_position_size(win_prob, avg_rr, confidence) * 0.33

        return TradeIdea(
            name="Scaled Position",
            strategy_type="SCALED",
            direction=direction,
            entry_type="SCALED",
            entry_price=avg_entry,
            entry_zone_high=max(entry_1, entry_2, entry_3),
            entry_zone_low=min(entry_1, entry_2, entry_3),
            stop_loss=stop_loss,
            stop_distance=stop_distance,
            target_1=target_1,
            target_1_pct=40.0,
            target_2=target_2,
            target_2_pct=35.0,
            target_3=target_3,
            target_3_pct=25.0,
            position_size_pct=position_size,
            risk_per_trade=stop_distance,
            win_probability=win_prob,
            risk_reward_ratio=avg_rr,
            expected_value=expected_value,
            max_holding_bars=35,
            entry_valid_until_bar=10,
            risk_level="LOW",
            confidence=confidence,
            trigger_condition=trigger,
            notes=f"Build position across 3 entries (33% each). "
                  f"If only partial fill, adjust stop accordingly. "
                  f"Most conservative approach with best risk management."
        )

    def _create_no_trade_idea(self, strategy_type: str, ctx: MarketContext) -> TradeIdea:
        """Create a NO_TRADE idea when conditions don't warrant a trade"""
        return TradeIdea(
            name=f"No Trade ({strategy_type})",
            strategy_type=strategy_type,
            direction=TradeDirection.NO_TRADE,
            entry_type="NONE",
            entry_price=0,
            stop_loss=0,
            stop_distance=0,
            target_1=0,
            target_2=0,
            target_3=0,
            position_size_pct=0,
            risk_per_trade=0,
            win_probability=0,
            risk_reward_ratio=0,
            expected_value=0,
            max_holding_bars=0,
            risk_level="NONE",
            confidence=self._get_confidence(ctx.sample_size),
            trigger_condition="No trade - insufficient edge",
            notes=f"Edge strength: {ctx.edge_strength}. "
                  f"High prob: {ctx.prob_high_bar1:.0%}, Low prob: {ctx.prob_low_bar1:.0%}. "
                  f"Bar type: {ctx.bar_type.value}. Consider waiting for better setup."
        )

    # -------------------------------------------------------------------------
    # MAIN GENERATION METHOD
    # -------------------------------------------------------------------------

    def generate_trade_ideas(self, bar: FirstBar, prev_close: float,
                             ma_50: float, atr: float = None) -> Tuple[MarketContext, List[TradeIdea]]:
        """
        Generate 3 complete trade ideas based on first bar analysis.

        Args:
            bar: FirstBar object with OHLC data
            prev_close: Previous day's closing price
            ma_50: 50-period moving average value
            atr: Average True Range (optional, defaults to estimated)

        Returns:
            Tuple of (MarketContext, List of 3 TradeIdea objects)
        """
        # Use default ATR if not provided
        if atr is None:
            atr = self.default_atr

        # Build market context
        ctx = self.build_context(bar, prev_close, ma_50)

        # Determine trade direction
        direction = self._determine_direction(ctx)

        # Generate all 3 trade ideas
        ideas = [
            self._generate_aggressive_fade(bar, ctx, atr, direction),
            self._generate_confirmation_entry(bar, ctx, atr, direction),
            self._generate_scaled_entry(bar, ctx, atr, direction)
        ]

        return ctx, ideas

    # -------------------------------------------------------------------------
    # OUTPUT FORMATTING
    # -------------------------------------------------------------------------

    def format_analysis(self, bar: FirstBar, prev_close: float,
                        ma_50: float, atr: float = None) -> str:
        """
        Generate formatted analysis report.
        """
        ctx, ideas = self.generate_trade_ideas(bar, prev_close, ma_50, atr)

        output = []
        output.append("=" * 80)
        output.append("FIRST BAR TRADE ANALYSIS")
        output.append("=" * 80)
        output.append("")

        # Bar Analysis
        output.append("FIRST BAR DATA:")
        output.append(f"  Open:  {bar.open:.2f}")
        output.append(f"  High:  {bar.high:.2f}")
        output.append(f"  Low:   {bar.low:.2f}")
        output.append(f"  Close: {bar.close:.2f}")
        output.append(f"  Range: {bar.range:.2f} pts")
        output.append(f"  Body:  {bar.body:.2f} pts ({bar.body_pct:.0%} of range)")
        output.append("")

        # Market Context
        output.append("MARKET CONTEXT:")
        output.append(f"  Bar Type:       {ctx.bar_type.value.upper()}")
        output.append(f"  Gap:            {ctx.gap_points:+.0f} pts ({ctx.gap_type.value})")
        output.append(f"  Trend:          {ctx.trend.value.upper()} ({ctx.trend_strength:+.2f}% from MA)")
        output.append(f"  Edge Strength:  {ctx.edge_strength}")
        output.append("")

        # Probability Analysis
        output.append("PROBABILITY ANALYSIS:")
        output.append(f"  P(Bar 1 = Day High):      {ctx.prob_high_bar1:.0%}")
        output.append(f"  P(Bar 1 = Day High ±10):  {ctx.prob_high_bar1_offset10:.0%}")
        output.append(f"  P(Bar 1 = Day Low):       {ctx.prob_low_bar1:.0%}")
        output.append(f"  P(Bar 1 = Day Low ±10):   {ctx.prob_low_bar1_offset10:.0%}")
        output.append(f"  High:Low Ratio:           {ctx.high_low_ratio:.1f}:1")
        output.append(f"  Historical Sample:        {ctx.sample_size} days")
        output.append("")

        # Trade Ideas
        for i, idea in enumerate(ideas, 1):
            output.append("-" * 80)
            output.append(f"TRADE IDEA {i}: {idea.name.upper()}")
            output.append("-" * 80)

            if idea.direction == TradeDirection.NO_TRADE:
                output.append(f"  Status:     NO TRADE RECOMMENDED")
                output.append(f"  Reason:     {idea.notes}")
                output.append("")
                continue

            output.append(f"  Direction:      {idea.direction.value}")
            output.append(f"  Entry Type:     {idea.entry_type}")
            output.append(f"  Entry Price:    {idea.entry_price:.2f}")

            if idea.entry_zone_high > 0:
                output.append(f"  Entry Zone:     {idea.entry_zone_low:.2f} - {idea.entry_zone_high:.2f}")

            output.append(f"  Stop Loss:      {idea.stop_loss:.2f} ({idea.stop_distance:.0f} pts)")
            output.append("")
            output.append(f"  Target 1:       {idea.target_1:.2f} (exit {idea.target_1_pct:.0f}%)")
            output.append(f"  Target 2:       {idea.target_2:.2f} (exit {idea.target_2_pct:.0f}%)")
            output.append(f"  Target 3:       {idea.target_3:.2f} (exit {idea.target_3_pct:.0f}%)")
            output.append("")
            output.append(f"  Position Size:  {idea.position_size_pct:.1f}% of capital")
            output.append(f"  Win Prob:       {idea.win_probability:.0%}")
            output.append(f"  Risk:Reward:    1:{idea.risk_reward_ratio:.1f}")
            output.append(f"  Expected Value: {idea.expected_value:.1f} pts/trade")
            output.append("")
            output.append(f"  Max Hold:       {idea.max_holding_bars} bars")
            output.append(f"  Entry Valid:    Until bar {idea.entry_valid_until_bar}")
            output.append(f"  Risk Level:     {idea.risk_level}")
            output.append(f"  Confidence:     {idea.confidence}")
            output.append("")
            output.append(f"  TRIGGER: {idea.trigger_condition}")
            output.append(f"  NOTES:   {idea.notes}")
            output.append("")

        output.append("=" * 80)
        output.append("RECOMMENDATION SUMMARY")
        output.append("=" * 80)

        # Find best idea by expected value
        tradeable = [i for i in ideas if i.direction != TradeDirection.NO_TRADE]
        if tradeable:
            best = max(tradeable, key=lambda x: x.expected_value)
            output.append(f"  Best Strategy:  {best.name}")
            output.append(f"  Direction:      {best.direction.value}")
            output.append(f"  Expected Edge:  {best.expected_value:.1f} pts/trade")

            # Risk warnings
            output.append("")
            output.append("  RISK WARNINGS:")
            if ctx.sample_size < 100:
                output.append("  ⚠️  Low sample size - use reduced position size")
            if ctx.edge_strength in ["WEAK", "NONE"]:
                output.append("  ⚠️  Weak edge - consider skipping this trade")
            if best.risk_level == "HIGH":
                output.append("  ⚠️  High risk strategy - ensure proper risk management")
        else:
            output.append("  NO TRADE RECOMMENDED")
            output.append(f"  Reason: {ctx.edge_strength} edge detected")

        output.append("")

        return "\n".join(output)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def analyze_first_bar(open_price: float, high: float, low: float, close: float,
                      prev_close: float, ma_50: float, atr: float = 100.0) -> str:
    """
    Quick analysis function for command-line use.

    Args:
        open_price: First bar open
        high: First bar high
        low: First bar low
        close: First bar close
        prev_close: Previous day's close
        ma_50: 50-period moving average
        atr: Average True Range (default 100)

    Returns:
        Formatted analysis string
    """
    bar = FirstBar(open=open_price, high=high, low=low, close=close)
    generator = FirstBarTradeGenerator(default_atr=atr)
    return generator.format_analysis(bar, prev_close, ma_50, atr)


def get_trade_ideas(open_price: float, high: float, low: float, close: float,
                    prev_close: float, ma_50: float, atr: float = 100.0) -> List[dict]:
    """
    Get trade ideas as list of dictionaries (for programmatic use).

    Returns:
        List of trade idea dictionaries
    """
    bar = FirstBar(open=open_price, high=high, low=low, close=close)
    generator = FirstBarTradeGenerator(default_atr=atr)
    ctx, ideas = generator.generate_trade_ideas(bar, prev_close, ma_50, atr)
    return [idea.to_dict() for idea in ideas]


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # Example: Analyze a first bar
    print("\n" + "="*80)
    print("EXAMPLE 1: Bearish First Bar in Uptrend with Small Gap Up")
    print("="*80 + "\n")

    analysis = analyze_first_bar(
        open_price=21500,
        high=21520,
        low=21450,
        close=21460,  # Bearish close (below open)
        prev_close=21470,  # Small gap up (+30 pts)
        ma_50=21400,  # Price above MA (uptrend)
        atr=100
    )
    print(analysis)

    print("\n" + "="*80)
    print("EXAMPLE 2: Strong Bullish First Bar in Bull Trend with Large Gap Down")
    print("="*80 + "\n")

    analysis = analyze_first_bar(
        open_price=21300,
        high=21380,
        low=21290,
        close=21370,  # Strong bullish (body 78% of range)
        prev_close=21420,  # Large gap down (-120 pts)
        ma_50=21250,  # Price above MA (bull trend)
        atr=120
    )
    print(analysis)

    print("\n" + "="*80)
    print("EXAMPLE 3: Neutral First Bar (Doji)")
    print("="*80 + "\n")

    analysis = analyze_first_bar(
        open_price=21500,
        high=21540,
        low=21470,
        close=21505,  # Neutral (body only 7% of range)
        prev_close=21480,  # Small gap up
        ma_50=21520,  # Slight downtrend
        atr=100
    )
    print(analysis)
