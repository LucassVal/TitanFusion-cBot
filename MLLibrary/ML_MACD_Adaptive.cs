// ==================================================================================
// ML ENGINE #6: MACD Parameters Adaptive + ADX for Trend Detection
// Purpose: Adjusts MACD parameters based on trend strength (ADX)
// ==================================================================================

// === REQUIRED FIELDS ===
// private DirectionalMovementSystem _adx;
// private MacdHistogram _macd;
// private int _adaptiveMacdFast = 12;
// private int _adaptiveMacdSlow = 26;
// private int _lastMacdAdjustment = 0;
// public bool EnableMLEngines { get; set; }
// public bool MLEnableMACD { get; set; }

private void AdjustMacdParameters()
{
    if (!EnableMLEngines || !MLEnableMACD) return;
    
    // Initialize ADX if needed
    if (_adx == null)
        _adx = Indicators.DirectionalMovementSystem(14);
    
    // Check every 50 bars (not too frequent)
    if (Bars.Count % 50 != 0) return;
    
    double currentADX = _adx.ADX.Last(0);
    
    // === ADAPTIVE LOGIC ===
    
    // Case 1: Strong trend (ADX > 25) → Fast MACD
    if (currentADX > 25)
    {
        if (_adaptiveMacdFast != 8) // Trending parameters
        {
            _adaptiveMacdFast = 8;
            _adaptiveMacdSlow = 17;
            _lastMacdAdjustment = Bars.Count;
            
            // Reinitialize MACD
            _macd = Indicators.MacdHistogram(Bars.ClosePrices, _adaptiveMacdFast, _adaptiveMacdSlow, 9);
            Print($"🤖 ML MACD: ADX {Math.Round(currentADX, 1)} (trending) → Fast MACD ({_adaptiveMacdFast},{_adaptiveMacdSlow},9)");
        }
        return;
    }
    
    // Case 2: Weak trend/ranging (ADX < 20) → Slow MACD
    if (currentADX < 20)
    {
        if (_adaptiveMacdFast != 16) // Ranging parameters
        {
            _adaptiveMacdFast = 16;
            _adaptiveMacdSlow = 35;
            _lastMacdAdjustment = Bars.Count;
            
            // Reinitialize MACD
            _macd = Indicators.MacdHistogram(Bars.ClosePrices, _adaptiveMacdFast, _adaptiveMacdSlow, 9);
            Print($"🤖 ML MACD: ADX {Math.Round(currentADX, 1)} (ranging) → Slow MACD ({_adaptiveMacdFast},{_adaptiveMacdSlow},9)");
        }
        return;
    }
    
    // Case 3: Moderate trend → Keep standard MACD (12,26,9)
    if (_adaptiveMacdFast != 12)
    {
        _adaptiveMacdFast = 12;
        _adaptiveMacdSlow = 26;
        _macd = Indicators.MacdHistogram(Bars.ClosePrices, 12, 26, 9);
        Print($"🤖 ML MACD: ADX {Math.Round(currentADX, 1)} (moderate) → Standard MACD (12,26,9)");
    }
}
