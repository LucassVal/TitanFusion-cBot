// ==================================================================================
// ML ENGINE #12: ORDER FLOW ANALYSIS (Simplified)
// Purpose: Analyzes buy/sell volume delta to detect smart money
// Positive delta = buying pressure, Negative = selling pressure
// Source: Concept from srlcarlg/srl-ctrader-indicators
// ==================================================================================

// === REQUIRED FIELDS ===
// private double _volumeDelta = 0;          // Current delta
// private double _cumulativeDelta = 0;      // Cumulative delta
// private double _deltaMA = 0;              // Moving average of delta
// private Queue<double> _deltaHistory = new Queue<double>();

private double _volumeDelta = 0;
private double _cumulativeDelta = 0;
private double _deltaMA = 0;
private Queue<double> _deltaHistory = new Queue<double>();
private const int DELTA_PERIOD = 20;

/// <summary>
/// Estimates buy/sell volume using candle structure
/// Green candle with long body = more buying, Red candle = more selling
/// </summary>
private void CalculateOrderFlowDelta()
{
    double open = Bars.OpenPrices.LastValue;
    double close = Bars.ClosePrices.LastValue;
    double high = Bars.HighPrices.LastValue;
    double low = Bars.LowPrices.LastValue;
    double volume = Bars.TickVolumes.LastValue;
    
    double range = high - low;
    if (range <= 0) range = Symbol.PipSize;
    
    double body = Math.Abs(close - open);
    double bodyRatio = body / range;
    
    // Estimate delta: positive = more buying, negative = more selling
    if (close > open)
    {
        // Green candle: buying dominates
        double buyStrength = bodyRatio;
        double upperWick = high - close;
        double lowerWick = open - low;
        
        // Long lower wick = absorption of sellers
        if (lowerWick > upperWick * 2)
            buyStrength *= 1.5;
        
        _volumeDelta = volume * buyStrength;
    }
    else
    {
        // Red candle: selling dominates
        double sellStrength = bodyRatio;
        double upperWick = high - open;
        double lowerWick = close - low;
        
        // Long upper wick = absorption of buyers
        if (upperWick > lowerWick * 2)
            sellStrength *= 1.5;
        
        _volumeDelta = -volume * sellStrength;
    }
    
    // Update cumulative delta
    _cumulativeDelta += _volumeDelta;
    
    // Update delta MA
    _deltaHistory.Enqueue(_volumeDelta);
    if (_deltaHistory.Count > DELTA_PERIOD)
        _deltaHistory.Dequeue();
    
    _deltaMA = _deltaHistory.Average();
}

/// <summary>
/// Returns Order Flow signal strength (-100 to +100)
/// Positive = smart money buying, Negative = smart money selling
/// </summary>
private double GetOrderFlowSignal()
{
    CalculateOrderFlowDelta();
    
    if (_deltaMA == 0) return 0;
    
    // Normalize: current delta vs moving average
    double signal = (_volumeDelta / Math.Abs(_deltaMA)) * 50;
    
    // Boost if cumulative delta confirms direction
    if (_cumulativeDelta > 0 && _volumeDelta > 0)
        signal *= 1.2;
    else if (_cumulativeDelta < 0 && _volumeDelta < 0)
        signal *= 1.2;
    
    return Math.Max(-100, Math.Min(100, signal));
}

/// <summary>
/// Returns true if Order Flow confirms direction
/// </summary>
private bool IsOrderFlowConfirming(bool isBullish)
{
    double signal = GetOrderFlowSignal();
    
    if (isBullish)
        return signal > 20; // Buying pressure
    else
        return signal < -20; // Selling pressure
}
