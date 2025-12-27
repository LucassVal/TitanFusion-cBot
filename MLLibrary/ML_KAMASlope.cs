                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            // ==================================================================================
// ML ENGINE #11: KAMA SLOPE (Kaufman's Adaptive Moving Average)
// Purpose: Detects trending vs ranging market using KAMA slope
// Slope = 0 means ranging, +/- means bull/bear trend
// Source: Adapted from opplieam/ctrader-bot-indicator
// ==================================================================================

// === REQUIRED FIELDS ===
// private double _kamaValue = 0;
// private double _kamaSlope = 0;
// private double _prevKamaValue = 0;
// private int _kamaPeriod = 10;
// private int _kamaFastPeriod = 2;
// private int _kamaSlowPeriod = 30;

private double _kamaValue = 0;
private double _kamaSlope = 0;
private double _prevKamaValue = 0;

private double CalculateKAMA(int period = 10, int fastPeriod = 2, int slowPeriod = 30)
{
    if (Bars.Count < period + 1) return Bars.ClosePrices.LastValue;
    
    // Efficiency Ratio (ER)
    double change = Math.Abs(Bars.ClosePrices.LastValue - Bars.ClosePrices.Last(period));
    double volatility = 0;
    for (int i = 0; i < period; i++)
    {
        volatility += Math.Abs(Bars.ClosePrices.Last(i) - Bars.ClosePrices.Last(i + 1));
    }
    
    double er = volatility > 0 ? change / volatility : 0;
    
    // Smoothing Constant (SC)
    double fastSC = 2.0 / (fastPeriod + 1);
    double slowSC = 2.0 / (slowPeriod + 1);
    double sc = Math.Pow(er * (fastSC - slowSC) + slowSC, 2);
    
    // Calculate KAMA
    if (_kamaValue == 0)
        _kamaValue = Bars.ClosePrices.Last(period);
    
    _prevKamaValue = _kamaValue;
    _kamaValue = _kamaValue + sc * (Bars.ClosePrices.LastValue - _kamaValue);
    
    return _kamaValue;
}

private double GetKAMASlope()
{
    if (_prevKamaValue == 0) return 0;
    
    double slopePips = (_kamaValue - _prevKamaValue) / Symbol.PipSize;
    
    // Normalize slope: 0 = flat, >0.5 = up trend, <-0.5 = down trend
    _kamaSlope = Math.Max(-3, Math.Min(3, slopePips));
    
    return _kamaSlope;
}

/// <summary>
/// Returns true if KAMA indicates ranging market (slope near 0)
/// </summary>
private bool IsKAMARanging(double threshold = 0.3)
{
    CalculateKAMA();
    GetKAMASlope();
    
    return Math.Abs(_kamaSlope) < threshold;
}

/// <summary>
/// Returns KAMA direction: 1 = bullish, -1 = bearish, 0 = ranging
/// </summary>
private int GetKAMADirection(double threshold = 0.5)
{
    CalculateKAMA();
    GetKAMASlope();
    
    if (_kamaSlope > threshold) return 1;   // Bullish
    if (_kamaSlope < -threshold) return -1; // Bearish
    return 0; // Ranging
}
