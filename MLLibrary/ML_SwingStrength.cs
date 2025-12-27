// ==================================================================================
// ML ENGINE #5: Swing Strength Adaptive
// Purpose: Adjusts swing level strength based on hold rate
// ==================================================================================

// === REQUIRED FIELDS ===
// private List<SwingQuality> _swingQualities = new List<SwingQuality>();
// private int _lastSwingAdjustment = 0;
// private int _adaptiveSwingStrength = 5;
// public bool EnableMLEngines { get; set; }
// public int MLAdjustmentFrequency { get; set; }

// === SWING QUALITY CLASS ===
private class SwingQuality
{
    public int Strength { get; set; }
    public bool LevelHeld { get; set; }
}
private List<SwingQuality> _swingQualities = new List<SwingQuality>();

private void AdjustSwingStrength()
{
    if (!EnableMLEngines) return;
    
    int qualityCount = _swingQualities.Count;
    
    // Need at least MLAdjustmentFrequency * 2 (swing levels are frequent)
    if (qualityCount < MLAdjustmentFrequency * 2) return;
    
    // Only adjust every MLAdjustmentFrequency * 2 new records
    if (qualityCount - _lastSwingAdjustment < MLAdjustmentFrequency * 2) return;
    
    _lastSwingAdjustment = qualityCount;
    
    // Calculate level quality
    double holdRate = _swingQualities.Count(s => s.LevelHeld) / (double)qualityCount;
    int visibleLevels = _swingQualities.Where(s => s.Strength == _adaptiveSwingStrength).Count();
    
    // === ADAPTIVE LOGIC ===
    
    // Case 1: Low hold rate (<60%) → Increase strength (fewer, better levels)
    if (holdRate < 0.60)
    {
        if (_adaptiveSwingStrength < 10) // Max 10
        {
            _adaptiveSwingStrength++;
            Print($"🤖 ML Swing: Hold rate {Math.Round(holdRate * 100)}% → Increased strength to {_adaptiveSwingStrength} (fewer, stronger levels)");
        }
        return;
    }
    
    // Case 2: High hold rate (>80%) but too few levels (<3) → Decrease strength
    if (holdRate > 0.80 && visibleLevels < 3)
    {
        if (_adaptiveSwingStrength > 2) // Min 2
        {
            _adaptiveSwingStrength--;
            Print($"🤖 ML Swing: Hold rate {Math.Round(holdRate * 100)}% but only {visibleLevels} levels → Decreased strength to {_adaptiveSwingStrength} (more levels)");
        }
        return;
    }
    
    Print($"🤖 ML Swing: Hold rate {Math.Round(holdRate * 100)}%, {visibleLevels} levels → Strength maintained at {_adaptiveSwingStrength}");
}
