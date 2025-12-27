// ==================================================================================
// ML ENGINE #7: Session Scheduler + Time-Based Performance Tracking
// Purpose: Identifies golden hours (high win rate) and dead hours (low win rate)
// ==================================================================================

// === REQUIRED FIELDS ===
// private Dictionary<int, List<SessionPerformance>> _sessionStats = new Dictionary<int, List<SessionPerformance>>();
// private List<int> _goldenHours = new List<int>();
// private List<int> _deadHours = new List<int>();
// private int _lastSessionAdjustment = 0;
// public bool EnableMLEngines { get; set; }

// === SESSION PERFORMANCE CLASS ===
private class SessionPerformance
{
    public int Hour { get; set; }
    public DateTime SignalTime { get; set; }
    public bool Success { get; set; }
    public double PnL { get; set; }
}
private Dictionary<int, List<SessionPerformance>> _sessionStats = new Dictionary<int, List<SessionPerformance>>();
private List<int> _goldenHours = new List<int>();
private List<int> _deadHours = new List<int>();

private void AdjustSessionSchedule()
{
    if (!EnableMLEngines) return;
    
    // Count total signals across all hours
    int totalSignals = _sessionStats.Values.Sum(list => list.Count);
    
    // Need at least 20 signals to learn
    if (totalSignals < 20) return;
    
    // Only adjust every 10 new signals
    if (totalSignals - _lastSessionAdjustment < 10) return;
    
    _lastSessionAdjustment = totalSignals;
    
    _goldenHours.Clear();
    _deadHours.Clear();
    
    // Analyze each hour (0-23)
    for (int hour = 0; hour < 24; hour++)
    {
        if (!_sessionStats.ContainsKey(hour) || _sessionStats[hour].Count < 3)
            continue; // Need at least 3 signals for this hour
        
        var hourData = _sessionStats[hour];
        double hourWinRate = hourData.Count(s => s.Success) / (double)hourData.Count;
        
        // Identify golden hours (>70% win rate)
        if (hourWinRate > 0.70)
            _goldenHours.Add(hour);
        
        // Identify dead hours (<40% win rate)
        if (hourWinRate < 0.40)
            _deadHours.Add(hour);
    }
    
    if (_goldenHours.Count > 0 || _deadHours.Count > 0)
    {
        string goldenStr = _goldenHours.Count > 0 ? string.Join(", ", _goldenHours.Select(h => $"{h}h")) : "none";
        string deadStr = _deadHours.Count > 0 ? string.Join(", ", _deadHours.Select(h => $"{h}h")) : "none";
        Print($"🤖 ML Session: Golden hours: {goldenStr} | Dead hours: {deadStr}");
    }
}

private bool IsGoodTradingHour()
{
    if (!EnableMLEngines) return true; // ML disabled, trade anytime
    if (_goldenHours.Count == 0 && _deadHours.Count == 0) return true; // Not enough data yet
    
    int currentHour = Server.Time.Hour;
    
    // Block dead hours
    if (_deadHours.Contains(currentHour))
        return false;
    
    // If we have golden hours identified, only trade during those
    if (_goldenHours.Count > 0)
        return _goldenHours.Contains(currentHour);
    
    return true; // Default: allow trading
}

// ==================================================================================
// USAGE: Recording Session Performance
// ==================================================================================
// Call this after a signal is validated:
// void RecordSessionPerformance(bool success, double pnl)
// {
//     int hour = Server.Time.Hour;
//     if (!_sessionStats.ContainsKey(hour))
//         _sessionStats[hour] = new List<SessionPerformance>();
//     _sessionStats[hour].Add(new SessionPerformance { Hour = hour, SignalTime = Server.Time, Success = success, PnL = pnl });
// }
