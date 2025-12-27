// ==================================================================================
// ML ENGINE #2: MinMtfAlignment Adaptive
// Purpose: Adjusts minimum MTF alignment requirement based on accuracy
// ==================================================================================

// === REQUIRED FIELDS ===
// private List<MtfQualityRecord> _mtfQualities = new List<MtfQualityRecord>();
// private int _lastMtfAdjustment = 0;
// private int _adaptiveMinMtf = 3;
// public bool EnableMLEngines { get; set; }
// public int MLAdjustmentFrequency { get; set; }

// === MTFQUALITY RECORD CLASS ===
// private class MtfQualityRecord
// {
//     public int Alignment { get; set; }
//     public bool Success { get; set; }
// }

private void AdjustMinMtfAlignment()
{
    if (!EnableMLEngines) return;
    
    int qualityCount = _mtfQualities.Count;
    
    // Need at least MLAdjustmentFrequency signals to learn
    if (qualityCount < MLAdjustmentFrequency) return;
    
    // Only adjust every MLAdjustmentFrequency new signals
    if (qualityCount - _lastMtfAdjustment < MLAdjustmentFrequency) return;
    
    _lastMtfAdjustment = qualityCount;
    
    // Calculate accuracy with current alignment
    int correctCount = _mtfQualities.Where(m => m.Alignment == _adaptiveMinMtf && m.Success).Count();
    int totalWithAlignment = _mtfQualities.Where(m => m.Alignment == _adaptiveMinMtf).Count();
    
    if (totalWithAlignment == 0) return;
    
    double accuracy = (double)correctCount / totalWithAlignment;
    
    // === ADAPTIVE LOGIC ===
    
    // Case 1: High accuracy with 3/4 → Keep it (more signals, good quality)
    if (_adaptiveMinMtf == 3 && accuracy > 0.70)
    {
        Print($"🤖 ML MTF: Accuracy {Math.Round(accuracy * 100)}% with 3/4 alignment → Maintaining 3/4 (good balance)");
        return;
    }
    
    // Case 2: Low accuracy with 3/4 → Require 4/4 (stricter)
    if (_adaptiveMinMtf == 3 && accuracy < 0.60)
    {
        _adaptiveMinMtf = 4;
        Print($"🤖 ML MTF: Accuracy {Math.Round(accuracy * 100)}% with 3/4 → Increased to 4/4 (stricter confirmation)");
        return;
    }
    
    // Case 3: High accuracy with 4/4 but missing signals → Relax to 3/4
    if (_adaptiveMinMtf == 4 && accuracy > 0.75 && totalWithAlignment < 5)
    {
        _adaptiveMinMtf = 3;
        Print($"🤖 ML MTF: Accuracy {Math.Round(accuracy * 100)}% with 4/4 but only {totalWithAlignment} signals → Decreased to 3/4 (more opportunities)");
        return;
    }
    
    Print($"🤖 ML MTF: Accuracy {Math.Round(accuracy * 100)}% → MTF alignment maintained at {_adaptiveMinMtf}/4");
}
