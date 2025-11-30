# 🚀 Titan Pro - Hybrid GPU Trading System

**Advanced multi-strategy trading bot with dual GPU optimization and Walk-Forward validation**

![Python](https://img.shields.io/badge/Python-3.12-blue)
![GPU](https://img.shields.io/badge/GPU-CUDA%20%2B%20OpenCL-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🎯 Features

- **Dual GPU Processing**: Intel + NVIDIA GPUs working in parallel
- **100k Parameter Combinations**: Exhaustive grid search optimization
- **Walk-Forward Validation**: 70/30 train/test split with anti-overfitting
- **Multi-Strategy**: Scalper, Breakout, and Pullback strategies
- **Auto-Update**: Weekly data refresh and re-calibration
- **Institutional Data**: Dukascopy (real markets) + Deriv (synthetics)
- **Multi-Timeframe**: M1, M5, M15, M30, H1 support
- **8 Markets**: 4 real (XAUUSD, EURUSD, USDJPY, GBPUSD) + 4 synthetic (R_75, R_100, R_25, R_50)

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────┐
│           TITAN PRO HYBRID SYSTEM                   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────┐         ┌──────────────┐        │
│  │  CPU Engine  │         │  GPU Engine  │        │
│  │  <1ms Trade  │         │  100k Combos │        │
│  │   Execution  │         │  Optimization│        │
│  └──────┬───────┘         └──────┬───────┘        │
│         │                        │                 │
│         │    ┌──────────────────┘                 │
│         │    │                                     │
│    ┌────▼────▼────┐                               │
│    │ Data Manager │                               │
│    │  Auto-Update │                               │
│    └──────┬───────┘                               │
│           │                                        │
│  ┌────────▼────────────┐                          │
│  │  Dukascopy + Deriv  │                          │
│  │   3 Months History  │                          │
│  └─────────────────────┘                          │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### **⚡ One-Line Installer (Recommended)**
Open **PowerShell** as Administrator and run:
```powershell
irm https://raw.githubusercontent.com/LucassVal/TitanFusion-cBot/main/install.ps1 | iex
```

### **Manual Installation**
**1. Install Dependencies**
```bash
pip install pandas pandas_ta numpy pyopencl websockets requests
```

**2. Run Launcher**
```bash
cd "Titan pro"
python launcher.py
```

### **3. Select Market & Timeframe**
```
📊 SELECT MARKET:
[1-4] Synthetic (24/7)
[5-8] Real Forex

⏰ SELECT TIMEFRAME:
[1-5] M1, M5, M15, M30, H1
```

### **4. Auto-Download & Trade**
System automatically:
- Downloads 3 months of data
- Optimizes 100k parameter combinations
- Validates with Walk-Forward (70/30)
- Starts live trading with best parameters

---

## 📁 File Structure

```
Titan pro/
├── launcher.py .................. Interactive menu
├── titan_hybrid.py .............. Main trading engine
├── data_manager.py .............. Data download & caching
├── deriv_client.py .............. Deriv API connector
├── deriv_downloader.py .......... Deriv data downloader
├── dukascopy_downloader.py ...... Dukascopy data downloader
├── dashboard.html ............... Visual monitoring dashboard
├── check_cuda.py ................ GPU verification tool
└── data_cache.json .............. Update tracking (auto-created)

Data files (auto-downloaded):
├── dukascopy_XAUUSD_M1_3months.csv
├── dukascopy_EURUSD_M1_3months.csv
├── deriv_R_75_M1_3months.csv
└── deriv_R_100_M1_3months.csv
```

---

## ⚙️ Configuration

### **Optimization Settings**
```python
# titan_hybrid.py
OPTIMIZATION_INTERVAL = 100  # Re-optimize every 100 candles
HISTORY_SIZE = 8640          # Keep last 8640 candles (~3 months M15)
WALK_FORWARD_TRAIN_SIZE = 0.7  # 70% training
WALK_FORWARD_TEST_SIZE = 0.3   # 30% validation
```

### **Auto-Update**
```python
# data_manager.py
manager.needs_update(source, days=7)  # Check if data >7 days old
```

---

## 🧠 Optimization Strategy

### **Grid Search**
- **100,000 combinations** tested
- 3 strategies with independent parameters
- Dual GPU parallel processing (~1-2 min)

### **Walk-Forward Validation**
```python
1. Split data: 70% train | 30% test
2. Find best params on train set
3. Validate on unseen test data
4. Only update if:
   - Test fitness > -999k (no death condition)
   - Performance ratio ≥ 50% vs train
```

### **Anti-Overfitting Measures**
- Win rate penalties (>75% = suspicious)
- Profit factor limits (<1.2 or >5.0 = rejected)
- Trade count validation (20-500 trades)
- Drawdown hard stop (≥20% = death)

---

## 📈 Supported Markets

### **Real Markets** (Dukascopy Data)
- XAUUSD (Gold)
- EURUSD
- USDJPY
- GBPUSD

### **Synthetic Markets** (Deriv Data)
- R_75 (Volatility 75 Index)
- R_100 (Volatility 100 Index)
- R_25 (Volatility 25 Index)
- R_50 (Volatility 50 Index)

---

## 🔄 Weekly Re-Calibration

System automatically:
1. Checks data age every 7 days
2. Downloads fresh data
3. Re-optimizes 100k combinations
4. Validates with Walk-Forward
5. Updates parameters if validation passes

---

## 📊 Dashboard

Open `dashboard.html` in browser for real-time monitoring:
- 3 strategies with individual fitness scores
- Winner/Active/Standby status
- Trade history with P&L
- Parameter display per strategy

*(WebSocket backend in development)*

---

## 🛠️ Technical Stack

- **Language**: Python 3.12
- **GPU**: PyOpenCL (Intel + NVIDIA)
- **Indicators**: pandas_ta
- **Data Sources**: Dukascopy (real), Deriv (synthetic)
- **Optimization**: Random Search + Walk-Forward

---

## ⚠️ Risk Management

- **Max Drawdown**: 20% (hard stop)
- **Risk per Trade**: 2% of balance
- **Max Active Trades**: 2 (Central Engine limit)
- **Validation**: Walk-Forward prevents overfitting

---

## 📝 License

MIT License - Feel free to use and modify

---

## 🤝 Contributing

Pull requests welcome! Please:
1. Fork the repository
2. Create feature branch
3. Test thoroughly
4. Submit PR with description

---

## 📧 Contact

**Lucas Valério**
- GitHub: [@LucassVal](https://github.com/LucassVal)
- Project: [TitanFusion-cBot](https://github.com/LucassVal/TitanFusion-cBot)

---

**⚡ Titan Pro - Industrial-Grade Algorithmic Trading**
