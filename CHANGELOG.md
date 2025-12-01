# TITAN PRO - VERSION HISTORY

## v2.0.0 (2025-12-01) - Major Release
### 🎯 Working Capital & Risk Management Overhaul

**New Features:**
- ✅ **Working Capital Selection**: User chooses % or $ amount from Deriv balance
- ✅ **Real Balance Integration**: Fetches actual account balance via Deriv API
- ✅ **Tiered DD Thresholds**:
  - Training: 15% (find conservative params)
  - Validation: 20% (test robustness)
  - Live: 12% (protect capital)
- ✅ **Auto-Reconnection**: WebSocket ping keepalive + exponential backoff
- ✅ **5% Daily Profit Target**: Optimized fitness function for realistic returns

**Critical Fixes:**
- 🐛 Fixed fitness function using dynamic 15% DD instead of hardcoded $10
- 🐛 Fixed 100% parameter rejection issue
- 🐛 Fixed balance handling (was hardcoded $50)
- 🐛 Added optimization_phase parameter to kernel

**Console Display:**
- Window title now shows "Titan Pro 2.0.0"
- Banner displays version number
- VERSION constant in both launcher and titan_hybrid

**Files Changed:**
- `titan_hybrid.py`: Kernel, GPU engine, fitness function
- `launcher.py`: Working capital prompt, balance fetching
- `deriv_client.py`: Balance storage, reconnection logic
- `README.md`: Complete strategy documentation
- `WIKI.md`: Algorithm deep dive

---

## v1.0.0 (2025-11-30) - Initial Release
### 🚀 First Public Release

**Core Features:**
- Multi-strategy portfolio (Scalper + Breakout + Pullback)
- Dual GPU optimization (Intel + NVIDIA)
- Walk-Forward validation
- 100,000 parameter combinations
- Real-time Deriv API integration
- Dashboard HTML interface

**Strategies:**
1. Scalper: RSI mean reversion
2. Breakout: Bollinger squeeze + momentum
3. Pullback: EMA trend following

**Data Sources:**
- Dukascopy (real markets)
- Deriv (synthetic indices)

---

## Upcoming (v2.1.0)
**Planned Features:**
- [ ] Daily profit/loss stops implementation
- [ ] Kelly Criterion position sizing
- [ ] WebSocket backend for dashboard
- [ ] Trade execution via Deriv API
- [ ] Email/webhook notifications
- [ ] Performance analytics export

---

**Version Format**: MAJOR.MINOR.PATCH
- **MAJOR**: Breaking changes or major features
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes only
