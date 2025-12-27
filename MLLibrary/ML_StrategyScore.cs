// ==================================================================================
// ML ENGINE #13: STRATEGY SCORE (Signal Quality Scoring)
// Purpose: Scores each potential signal based on multiple factors
// Inspired by: johndpope/CryptoCurrencyTrader strategy scoring concept
// ==================================================================================

// === REQUIRED FIELDS ===
// Uses existing indicators: _hma*, _rsi, _adx, _atr, _volumeMa

/// <summary>
/// Calculates a comprehensive strategy score for a potential trade
/// Returns 0-100 where higher = better quality signal
/// </summary>
private double CalculateStrategyScore(bool isBuy)
{
    double score = 50; // Neutral start
    
    // ==========================================
    // FACTOR 1: Trend Alignment (0-20 points)
    // ==========================================
    double hmaTrend = GetHMATrendScore();
    if (isBuy && hmaTrend > 0)
        score += Math.Min(20, hmaTrend * 10);
    else if (!isBuy && hmaTrend < 0)
        score += Math.Min(20, Math.Abs(hmaTrend) * 10);
    else
        score -= 10; // Counter-trend penalty
    
    // ==========================================
    // FACTOR 2: Momentum (RSI) (0-15 points)
    // ==========================================
    if (_rsi != null && _rsi.Result.Count > 0)
    {
        double rsi = _rsi.Result.LastValue;
        
        if (isBuy)
        {
            // Best buy zone: RSI 30-50 (oversold recovering)
            if (rsi >= 30 && rsi <= 50)
                score += 15;
            else if (rsi < 30)
                score += 10; // Oversold, risky but potential
            else if (rsi > 70)
                score -= 10; // Overbought, bad buy
        }
        else
        {
            // Best sell zone: RSI 50-70 (overbought weakening)
            if (rsi >= 50 && rsi <= 70)
                score += 15;
            else if (rsi > 70)
                score += 10; // Overbought, risky but potential
            else if (rsi < 30)
                score -= 10; // Oversold, bad sell
        }
    }
    
    // ==========================================
    // FACTOR 3: Trend Strength (ADX) (0-15 points)
    // ==========================================
    if (_adx != null && _adx.ADX.Count > 0)
    {
        double adx = _adx.ADX.LastValue;
        
        if (adx > 30)
            score += 15; // Strong trend
        else if (adx > 20)
            score += 10; // Moderate trend
        else if (adx < 15)
            score -= 10; // Choppy market penalty
    }
    
    // ==========================================
    // FACTOR 4: Volume Confirmation (0-10 points)
    // ==========================================
    if (_volumeMa != null && _volumeMa.Result.Count > 0)
    {
        double currentVol = Bars.TickVolumes.LastValue;
        double avgVol = _volumeMa.Result.LastValue;
        
        if (avgVol > 0)
        {
            double ratio = currentVol / avgVol;
            if (ratio > 1.5)
                score += 10; // Volume spike
            else if (ratio > 1.2)
                score += 5;
            else if (ratio < 0.7)
                score -= 5; // Low volume warning
        }
    }
    
    // ==========================================
    // FACTOR 5: Volatility (ATR) (0-10 points)
    // ==========================================
    if (_atr != null && _atr.Result.Count > 50)
    {
        double currentATR = _atr.Result.LastValue;
        double avgATR = 0;
        for (int i = 0; i < 50; i++) avgATR += _atr.Result.Last(i);
        avgATR /= 50;
        
        double ratio = avgATR > 0 ? currentATR / avgATR : 1;
        
        if (ratio >= 0.8 && ratio <= 1.3)
            score += 10; // Normal volatility, good
        else if (ratio > 1.5)
            score -= 5; // Too volatile
        else if (ratio < 0.5)
            score -= 10; // Dead market
    }
    
    return Math.Max(0, Math.Min(100, score));
}

/// <summary>
/// Returns HMA trend score (-2 to +2)
/// </summary>
private double GetHMATrendScore()
{
    double score = 0;
    double price = Symbol.Bid;
    
    if (_hmaM15 != null && _hmaM15.Result.Count > 0)
    {
        if (price > _hmaM15.Result.LastValue) score += 0.5;
        else score -= 0.5;
    }
    
    if (_hmaH1 != null && _hmaH1.Result.Count > 0)
    {
        if (price > _hmaH1.Result.LastValue) score += 0.75;
        else score -= 0.75;
    }
    
    if (_hmaH4 != null && _hmaH4.Result.Count > 0)
    {
        if (price > _hmaH4.Result.LastValue) score += 0.75;
        else score -= 0.75;
    }
    
    return score;
}

/// <summary>
/// Returns signal quality level based on strategy score
/// </summary>
private string GetSignalQuality(double score)
{
    if (score >= 85) return "ALPHA";
    if (score >= 70) return "STRONG";
    if (score >= 55) return "STANDARD";
    if (score >= 40) return "WEAK";
    return "AVOID";
}
