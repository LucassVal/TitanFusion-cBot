using System;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    public enum LotMode
    {
        Auto,   // Calcula baseado em Risk% e SL
        Manual  // Usa FixedLots com limites Min/Max
    }

    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.FullAccess)]
    public class TitanFusionQuantumBot : Robot
    {
        private const string BOT_LABEL = "TF_Quantum";
        private const string BOT_VERSION = "1.0.0";
        private const string BOT_NAME = "Titan Fusion Quantum";
        #region Trading Parameters
        [Parameter("═══ TRADING ═══", DefaultValue = "")]
        public string TradingHeader { get; set; }
        
        [Parameter("Enable Auto-Trading", DefaultValue = true)]
        public bool EnableAutoTrade { get; set; }
        
        [Parameter("Min Confidence %", DefaultValue = 75, MinValue = 50, MaxValue = 100)]
        public int MinConfidence { get; set; }
        
        [Parameter("Max Open Positions", DefaultValue = 3, MinValue = 1, MaxValue = 10)]
        public int MaxPositions { get; set; }
        #endregion

        #region Risk Management (SIMPLIFIED)
        [Parameter("═══ RISCO ═══", DefaultValue = "")]
        public string RiskHeader { get; set; }
        
        [Parameter("Lot Mode (Auto/Manual)", DefaultValue = LotMode.Auto)]
        public LotMode LotSizeMode { get; set; }
        
        [Parameter("Risk Per Trade % (Auto)", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 5)]
        public double RiskPercent { get; set; }
        
        [Parameter("Fixed Lots (Manual)", DefaultValue = 0.01, MinValue = 0.01, MaxValue = 1000000.0)]
        public double FixedLots { get; set; }
        
        [Parameter("Max Total Lots", DefaultValue = 0.1, MinValue = 0.01, MaxValue = 1000000.0)]
        public double MaxTotalLots { get; set; }
        
        [Parameter("Max Daily Loss %", DefaultValue = 3.0, MinValue = 1, MaxValue = 20)]
        public double MaxDailyLossPercent { get; set; }
        
        [Parameter("Max Session Loss %", DefaultValue = 5.0, MinValue = 1, MaxValue = 30)]
        public double MaxSessionLossPercent { get; set; }
        
        [Parameter("Max Trades Per Day", DefaultValue = 10, MinValue = 1, MaxValue = 50)]
        public int MaxDailyTrades { get; set; }
        #endregion

        #region Trade Management
        [Parameter("═══ GESTAO ═══", DefaultValue = "")]
        public string ManagementHeader { get; set; }
        
        [Parameter("Enable Breakeven", DefaultValue = true)]
        public bool EnableBreakeven { get; set; }
        
        [Parameter("BE Trigger % (Price)", DefaultValue = 0.5, MinValue = 0.01, MaxValue = 10.0)]
        public double BreakevenTriggerPercent { get; set; }
        
        [Parameter("BE Lock % (Price)", DefaultValue = 0.1, MinValue = 0.0, MaxValue = 5.0)]
        public double BreakevenLockPercent { get; set; }
        
        [Parameter("BE Tier 2 Trigger % (Price)", DefaultValue = 3.0, MinValue = 0.01, MaxValue = 20.0)]
        public double BreakevenTier2TriggerPercent { get; set; }
        
        [Parameter("BE Tier 2 Lock % (Price)", DefaultValue = 1.5, MinValue = 0.1, MaxValue = 10.0)]
        public double BreakevenTier2LockPercent { get; set; }
        
        [Parameter("Enable Trailing Stop", DefaultValue = true)]
        public bool EnableTrailing { get; set; }
        
        [Parameter("Trail Start % (Price)", DefaultValue = 0.7, MinValue = 0.01, MaxValue = 10.0)]
        public double TrailStartPercent { get; set; }
        
        [Parameter("Trail Distance % (Price)", DefaultValue = 0.3, MinValue = 0.01, MaxValue = 5.0)]
        public double TrailDistancePercent { get; set; }
        
        [Parameter("Manage ALL Positions", DefaultValue = false)]
        public bool ManageAllPositions { get; set; }
        #endregion

        // Internal
        private string _dataFolder;
        private string _signalFile;
        private string _configFile;
        private string _lastProcessedSignalId = "";
        private DateTime _lastSignalCheck = DateTime.MinValue;
        private DateTime _lastPanelUpdate = DateTime.MinValue;
        private DateTime _lastExportTime = DateTime.MinValue;
        private int _dailyTrades = 0;
        private double _dailyStartBalance = 0;
        private DateTime _lastDayReset = DateTime.MinValue;
        
        // Session Stats
        private int _sessionWins = 0;
        private int _sessionLosses = 0;
        private double _sessionGrossProfit = 0;
        private double _sessionGrossLoss = 0;
        private double _sessionStartEquity = 0;  // Para Max Session Loss %
        
        // Panel
        private StackPanel _mainPanel;
        private TextBlock _txtStatus;
        private TextBlock _txtPrice;
        private TextBlock _txtAccount;
        private TextBlock _txtPositions;
        private TextBlock _txtSignal;
        private TextBlock _txtConfidence;
        private TextBlock _txtStrategy;
        private TextBlock _txtLevels;
        private TextBlock _txtPortfolio;
        private TextBlock _txtStats;
        private TextBlock _txtHistory;
        private TextBlock _txtBotState;
        private TextBlock _txtVirtualStats;  // NOVO: Stats de trades virtuais
        
        // Current signal data
        private QuantumSignal _currentSignal;

        protected override void OnStart()
        {
            _dataFolder = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "TitanFusionAI");
            _signalFile = Path.Combine(_dataFolder, "predictions.json");
            _configFile = Path.Combine(_dataFolder, "symbol_config.json");
            
            if (!Directory.Exists(_dataFolder))
                Directory.CreateDirectory(_dataFolder);
            
            _dailyStartBalance = Account.Balance;
            _sessionStartEquity = Account.Equity;  // Para Max Session Loss %
            _lastDayReset = Server.Time.Date;
            
            // Evento para rastrear W/L
            Positions.Closed += OnPositionClosed;
            
            BuildPanel();
            
            Print("═══════════════════════════════════════════════════");
            Print("   TITAN FUSION QUANTUM BOT - AI Auto-Trader");
            Print("═══════════════════════════════════════════════════");
            Print($"Symbol: {SymbolName}");
            Print($"Auto-Trade: {EnableAutoTrade}");
            Print($"Min Confidence: {MinConfidence}%");
            Print($"Lot Mode: {LotSizeMode}");
            Print("═══════════════════════════════════════════════════");
        }

        private void OnPositionClosed(PositionClosedEventArgs args)
        {
            var pos = args.Position;
            
            // Apenas posicoes deste bot
            if (pos.Label != BOT_LABEL || pos.SymbolName != SymbolName) return;
            
            double netProfit = pos.NetProfit;
            double grossProfit = pos.GrossProfit;
            
            if (netProfit >= 0)
            {
                _sessionWins++;
                _sessionGrossProfit += grossProfit;
                Print($"WIN! +${netProfit:F2} | Session: {_sessionWins}W/{_sessionLosses}L");
            }
            else
            {
                _sessionLosses++;
                _sessionGrossLoss += Math.Abs(grossProfit);
                Print($"LOSS: ${netProfit:F2} | Session: {_sessionWins}W/{_sessionLosses}L");
            }

        }

        protected override void OnTick()
        {
            // Reset diario
            if (Server.Time.Date > _lastDayReset)
            {
                _dailyTrades = 0;
                _dailyStartBalance = Account.Balance;
                _lastDayReset = Server.Time.Date;
            }
            
            // Atualizar config para Python
            WriteSymbolConfig();
            
            // Exportar candles para Python
            ExportMarketData();
            
            // Adotar trades antigas (sem comment/strategy) e ajustar SL/TP
            FixLegacyTrades();
            
            // Executar sugestões de revisão do Gemini (TIGHTEN_SL, CLOSE_NOW, etc)
            ProcessPositionReviews();
            
            // Gestao de trades existentes
            ManageOpenPositions();
            
            // Breakeven automatico em 2 pisos
            CheckBreakeven();
            
            // Verificar novos sinais
            if ((Server.Time - _lastSignalCheck).TotalSeconds >= 3)
            {
                LoadSignal();
                ProcessQuantumSignal();
                _lastSignalCheck = Server.Time;
            }
            
            // Atualizar painel
            if ((Server.Time - _lastPanelUpdate).TotalSeconds >= 1)
            {
                UpdatePanel();
                _lastPanelUpdate = Server.Time;
            }
        }

        #region Visual Panel
        private void BuildPanel()
        {
            var canvas = new Canvas { Width = 260, HorizontalAlignment = HorizontalAlignment.Right, VerticalAlignment = VerticalAlignment.Top };

            _mainPanel = new StackPanel { BackgroundColor = Color.FromHex("#0A0A0A"), Opacity = 0.95, Margin = "10 40 10 10", Width = 240 };

            // Header
            var header = new StackPanel { BackgroundColor = Color.FromHex("#1A1A2E") };
            header.AddChild(new TextBlock { Text = "QUANTUM BOT", ForegroundColor = Color.Gold, FontSize = 12, FontWeight = FontWeight.Bold, HorizontalAlignment = HorizontalAlignment.Center, Margin = "10 5" });
            _mainPanel.AddChild(header);

            // Status
            _txtStatus = new TextBlock { Text = "INICIALIZANDO...", FontSize = 10, ForegroundColor = Color.Yellow, HorizontalAlignment = HorizontalAlignment.Center, Margin = "10 3" };
            _mainPanel.AddChild(_txtStatus);

            AddSeparator();

            // Price
            _txtPrice = new TextBlock { Text = "---", FontSize = 14, ForegroundColor = Color.Gold, HorizontalAlignment = HorizontalAlignment.Center, Margin = "5 3" };
            _mainPanel.AddChild(_txtPrice);

            // Account
            _txtAccount = new TextBlock { Text = "Balance: ---", FontSize = 8, ForegroundColor = Color.White, HorizontalAlignment = HorizontalAlignment.Center, Margin = "5 2" };
            _mainPanel.AddChild(_txtAccount);

            // Positions
            _txtPositions = new TextBlock { Text = "POS: ---", FontSize = 8, ForegroundColor = Color.Gray, HorizontalAlignment = HorizontalAlignment.Center, Margin = "5 2" };
            _mainPanel.AddChild(_txtPositions);

            AddSeparator();

            // Signal Header
            _mainPanel.AddChild(new TextBlock { Text = "SINAL IA", FontSize = 8, ForegroundColor = Color.Cyan, HorizontalAlignment = HorizontalAlignment.Center, Margin = "5 2" });

            // Signal
            _txtSignal = new TextBlock { Text = "Aguardando...", FontSize = 11, FontWeight = FontWeight.Bold, ForegroundColor = Color.Gray, HorizontalAlignment = HorizontalAlignment.Center, Margin = "10 3" };
            _mainPanel.AddChild(_txtSignal);
            
            _txtConfidence = new TextBlock { Text = "Confianca: --%", FontSize = 9, ForegroundColor = Color.Gray, HorizontalAlignment = HorizontalAlignment.Center, Margin = "2 2" };
            _mainPanel.AddChild(_txtConfidence);

            // Strategy
            _txtStrategy = new TextBlock { Text = "", FontSize = 8, ForegroundColor = Color.White, HorizontalAlignment = HorizontalAlignment.Center, Margin = "5 2" };
            _mainPanel.AddChild(_txtStrategy);

            // Levels
            _txtLevels = new TextBlock { Text = "", FontSize = 8, ForegroundColor = Color.LightGray, Margin = "10 3", Width = 220 };
            _mainPanel.AddChild(_txtLevels);
            
            AddSeparator();
            
            // Portfolio Tracker
            _mainPanel.AddChild(new TextBlock { Text = "PORTFOLIO (SLOTS)", FontSize = 8, ForegroundColor = Color.Cyan, HorizontalAlignment = HorizontalAlignment.Center, Margin = "5 2" });
            _txtPortfolio = new TextBlock { Text = "Calculando...", FontSize = 9, ForegroundColor = Color.White, Margin = "10 2", Width = 220, HorizontalAlignment = HorizontalAlignment.Center };
            _mainPanel.AddChild(_txtPortfolio);

            AddSeparator();

            // Stats
            _txtStats = new TextBlock { Text = "Hoje: 0 trades | $0.00", FontSize = 8, ForegroundColor = Color.Cyan, HorizontalAlignment = HorizontalAlignment.Center, Margin = "5 3" };
            _mainPanel.AddChild(_txtStats);

            // History
            _txtHistory = new TextBlock { Text = "Sessao: 0W/0L | Bruto: $0 | Liq: $0", FontSize = 7, ForegroundColor = Color.White, HorizontalAlignment = HorizontalAlignment.Center, Margin = "5 2", Width = 220 };
            _mainPanel.AddChild(_txtHistory);

            // Bot State
            _txtBotState = new TextBlock { Text = "", FontSize = 7, ForegroundColor = Color.Gray, HorizontalAlignment = HorizontalAlignment.Center, Margin = "5 2", Width = 220 };
            _mainPanel.AddChild(_txtBotState);
            
            AddSeparator();
            
            // FIX Issue #7: Inicializar Virtual Stats
            _txtVirtualStats = new TextBlock { Text = "📊 VIRTUAL TRADES\nCarregando...", FontSize = 7, ForegroundColor = Color.White, HorizontalAlignment = HorizontalAlignment.Center, Margin = "5 2", Width = 220 };
            _mainPanel.AddChild(_txtVirtualStats);

            canvas.AddChild(_mainPanel);
            Chart.AddControl(canvas);
        }

        private void AddSeparator()
        {
            _mainPanel.AddChild(new StackPanel { Height = 1, BackgroundColor = Color.FromHex("#333"), Margin = "10 3" });
        }

        private void UpdatePanel()
        {
            if (_mainPanel == null) return;

            try
            {
                // Price
                _txtPrice.Text = $"{SymbolName}: {Symbol.Bid:F2}";

                // Account
                double dailyPnL = Account.Balance - _dailyStartBalance;
                _txtAccount.Text = $"Bal: ${Account.Balance:F2} | Eq: ${Account.Equity:F2}";

                // Positions
                var positions = Positions.Where(p => p.SymbolName == SymbolName && p.Label == BOT_LABEL).ToList();
                double posPnL = positions.Sum(p => p.NetProfit);
                if (positions.Count > 0)
                {
                    int buys = positions.Count(p => p.TradeType == TradeType.Buy);
                    int sells = positions.Count(p => p.TradeType == TradeType.Sell);
                    _txtPositions.Text = $"POS: {buys}B {sells}S | PnL: ${posPnL:F2}";
                    _txtPositions.ForegroundColor = posPnL >= 0 ? Color.Lime : Color.Red;
                }
                else
                {
                    _txtPositions.Text = "SEM POSICOES ABERTAS";
                    _txtPositions.ForegroundColor = Color.Gray;
                }

                // Status
                if (!EnableAutoTrade)
                {
                    _txtStatus.Text = "AUTO-TRADE DESATIVADO";
                    _txtStatus.ForegroundColor = Color.Red;
                }
                else if (!PassesSafetyChecks())
                {
                    _txtStatus.Text = "LIMITE ATINGIDO - PAUSADO";
                    _txtStatus.ForegroundColor = Color.Red;
                }
                else if (positions.Count >= MaxPositions)
                {
                    _txtStatus.Text = "MAX POSICOES - AGUARDANDO";
                    _txtStatus.ForegroundColor = Color.Orange;
                }
                else
                {
                    _txtStatus.Text = "MONITORANDO SINAIS";
                    _txtStatus.ForegroundColor = Color.Lime;
                }

                // Signal
                // Signal Logic
                    string confText = "Conf: --%";
                    Color confColor = Color.Gray;
                    
                    if (_currentSignal != null)
                    {
                        confText = $"Conf: {_currentSignal.Confidence}%";
                        confColor = _currentSignal.Confidence >= MinConfidence ? Color.Lime : Color.Orange;
                    }
                    
                    _txtConfidence.Text = confText;
                    _txtConfidence.ForegroundColor = confColor;

                if (_dailyTrades >= MaxDailyTrades)
                {
                   _txtSignal.Text = "Limite Diario Atingido";
                   _txtSignal.ForegroundColor = Color.Orange;
                }
                else if (Positions.Count(p => p.SymbolName == SymbolName) > 0)
                {
                   int openPos = Positions.Count(p => p.SymbolName == SymbolName);
                   _txtSignal.Text = $"GERENCIANDO {openPos} ORDEN(S)";
                   _txtSignal.ForegroundColor = Color.Cyan;
                   _txtStrategy.Text = "Monitorando TP/SL/Trail...";
                   
                   // Se tiver sinal novo, mostra nos levels
                   if (_currentSignal != null && _currentSignal.Status == "APPROVED" && _currentSignal.Confidence >= MinConfidence)
                   {
                        _txtLevels.Text = $"Novo Sinal: {_currentSignal.Signal}";
                   }
                   else
                   {
                        _txtLevels.Text = "";
                   }
                }
                else if (_currentSignal != null)
                {
                    bool hasSignal = _currentSignal.Status == "APPROVED" && _currentSignal.Confidence >= MinConfidence;
                    
                    if (hasSignal)
                    {
                        _txtSignal.Text = $">>> {_currentSignal.Signal} <<<";
                        _txtSignal.ForegroundColor = _currentSignal.Signal == "BUY" ? Color.Lime : Color.Red;
                        
                        _txtStrategy.Text = $"{_currentSignal.BestStrategy}";
                        _txtStrategy.ForegroundColor = Color.White;
                        
                        double slPct = Math.Abs(_currentSignal.Entry - _currentSignal.Stop) / _currentSignal.Entry * 100;
                        double tpPct = Math.Abs(_currentSignal.Target1 - _currentSignal.Entry) / _currentSignal.Entry * 100;
                        
                        _txtLevels.Text = $"Entry: {_currentSignal.Entry:F4}\n" +
                                          $"SL: {_currentSignal.Stop:F4} (-{slPct:F2}%)\n" +
                                          $"TP: {_currentSignal.Target1:F4} (+{tpPct:F2}%)";
                    }
                    else
                    {
                        _txtSignal.Text = "Sinal Fraco/Reprovado";
                        _txtSignal.ForegroundColor = Color.Gray;
                        _txtStrategy.Text = $"Min: {MinConfidence}% para executar";
                        _txtLevels.Text = "";
                    }
                }
                else
                {
                    _txtSignal.Text = "Aguardando Python...";
                    _txtSignal.ForegroundColor = Color.Yellow;
                    _txtStrategy.Text = "";
                    _txtLevels.Text = "";
                }

                // Stats
                _txtStats.Text = $"Hoje: {_dailyTrades} trades | ${dailyPnL:F2}";
                _txtStats.ForegroundColor = dailyPnL >= 0 ? Color.Lime : Color.Red;

                // History - Sessao W/L e lucros
                int totalTrades = _sessionWins + _sessionLosses;
                double winRate = totalTrades > 0 ? ((double)_sessionWins / totalTrades) * 100 : 0;
                double netProfit = _sessionGrossProfit - _sessionGrossLoss;
                _txtHistory.Text = $"Sessao: {_sessionWins}W/{_sessionLosses}L ({winRate:F0}%)\nBruto: +${_sessionGrossProfit:F2} | Liq: ${netProfit:F2}";
                _txtHistory.ForegroundColor = netProfit >= 0 ? Color.Lime : Color.Orange;

                // Bot State
                string lotMode = LotSizeMode == LotMode.Auto ? $"Auto {RiskPercent}%" : $"Fix {FixedLots}";
                string beState = EnableBreakeven ? $"BE:{BreakevenTriggerPercent}%" : "BE:OFF";
                _txtBotState.Text = $"Lots:{lotMode} | {beState}";
                
                // Update Portfolio Tracker
                var myPos = Positions.Where(p => p.SymbolName == SymbolName && p.Label == BOT_LABEL).ToList();
                int cScalp = myPos.Count(p => (p.Comment ?? "").ToLower().Contains("fast") || (p.Comment ?? "").ToLower().Contains("scalp"));
                int cIntra = myPos.Count(p => (p.Comment ?? "").ToLower().Contains("intra"));
                int cSwing = myPos.Count(p => (p.Comment ?? "").ToLower().Contains("swing"));
                
                int totalScalp = cScalp; 
                
                _txtPortfolio.Text = $"SCALP: {totalScalp}/3  |  INTRA: {cIntra}/1  |  SWING: {cSwing}/1";
            }
            catch { }
        }
        #endregion

        #region Signal Processing
        private void LoadSignal()
        {
            try
            {
                if (!File.Exists(_signalFile)) return;

                string json = "";
                for (int i = 0; i < 3; i++)
                {
                    try { json = File.ReadAllText(_signalFile); break; }
                    catch (IOException) { Thread.Sleep(100); }
                }
                
                if (string.IsNullOrEmpty(json)) return;
                _currentSignal = JsonSerializer.Deserialize<QuantumSignal>(json);
            }
            catch { }
        }

        private void WriteSymbolConfig()
        {
            try
            {
                var positions = Positions.Where(p => p.SymbolName == SymbolName && p.Label == BOT_LABEL).ToList();
                
                var config = new
                {
                    symbol_ctrader = SymbolName,
                    current_price = Symbol.Bid,
                    spread = Symbol.Spread / Symbol.PipSize,
                    positions = new
                    {
                        buy_count = positions.Count(p => p.TradeType == TradeType.Buy),
                        sell_count = positions.Count(p => p.TradeType == TradeType.Sell),
                        total_volume = positions.Sum(p => p.VolumeInUnits),
                        unrealized_pnl = positions.Sum(p => p.NetProfit)
                    },
                    account_balance = Account.Balance,
                    account_equity = Account.Equity,
                    bot_status = new
                    {
                        auto_trade = EnableAutoTrade,
                        daily_trades = _dailyTrades,
                        daily_pnl = Account.Balance - _dailyStartBalance
                    },
                    last_update = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
                };

                string json = JsonSerializer.Serialize(config, new JsonSerializerOptions { WriteIndented = true });
                string temp = _configFile + ".tmp";
                File.WriteAllText(temp, json);
                File.Move(temp, _configFile, true);
            }
            catch { }
        }

        private void ProcessQuantumSignal()
        {
            if (!EnableAutoTrade) return;
            if (_currentSignal == null) return;
            
            // Verificar se ja processou
            if (_currentSignal.SignalId == _lastProcessedSignalId) return;
            
            // Verificar se aprovado
            if (_currentSignal.Status != "APPROVED") return;
            
            // Verificar confianca minima
            if (_currentSignal.Confidence < MinConfidence)
            {
                _lastProcessedSignalId = _currentSignal.SignalId;
                return;
            }
            
            // Verificar timeout
            if (!string.IsNullOrEmpty(_currentSignal.Timestamp))
            {
                try
                {
                    var signalTime = DateTime.Parse(_currentSignal.Timestamp);
                    var age = (DateTime.Now - signalTime).TotalMinutes;
                    if (age > 15) // Hardcoded timeout (15 min)
                    {
                        Print($"Sinal expirado ({age:F0} min). Ignorando.");
                        _lastProcessedSignalId = _currentSignal.SignalId;
                        return;
                    }
                }
                catch { }
            }
            
            // Verificar direcao valida
            if (_currentSignal.Signal != "BUY" && _currentSignal.Signal != "SELL")
            {
                _lastProcessedSignalId = _currentSignal.SignalId;
                return;
            }
            
            // Safety checks
            if (!PassesSafetyChecks()) return;
            
            // Verificar se ja tem posicao
            var existingPositions = Positions.Where(p => p.SymbolName == SymbolName && p.Label == BOT_LABEL).ToList();
            if (existingPositions.Count >= MaxPositions)
            {
                _lastProcessedSignalId = _currentSignal.SignalId;
                return;
            }
            
            // Verificar se Entry, SL, TP validos
            if (_currentSignal.Entry <= 0 || _currentSignal.Stop <= 0 || _currentSignal.Target1 <= 0)
            {
                _lastProcessedSignalId = _currentSignal.SignalId;
                return;
            }
            
            // EXECUTAR TRADE!
            ExecuteTrade(_currentSignal);
            _lastProcessedSignalId = _currentSignal.SignalId;
        }

        private bool PassesSafetyChecks()
        {
            // 1. Daily Loss Check
            double dailyPnL = Account.Balance - _dailyStartBalance;
            double maxDailyLoss = _dailyStartBalance * (MaxDailyLossPercent / 100.0);
            
            if (dailyPnL < -maxDailyLoss)
            {
                Print($"BLOQUEADO! Perda diaria {dailyPnL:F2} > limite {maxDailyLoss:F2}");
                return false;
            }
            
            // 2. Session Loss Check (NEW!)
            if (_sessionStartEquity > 0)
            {
                double sessionLoss = (_sessionStartEquity - Account.Equity) / _sessionStartEquity * 100;
                if (sessionLoss >= MaxSessionLossPercent)
                {
                    Print($"BLOQUEADO! Perda sessao {sessionLoss:F1}% >= limite {MaxSessionLossPercent}%");
                    return false;
                }
            }
            
            // 3. Max Trades Check
            if (_dailyTrades >= MaxDailyTrades)
            {
                Print($"BLOQUEADO! Trades diarios {_dailyTrades} >= limite {MaxDailyTrades}");
                return false;
            }
            
            // 4. Max Total Lots Check (NEW!)
            double currentTotalLots = Positions
                .Where(p => p.SymbolName == SymbolName)
                .Sum(p => Symbol.VolumeInUnitsToQuantity(p.VolumeInUnits));
            
            if (currentTotalLots >= MaxTotalLots)
            {
                Print($"BLOQUEADO! Lotes totais {currentTotalLots:F2} >= limite {MaxTotalLots}");
                return false;
            }
            
            // 5. Free Margin Check (NEW!)
            // Adapta para contas pequenas: Minimo $50 ou 10% do balance (o que for menor)
            double minFreeMargin = Math.Min(50, Account.Balance * 0.1);
            
            if (Account.FreeMargin < minFreeMargin)
            {
                Print($"BLOQUEADO! Margem livre ${Account.FreeMargin:F2} < minimo dinâmico ${minFreeMargin:F2}");
                return false;
            }
            
            return true;
        }

        private void ExecuteTrade(QuantumSignal signal)
{
    try
    {
        TradeType tradeType = signal.Signal == "BUY" ? TradeType.Buy : TradeType.Sell;
        
        // Calcular volume baseado no modo
        double volumeInUnits;
        string lotInfo;
        
        // Para cálculo de risco, ainda precisamos saber a distância do SL em pips
        double slPips = Math.Abs(signal.Entry - signal.Stop) / Symbol.PipSize;
        
        if (LotSizeMode == LotMode.Auto)
        {
            // Modo Auto: calcula baseado em Risk% e SL
            double riskAmount = Account.Balance * (RiskPercent / 100.0);
            double pipValue = Symbol.PipValue;
            volumeInUnits = riskAmount / (slPips * pipValue);
            lotInfo = $"AUTO (Risk {RiskPercent}%)";
        }
        else
        {
            // Modo Manual: usa FixedLots
            volumeInUnits = Symbol.QuantityToVolumeInUnits(FixedLots);
            lotInfo = $"MANUAL ({FixedLots} lots)";
        }
        
        // Aplicar limites Min/Max do Symbol
        double minVol = Symbol.VolumeInUnitsMin;
        double maxVol = Symbol.VolumeInUnitsMax;
        volumeInUnits = Math.Max(minVol, Math.Min(maxVol, volumeInUnits));
        
        // Normalizar
        volumeInUnits = Symbol.NormalizeVolumeInUnits(volumeInUnits, RoundingMode.Down);
        
        // --- MARGIN CHECK & AUTO-SCALE ---
        double requiredMargin = Symbol.GetEstimatedMargin(tradeType, volumeInUnits);
        double freeMargin = Account.FreeMargin;
        
        if (requiredMargin > freeMargin * 0.95)
        {
            double ratio = (freeMargin * 0.95) / requiredMargin;
            double newVolume = volumeInUnits * ratio;
            newVolume = Symbol.NormalizeVolumeInUnits(newVolume, RoundingMode.Down);
            
            Print($"⚠️ Margem insuficiente para {volumeInUnits} units (Req: ${requiredMargin:F2}). Reduzindo para {newVolume} (Free: ${freeMargin:F2})");
            volumeInUnits = newVolume;
            lotInfo += " [SCALED]";
        }
        
        if (volumeInUnits < Symbol.VolumeInUnitsMin)
        {
            Print($"❌ Volume insuficiente ({volumeInUnits}) < Min ({Symbol.VolumeInUnitsMin}) após ajuste de risco/margem.");
            return;
        }
        
        double lots = Symbol.VolumeInUnitsToQuantity(volumeInUnits);
        
        double slDistPct = Math.Abs(signal.Entry - signal.Stop) / signal.Entry * 100;
        double tpDistPct = Math.Abs(signal.Target1 - signal.Entry) / signal.Entry * 100;
        
        Print("═══════════════════════════════════════════════════");
        Print($"   EXECUTANDO {signal.Signal} - {signal.BestStrategy}");
        Print($"   Confidence: {signal.Confidence}%");
        Print($"   Entry: {signal.Entry:F4} | SL: {signal.Stop:F4} ({slDistPct:F2}%) | TP: {signal.Target1:F4} ({tpDistPct:F2}%)");
        Print($"   Volume: {lots:F2} lots | Mode: {lotInfo}");
        Print("═══════════════════════════════════════════════════");
        
        // PASSAGEM PARA 2 ETAPAS (Open -> Modify)
        // Isso evita erros de 'TechnicalError' e confusão Pips vs Price
        
        // 1. Executar Ordem a Mercado (SEM SL/TP POR ENQUANTO)
        var result = ExecuteMarketOrder(tradeType, SymbolName, volumeInUnits, BOT_LABEL, null, null, signal.BestStrategy);
        
        if (result.IsSuccessful)
        {
            _dailyTrades++;
            var position = result.Position;
            Print($"SUCESSO! Posicao aberta. ID: {position.Id}");
            
            // 2. Modificar Posicionamento com Persistência
            // Tenta REPETIDAMENTE até conseguir (limite segurança: 20x)
            bool success = false;
            double currentSl = signal.Stop;
            double currentTp = signal.Target1;
            int attempt = 0;
            int maxRetries = 20; // Praticamente "até conseguir"
            
            while (!success && attempt < maxRetries)
            {
                attempt++;
                var modResult = ModifyPosition(position, currentSl, currentTp, true);
                
                if (modResult.IsSuccessful)
                {
                    Print($"SL/TP definidos com sucesso na tentativa {attempt}");
                    success = true;
                }
                else
                {
                    Print($"[ALERTA] Falha Modify tentativa {attempt}/{maxRetries}: {modResult.Error}. Ajustando e aguardando...");
                    
                    // Ajuste tecnico: Afastar 0.2% a cada falha
                    double adjustment = position.EntryPrice * 0.002; 
                    
                    if (position.TradeType == TradeType.Buy)
                    {
                        if (currentSl > 0) currentSl -= adjustment; // Desce SL
                        if (currentTp > 0) currentTp += adjustment; // Sobe TP
                    }
                    else
                    {
                        if (currentSl > 0) currentSl += adjustment; // Sobe SL
                        if (currentTp > 0) currentTp -= adjustment; // Desce TP
                    }
                    
                    // Pequena pausa para nao travar o servidor (rate limit)
                    System.Threading.Thread.Sleep(300);
                }
            }
            
            if (!success)
            {
                 Print($"[ERRO CRITICO] DESISTENCIA apos {maxRetries} tentativas de definir SL/TP.");
                 // Opcional: Fechar posicao por seguranca?
                 // ClosePosition(position);
            }
        }
        else
        {
            Print($"FALHA! {result.Error}");
        }
    }
    catch (Exception ex)
    {
        Print($"Erro: {ex.Message}");
    }
}
#endregion

#region Safe Modify with Retry
private bool SafeModifyPosition(Position pos, double? targetSL, double? targetTP, string context = "")
{
    const int maxRetries = 10;
    double incrementPct = 0.1; // Aumenta 0.1% por tentativa
    
            // --- VALIDAÇÃO 1: SL/TP Igual ao Atual? ---
            bool slChanged = targetSL.HasValue && (!pos.StopLoss.HasValue || Math.Abs(targetSL.Value - pos.StopLoss.Value) > Symbol.PipSize);
            bool tpChanged = targetTP.HasValue && (!pos.TakeProfit.HasValue || Math.Abs(targetTP.Value - pos.TakeProfit.Value) > Symbol.PipSize);
            
            if (!slChanged && !tpChanged)
            {
                // Nada mudou: OK, não precisa modificar
                return true;
            }
            
            // --- VALIDAÇÃO 2: SL/TP no Lado CORRETO? ---
            double entry = pos.EntryPrice;
            double currentPrice = pos.TradeType == TradeType.Buy ? Symbol.Bid : Symbol.Ask;
            
            if (targetSL.HasValue)
            {
                bool slValidSide = pos.TradeType == TradeType.Buy 
                    ? targetSL.Value < entry  // BUY: SL abaixo da entry
                    : targetSL.Value > entry; // SELL: SL acima da entry
                
                if (!slValidSide)
                {
                    Print($"[SIDE-ERROR] SL no lado errado! {pos.TradeType}: Entry={entry:F4}, SL={targetSL:F4} | {context}");
                    return false;
                }
            }
            
            if (targetTP.HasValue)
            {
                bool tpValidSide = pos.TradeType == TradeType.Buy 
                    ? targetTP.Value > entry  // BUY: TP acima da entry
                    : targetTP.Value < entry; // SELL: TP abaixo da entry
                
                if (!tpValidSide)
                {
                    Print($"[SIDE-ERROR] TP no lado errado! {pos.TradeType}: Entry={entry:F4}, TP={targetTP:F4} | {context}");
                    return false;
                }
            }
            
            // --- VALIDAÇÃO 3: Retry com Incremento (Distância Mínima) ---
            for (int attempt = 0; attempt < maxRetries; attempt++)
            {
                try
                {
                    var result = ModifyPosition(pos, targetSL, targetTP, true);
                    
                    if (result.IsSuccessful)
                    {
                        if (attempt > 0)
                            Print($"[RETRY-OK] Tentativa {attempt + 1} funcionou | {context}");
                        return true;
                    }
                    else
                    {
                        // Broker rejeitou: Aumentar distância
                        if (targetSL.HasValue && attempt < maxRetries - 1)
                        {
                            double currentDist = Math.Abs(targetSL.Value - entry);
                            double newDist = currentDist * (1.0 + incrementPct / 100.0);
                            
                            targetSL = pos.TradeType == TradeType.Buy 
                                ? entry - newDist 
                                : entry + newDist;
                        }
                        
                        if (targetTP.HasValue && attempt < maxRetries - 1)
                        {
                            double currentDist = Math.Abs(targetTP.Value - entry);
                            double newDist = currentDist * (1.0 + incrementPct / 100.0);
                            
                            targetTP = pos.TradeType == TradeType.Buy 
                                ? entry + newDist 
                                : entry - newDist;
                        }
                        
                        // Log apenas na última tentativa
                        if (attempt == maxRetries - 1)
                        {
                            Print($"[MODIFY-FAIL] {result.Error} (10 tentativas) | {context}");
                            return false;
                        }
                    }
                }
                catch (Exception ex)
                {
                    if (attempt == maxRetries - 1)
                    {
                        Print($"[MODIFY-EXCEPTION] {ex.Message} | {context}");
                        return false;
                    }
                }
            }
            
            return false;
        }
        #endregion

        #region AI-Driven Position Reviews
        private DateTime _lastReviewCheck = DateTime.MinValue;
        
        private void ProcessPositionReviews()
        {
            try
            {
                // Throttle: Verificar a cada 30 segundos
                if ((Server.Time - _lastReviewCheck).TotalSeconds < 30) return;
                _lastReviewCheck = Server.Time;
                
                string reviewFile = Path.Combine(_dataFolder, "position_reviews.json");
                if (!File.Exists(reviewFile)) return;
                
                string json = File.ReadAllText(reviewFile);
                if (string.IsNullOrEmpty(json)) return;
                
                // Parse JSON
                var doc = JsonDocument.Parse(json);
                var root = doc.RootElement;
                
                if (!root.TryGetProperty("reviews", out var reviews)) return;
                
                int executed = 0;
                
                foreach (var review in reviews.EnumerateArray())
                {
                    if (!review.TryGetProperty("position_id", out var pidProp)) continue;
                    if (!review.TryGetProperty("action", out var actionProp)) continue;
                    
                    long posId = pidProp.GetInt64();
                    string action = actionProp.GetString();
                    string reason = review.TryGetProperty("reason", out var r) ? r.GetString() : "N/A";
                    
                    var position = Positions.FirstOrDefault(p => p.Id == posId);
                    if (position == null)
                    {
                        Print($"[AI-REVIEW] Posição #{posId} não encontrada. Pulando.");
                        continue;
                    }
                    
                    Print($"[AI-REVIEW] Pos #{posId} → {action}");
                    Print($"  Razão: {reason}");
                    
                    switch (action)
                    {
                        case "KEEP":
                            // Nada a fazer
                            break;
                            
                        case "TIGHTEN_SL":
                            // Apertar SL para 60% da distância atual
                            if (position.StopLoss.HasValue)
                            {
                                double entry = position.EntryPrice;
                                double currentDist = Math.Abs(position.StopLoss.Value - entry);
                                double newDist = currentDist * 0.6; // 60%
                                
                                double newSL = position.TradeType == TradeType.Buy
                                    ? entry - newDist
                                    : entry + newDist;
                                
                                bool success = SafeModifyPosition(position, newSL, position.TakeProfit, $"AI Tighten SL #{posId}");
                                if (success)
                                {
                                    Print($"[AI-EXEC] SL apertado de {currentDist*100/entry:F2}% para {newDist*100/entry:F2}%");
                                    executed++;
                                }
                            }
                            break;
                            
                        case "MOVE_TP_CLOSER":
                            // Mover TP 40% mais perto para garantir lucro
                            if (position.TakeProfit.HasValue)
                            {
                                double entry = position.EntryPrice;
                                double currentDist = Math.Abs(position.TakeProfit.Value - entry);
                                double newDist = currentDist * 0.6; // 60% da distância = 40% mais perto
                                
                                double newTP = position.TradeType == TradeType.Buy
                                    ? entry + newDist
                                    : entry - newDist;
                                
                                bool success = SafeModifyPosition(position, position.StopLoss, newTP, $"AI Move TP #{posId}");
                                if (success)
                                {
                                    Print($"[AI-EXEC] TP movido para {newDist*100/entry:F2}% (era {currentDist*100/entry:F2}%)");
                                    executed++;
                                }
                            }
                            break;
                            
                        case "CLOSE_NOW":
                            // Fechar posição imediatamente
                            var result = ClosePosition(position);
                            if (result.IsSuccessful)
                            {
                                Print($"[AI-EXEC] Posição #{posId} fechada ao mercado por sugestão da IA");
                                Print($"  Resultado: {(position.NetProfit >= 0 ? "✅ Lucro" : "❌ Loss")} ${position.NetProfit:F2}");
                                executed++;
                            }
                            else
                            {
                                Print($"[AI-FAIL] Não foi possível fechar #{posId}: {result.Error}");
                            }
                            break;
                            
                        default:
                            Print($"[AI-SKIP] Ação desconhecida: {action}");
                            break;
                    }
                }
                
                if (executed > 0)
                {
                    Print($"[AI-REVIEW] {executed} sugestões executadas com sucesso");
                    // Limpar arquivo para evitar re-execução
                    File.Delete(reviewFile);
                }
            }
            catch (Exception ex)
            {
                Print($"[AI-REVIEW ERROR] {ex.Message}");
            }
        }
        #endregion

        #region Legacy Trade Adoption
        private DateTime _lastLegacyCheck = DateTime.MinValue;
        
        private void FixLegacyTrades()
        {
            try
            {
                // Throttle: Verificar a cada 30 segundos
                if ((Server.Time - _lastLegacyCheck).TotalSeconds < 30) return;
                _lastLegacyCheck = Server.Time;
                
                var legacyPositions = Positions.Where(p => 
                    p.SymbolName == SymbolName && 
                    p.Label == BOT_LABEL && 
                    string.IsNullOrEmpty(p.Comment)).ToList();
                
                if (legacyPositions.Count == 0) return;
                
                Print($"[LEGACY] {legacyPositions.Count} ordens antigas detectadas. Ajustando SL/TP...");
                
                foreach (var pos in legacyPositions)
                {
                    var holdTime = Server.Time - pos.EntryTime;
                    string strategy = "SCALP"; // Default seguro
                    double slPct = 0.6;
                    double tpPct = 1.2;
                    
                   if (holdTime.TotalMinutes < 5)
                    {
                        strategy = "FAST_SCALP";
                        slPct = 0.3;
                        tpPct = 0.6;
                    }
                    else if (holdTime.TotalMinutes >= 5 && holdTime.TotalMinutes < 15)
                    {
                        strategy = "SCALP";
                        slPct = 0.6;
                        tpPct = 1.2;
                    }
                    else if (holdTime.TotalMinutes >= 30 && holdTime.TotalMinutes < 60)
                    {
                        strategy = "SWING";
                        slPct = 3.0;
                        tpPct = 6.0;
                    }
                    else if (holdTime.TotalHours >= 1)
                    {
                        strategy = "INTRADAY";
                        slPct = 1.6;
                        tpPct = 3.0;
                    }
                    
                    bool isCrypto = SymbolName.Contains("BTC") || SymbolName.Contains("ETH") || 
                                   SymbolName.Contains("XRP") || SymbolName.Contains("LTC");
                    if (isCrypto)
                    {
                        slPct *= 2.0;
                        tpPct *= 2.0;
                    }
                    
                    double entry = pos.EntryPrice;
                    double slDist = entry * (slPct / 100.0);
                    double tpDist = entry * (tpPct / 100.0);
                    
                    double newSL = pos.TradeType == TradeType.Buy ? entry - slDist : entry + slDist;
                    double newTP = pos.TradeType == TradeType.Buy ? entry + tpDist : entry - tpDist;
                    
                    bool updateSL = !pos.StopLoss.HasValue;
                    if (pos.StopLoss.HasValue)
                    {
                        if (pos.TradeType == TradeType.Buy)
                            updateSL = newSL > pos.StopLoss.Value;
                        else
                            updateSL = newSL < pos.StopLoss.Value;
                    }
                    
                    double? finalSL = updateSL ? newSL : pos.StopLoss;
                    double? finalTP = pos.TakeProfit ?? newTP;
                    
                    bool success = SafeModifyPosition(pos, finalSL, finalTP, $"Legacy #{pos.Id} {strategy}");
                    
                    if (success)
                        Print($"[LEGACY] #{pos.Id} → {strategy} | SL:{slPct:F1}% TP:{tpPct:F1}% | Hold:{holdTime.TotalMinutes:F0}min");
                }
                
                Print($"[LEGACY] {legacyPositions.Count} ordens adotadas. Contam no Portfolio.");
            }
            catch (Exception ex)
            {
                Print($"[LEGACY] Erro: {ex.Message}");
            }
        }
        #endregion

        #region Trade Management
        private void ManageOpenPositions()
        {
            // Se ManageAllPositions=true, gerencia todas as posicoes do simbolo
            // Se ManageAllPositions=false, gerencia apenas as do bot
            var positions = ManageAllPositions 
                ? Positions.Where(p => p.SymbolName == SymbolName).ToList()
                : Positions.Where(p => p.SymbolName == SymbolName && p.Label == BOT_LABEL).ToList();
            
            foreach (var pos in positions)
            {
                try
                {
                    double currentPrice = pos.TradeType == TradeType.Buy ? Symbol.Bid : Symbol.Ask;
                    double entryPrice = pos.EntryPrice;
                    
                    // Calcular Ganho em % do Preço
                    // Ex: Entry 100, Price 101 => 1% Gain
                    double priceDistance = Math.Abs(currentPrice - entryPrice);
                    double gainPercent = (priceDistance / entryPrice) * 100.0;
                    
                    // Se estiver perdendo, gainPercent não importa para BE/Trail
                    if (pos.NetProfit < 0) continue; 
                    
                    // Breakeven logic (Price %)
                    if (EnableBreakeven && gainPercent >= BreakevenTriggerPercent)
                    {
                        double lockDistance = entryPrice * (BreakevenLockPercent / 100.0);
                        double newSL = pos.TradeType == TradeType.Buy 
                            ? entryPrice + lockDistance
                            : entryPrice - lockDistance;
                        
                        // Atualiza apenas se melhorar o SL
                        bool needsUpdate = pos.TradeType == TradeType.Buy 
                            ? (pos.StopLoss == null || pos.StopLoss < newSL)
                            : (pos.StopLoss == null || pos.StopLoss > newSL);
                        
                        if (needsUpdate)
                        {
                            SafeModifyPosition(pos, newSL, pos.TakeProfit, "Breakeven");
                            Print($"BE ativado! Gain {gainPercent:F2}% > Trigger {BreakevenTriggerPercent}% | SL Ajustado");
                        }
                    }
                    
                    // Trailing Stop Logic (Price %)
                    if (EnableTrailing && gainPercent >= TrailStartPercent)
                    {
                        double trailDistance = currentPrice * (TrailDistancePercent / 100.0);
                        double newSL = pos.TradeType == TradeType.Buy
                            ? currentPrice - trailDistance
                            : currentPrice + trailDistance;
                            
                        bool shouldUpdate = pos.TradeType == TradeType.Buy
                            ? (pos.StopLoss == null || newSL > pos.StopLoss)
                            : (pos.StopLoss == null || newSL < pos.StopLoss);
                            
                        if (shouldUpdate)
                        {
                            SafeModifyPosition(pos, newSL, pos.TakeProfit, "Trailing");
                            Print($"Trailing ativado! Gain {gainPercent:F2}% | SL movido para {newSL}");
                        }
                    }
                }
                catch { }
            }
        }
        #endregion

        protected override void OnStop()
        {
            Print("═══════════════════════════════════════════════════");
            Print("   TITAN FUSION QUANTUM BOT - Encerrado");
            Print($"   Trades hoje: {_dailyTrades}");
            Print($"   P&L dia: ${Account.Balance - _dailyStartBalance:F2}");
            Print("═══════════════════════════════════════════════════");
        }

        // JSON Classes
        private class QuantumSignal
        {
            [JsonPropertyName("status")] public string Status { get; set; }
            [JsonPropertyName("signal_id")] public string SignalId { get; set; }
            [JsonPropertyName("best_strategy")] public string BestStrategy { get; set; }
            [JsonPropertyName("signal")] public string Signal { get; set; }
            [JsonPropertyName("confidence")] public double Confidence { get; set; }
            [JsonPropertyName("entry")] public double Entry { get; set; }
            [JsonPropertyName("stop")] public double Stop { get; set; }
            [JsonPropertyName("target1")] public double Target1 { get; set; }
            [JsonPropertyName("target2")] public double Target2 { get; set; }
            [JsonPropertyName("timestamp")] public string Timestamp { get; set; }
        }
        #region Data Export
        private void ExportMarketData()
        {
            try
            {
                // Throttle: Exportar a cada 10 segundos
                if ((Server.Time - _lastExportTime).TotalSeconds < 10) return;
                _lastExportTime = Server.Time;

                // 1. Coletar posicoes abertas (para Portfolio Check)
                var myPositions = Positions
                    .Where(p => p.SymbolName == SymbolName && p.Label == BOT_LABEL)
                    .Select(p => new 
                    {
                        id = p.Id,
                        type = p.TradeType.ToString().ToUpper(), // BUY ou SELL (maiúsculas)
                        entry = p.EntryPrice,
                        sl = p.StopLoss.HasValue ? p.StopLoss.Value : 0.0, // CRITICO: Exportar SL
                        tp = p.TakeProfit.HasValue ? p.TakeProfit.Value : 0.0, // CRITICO: Exportar TP
                        pnl = p.NetProfit,
                        strategy = p.Comment // Estratégia vem do comentário
                    })
                    .ToArray();

                // 2. Coletar dados de Candles
                var data = new
                {
                    symbol = SymbolName,
                    current_price = Symbol.Bid,
                    active_positions = myPositions,
                    
                    // METADADOS DO SIMBOLO
                    symbol_metadata = new
                    {
                        pip_size = Symbol.PipSize,
                        pip_value = Symbol.PipValue,
                        tick_size = Symbol.TickSize,
                        digits = Symbol.Digits,
                        
                        // Volume em UNITS (usado para execução)
                        volume_min = Symbol.VolumeInUnitsMin,
                        volume_max = Symbol.VolumeInUnitsMax,
                        volume_step = Symbol.VolumeInUnitsStep,
                        
                        description = Symbol.Description,
                        spread_current = Symbol.Spread,
                        ask = Symbol.Ask,
                        bid = Symbol.Bid
                    },
                    
                    // MARKET SENTIMENT (Real Broker Data)
                    sentiment = new
                    {
                        buy_percent = Symbol.Sentiment?.BuyPercentage ?? 50.0,
                        sell_percent = Symbol.Sentiment?.SellPercentage ?? 50.0,
                        is_extreme = IsExtremeSentiment(Symbol.Sentiment),
                        bias = GetSentimentBias(Symbol.Sentiment),
                        available = Symbol.Sentiment != null
                    },
                    
                    m1 = GetCandlesFrom(TimeFrame.Minute),
                    m5 = GetCandlesFrom(TimeFrame.Minute5),
                    m15 = GetCandlesFrom(TimeFrame.Minute15),
                    m30 = GetCandlesFrom(TimeFrame.Minute30),
                    h1 = GetCandlesFrom(TimeFrame.Hour),
                    h2 = GetCandlesFrom(TimeFrame.Hour2),
                    h4 = GetCandlesFrom(TimeFrame.Hour4)
                };

                // 3. Serializar e Salvar (Multi-Symbol Support)
                string json = JsonSerializer.Serialize(data);
                
                // CRITICO: Criar pasta do simbolo
                string symbolFolder = Path.Combine(_dataFolder, SymbolName);
                if (!Directory.Exists(symbolFolder))
                    Directory.CreateDirectory(symbolFolder);

                string fullPath = Path.Combine(symbolFolder, "symbol_config.json");
                File.WriteAllText(fullPath, json);
            }
            catch (Exception ex)
            {
                Print($"Erro Export: {ex.Message}");
            }
        }
        
        // Sentiment Helper Functions (Market-Specific Thresholds)
        private string DetectMarketType()
        {
            string symbolName = SymbolName.ToUpper();
            
            // Gold/Silver detection
            if (symbolName.Contains("XAU") || symbolName.Contains("GOLD") || 
                symbolName.Contains("XAG") || symbolName.Contains("SILVER"))
                return "GOLD";
            
            // Bitcoin/Crypto detection
            if (symbolName.Contains("BTC") || symbolName.Contains("ETH") || 
                symbolName.Contains("CRYPTO") || symbolName.Contains("BITCOIN") || 
                symbolName.Contains("ETHEREUM") || symbolName.Contains("XRP") ||
                symbolName.Contains("NEO") || symbolName.Contains("FET"))
                return "BITCOIN";
            
            // Indices detection
            if (symbolName.Contains("US30") || symbolName.Contains("NAS") || 
                symbolName.Contains("SPX") || symbolName.Contains("GER") || 
                symbolName.Contains("UK100") || symbolName.Contains("JPN") ||
                symbolName.Contains("DOW") || symbolName.Contains("DAX") || 
                symbolName.Contains("FTSE") || symbolName.Contains("NIKKEI"))
                return "INDICES";
            
            // Forex detection (default)
            return "FOREX";
        }
        
        private double GetOverboughtLevel()
        {
            string marketType = DetectMarketType();
            if (marketType == "GOLD") return 70.0;
            if (marketType == "BITCOIN") return 80.0;
            if (marketType == "INDICES") return 72.0;
            return 75.0; // FOREX default
        }
        
        private double GetOversoldLevel()
        {
            string marketType = DetectMarketType();
            if (marketType == "GOLD") return 30.0;
            if (marketType == "BITCOIN") return 20.0;
            if (marketType == "INDICES") return 28.0;
            return 25.0; // FOREX default
        }
        
        private bool IsExtremeSentiment(SymbolSentiment sent)
        {
            if (sent == null) return false;
            double overbought = GetOverboughtLevel();
            double oversold = GetOversoldLevel();
            return sent.BuyPercentage >= overbought || sent.BuyPercentage <= oversold;
        }
        
        private string GetSentimentBias(SymbolSentiment sent)
        {
            if (sent == null) return "NEUTRAL";
            double overbought = GetOverboughtLevel();
            double oversold = GetOversoldLevel();
            
            if (sent.BuyPercentage >= overbought) return "OVERBOUGHT";
            if (sent.BuyPercentage <= oversold) return "OVERSOLD";
            return "NEUTRAL";
        }

        private object[] GetCandlesFrom(TimeFrame tf)
        {
            var bars = MarketData.GetBars(tf);
            var exportBars = new System.Collections.Generic.List<object>();
            
            // Pegar ultimos 100 candles (ou menos se nao tiver historico suficiente)
            int count = 100;
            int start = Math.Max(0, bars.Count - count);
            
            for (int i = start; i < bars.Count; i++)
            {
                exportBars.Add(new 
                {
                    time = bars[i].OpenTime.ToString("yyyy-MM-dd HH:mm:ss"),
                    open = bars[i].Open,
                    high = bars[i].High,
                    low = bars[i].Low,
                    close = bars[i].Close,
                    volume = bars[i].TickVolume
                });
            }
            return exportBars.ToArray();
        }
        #endregion
        
        #region Virtual Stats Loading
        private struct VirtualStats
        {
            public int ExecutedTotal;
            public int ExecutedWins;
            public int ExecutedLosses;
            public double ExecutedWinRate;
            public int VirtualTotal;
            public int VirtualWins;
            public int VirtualLosses;
            public double VirtualWinRate;
            public int BlockedCount;
            public double MissedProfitPct;
        }
        
        private VirtualStats LoadVirtualStats()
        {
            var stats = new VirtualStats();
            
            try
            {
                string file = Path.Combine(_dataFolder, "virtual_stats.json");
                if (!File.Exists(file)) return stats;
                
                string json = File.ReadAllText(file);
                var doc = JsonDocument.Parse(json);
                var root = doc.RootElement;
                
                if (root.TryGetProperty("executed", out var exec))
                {
                    stats.ExecutedTotal = exec.GetProperty("total").GetInt32();
                    stats.ExecutedWins = exec.GetProperty("wins").GetInt32();
                    stats.ExecutedLosses = exec.GetProperty("losses").GetInt32();
                    stats.ExecutedWinRate = exec.GetProperty("win_rate").GetDouble();
                }
                
                if (root.TryGetProperty("virtual", out var virt))
                {
                    stats.VirtualTotal = virt.GetProperty("total").GetInt32();
                    stats.VirtualWins = virt.GetProperty("wins").GetInt32();
                    stats.VirtualLosses = virt.GetProperty("losses").GetInt32();
                    stats.VirtualWinRate = virt.GetProperty("win_rate").GetDouble();
                }
                
                if (root.TryGetProperty("blocked_count", out var blocked))
                    stats.BlockedCount = blocked.GetInt32();
                    
                if (root.TryGetProperty("missed_profit_pct", out var missed))
                    stats.MissedProfitPct = missed.GetDouble();
            }
            catch (Exception ex)
            {
                Print($"[VIRTUAL-STATS] Erro ao carregar: {ex.Message}");
            }
            
            return stats;
        }
        
        // Método para exibir Virtual Stats no painel (chamar no UpdatePanel)
        private void UpdateVirtualStatsDisplay()
        {
            if (_txtVirtualStats == null) return;
            
            var vStats = LoadVirtualStats();
            
            if (vStats.ExecutedTotal == 0 && vStats.VirtualTotal == 0)
            {
                _txtVirtualStats.Text = "📊 VIRTUAL: Aguardando dados...";
                return;
            }
            
            string execColor = vStats.ExecutedWinRate >= 70 ? "🟢" : vStats.ExecutedWinRate >= 50 ? "🟡" : "🔴";
            string virtColor = vStats.VirtualWinRate >= 70 ? "🟢" : vStats.VirtualWinRate >= 50 ? "🟡" : "🔴";
            
            _txtVirtualStats.Text = 
                $"📊 VIRTUAL TRADES\n" +
                $"{execColor} Exec: {vStats.ExecutedWins}W/{vStats.ExecutedLosses}L ({vStats.ExecutedWinRate:F1}%)\n" +
                $"{virtColor} Block: {vStats.VirtualWins}W/{vStats.VirtualLosses}L ({vStats.VirtualWinRate:F1}%)\\n" +
                $"💰 Missed: +{vStats.MissedProfitPct:F2}%";
        }
        #endregion
        
        #region Breakeven Management (2-Tier System)
        private void CheckBreakeven()
        {
            if (!EnableBreakeven) return;
            
            var myPositions = Positions.Where(p => 
                p.SymbolName == SymbolName && 
                (ManageAllPositions || p.Label == BOT_LABEL)
            );
            
            foreach (var pos in myPositions)
            {
                // Calcular lucro atual em %
                double profitPct = ((Symbol.Bid - pos.EntryPrice) / pos.EntryPrice) * 100;
                if (pos.TradeType == TradeType.Sell)
                    profitPct = ((pos.EntryPrice - Symbol.Ask) / pos.EntryPrice) * 100;
                
                // SL atual
                double? currentSL = pos.StopLoss;
                if (!currentSL.HasValue) continue; // Sem SL definido, pular
                
                double newSL = 0;
                bool shouldMove = false;
                string reason = "";
                
                // TIER 2: Lucro Garantido (>= 3%)
                if (profitPct >= BreakevenTier2TriggerPercent)
                {
                    double tier2Target = pos.EntryPrice + (pos.EntryPrice * (BreakevenTier2LockPercent / 100));
                    if (pos.TradeType == TradeType.Sell)
                        tier2Target = pos.EntryPrice - (pos.EntryPrice * (BreakevenTier2LockPercent / 100));
                    
                    // Só move se ainda não estiver nesse nível
                    if (pos.TradeType == TradeType.Buy && currentSL.Value < tier2Target)
                    {
                        newSL = tier2Target;
                        shouldMove = true;
                        reason = $"TIER2 ({profitPct:F2}%): Garantindo +{BreakevenTier2LockPercent}%";
                    }
                    else if (pos.TradeType == TradeType.Sell && currentSL.Value > tier2Target)
                    {
                        newSL = tier2Target;
                        shouldMove = true;
                        reason = $"TIER2 ({profitPct:F2}%): Garantindo +{BreakevenTier2LockPercent}%";
                    }
                }
                // TIER 1: Breakeven (>= 0.5%)
                else if (profitPct >= BreakevenTriggerPercent)
                {
                    double tier1Target = pos.EntryPrice + (pos.EntryPrice * (BreakevenLockPercent / 100));
                    if (pos.TradeType == TradeType.Sell)
                        tier1Target = pos.EntryPrice - (pos.EntryPrice * (BreakevenLockPercent / 100));
                    
                    // Só move se ainda não estiver em breakeven
                    if (pos.TradeType == TradeType.Buy && currentSL.Value < tier1Target)
                    {
                        newSL = tier1Target;
                        shouldMove = true;
                        reason = $"TIER1 ({profitPct:F2}%): Breakeven +{BreakevenLockPercent}%";
                    }
                    else if (pos.TradeType == TradeType.Sell && currentSL.Value > tier1Target)
                    {
                        newSL = tier1Target;
                        shouldMove = true;
                        reason = $"TIER1 ({profitPct:F2}%): Breakeven +{BreakevenLockPercent}%";
                    }
                }
                
                if (shouldMove)
                {
                    // FIX Issue #6: Preservar TP existente, não setar para 0
                    double? tpValue = pos.TakeProfit.HasValue ? pos.TakeProfit.Value : (double?)null;
                    
                    if (tpValue.HasValue)
                    {
                        // TP existe: mover SL E preservar TP
                        var result = ModifyPosition(pos, newSL, tpValue.Value, true);
                        if (result.IsSuccessful)
                        {
                            Print($"✅ [{reason}] SL movido: {currentSL.Value:F5} → {newSL:F5} | TP preservado: {tpValue.Value:F5} (PID{pos.Id})");
                        }
                        else
                        {
                            Print($"❌ Falha BE: {result.Error} (PID{pos.Id})");
                        }
                    }
                    else
                    {
                        // TP não existe: apenas mover SL sem setar TP
                        // Passando 0 com protectionType=false para não criar TP
                        var result = ModifyPosition(pos, newSL, 0, false);
                        if (result.IsSuccessful)
                        {
                            Print($"✅ [{reason}] SL movido: {currentSL.Value:F5} → {newSL:F5} | Sem TP (PID{pos.Id})");
                        }
                        else
                        {
                            Print($"❌ Falha BE: {result.Error} (PID{pos.Id})");
                        }
                    }
                }
            }
        }
        #endregion
    }
}
