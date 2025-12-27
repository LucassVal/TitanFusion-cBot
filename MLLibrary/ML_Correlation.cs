// ==================================================================================
// ML ENGINE: Multi-Symbol Correlation Analysis
// Purpose: Analyzes correlated symbols to determine market bias
// Usage: Add to indicator class and call InitializeCorrelations in Initialize()
//        Call CalculateCorrelationBias in Calculate() periodically
//        Call ApplyCorrelationFilter when generating signals
// ==================================================================================

// === REQUIRED PARAMETERS (add to your indicator) ===
// [Parameter("Enable ML Engines", DefaultValue = true, Group = "ML")]
// public bool EnableMLEngines { get; set; }
// [Parameter("Use Multi-Symbol ML", DefaultValue = true, Group = "ML")]
// public bool UseMultiSymbolML { get; set; }

// === DATA STRUCTURE ===
private class SymbolCorrelation
{
    public string Symbol { get; set; }
    public double Correlation { get; set; } // -1 to +1
    public double Weight { get; set; }      // Importance
}

// === REQUIRED FIELDS ===
private List<SymbolCorrelation> _correlatedSymbols = new List<SymbolCorrelation>();
private Dictionary<string, Bars> _correlatedBarsCache = new Dictionary<string, Bars>();
private DateTime _lastCorrelationCheck = DateTime.MinValue;
private double _correlationBias = 0; // -1 (bearish) to +1 (bullish)

// ==================================================================================
// FUNCTION: InitializeCorrelations
// Purpose: Setup correlated symbols based on the current symbol
// Call: Once in Initialize() method
// ==================================================================================
private void InitializeCorrelations()
{
    _correlatedSymbols.Clear();
    string name = Symbol.Name.ToUpper();
    
    // =============== GOLD (XAUUSD) ===============
    if (name.Contains("XAU") || name.Contains("GOLD"))
    {
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "EURUSD", Correlation = 0.80, Weight = 1.0 });   // EUR up = USD weak = Gold up
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "USDJPY", Correlation = -0.70, Weight = 0.8 });  // USD/JPY up = USD strong = Gold down
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "GBPUSD", Correlation = 0.75, Weight = 0.7 });   // GBP up = USD weak = Gold up
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "USDCHF", Correlation = -0.85, Weight = 0.9 });  // USD/CHF up = USD strong = Gold down
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "XAGUSD", Correlation = 0.90, Weight = 0.6 });   // Silver follows Gold
        Print("🔗 Multi-Symbol ML: Initialized 5 correlations for GOLD");
    }
    
    // =============== SILVER (XAGUSD) ===============
    else if (name.Contains("XAG") || name.Contains("SILVER"))
    {
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "XAUUSD", Correlation = 0.90, Weight = 1.0 });   // Gold leads Silver
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "EURUSD", Correlation = 0.75, Weight = 0.8 });
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "USDCHF", Correlation = -0.80, Weight = 0.7 });
        Print("🔗 Multi-Symbol ML: Initialized 3 correlations for SILVER");
    }
    
    // =============== OIL (USOIL, XTIUSD, WTI) ===============
    else if (name.Contains("OIL") || name.Contains("XTI") || name.Contains("WTI") || name.Contains("BRENT"))
    {
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "USDCAD", Correlation = -0.75, Weight = 1.0 });  // Oil up = CAD strong = USDCAD down
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "CADJPY", Correlation = 0.70, Weight = 0.8 });   // Oil up = CAD up
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "USDRUB", Correlation = -0.60, Weight = 0.5 });  // Oil up = RUB strong
        Print("🔗 Multi-Symbol ML: Initialized 3 correlations for OIL");
    }
    
    // =============== EUR PAIRS ===============
    else if (name.StartsWith("EUR"))
    {
        if (name.Contains("USD"))
        {
            _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "GBPUSD", Correlation = 0.90, Weight = 1.0 });
            _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "AUDUSD", Correlation = 0.70, Weight = 0.7 });
            _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "USDCHF", Correlation = -0.95, Weight = 0.9 });
            _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "USDJPY", Correlation = -0.50, Weight = 0.5 });
        }
        else if (name.Contains("GBP"))
        {
            _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "EURUSD", Correlation = 0.60, Weight = 0.8 });
            _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "GBPUSD", Correlation = -0.65, Weight = 0.8 });
        }
        else if (name.Contains("JPY"))
        {
            _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "USDJPY", Correlation = 0.80, Weight = 0.9 });
            _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "GBPJPY", Correlation = 0.85, Weight = 0.8 });
        }
        Print($"🔗 Multi-Symbol ML: Initialized {_correlatedSymbols.Count} correlations for EUR pair");
    }
    
    // =============== GBP PAIRS ===============
    else if (name.StartsWith("GBP"))
    {
        if (name.Contains("USD"))
        {
            _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "EURUSD", Correlation = 0.90, Weight = 1.0 });
            _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "AUDUSD", Correlation = 0.65, Weight = 0.6 });
            _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "USDCHF", Correlation = -0.85, Weight = 0.8 });
        }
        else if (name.Contains("JPY"))
        {
            _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "USDJPY", Correlation = 0.75, Weight = 0.9 });
            _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "EURJPY", Correlation = 0.90, Weight = 0.8 });
        }
        Print($"🔗 Multi-Symbol ML: Initialized {_correlatedSymbols.Count} correlations for GBP pair");
    }
    
    // =============== USD PAIRS ===============
    else if (name.StartsWith("USD"))
    {
        if (name.Contains("JPY"))
        {
            _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "EURJPY", Correlation = 0.80, Weight = 0.8 });
            _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "GBPJPY", Correlation = 0.75, Weight = 0.7 });
            _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "EURUSD", Correlation = -0.50, Weight = 0.5 });
        }
        else if (name.Contains("CHF"))
        {
            _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "EURUSD", Correlation = -0.95, Weight = 1.0 });
            _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "GBPUSD", Correlation = -0.85, Weight = 0.8 });
        }
        else if (name.Contains("CAD"))
        {
            _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "XTIUSD", Correlation = -0.75, Weight = 0.9 });  // Oil inverse
            _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "AUDUSD", Correlation = -0.60, Weight = 0.6 });
        }
        Print($"🔗 Multi-Symbol ML: Initialized {_correlatedSymbols.Count} correlations for USD pair");
    }
    
    // =============== AUD/NZD PAIRS ===============
    else if (name.StartsWith("AUD") || name.StartsWith("NZD"))
    {
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "AUDUSD", Correlation = name.Contains("NZD") ? 0.85 : 1.0, Weight = 0.9 });
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "NZDUSD", Correlation = name.Contains("AUD") ? 0.85 : 1.0, Weight = 0.9 });
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "XAUUSD", Correlation = 0.55, Weight = 0.5 });  // Commodity currencies
        Print($"🔗 Multi-Symbol ML: Initialized {_correlatedSymbols.Count} correlations for AUD/NZD pair");
    }
    
    // =============== US INDICES (US30, US100, US500) ===============
    else if (name.Contains("US30") || name.Contains("DJ30") || name.Contains("DOW"))
    {
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "US100", Correlation = 0.95, Weight = 1.0 });
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "US500", Correlation = 0.97, Weight = 0.9 });
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "DE40", Correlation = 0.80, Weight = 0.6 });
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "USDJPY", Correlation = 0.50, Weight = 0.4 });  // Risk-on = JPY weak
        Print("🔗 Multi-Symbol ML: Initialized 4 correlations for US30");
    }
    else if (name.Contains("US100") || name.Contains("NAS") || name.Contains("NDX"))
    {
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "US30", Correlation = 0.95, Weight = 1.0 });
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "US500", Correlation = 0.96, Weight = 0.9 });
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "BTCUSD", Correlation = 0.60, Weight = 0.5 });   // Tech correlation
        Print("🔗 Multi-Symbol ML: Initialized 3 correlations for US100");
    }
    else if (name.Contains("US500") || name.Contains("SPX") || name.Contains("SP500"))
    {
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "US30", Correlation = 0.97, Weight = 1.0 });
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "US100", Correlation = 0.96, Weight = 0.9 });
        Print("🔗 Multi-Symbol ML: Initialized 2 correlations for US500");
    }
    
    // =============== EUROPEAN INDICES (DE40, UK100, FR40) ===============
    else if (name.Contains("DE40") || name.Contains("DAX") || name.Contains("GER"))
    {
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "FR40", Correlation = 0.95, Weight = 1.0 });
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "UK100", Correlation = 0.85, Weight = 0.8 });
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "US500", Correlation = 0.80, Weight = 0.7 });
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "EURUSD", Correlation = -0.40, Weight = 0.4 });  // EUR strong = DAX down
        Print("🔗 Multi-Symbol ML: Initialized 4 correlations for DE40");
    }
    else if (name.Contains("UK100") || name.Contains("FTSE"))
    {
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "DE40", Correlation = 0.85, Weight = 1.0 });
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "GBPUSD", Correlation = -0.50, Weight = 0.6 });  // GBP strong = FTSE down
        Print("🔗 Multi-Symbol ML: Initialized 2 correlations for UK100");
    }
    
    // =============== CRYPTO (BTCUSD, ETHUSD) ===============
    else if (name.Contains("BTC"))
    {
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "ETHUSD", Correlation = 0.90, Weight = 1.0 });
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "US100", Correlation = 0.60, Weight = 0.5 });   // Tech/risk correlation
        Print("🔗 Multi-Symbol ML: Initialized 2 correlations for BTC");
    }
    else if (name.Contains("ETH"))
    {
        _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "BTCUSD", Correlation = 0.90, Weight = 1.0 });
        Print("🔗 Multi-Symbol ML: Initialized 1 correlation for ETH");
    }
    
    // =============== FALLBACK (Unknown symbol) ===============
    else
    {
        // Try to add basic USD correlation
        if (name.Contains("USD"))
        {
            _correlatedSymbols.Add(new SymbolCorrelation { Symbol = "EURUSD", Correlation = name.StartsWith("USD") ? -0.70 : 0.70, Weight = 0.7 });
        }
        Print($"🔗 Multi-Symbol ML: Generic correlation added for {name}");
    }
}

// ==================================================================================
// FUNCTION: CalculateCorrelationBias
// Purpose: Analyze correlated symbols to determine overall market bias
// Call: In Calculate() method (automatically throttles to every 30 minutes)
// ==================================================================================
private void CalculateCorrelationBias()
{
    if (!EnableMLEngines || !UseMultiSymbolML || _correlatedSymbols.Count == 0) return;
    
    // Update every 30 minutes (more frequent than before)
    if ((Server.Time - _lastCorrelationCheck).TotalMinutes < 30) return;
    _lastCorrelationCheck = Server.Time;
    
    double totalBias = 0;
    double totalWeight = 0;
    int successfulChecks = 0;
    
    foreach (var corr in _correlatedSymbols)
    {
        try
        {
            // Get or cache bars
            Bars corrBars;
            if (!_correlatedBarsCache.ContainsKey(corr.Symbol))
            {
                corrBars = MarketData.GetBars(TimeFrame.Hour, corr.Symbol);
                if (corrBars != null && corrBars.Count > 10)
                    _correlatedBarsCache[corr.Symbol] = corrBars;
                else
                    continue;
            }
            else
            {
                corrBars = _correlatedBarsCache[corr.Symbol];
            }
            
            if (corrBars.Count < 5) continue;
            
            // Calculate % change in last 4 hours
            double close0 = corrBars.ClosePrices.Last(0);
            double close4 = corrBars.ClosePrices.Last(4);
            double change = (close0 - close4) / close4;
            
            // Apply correlation and weight
            double symbolBias = change * corr.Correlation * corr.Weight * 20; // Scale to meaningful range
            totalBias += symbolBias;
            totalWeight += corr.Weight;
            successfulChecks++;
        }
        catch
        {
            // Symbol not available, skip silently
        }
    }
    
    if (totalWeight > 0)
    {
        _correlationBias = totalBias / totalWeight;
        _correlationBias = Math.Max(-1, Math.Min(1, _correlationBias)); // Clamp to [-1, +1]
        
        if (Math.Abs(_correlationBias) > 0.02)
        {
            string direction = _correlationBias > 0 ? "BULLISH" : "BEARISH";
            Print($"🔗 Multi-Symbol ML: {successfulChecks} symbols analyzed → {direction} bias ({Math.Round(_correlationBias * 100, 1)}%)");
        }
    }
}

// ==================================================================================
// FUNCTION: ApplyCorrelationFilter
// Purpose: Filter signals based on correlation bias
// Call: When generating BUY/SELL signals
// ==================================================================================
private void ApplyCorrelationFilter(ref bool isBuy, ref bool isSell)
{
    if (!EnableMLEngines || !UseMultiSymbolML) return;
    if (Math.Abs(_correlationBias) < 0.03) return; // Minimum threshold
    
    // Strong bullish bias blocks sells
    if (_correlationBias > 0.05 && isSell)
    {
        Print($"🔗 Correlation Filter: Bullish bias ({Math.Round(_correlationBias * 100, 1)}%) → SELL blocked");
        isSell = false;
    }
    
    // Strong bearish bias blocks buys
    if (_correlationBias < -0.05 && isBuy)
    {
        Print($"🔗 Correlation Filter: Bearish bias ({Math.Round(_correlationBias * 100, 1)}%) → BUY blocked");
        isBuy = false;
    }
}
