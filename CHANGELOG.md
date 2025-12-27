# Changelog

All notable changes to Titan Fusion Quantum will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2025-12-27

### 🎉 Initial Release - Titan Fusion Quantum

First stable release of the AI-powered trading system for cTrader.

### ✨ Added

#### Core System
- **cTrader cBot** (`TitanFusion_QuantumBot.cs`)
  - Multi-symbol support with isolated analysis per trading pair
  - Real-time data export (candles, positions, sentiment, metadata)
  - 2-tier breakeven system (Tier 1: +0.5%, Tier 2: +3.0%)
  - Dynamic SL/TP management
  - Risk management layers (daily loss, max trades, margin checks)
  - Portfolio exposure tracking

- **Python AI Brain** (`quantum_brain.py`)
  - Google Gemini 2.0 Flash integration
  - Multi-timeframe analysis (M1, M5, M15, M30, H1, H2, H4)
  - 4-layer validation system
  - Signal history tracking
  - Automated market data fetching

#### Market Sentiment System
- Real broker sentiment data integration
  - Buy/Sell percentage tracking
  - Overbought/Oversold detection
  - Market-specific thresholds:
    - Gold/Silver: 70%/30%
    - Bitcoin/Crypto: 80%/20%
    - Forex pairs: 75%/25%
    - Stock indices: 72%/28%

- **Sentiment divergence detection**
  - Bullish divergence: Price falling + Sentiment rising
  - Bearish divergence: Price rising + Sentiment falling
  - Historical sentiment tracking (20 data points)
  - Automatic storage per symbol

- **Contrarian analysis**
  - Fade-the-crowd strategy
  - Crowd behavior emojis (🔥 = hot, ❄️ = cold)
  - Extreme zone warnings

#### Technical Analysis
- **Indicators**
  - RSI-14 with overbought/oversold zones
  - EMA-200 (long-term trend)
  - EMA-20 (short-term momentum)
  - **RSI + Sentiment correlation alerts**

- **Candlestick Patterns**
  - Bullish/Bearish Engulfing
  - Hammer/Inverted Hammer
  - Doji patterns
  - Pattern detection across multiple timeframes

- **Multi-Timeframe Analysis**
  - H4: Macro bias
  - H1: Intermediate trend
  - M30/M15: Entry refinement
  - M5: Execution timing

#### Trading Strategies
- **Fast Scalp** (M1-M5, RR 1:2)
- **Scalp** (M5-M15, RR 1:3)
- **Intraday** (M15-H1, RR 1:4)
- **Swing** (H1-H4, RR 1:5+)

Each strategy with independent confidence scoring.

#### Risk Management
- **2-Tier Breakeven System**
  - Tier 1: Move SL to +0.1% when trade reaches +0.5% profit
  - Tier 2: Lock +1.5% profit when trade reaches +3.0% gain
  - Preserves existing Take Profit levels
  - Prevents accidental TP removal

- **Protection Layers**
  - Maximum daily loss percentage
  - Maximum trades per day
  - Portfolio exposure limits
  - Free margin verification before trade execution
  - Volume normalization

#### AI Integration
- Google Gemini 2.0 Flash API
- Natural language trade analysis
- Context-aware decision making
- Confidence scoring (0-100%)
- Multi-strategy synthesis
- Macro sentiment integration (VIX, DXY)

#### Data Management
- Symbol-specific data folders
- Signal history per symbol
- Sentiment history tracking
- Atomic file writes (crash-safe)
- JSON-based data exchange

### 🔧 Configuration
- Comprehensive parameter set for cBot
- Python configuration via `config.py`
- Environment variable support
- Data folder customization

### 📚 Documentation
- Comprehensive README.md
- Configuration examples
- Troubleshooting guide
- System architecture diagrams

### 🔒 Security
- API key protection via `.gitignore`
- Configuration templates (`config.example.py`)
- Sensitive data exclusion from repository

---

## [Unreleased]

### Planned Features
- Backtesting module
- Performance dashboard
- Trade statistics visualizations
- Multi-account support
- Telegram notifications
- Custom strategy builder

---

## Version History

- **v1.0.0** (2025-12-27) - Initial stable release
- **v0.9.x** (2025-12) - Beta testing phase
- **v0.5.x** (2025-11) - Alpha development

---

## Migration Notes

### From Gold Emperor Quantum → Titan Fusion Quantum

If upgrading from the previous Gold Emperor system:

1. **Rename data folder:**
   - Old: `C:\Users\USERNAME\Documents\GoldEmperorAI`
   - New: `C:\Users\USERNAME\Documents\TitanFusionAI`

2. **Update cBot:**
   - Remove old `GoldEmperor_QuantumBot.cs`
   - Import new `TitanFusion_QuantumBot.cs`

3. **Update Python:**
   - Update `DATA_FOLDER` in `config.py`
   - Verify Gemini API key is set

4. **Preserve history (optional):**
   ```bash
   # Copy signal history
   xcopy "C:\Users\USERNAME\Documents\GoldEmperorAI" "C:\Users\USERNAME\Documents\TitanFusionAI" /E /I
   ```

---

## Support

For issues, feature requests, or questions:
- 🐛 [Report a Bug](https://github.com/LucassVal/TitanFusion-cBot/issues)
- 💡 [Request a Feature](https://github.com/LucassVal/TitanFusion-cBot/issues)
- 📧 [Contact Author](https://github.com/LucassVal)

---

**[Full Changelog](https://github.com/LucassVal/TitanFusion-cBot/compare/v0.9.0...v1.0.0)**
