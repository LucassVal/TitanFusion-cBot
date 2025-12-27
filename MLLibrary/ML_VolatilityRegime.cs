// ==================================================================================
// ML ENGINE #8: Volatility Regime Detector + Parameter Autotune
// Purpose: Detects market regime (Trending, Ranging, Spiking, LowVolatility)
//          and automatically adjusts parameters accordingly
// ==================================================================================

// === REQUIRED FIELDS ===
// private DirectionalMovementSystem _adx;
// private AverageTrueRange _atr;
// private HullMovingAverage _hmaHigh, _hmaLow, _hmaClose;
// private int _adaptiveTunnelPeriod;
// private double _atrThreshold;
// private double _adaptiveRRRatio;
// public bool EnableMLEngines { get; set; }

// === REGIME ENUM ===
private enum VolatilityRegime
{
    Trending,
    Ranging,
    Spiking,
    LowVolatility  // Dead market, avoid signals
}
private VolatilityRegime _currentRegime = VolatilityRegime.Ranging;
private VolatilityRegime _lastRegime = VolatilityRegime.Ranging;

private void DetectVolatilityRegime()
{
    if (!EnableMLEngines) return;
    
    // Check every 20 bars
    if (Bars.Count % 20 != 0) return;
    
    // Safety check for _atr
    if (_atr == null || _atr.Result == null || _atr.Result.Count < 5) return;
    
    double currentATR = _atr.Result.Last(0);
    
    // Calculate average ATR with safety check for NaN
    double avgATR = 0;
    int count = Math.Min(50, _atr.Result.Count);
    if (count > 0)
    {
        for (int i = 0; i < count; i++)
            avgATR += _atr.Result.Last(i);
        avgATR /= count;
    }
    
    double atrRatio = avgATR > 0 ? currentATR / avgATR : 1.0; // Default to 1.0 if no data
    
    // Initialize ADX if needed
    if (_adx == null)
        _adx = Indicators.DirectionalMovementSystem(14);
    
    double currentADX = _adx.ADX.Last(0);
    
    // Detect current bar size
    double barRange = Bars.HighPrices.Last(0) - Bars.LowPrices.Last(0);
    double avgBarRange = 0;
    for (int i = 1; i <= 20; i++)
        avgBarRange += Bars.HighPrices.Last(i) - Bars.LowPrices.Last(i);
    avgBarRange /= 20;
    
    _lastRegime = _currentRegime;
    
    // === REGIME DETECTION ===
    
    // SPIKING: ATR spike >150%, wide bars
    if (atrRatio > 1.5 || barRange > avgBarRange * 2.0)
    {
        _currentRegime = VolatilityRegime.Spiking;
    }
    // LOW VOLATILITY: ATR below 50% of average (dead market)
    else if (atrRatio < 0.5)
    {
        _currentRegime = VolatilityRegime.LowVolatility;
    }
    // TRENDING: High ADX, stable ATR
    else if (currentADX > 25 && atrRatio < 1.3)
    {
        _currentRegime = VolatilityRegime.Trending;
    }
    // RANGING: Low ADX
    else if (currentADX < 20)
    {
        _currentRegime = VolatilityRegime.Ranging;
    }
    
    // Log regime transitions
    if (_currentRegime != _lastRegime)
    {
        Print($"🔄 REGIME CHANGE: {_lastRegime} → {_currentRegime} (ADX: {Math.Round(currentADX, 1)}, ATR ratio: {Math.Round(atrRatio, 2)})");
        ApplyRegimeParameters();
    }
}

private void ApplyRegimeParameters()
{
    if (!EnableMLEngines) return;
    
    switch (_currentRegime)
    {
        case VolatilityRegime.Trending:
            // Fast tunnel, low ATR filter, high RR
            if (_adaptiveTunnelPeriod > 30)
            {
                _adaptiveTunnelPeriod = Math.Max(30, _adaptiveTunnelPeriod - 10);
                _hmaHigh = Indicators.HullMovingAverage(Bars.HighPrices, _adaptiveTunnelPeriod);
                _hmaLow = Indicators.HullMovingAverage(Bars.LowPrices, _adaptiveTunnelPeriod);
                _hmaClose = Indicators.HullMovingAverage(Bars.ClosePrices, _adaptiveTunnelPeriod);
            }
            _atrThreshold *= 0.85; // More permissive
            if (_adaptiveRRRatio < 2.5)
                _adaptiveRRRatio += 0.1;
            Print($"⚙️ TRENDING MODE: Fast tunnel ({_adaptiveTunnelPeriod}), Low filter, High RR ({Math.Round(_adaptiveRRRatio, 1)})");
            break;
        
        case VolatilityRegime.Ranging:
            // Slow tunnel, high ATR filter, low RR
            if (_adaptiveTunnelPeriod < 70)
            {
                _adaptiveTunnelPeriod = Math.Min(70, _adaptiveTunnelPeriod + 10);
                _hmaHigh = Indicators.HullMovingAverage(Bars.HighPrices, _adaptiveTunnelPeriod);
                _hmaLow = Indicators.HullMovingAverage(Bars.LowPrices, _adaptiveTunnelPeriod);
                _hmaClose = Indicators.HullMovingAverage(Bars.ClosePrices, _adaptiveTunnelPeriod);
            }
            _atrThreshold *= 1.20; // More restrictive
            if (_adaptiveRRRatio > 1.5)
                _adaptiveRRRatio -= 0.1;
            Print($"⚙️ RANGING MODE: Slow tunnel ({_adaptiveTunnelPeriod}), High filter, Low RR ({Math.Round(_adaptiveRRRatio, 1)})");
            break;
        
        case VolatilityRegime.Spiking:
            // DISABLE signals entirely, wait for normalization
            Print($"⚠️ SPIKING MODE: All signals DISABLED until regime normalizes");
            break;
        
        case VolatilityRegime.LowVolatility:
            // Dead market - be very cautious
            _atrThreshold *= 1.50; // Very restrictive
            Print($"⚠️ LOW VOLATILITY MODE: Very restrictive filters applied");
            break;
    }
}

// ==================================================================================
// USAGE: Check if signals should be blocked
// ==================================================================================
private bool IsRegimeBlocking()
{
    return _currentRegime == VolatilityRegime.Spiking || _currentRegime == VolatilityRegime.LowVolatility;
}
