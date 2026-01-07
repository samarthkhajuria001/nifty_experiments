# Nifty Experiments

A collection of questions, thoughts, and explorations regarding NIFTY 50 trading patterns and probability analysis.

## Project Structure

```
nifty_experiments/
├── data/                              # Market data (CSV files)
│   ├── nifty50_minute_complete-5min.csv    # 5-minute OHLC data
│   ├── nifty50_minute_complete-120min.csv  # 2-hour OHLC data
│   └── nifty50_minute_2022-30min.csv       # 30-minute data (2022)
│
├── scripts/                           # Python analysis scripts
│   ├── high_low_probability/          # High/Low timing probability analysis
│   ├── opening_patterns/              # Opening bar pattern analysis
│   ├── trend_analysis/                # Trend-based analysis
│   └── utils/                         # Utility/helper scripts
│
├── notebooks/                         # Jupyter notebooks
│   ├── high_low_day_prob.ipynb
│   └── high_low_prob_analysis_v2.ipynb
│
├── analysis/                          # Analysis reports (Markdown)
│   ├── comprehensive_high_low_analysis.md  # Complete high/low timing analysis
│   ├── trading_analysis_qa.md              # Q&A format analysis
│   ├── 30min_bar_analysis.md               # 30-min opening patterns
│   ├── 30min_pattern_outcomes.md           # Pattern outcomes
│   ├── 30min_opening_patterns_analysis.md  # Detailed 30-min analysis
│   └── 2hr_bar_analysis.md                 # 2-hour bar analysis
│
├── output/                            # Generated outputs (CSVs, PNGs)
│   ├── high_low_probability/          # Base probability analysis
│   ├── gap_analysis/                  # Gap-based analysis
│   ├── trend_patterns/                # Trend-filtered analysis
│   │   ├── bull/
│   │   └── bear/
│   └── small_gap/                     # Small gap (<50 pts) analysis
│       ├── uptrend/
│       └── downtrend/
│
├── README.md
├── LICENSE
└── rules.md                           # Trading rules
```

## Running Scripts

Scripts should be run from the project root directory or from their respective folders. Each script references data files using relative paths.

Example:
```bash
cd scripts/high_low_probability
python high_low_prob_analysis.py
```

## Key Analyses

### High/Low Probability Analysis
Scripts in `scripts/high_low_probability/` analyze when the day's high and low are typically established based on various market conditions.

### Opening Patterns
Scripts in `scripts/opening_patterns/` analyze the first 30 minutes to 1.5 hours of trading to predict day close direction.

### Trend Analysis
Scripts in `scripts/trend_analysis/` examine how 2-hour trends affect daily patterns and reversals.

## Data Requirements

The analysis requires NIFTY 50 minute-level OHLC data in CSV format with columns:
- `datetime` or `date`
- `open`, `high`, `low`, `close`
- `volume` (optional)
