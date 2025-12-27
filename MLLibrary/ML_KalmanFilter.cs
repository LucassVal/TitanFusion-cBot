// ==================================================================================
// ML ENGINE #14: KALMAN FILTER (Adaptive Price Smoothing)
// Purpose: Provides smoother price estimation with noise reduction
// Adapts to market volatility automatically
// Source: johndpope/CryptoCurrencyTrader concept
// ==================================================================================

// === REQUIRED FIELDS ===
// private double _kalmanEstimate = 0;
// private double _kalmanErrorEstimate = 1;
// private double _kalmanMeasurementNoise = 0.1;
// private double _kalmanProcessNoise = 0.01;

private double _kalmanEstimate = 0;
private double _kalmanErrorEstimate = 1;
private double _kalmanGain = 0;
private double _kalmanMeasurementNoise = 0.1;
private double _kalmanProcessNoise = 0.01;

/// <summary>
/// Updates Kalman Filter with new price measurement
/// Returns the smoothed estimated price
/// </summary>
private double UpdateKalmanFilter(double measurement)
{
    // Initialize on first call
    if (_kalmanEstimate == 0)
    {
        _kalmanEstimate = measurement;
        _kalmanErrorEstimate = 1;
        return _kalmanEstimate;
    }
    
    // Prediction Step
    double predictedEstimate = _kalmanEstimate;
    double predictedError = _kalmanErrorEstimate + _kalmanProcessNoise;
    
    // Update Step
    _kalmanGain = predictedError / (predictedError + _kalmanMeasurementNoise);
    _kalmanEstimate = predictedEstimate + _kalmanGain * (measurement - predictedEstimate);
    _kalmanErrorEstimate = (1 - _kalmanGain) * predictedError;
    
    return _kalmanEstimate;
}

/// <summary>
/// Gets the current Kalman-filtered price
/// </summary>
private double GetKalmanPrice()
{
    return UpdateKalmanFilter(Symbol.Bid);
}

/// <summary>
/// Calculates difference between actual price and Kalman estimate
/// Positive = price above estimate (bullish momentum)
/// Negative = price below estimate (bearish momentum)
/// </summary>
private double GetKalmanDeviation()
{
    double kalmanPrice = GetKalmanPrice();
    double actualPrice = Symbol.Bid;
    
    return (actualPrice - kalmanPrice) / Symbol.PipSize;
}

/// <summary>
/// Returns true if price momentum is consistent with Kalman trend
/// </summary>
private bool IsKalmanTrendConfirmed(bool isBullish)
{
    double deviation = GetKalmanDeviation();
    
    // Kalman gain indicates filter responsiveness
    // Higher gain = filter tracking price closely = trending
    bool isResponsive = _kalmanGain > 0.3;
    
    if (isBullish)
        return deviation > 2 && isResponsive; // Price above estimate
    else
        return deviation < -2 && isResponsive; // Price below estimate
}

/// <summary>
/// Adjusts Kalman noise parameters based on market conditions
/// </summary>
private void AdaptKalmanToVolatility()
{
    if (_atr == null || _atr.Result.Count < 20) return;
    
    double currentATR = _atr.Result.LastValue;
    double avgATR = 0;
    for (int i = 0; i < 20; i++) avgATR += _atr.Result.Last(i);
    avgATR /= 20;
    
    double atrRatio = avgATR > 0 ? currentATR / avgATR : 1;
    
    // High volatility: increase measurement noise (trust price less)
    // Low volatility: decrease measurement noise (trust price more)
    if (atrRatio > 1.3)
        _kalmanMeasurementNoise = 0.2;
    else if (atrRatio < 0.7)
        _kalmanMeasurementNoise = 0.05;
    else
        _kalmanMeasurementNoise = 0.1;
}
