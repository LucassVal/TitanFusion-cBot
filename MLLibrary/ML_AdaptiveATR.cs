// ==================================================================================
// ML ENGINE #1: Adaptive ATR Threshold
// Purpose: Adjusts ATR threshold based on historical signal accuracy
// Increases threshold when accuracy is low, decreases when high
// ==================================================================================

// === REQUIRED FIELDS ===
// private List<SignalPrediction> _predictions = new List<SignalPrediction>();
// private int _lastMLAdjustment = 0;
// private double _atrThreshold = 1.0;        // Current threshold
// private double _initialATRThreshold = 1.0; // Initial value for bounds

// === SIGNAL PREDICTION CLASS ===
// private class SignalPrediction
// {
//     public bool? Result { get; set; }      // true = correct, false = wrong, null = pending
//     public double ActualMove { get; set; } // Actual price movement in pips
// }

private void AdjustATRThreshold()
{
    int validatedCount = _predictions.Count(p => p.Result != null);
    
    // Need at least 10 signals to start learning
    if (validatedCount < 10) return;
    
    // Only adjust every 10 new signals
    if (validatedCount - _lastMLAdjustment < 10) return;
    
    _lastMLAdjustment = validatedCount;
    
    // Calculate current performance
    int correctCount = _predictions.Count(p => p.Result == true);
    double accuracy = (double)correctCount / validatedCount;
    
    var wins = _predictions.Where(p => p.Result == true).ToList();
    var losses = _predictions.Where(p => p.Result == false).ToList();
    
    double avgWinPips = wins.Any() ? wins.Average(p => Math.Abs(p.ActualMove) / Symbol.PipSize) : 0;
    double avgLossPips = losses.Any() ? losses.Average(p => Math.Abs(p.ActualMove) / Symbol.PipSize) : 0;
    
    // === ADAPTIVE LOGIC ===
    
    // Case 1: Low accuracy (<50%) → Market too noisy, increase ATR filter
    if (accuracy < 0.50)
    {
        _atrThreshold *= 1.15; // Increase 15%
        Print($"🤖 ML: Accuracy {Math.Round(accuracy * 100)}% → Increased ATR threshold to {Math.Round(_atrThreshold, 2)} (filtering more noise)");
        return;
    }
    
    // Case 2: Good accuracy (50-70%) but small wins → Increase filter for better quality
    if (accuracy >= 0.50 && accuracy < 0.70 && avgWinPips < avgLossPips * 1.5)
    {
        _atrThreshold *= 1.08; // Increase 8%
        Print($"🤖 ML: Accuracy {Math.Round(accuracy * 100)}% but W/L ratio low → Increased ATR threshold to {Math.Round(_atrThreshold, 2)}");
        return;
    }
    
    // Case 3: High accuracy (>75%) and good W/L → Reduce filter for more signals
    if (accuracy > 0.75 && avgWinPips > avgLossPips * 2.0)
    {
        // Don't go below 50% of initial threshold
        if (_atrThreshold > _initialATRThreshold * 0.5)
        {
            _atrThreshold *= 0.95; // Decrease 5%
            Print($"🤖 ML: Accuracy {Math.Round(accuracy * 100)}% excellent → Decreased ATR threshold to {Math.Round(_atrThreshold, 2)} (allowing more signals)");
        }
        return;
    }
    
    // Case 4: Stable performance (70-75%) → Maintain current threshold
    Print($"🤖 ML: Accuracy {Math.Round(accuracy * 100)}% stable → ATR threshold maintained at {Math.Round(_atrThreshold, 2)}");
}
