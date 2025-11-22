<img width="300" height="300" alt="titan fusion" src="https://github.com/user-attachments/assets/c7b6b294-2c03-4d9b-ae20-c6ccc7b3252c" />

# TitanFusion cBot (Open Source)

[![Platform](https://img.shields.io/badge/Platform-cTrader-green?style=for-the-badge)](https://ctrader.com)
[![Version](https://img.shields.io/badge/Version-v3.3_Development-orange?style=for-the-badge)](https://github.com/LucassVal/TitanFusion-cBot/releases)
[![Asset](https://img.shields.io/badge/Asset-XAUUSD_(Gold)-gold?style=for-the-badge)](https://www.tradingview.com/symbols/XAUUSD/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey?style=for-the-badge)](https://github.com/LucassVal/TitanFusion-cBot/blob/main/LICENSE)
[![Status](https://img.shields.io/badge/Status-Testing_Phase-yellow?style=for-the-badge)](https://github.com/LucassVal/TitanFusion-cBot)

<!-- ADD YOUR CTRADER BOT STORE LINK HERE WHEN AVAILABLE -->
<!-- [![cTrader Store](https://img.shields.io/badge/cTrader-Bot_Store-blue?style=for-the-badge)](YOUR_STORE_LINK_HERE) -->

<br>

**The "System Architect" Edition.**  

A modular, open-source algorithmic trading system optimized for **XAUUSD (Gold)** on the **H1 Timeframe**.

<br>

> *TitanFusion is not just a bot; it is a portfolio of strategies working in harmony with a central Risk Controller.*

<br>

---

<br>

## 💙 A Message from the Developer

<br>

Hello! My name is **Lucas Valério**, and I'm an **enthusiast**, not a professional programmer.

<br>

I created this project out of **passion for algorithmic trading** and a desire to learn and share knowledge with the community.

<br>

**I'm being completely honest with you:**

<br>

- 🎓 I'm **learning** as I build this
- 🧪 This bot is in **early testing phase**
- 📊 I have **no verified performance data** yet
- 💰 This project aims to grow **$50 accounts** (micro account challenge)
- 🤝 I **need your help** to improve and validate it

<br>

**I'm sharing this openly because:**

<br>

- ✅ I believe in **transparency**
- ✅ I want to **learn from experienced traders**
- ✅ I hope to **contribute to the community**
- ✅ I'm asking for your **patience and guidance**

<br>

If you're an experienced developer, trader, or tester, **your feedback would mean the world to me**. 

<br>

I'm here to learn, improve, and grow together with this amazing community.

<br>

**Thank you for taking the time to look at my work.** 🙏

<br>

*- Lucas Valério*

<br>

---

<br>

## ⚠️ PROJECT STATUS: ACTIVE DEVELOPMENT

<br>


🚧 This project is in EARLY TESTING PHASE

📊 NO verified backtest results available

🧪 DEMO ACCOUNTS ONLY - Do NOT use with real money

💡 Community feedback desperately needed

🙏 Looking for experienced testers to help validate


<br>

---

<br>

## 📖 Table of Contents

<br>

1. [Philosophy](#philosophy)
2. [Core Strategies](#core-strategies)
3. [Operation Modes](#operation-modes)
4. [Key Features](#key-features)
5. [Installation](#installation)
6. [Configuration](#configuration)
7. [Technical Architecture](#technical-architecture)
8. [Testing Status](#testing-status)
9. [Risk Management](#risk-management)
10. [Technical Documentation](#technical-documentation)
11. [How You Can Help](#how-you-can-help)
12. [Contributing](#contributing)
13. [License & Disclaimers](#license--disclaimers)

<br>

---

<br>

## Philosophy

<br>

TitanFusion adopts a **"Fusion System"** approach, fundamentally different from single-strategy bots.

<br>

### What makes it unique?

<br>

Instead of one strategy trying to capture all market movements, TitanFusion operates as an **independent portfolio of specialized mini-strategies**, each designed for specific market conditions:

<br>

- **⚡ Scalper Strategy:** Mean reversion in consolidation zones

- **💥 Breakout Strategy:** Explosive volatility exploitation

- **🌊 Pullback Strategy:** Trend following with intelligent entries

<br>

### The Secret: Central Risk Controller

<br>

A unified risk management system dampens total exposure when multiple strategies align:

<br>


Total Risk = Strategy Risk × (1 - Risk Dampening)


<br>

This prevents overexposure during rare moments when all strategies signal simultaneously.

<br>

**Note:** This is the theoretical design. Real-world validation is ongoing.

<br>

---

<br>

## Core Strategies

<br>

### ⚡ 1. Scalper Strategy

<br>

**Type:** Mean Reversion  

**Primary Indicator:** RSI (14)  

**Best Market Condition:** Consolidation / Range-bound

<br>


Entry Logic:
  • BUY: RSI crosses above 30 (oversold recovery)
  • SELL: RSI crosses below 70 (overbought correction)


<br>


Validation Filters:
  • ATR-based volatility check
  • Maximum spread filter
  • Time-based session filter (London/NY)


<br>


Exit Strategy:
  • Take Profit: 3.0 × ATR (default, untested)
  • Stop Loss: 2.0 × ATR (default, untested)
  • Partial profit taking at 50% position
  • Parabolic SAR trailing stop (optional)


<br>

**Status:** ⚠️ Logic implemented, awaiting real-world testing

<br>

---

<br>

### 💥 2. Breakout Strategy

<br>

**Type:** Volatility Exploitation  

**Primary Indicator:** Bollinger Bands (20, 2.0)  

**Best Market Condition:** High momentum / News events

<br>


Entry Logic:
  • BUY: Close above Upper Bollinger Band
  • SELL: Close below Lower Bollinger Band


<br>


Validation Filters:
  • Band width < maximum threshold (prevents overexpansion)
  • Strong candle body (> 60% of total range)
  • ATR and spread validation


<br>


Exit Strategy:
  • Take Profit: 5.0 × ATR (default, untested)
  • Stop Loss: 1.5 × ATR (default, untested)
  • Trailing stop activation after breakout confirmation


<br>

**Status:** ⚠️ Logic implemented, awaiting real-world testing

<br>

---

<br>

### 🌊 3. Pullback Strategy

<br>

**Type:** Trend Following  

**Primary Indicators:** EMA (34/144) + RSI (14)  

**Best Market Condition:** Established trends with retracements

<br>


Entry Logic:
  • BUY: EMA 34 > EMA 144 (uptrend) + RSI < 40 (pullback)
  • SELL: EMA 34 < EMA 144 (downtrend) + RSI > 60 (rally)


<br>


Validation Filters:
  • Trend strength confirmation (EMA separation)
  • Volume/momentum validation
  • H1 timeframe trend filter (optional)


<br>


Exit Strategy:
  • Take Profit: 4.0 × ATR (default, untested)
  • Stop Loss: 1.5 × ATR (default, untested)
  • Trend reversal exit (EMA crossover)


<br>

**Status:** ⚠️ Logic implemented, awaiting real-world testing

<br>

---

<br>

## Operation Modes

<br>

TitanFusion offers **7 testing configurations** to isolate and combine strategies:

<br>

| Mode | Icon | Active Strategies | Risk Dampening | Primary Use Case |
|------|------|-------------------|----------------|------------------|
| **All** | 🎯 | ⚡💥🌊 (All Three) | 40% | Full system testing |
| **ScalperOnly** | ⚡ | Scalper | 0% | Isolate mean reversion testing |
| **BreakoutOnly** | 💥 | Breakout | 0% | Volatility strategy testing |
| **PullbackOnly** | 🌊 | Pullback | 0% | Trend following testing |
| **ScalperBreakout** | ⚡💥 | Scalper + Breakout | 20% | High-frequency combo |
| **ScalperPullback** | ⚡🌊 | Scalper + Pullback | 20% | Balanced approach |
| **BreakoutPullback** | 💥🌊 | Breakout + Pullback | 20% | Momentum + Trend combo |

<br>

### Why Multiple Modes?

<br>

Each mode allows **isolated strategy testing** and **performance comparison**:

<br>

- **Isolation:** Test individual strategies without interference

- **Combination:** Validate strategy synergies and conflicts

- **Risk Analysis:** Compare risk-adjusted returns

- **Optimization:** Fine-tune parameters independently

<br>

**Status:** ⚠️ Modes implemented, none tested in real conditions yet

<br>

---

<br>

## Key Features

<br>

### 🛡️ Risk Management (Implemented in Code)

<br>

- **ATR-Based Dynamic Stops:** Adapts to market volatility

- **Chaos Guard:** Emergency shutdown when ATR > 500 pips

- **Partial Profit Taking:** Locks in 50% gains at intermediate targets

- **Daily Drawdown Limits:** Auto-halt at loss threshold (default: 15%)

- **Daily Target System:** Stops after profit goal (default: 8%)

- **Smart Position Sizing:** Risk-adjusted volume calculation

<br>

### 🔧 Market Filters (Implemented in Code)

<br>

- **Time-Based Filter:** London/NY session focus (07:00-20:00 UTC)

- **Spread Filter:** Rejects entries if spread > 10 pips

- **ATR Range Filter:** Min 2.0 pips / Max 500.0 pips

- **Flat Market Protection:** Prevents entries in ranging conditions

- **H1 Trend Filter:** Optional higher timeframe bias

- **Opposite Position Prevention:** Avoids conflicting trades

<br>

### 📊 Monitoring & Logging

<br>

- **Visual Dashboard:** On-chart metrics with emoji indicators

- **Detailed Logging:** Every decision explained

- **Position Tracking:** Live P&L and drawdown monitoring

- **Performance Stats:** Win rate, profit factor calculation

<br>

### 🔒 Stability Features (v3.3)

<br>

- **EntityNotFound Protection:** Position validation before operations

- **Real-Time Validation:** Live entity checking

- **Graceful Error Recovery:** Automatic fallbacks

- **Resource Optimization:** OnBar() execution (efficient CPU)

- **Safe Mode:** `AccessRights = None` (no file/network access)

<br>

**Status:** ✅ All features coded, ⚠️ real-world effectiveness unproven

<br>

---

<br>

## Installation

<br>

### 📋 Prerequisites

<br>

- **Platform:** cTrader Desktop **5.5.13+** ([Download Here](https://ctrader.com/download))

- **Symbol:** XAUUSD (Gold) - Must be available with your broker

- **Timeframe:** H1 (1 Hour) - Mandatory

- **Account Type:** **DEMO ACCOUNT ONLY** (testing phase)

- **Starting Balance:** **$50+ USD** (this project's target)

<br>

---

<br>

### 📥 Step-by-Step Installation

<br>

#### Method 1: Clone Repository

<br>

```bash
# Clone the repository
git clone https://github.com/LucassVal/TitanFusion-cBot.git

# Navigate to project folder
cd TitanFusion-cBot

Method 2: Download Release

Visit Releases Page


Download latest TitanFusion.cs file


Save to your computer

🔧 Import to cTrader

Step 1: Open Automate Panel

Launch cTrader Desktop 5.5.13+


Click "Automate" tab (top menu)


Click "New" → Select "cBot"

Step 2: Paste Code

Open TitanFusion.cs file in text editor


Copy ALL code (from first line to last)


Paste into cTrader code editor


Click "Build" button (or press F6)

Step 3: Verify Compilation

Expected Output:
✅ Build successful
✅ No compilation errors
✅ "TitanFusion" appears in cBot list

If errors appear:

Verify you copied the complete code
Check cTrader version is 5.5.13 or higher
Look for missing brackets or syntax issues


⚙️ Attach to Chart

Step 1: Open Chart

Open XAUUSD chart in cTrader


Set timeframe to H1 (1 Hour)


Verify chart has historical data (minimum 200 bars)

Step 2: Attach Bot

Locate "TitanFusion" in Automate panel


Drag cBot onto XAUUSD H1 chart


Parameters window opens automatically

Step 3: Configure

See Configuration Section below

Step 4: Start

Click "Start" button


Watch console log for initialization messages


Verify dashboard appears on chart (if enabled)


Configuration

🎯 Starting Point Configuration

⚠️ IMPORTANT: These are code defaults, NOT optimized values.

I recommend starting with these conservative settings for your first test:

📊 Basic Setup

Operation Mode: ScalperOnly
// Start with just one strategy to understand behavior

Show Text Info: true
// Enable on-chart dashboard

Risk % Per Trade: 1.5%
// Default in code (for $50 account = $0.75 risk/trade)

Daily Target %: 8.0%
// Stop trading after reaching this profit

Max Daily Drawdown %: 15.0%
// Emergency stop if losses exceed this


⚡ Scalper Strategy (Code Defaults)

Base Volume: 0.01
// Minimum lot size (check your broker allows this)

RSI Period: 14
// Standard RSI setting

Oversold Level: 30
// Buy signal trigger

Overbought Level: 70
// Sell signal trigger

TP ATR Multiplier: 3.0
// ⚠️ UNTESTED - may need adjustment

SL ATR Multiplier: 2.0
// ⚠️ UNTESTED - may need adjustment


💥 Breakout Strategy (Code Defaults)

Base Volume: 0.01

BB Period: 20

BB Deviation: 2.0

Max Band Width: 500.0 pips
// ⚠️ UNTESTED

Min Body Ratio: 0.5
// ⚠️ UNTESTED

TP ATR Multiplier: 5.0
// ⚠️ UNTESTED

SL ATR Multiplier: 1.5
// ⚠️ UNTESTED


🌊 Pullback Strategy (Code Defaults)

Base Volume: 0.01

Trend EMA Fast: 34

Trend EMA Slow: 144

Pullback RSI Trigger: 40
// ⚠️ UNTESTED

TP ATR Multiplier: 4.0
// ⚠️ UNTESTED

SL ATR Multiplier: 1.5
// ⚠️ UNTESTED


🛡️ Risk Filters

Min ATR Pips: 2.0
// ⚠️ UNTESTED - prevents trading in dead markets

Max ATR Pips: 500.0
// ✅ TESTED - bot stops trading above this volatility

Max Spread Pips: 10.0
// ⚠️ UNTESTED - rejects entries if spread too wide

Enable H1 Trend Filter: false
// Start with this disabled (optional filter)


🔧 Advanced Settings

Use Auto-Compound: true
// Volume scales with balance

Enable Profit Shield: true
// Locks in gains

Enable Trailing SAR: true
// Dynamic trailing stops

Enable Partial TP: true
// Take 50% profit at intermediate levels

Partial Trigger (ATR): 1.0
// When to activate partial TP


⚠️ CRITICAL REMINDERS

1. These parameters are CODE DEFAULTS
   
2. ONLY Max ATR 500 has been tested (basic functionality)

3. ALL other ranges are UNTESTED

4. Operation modes are UNTESTED

5. Start with ScalperOnly mode first

6. Document what happens in your tests

7. Share results in Discussions to help improve the bot


Technical Architecture

Code Structure

TitanFusion : Robot
├── Parameters (40+ configurable settings)
├── Indicators
│   ├── RSI (Scalper & Pullback)
│   ├── Bollinger Bands (Breakout)
│   ├── EMA (Trend detection)
│   ├── ATR (Volatility measurement)
│   └── Parabolic SAR (Trailing stops)
├── Execution Engine
│   ├── OnStart() - Initialization
│   ├── OnBar() - Strategy execution (H1 intervals)
│   ├── OnTick() - Position management (real-time)
│   └── OnStop() - Cleanup & reporting
└── Strategy Modules
    ├── ProcessScalperEntry()
    ├── ProcessBreakoutEntry()
    ├── ProcessPullbackEntry()
    └── ManagePositions()


Execution Flow

1. OnStart()
   ├── Initialize all indicators
   ├── Load H1 trend filter (if enabled)
   ├── Record initial balance
   └── Subscribe to position events

2. OnBar() [Every H1 Candle Close]
   ├── Check early stopping criteria
   ├── Validate daily P/L limits
   ├── Apply trading filters
   │   ├── Time filter (07:00-20:00 UTC)
   │   ├── ATR range (2-500 pips)
   │   ├── Spread filter (< 10 pips)
   │   └── H1 trend filter (optional)
   ├── Execute selected strategy mode
   │   ├── ScalperOnly
   │   ├── BreakoutOnly
   │   ├── PullbackOnly
   │   └── Combinations
   └── Update dashboard display

3. OnTick() [Every Price Update]
   ├── Scan all open positions
   ├── Apply partial profit taking
   ├── Update trailing stops (Parabolic SAR)
   └── Validate stop loss levels

4. OnStop()
   ├── Close remaining positions
   ├── Calculate final statistics
   └── Generate performance report


Risk Dampening System

// Strategy-specific multipliers
Scalper: 0.8× (more conservative)
Breakout: 1.0× (baseline)
Pullback: 1.2× (more aggressive)

// Mode-specific dampening
All Strategies Active: 0.6× (40% dampening)
Two Strategies Active: 0.8× (20% dampening)
Single Strategy: 1.0× (no dampening)

// Final volume calculation
Volume = BaseRisk × StrategyMultiplier × ModeDampener
         × AccountBalance / (StopLoss × PipValue)


Testing Status

What Has Been Tested

✅ Code compiles without errors in cTrader 5.5.13

✅ Bot initializes and attaches to chart successfully

✅ Max ATR 500 threshold works (prevents trading in extreme volatility)

✅ Basic code structure and logic flow validated


What Has NOT Been Tested

❌ Strategy entry/exit logic in real market conditions

❌ Parameter ranges (ATR min/max, spreads, multipliers)

❌ All 7 operation modes

❌ Partial profit taking execution

❌ Trailing stop functionality

❌ H1 trend filter effectiveness

❌ Time filter optimization

❌ Daily drawdown/target limits

❌ Risk dampening system performance

❌ $50 account viability


Current Testing Phase

📅 Started: November 20, 2025

🎯 Goal: Validate basic functionality and parameter ranges

👤 Tester: Solo developer (looking for help!)

📊 Results: None yet - just beginning testing

🙏 Status: Seeking community testers


Risk Management

⚠️ CRITICAL: UNTESTED FEATURES

🚧 This bot includes safety features in the CODE

❌ Parameter ranges NOT validated in real conditions

❌ Operation modes NOT tested with live data

✅ Only Max ATR 500 threshold confirmed working

⚠️ ALL recommendations below are EXPERIMENTAL

⚠️ Use at your own risk in DEMO accounts only


🔒 Built-In Safety Features

These features exist in the code but performance is unproven:

Position-Level Protection

✅ ATR-based dynamic stop loss (implemented, not optimized)
✅ Take profit targets scaled by ATR (default multipliers: 2-5x)
✅ Partial profit taking at 50% position (untested execution)
✅ Trailing stops with Parabolic SAR (optional, untested)
✅ Maximum 1 position per strategy (code enforced)
✅ Maximum 3 total positions (code enforced)


Account-Level Protection

✅ Daily drawdown limit (default: 15% - adjustable, untested)
✅ Daily profit target (default: 8% - adjustable, untested)
✅ Risk % per trade calculation (default: 1.5% - untested)
✅ Auto-compound mode (volume scales with balance)
✅ Early stopping if trade frequency too low (optional)


Market-Level Protection

✅ Chaos Guard (stops if ATR > 500 pips - only tested threshold)
⚠️ Spread filter (default: >10 pips - NOT validated)
⚠️ Flat market detection (EMA separation - NOT tested)
⚠️ Time filter (07:00-20:00 UTC - NOT validated for XAUUSD)
⚠️ H1 trend alignment (optional - NOT tested)


🎯 Project Goal: $50 Micro Account Challenge

This bot was designed with a specific goal in mind:

💰 Starting Capital: $50 USD

🎯 Challenge: Grow micro account systematically

📊 Target: Consistent small gains with strict risk control

⚠️ Reality: Very difficult - most $50 accounts fail


💡 Why $50?

Accessibility: Almost anyone can risk $50 to learn


Learning: Test strategies without major financial risk


Reality Check: Forces extreme discipline and risk management


Proof of Concept: If it works with $50, it validates the logic

⚠️ Honest Truth: Growing $50 accounts is extremely challenging due to:

Broker spread eating large % of profits
Limited margin for multiple positions
Psychological pressure to "grow fast"
No room for error or large drawdowns


📊 $50 Account Mathematics

Starting Balance: $50.00

Risk Per Trade (1.5%): $0.75

Minimum Trade Size: 0.01 lots (broker dependent)

Daily Target (8%): $4.00 profit

Daily Stop Loss (15%): $7.50 max loss

Margin Required (3 positions): Check your broker!

Before starting:

✅ Verify your broker allows 0.01 lot minimum on XAUUSD


✅ Check margin requirements (you need room for 3 positions)


✅ Understand average spread (can be 20-50% of profit targets)


✅ Have realistic expectations (this is a learning exercise)


⚠️ What I Need Community Help Testing

Since I haven't tested most parameters, I need your help to discover:

1. ATR Range Testing

Questions:
- Is 2.0 min ATR realistic for XAUUSD H1?
- Does 500 max ATR catch all chaos events?
- What ATR range produces best trade frequency?
- Should ranges be different per strategy?

2. Operation Mode Testing

Questions:
- Which mode trades most frequently?
- Which has best risk/reward profile?
- Do combined modes cause conflicts?
- Is risk dampening system effective?

3. TP/SL Multiplier Testing

Questions:
- Are 2-5x ATR multipliers realistic for XAUUSD?
- Do trades hit TP or SL more often?
- Should multipliers vary by strategy?
- What's the optimal risk/reward ratio?

4. Time Filter Optimization

Questions:
- Does 07:00-20:00 UTC capture best moves?
- Should we include Asian session?
- Which specific hours have best win rate?
- Does time filter improve or hurt performance?

5. Spread Impact Analysis

Questions:
- What's average XAUUSD spread at your broker?
- How much does spread eat into profits?
- Should spread filter be more/less strict?
- Does spread vary significantly by session?

6. $50 Account Viability

Questions:
- Can $50 accounts survive broker spreads?
- What's realistic expectation for monthly growth?
- How often do accounts blow up?
- What parameters work best for micro accounts?


🚨 Safety Rules for Testing

1. ❌ NEVER use real money - DEMO ONLY

2. ✅ Start with ScalperOnly mode (simplest)

3. ✅ Use minimum risk (0.5-1% per trade)

4. ✅ Document EVERY parameter change you make

5. ✅ Test for MINIMUM 1 week before changing anything

6. ✅ Share results in GitHub Discussions

7. ❌ Don't expect profits - expect LEARNING

8. ✅ Be patient - strategy validation takes months


📊 Realistic Expectations

Best Case Scenario (hypothetical, unproven):

- 60% win rate
- 1:2 Risk/Reward ratio
- 10-15 trades per month
- +10-20% monthly growth
- Controlled drawdowns < 10%

Likely Scenario (realistic for new strategy):

- 40-50% win rate initially
- 1:1.5 Risk/Reward ratio
- 5-8 trades per month
- Break even to +5% monthly
- Frequent 5-15% drawdowns
- Months of optimization needed

Worst Case (possible, must be prepared for):

- Account blown due to:
  * Untested parameters being wrong
  * Poor market conditions
  * High broker spreads
  * Technical bugs or errors
  * Unexpected market events


Technical Documentation

Official cTrader Resources

cBot Creation Guide - Official tutorial


API Reference - Complete API docs


Code Samples - Official examples


Community Forum - Support forum


Video Tutorials - Visual guides


Repository Documentation

CONTRIBUTING.md - How to contribute


CODE_OF_CONDUCT.md - Community standards


SECURITY.md - Security policies


Issue Templates - Bug reports


Technical Specifications

Language: C# (.NET Framework 4.x)

Platform: cTrader Automate API

Minimum Version: cTrader 5.5.13

Execution Model: OnBar() + OnTick()

Access Rights: None (Safe Mode)

Timezone: UTC

Primary Symbol: XAUUSD (Gold)

Primary Timeframe: H1 (1 Hour)

Code Lines: ~800 lines


Indicator Dependencies (All Built-in)

✅ RelativeStrengthIndex (RSI)
✅ BollingerBands
✅ MovingAverage (EMA)
✅ AverageTrueRange (ATR)
✅ ParabolicSAR

No external indicators or libraries required.


How You Can Help

This section is the most important to me. I really need your help.

👥 I'm Looking For:

🧪 Testers

If you can:

Run the bot in demo account for 1+ weeks
Document what happens (screenshots, logs)
Share results honestly (good or bad)
Try different parameter combinations

Please help! Open a Discussion with your findings.


💻 Developers

If you're experienced with C# or cTrader:

Review my code for bugs or improvements
Suggest better implementation approaches
Help optimize performance
Teach me better coding practices

I'm eager to learn! Feel free to open Issues or Pull Requests.


📊 Traders

If you have trading experience:

Review strategy logic for flaws
Suggest realistic parameter ranges
Share what works/doesn't work for XAUUSD
Help identify unrealistic expectations

Your wisdom is invaluable! Join the Discussions.


📝 Writers

If you're good with documentation:

Fix typos or unclear explanations
Add examples or tutorials
Translate to other languages
Improve README structure

Every improvement helps! Submit Pull Requests.


📊 How to Share Test Results

If you test TitanFusion, please share:

Basic Information:

- Starting balance
- Broker name (for spread reference)
- cTrader version
- Test duration

Configuration Used:

- Operation mode
- Risk % per trade
- Key parameter values
- Which filters enabled/disabled

Results:

- Number of trades opened
- Win rate
- Total profit/loss
- Maximum drawdown
- Any errors encountered

Observations:

- What worked well?
- What didn't work?
- What would you change?
- Any unexpected behavior?

Where to Share:

GitHub Discussions - Best for detailed results


GitHub Issues - For bugs or problems


Email: &#x6c;&#117;&#x63;&#x61;&#x73;&#x76;&#97;&#x6c;&#x65;&#x72;&#x69;&#x6f;&#112;&#x40;&#x67;&#109;&#97;&#x69;&#x6c;&#x2e;&#x63;&#x6f;&#109; - For private feedback


Contributing

All contributions are welcome with open arms! 

This is a community learning project - we're all here to improve together.

Ways to Contribute

🐛 Report Bugs

Found something broken?

Check existing issues


Create a new issue with:

What you expected to happen
What actually happened
Steps to reproduce
Your cTrader version
Parameter settings used
Log output (if available)


💡 Suggest Features

Have an idea to improve the bot?

Open a Discussion


Describe:

The feature idea
Why it would be useful
How it might work
(Optional) Implementation suggestions


🔧 Submit Code

Want to contribute code improvements?

Process:

Fork this repository


Create a feature branch:

git checkout -b feature/YourFeatureName


Make your changes


Test thoroughly in demo account


Commit with clear message:

git commit -m 'Add: Clear description of what you changed'


Push to your fork:

git push origin feature/YourFeatureName


Open a Pull Request with:

Description of changes
Why the change is needed
Testing you performed

Don't worry if you're not perfect! I'm learning too - we'll figure it out together.


📖 Improve Documentation

Help make docs better:

Fix typos or grammar
Add clearer explanations
Create examples or tutorials
Translate to other languages
Add screenshots or videos

Even small improvements matter!


📜 Code of Conduct

This project follows a simple principle:

🤝 Be kind, patient, and respectful

💡 We're all here to learn

🙏 Criticism should be constructive

❤️ Celebrate each other's contributions

Full details: CODE_OF_CONDUCT.md


Community Channels

💬 Discussions: General chat & ideas


🐛 Issues: Bug reports


📧 Email: &#108;&#x75;&#x63;&#x61;&#115;&#x76;&#x61;&#x6c;&#101;&#x72;&#x69;&#111;&#112;&#64;&#103;&#109;&#x61;&#105;&#x6c;&#46;&#x63;&#x6f;&#109;


License & Disclaimers

📄 MIT License

This project is open source under the MIT License.

See LICENSE file for details.

You are free to:

✅ Use commercially
✅ Modify the code
✅ Distribute copies
✅ Sublicense your changes
✅ Private use

Conditions:

📝 Include original license and copyright notice
📝 State changes you made


⚠️ CRITICAL RISK WARNING

🚨 TRADING INVOLVES SUBSTANTIAL RISK OF LOSS

This software is provided for EDUCATIONAL PURPOSES ONLY.

⚠️ PLEASE UNDERSTAND:

This bot is in EARLY TESTING PHASE


I'm an enthusiast, not a professional


NO verified performance data exists


NO parameters have been optimized


You can LOSE MORE than your investment


Market conditions change constantly


Technical bugs may exist


Broker issues can cause losses

⚠️ MANDATORY REQUIREMENTS:

❌ NEVER use real money during testing phase


✅ ONLY use DEMO accounts


✅ START with conservative settings


✅ MONITOR daily during testing


✅ UNDERSTAND the code before running


✅ KEEP updated to latest version


✅ ACCEPT you may lose everything


🔒 Legal Disclaimer

No Financial Advice

I am NOT:

❌ A financial advisor
❌ A professional trader
❌ A certified programmer
❌ Recommending you trade

I am:

✅ An enthusiast sharing a learning project
✅ Testing ideas in demo accounts
✅ Being honest about limitations
✅ Seeking community help and guidance


No Guarantees

⚠️ I make NO claims about:
- Profitability
- Win rates
- Risk levels
- Parameter effectiveness
- Strategy viability
- Account growth

⚠️ Real trading involves:
- Slippage (price differences)
- Spread costs (broker fees)
- Execution delays
- Server downtime
- Unexpected market events
- Technical failures


Your Responsibility

BY USING THIS SOFTWARE, YOU ACKNOWLEDGE:

✅ You understand the risks
✅ You accept full responsibility for your decisions
✅ You will not hold me liable for any losses
✅ You will test thoroughly before any real money use
✅ You understand this is experimental software


Platform Compliance

✅ Compliant with cTrader Automate policies
✅ Uses AccessRights = None (maximum safety)
✅ No external file or network access
✅ Open source and auditable
✅ No hidden functionality


✅ Before You Start Checklist

Please confirm you:

✅ Read and understood all warnings above

✅ Will ONLY use demo accounts for testing

✅ Understand this is an unproven, experimental bot

✅ Know the developer is an enthusiast, not pro

✅ Accept that parameters are untested

✅ Are prepared to potentially lose your demo balance

✅ Have realistic expectations (learning, not profits)

✅ Will monitor performance daily

✅ Know how to stop the bot in emergency

✅ Will share results to help improve the project


🎊 Acknowledgments

💙 Thank You

To the cTrader Community:

Thank you for providing such an excellent platform and learning resources. Your documentation and examples made this project possible.

To Future Contributors:

If you're reading this and considering helping - thank you. 

Your knowledge, testing, and feedback will make this project better than I could ever make it alone.

To Open Source:

This project stands on the shoulders of giants. Thank you to everyone who shares knowledge freely.


🛠️ Built With

cTrader Automate - Trading platform


C# .NET - Programming language


GitHub - Version control & collaboration


Love for learning ❤️


📞 Contact & Support

Get in Touch

I'm always happy to hear from you!

🐛 Bug Reports: Open an Issue


💡 Ideas & Discussion: Start a Discussion


📧 Email: &#x6c;&#117;&#99;&#97;&#115;&#x76;&#97;&#108;&#x65;&#x72;&#105;&#111;&#x70;&#64;&#x67;&#109;&#x61;&#105;&#108;&#x2e;&#x63;&#x6f;&#109;


⭐ Show Support: Star this repository if you find it interesting

Response Time:

I'm not a company - just one person learning and building. 

I'll respond as quickly as I can, but please be patient. 🙏


Stay Updated

⭐ Star this repo - Get notified of updates


👀 Watch releases - New versions announced


🔔 Follow me - See project progress


📊 Project Information

📅 Project Created: November 20, 2025

📅 Last Updated: November 20, 2025

👤 Developer: Lucas Valério (Enthusiast)

🎯 Status: Early Testing Phase

💰 Goal: $50 Account Challenge

⭐ Stars: [Live count on badge]

🔀 Forks: [Live count on badge]

🐛 Issues: Check Issues tab

💬 Discussions: Check Discussions tab


⭐ If this project interests you, please star the repository!

🙏 If you can help with testing or development, please reach out!

💬 If you have questions or suggestions, start a discussion!


Version: v3.3 Development Build  

Status: Active Testing - Demo Only

Developer: Learning Enthusiast


Made with ❤️, humility, and a desire to learn

Let's learn and grow together 🚀📈


💭 Final Thoughts

Thank you for taking the time to read about TitanFusion.

This project represents countless hours of learning, trial and error, and passion for algorithmic trading.

I'm sharing it openly and honestly because I believe:

🤝 Collaboration beats competition
📚 Shared knowledge helps everyone grow
💡 Honest feedback leads to improvement
❤️ Community support makes the impossible possible

I don't have all the answers. I'm learning as I build.

But I'm committed to transparency, open to feedback, and excited to improve.

If you see potential in this project, please join me on this journey.

Together, we can validate these strategies, optimize the parameters, and create something truly useful for the trading community.

Thank you for believing in open source and collaborative learning. 🙏

- Lucas Valério


Happy (Demo) Trading! 🎯


✅ PRONTO! AGORA COM:

✅ Links do Table of Contents funcionando (removido emojis dos IDs)

✅ Espaço para cTrader Bot Store (comentado, pronto para você adicionar)

✅ Toda estrutura honesta e humilde

✅ Espaçamento correto

✅ Tom acolhedor

📝 Copie e cole direto no seu README.md do GitHub!

🔗 Quando tiver o link da Bot Store, só descomentar a seção e adicionar!
