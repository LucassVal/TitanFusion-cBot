# 🤝 Contribution Guidelines - TitanFusion Community

## 🌟 Welcome Contributors!

Thank you for your interest in contributing to the TitanFusion project! We are a community of traders and enthusiasts dedicated to making algorithmic trading accessible and transparent.

This is an **enthusiast-driven open-source project.** We prioritize clarity, safety, and functional trading ideas over formal coding standards.

---

## 🎯 Types of Contributions

We welcome any contribution that makes the bot safer, cleaner, or more profitable.

- **New Trading Strategies** (Scalpers, Breakouts, etc.)
- **Risk Management Improvements** (e.g., better Trailing Stop logic)
- **Bug Fixes** and **Performance Optimizations**
- **Documentation and Educational Content** (e.g., Wiki articles)
- **Sharing Proven Optimization Presets (.cbotset files)**

### Priority Focus Areas:
1. XAUUSD (Gold) Optimizations and Filters.
2. Multi-Timeframe Analysis and Confirmation.
3. Improving the current three core strategies.

---

## 🚀 Getting Started

### Prerequisites
- Familiarity with the **cTrader** platform.
- The ability to **read and understand C# code** (you don't need to be an expert!).

### How to Submit an Idea or Code:
1.  **Fork the repository.**
2.  **Create a feature branch** for your specific change (e.g., `feature/new-atr-filter`).
3.  Implement your changes in the `.cs` file.

### First Interaction:
- **Found a Strategy Idea?** Go to the **Discussions** tab and share your logic first.
- **Found a Bug?** Open an **Issue** with a description and any relevant log output.

---

## 🔄 Development Workflow & Standards

### Branch Naming Convention:
Use clear prefixes to indicate the type of change (e.g., `feat/` for new features, `fix/` for bug corrections).

### Code Focus: Clarity over Complexity
We prioritize code that is **easy for another enthusiast to read** and verify.
- **Clarity:** Use meaningful variable names (`longTermEMA` instead of `LMA`).
- **Safety:** Add `try-catch` blocks around critical execution points (`ExecuteMarketOrder`).
- **Comments:** Explain the *trading logic* behind the code (e.g., `// This calculates the Squeeze threshold to avoid noise`).

### Risk Requirements (Mandatory for PRs):
When submitting code, you **must** confirm the following in your Pull Request description:
- **Maximum Drawdown:** Disclose the maximum drawdown seen in your backtests (e.g., "Max DD: 15%").
- **Win Rate/Profit Factor:** Provide basic performance metrics (e.g., "Win Rate: 55%, PF: 1.4").
- **Testing Period:** Specify the start and end dates you used for validation.

---

## 📈 Strategy Submission Template

Please use this template in your Pull Request description or when posting a new idea:

```markdown
## 🏆 Strategy Proposal: [Your Strategy Name]

- **Strategy Type:** [Scalper / Trend / Counter-Trend]
- **Entry Conditions:** [Simple explanation of the signal]
- **Exit Conditions:** [SL/TP Multipliers used]
- **Backtest Period:** [Date] to [Date]
- **Timeframe/Symbol:** [e.g., H1 / XAUUSD]
