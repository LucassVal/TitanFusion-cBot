// ==================================================================================
// ML ENGINE #4: Tunnel Period Adaptive
// Purpose: Adjusts HMA tunnel period based on lag and whipsaw rate
// ==================================================================================

// === REQUIRED FIELDS ===
// private List<TunnelQuality> _tunnelQualities = new List<TunnelQuality>();
// private int _lastTunnelAdjustment = 0;
// private int _adaptiveTunnelPeriod = 55;
// private HullMovingAverage _hmaHigh, _hmaLow, _hmaClose;
// public bool EnableMLEngines { get; set; }
// public int MLAdjustmentFrequency { get; set; }

// === TUNNEL QUALITY CLASS ===
private class TunnelQuality
{
    public int Period { get; set; }
    public int LagBars { get; set; }
    public bool Whipsaw { get; set; }
}
private List<TunnelQuality> _tunnelQualities = new List<TunnelQuality>();

private void AdjustTunnelPeriod()
{
    if (!EnableMLEngines) return;
    
    int qualityCount = _tunnelQualities.Count;
    
    // Need at least MLAdjustmentFrequency signals
    if (qualityCount < MLAdjustmentFrequency) return;
    
    // Only adjust every MLAdjustmentFrequency new signals
    if (qualityCount - _lastTunnelAdjustment < MLAdjustmentFrequency) return;
    
    _lastTunnelAdjustment = qualityCount;
    
    // Calculate metrics
    double avgLag = _tunnelQualities.Average(t => t.LagBars);
    double whipsawRate = _tunnelQualities.Count(t => t.Whipsaw) / (double)qualityCount;
    
    // === ADAPTIVE LOGIC ===
    
    // Case 1: High lag (>5 bars) → Decrease period (faster response)
    if (avgLag > 5 && whipsawRate < 0.3)
    {
        if (_adaptiveTunnelPeriod > 20) // Min 20
        {
            _adaptiveTunnelPeriod -= 5;
            Print($"🤖 ML Tunnel: Avg lag {Math.Round(avgLag, 1)} bars → Decreased period to {_adaptiveTunnelPeriod} (faster response)");
            
            // Reinitialize HMAs with new period
            _hmaHigh = Indicators.HullMovingAverage(Bars.HighPrices, _adaptiveTunnelPeriod);
            _hmaLow = Indicators.HullMovingAverage(Bars.LowPrices, _adaptiveTunnelPeriod);
            _hmaClose = Indicators.HullMovingAverage(Bars.ClosePrices, _adaptiveTunnelPeriod);
        }
        return;
    }
    
    // Case 2: High whipsaw rate (>40%) → Increase period (smoother)
    if (whipsawRate > 0.4)
    {
        if (_adaptiveTunnelPeriod < 100) // Max 100
        {
            _adaptiveTunnelPeriod += 5;
            Print($"🤖 ML Tunnel: Whipsaw rate {Math.Round(whipsawRate * 100)}% → Increased period to {_adaptiveTunnelPeriod} (smoother)");
            
            // Reinitialize HMAs
            _hmaHigh = Indicators.HullMovingAverage(Bars.HighPrices, _adaptiveTunnelPeriod);
            _hmaLow = Indicators.HullMovingAverage(Bars.LowPrices, _adaptiveTunnelPeriod);
            _hmaClose = Indicators.HullMovingAverage(Bars.ClosePrices, _adaptiveTunnelPeriod);
        }
        return;
    }
    
    // Case 3: Optimal performance → Maintain
    Print($"🤖 ML Tunnel: Lag {Math.Round(avgLag, 1)}, whipsaw {Math.Round(whipsawRate * 100)}% → Period maintained at {_adaptiveTunnelPeriod}");
}
