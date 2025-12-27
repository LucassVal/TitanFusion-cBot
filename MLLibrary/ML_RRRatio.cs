// ==================================================================================
// ML ENGINE #3: RR Ratio Adaptive
// Purpose: Adjusts Risk/Reward ratio based on historical win rate
// ==================================================================================

// === REQUIRED FIELDS ===
// private List<RRRecord> _rrRecords = new List<RRRecord>();
// private int _lastRRAdjustment = 0;
// private double _adaptiveRRRatio = 2.0;
// public bool EnableMLEngines { get; set; }
// public int MLAdjustmentFrequency { get; set; }

// === RR RECORD CLASS ===
// private class RRRecord
// {
//     public double ExpectedRR { get; set; }
//     public double ActualRR { get; set; }
//     public bool HitTarget { get; set; }
// }

private void AdjustRRRatio()
{
    if (!EnableMLEngines) return;
    
    int recordCount = _rrRecords.Count;
    
    // Need at least MLAdjustmentFrequency records
    if (recordCount < MLAdjustmentFrequency) return;
    
    // Only adjust every MLAdjustmentFrequency new records
    if (recordCount - _lastRRAdjustment < MLAdjustmentFrequency) return;
    
    _lastRRAdjustment = recordCount;
    
    // Calculate performance metrics
    double avgExpectedRR = _rrRecords.Average(r => r.ExpectedRR);
    double avgActualRR = _rrRecords.Where(r => r.HitTarget).Average(r => r.ActualRR);
    double hitRate = _rrRecords.Count(r => r.HitTarget) / (double)recordCount;
    
    // === ADAPTIVE LOGIC ===
    
    // Case 1: High win rate (>80%) AND actualRR beats expectedRR → Increase RR
    if (hitRate > 0.80 && avgActualRR > avgExpectedRR * 1.2)
    {
        if (_adaptiveRRRatio < 2.5)
        {
            _adaptiveRRRatio = Math.Min(2.5, _adaptiveRRRatio + 0.1);
            Print($"🤖 ML RR: Win rate {Math.Round(hitRate * 100)}% → Increased RR to {Math.Round(_adaptiveRRRatio, 2)}");
        }
        return;
    }
    
    // Case 2: Low win rate (<50%) → Decrease RR (more conservative)
    if (hitRate < 0.50)
    {
        if (_adaptiveRRRatio > 1.5) // Min 1.5
        {
            _adaptiveRRRatio -= 0.3;
            Print($"🤖 ML RR: Win rate {Math.Round(hitRate * 100)}% → Decreased RR to {Math.Round(_adaptiveRRRatio, 1)} (more conservative)");
        }
        return;
    }
    
    // Case 3: Good performance (60-75%) → Maintain
    Print($"🤖 ML RR: Win rate {Math.Round(hitRate * 100)}%, RR {Math.Round(avgActualRR, 1)} → RR ratio maintained at {Math.Round(_adaptiveRRRatio, 1)}");
}
