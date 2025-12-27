# ══════════════════════════════════════════════════════════════════
# TITAN FUSION QUANTUM - Configuration Example
# ══════════════════════════════════════════════════════════════════
# 
# INSTRUCTIONS:
# 1. Copy this file to: config.py
# 2. Replace all placeholder values with your real credentials
# 3. NEVER commit config.py to Git (it's in .gitignore)
#
# ══════════════════════════════════════════════════════════════════

# ═══ GEMINI AI API ═══
# Get your free API key at: https://ai.google.dev/
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"

# ═══ DATA FOLDER ═══
# Where cTrader bot exports data (must match cBot configuration)
DATA_FOLDER = r"C:\Users\YOUR_USERNAME\Documents\TitanFusionAI"

# ═══ DERIV API (Optional - if using Deriv integration) ═══
DERIV_APP_ID = "YOUR_DERIV_APP_ID"  # Get at: https://api.deriv.com
DERIV_API_TOKEN = "YOUR_DERIV_TOKEN"

# ═══ TRADING PARAMETERS ═══
# Timeout in minutes before restarting analysis loop
TIMEOUT_MINUTES = 120

# Minimum confidence level to execute trades (0-100)
MIN_CONFIDENCE = 70

# ═══ MACRO DATA (Optional) ═══
# Set to False to use simulated data (faster but less accurate)
USE_REAL_MACRO_DATA = True
