// ==================================================================================
// ML ENGINE #9: RSI Adaptive Thresholds + Divergence Detection
// Purpose: Adjusts RSI overbought/oversold thresholds and detects divergences
// ==================================================================================

// === REQUIRED FIELDS ===
// private double _adaptiveRsiOverbought = 70.0;
// private double _adaptiveRsiOversold = 30.0;
// private int _divergenceLookback = 10;
// private RelativeStrengthIndex _rsi;
// private MacdHistogram _macd;
// private List<SignalPrediction> _predictions;
// public bool EnableMLEngines { get; set; }

private void AdjustRsiThresholds()
{
    if (!EnableMLEngines) return;
    
    int validated = _predictions.Count(p => p.Result != null);
    int correct = _predictions.Count(p => p.Result == true);
    double accuracy = validated > 0 ? (double)correct / validated : 0.5;
    
    // If accuracy is low, tighten RSI thresholds (more conservative)
    if (accuracy < 0.50)
    {
        _adaptiveRsiOverbought = Math.Max(65, _adaptiveRsiOverbought - 1);
        _adaptiveRsiOversold = Math.Min(35, _adaptiveRsiOversold + 1);
        Print($"🤖 ML RSI: Accuracy {Math.Round(accuracy*100)}% low → Tightened to {_adaptiveRsiOverbought}/{_adaptiveRsiOversold}");
    }
    // If accuracy is high, loosen thresholds (allow more signals)
    else if (accuracy > 0.70)
    {
        _adaptiveRsiOverbought = Math.Min(75, _adaptiveRsiOverbought + 0.5);
        _adaptiveRsiOversold = Math.Max(25, _adaptiveRsiOversold - 0.5);
        Print($"🤖 ML RSI: Accuracy {Math.Round(accuracy*100)}% good → Loosened to {_adaptiveRsiOverbought}/{_adaptiveRsiOversold}");
    }
}

// ==================================================================================
// DIVERGENCE DETECTION (RSI + MACD)
// ==================================================================================

private bool DetectBullishDivergence(int index)
{
    if (index < _divergenceLookback + 5) return false;
    
    // Find recent swing lows in price
    double currentLow = Bars.LowPrices[index];
    double prevLow = double.MaxValue;
    int prevLowIndex = -1;
    
    for (int i = index - 3; i >= index - _divergenceLookback; i--)
    {
        if (IsSwingLow(i) && Bars.LowPrices[i] < prevLow)
        {
            prevLow = Bars.LowPrices[i];
            prevLowIndex = i;
            break;
        }
    }
    
    if (prevLowIndex < 0) return false;
    
    // Bullish divergence: Price makes lower low, but RSI makes higher low
    bool priceLowerLow = currentLow < prevLow;
    double currentRsi = _rsi.Result[index];
    double prevRsi = _rsi.Result[prevLowIndex];
    bool rsiHigherLow = currentRsi > prevRsi;
    
    // Also check MACD
    double currentMacd = _macd.Histogram[index];
    double prevMacd = _macd.Histogram[prevLowIndex];
    bool macdHigherLow = currentMacd > prevMacd;
    
    bool hasDivergence = priceLowerLow && (rsiHigherLow || macdHigherLow);
    
    if (hasDivergence && IsLastBar)
    {
        Print($"📈 BULLISH DIVERGENCE detected! Price LL but RSI/MACD HL");
    }
    
    return hasDivergence;
}

private bool DetectBearishDivergence(int index)
{
    if (index < _divergenceLookback + 5) return false;
    
    // Find recent swing highs in price
    double currentHigh = Bars.HighPrices[index];
    double prevHigh = double.MinValue;
    int prevHighIndex = -1;
    
    for (int i = index - 3; i >= index - _divergenceLookback; i--)
    {
        if (IsSwingHigh(i) && Bars.HighPrices[i] > prevHigh)
        {
            prevHigh = Bars.HighPrices[i];
            prevHighIndex = i;
            break;
        }
    }
    
    if (prevHighIndex < 0) return false;
    
    // Bearish divergence: Price makes higher high, but RSI makes lower high
    bool priceHigherHigh = currentHigh > prevHigh;
    double currentRsi = _rsi.Result[index];
    double prevRsi = _rsi.Result[prevHighIndex];
    bool rsiLowerHigh = currentRsi < prevRsi;
    
    // Also check MACD
    double currentMacd = _macd.Histogram[index];
    double prevMacd = _macd.Histogram[prevHighIndex];
    bool macdLowerHigh = currentMacd < prevMacd;
    
    bool hasDivergence = priceHigherHigh && (rsiLowerHigh || macdLowerHigh);
    
    if (hasDivergence && IsLastBar)
    {
        Print($"📉 BEARISH DIVERGENCE detected! Price HH but RSI/MACD LH");
    }
    
    return hasDivergence;
}
