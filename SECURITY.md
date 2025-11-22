🛡️ Security Policy - TitanFusion cBot
Welcome to the TitanFusion Security Policy. This is an open-source project with absolutely no restrictions on modification or use under the MIT License.

A security flaw in our project is defined as a Risk Logic Vulnerability—a bug that could lead to unintended capital loss or failure of position limits.

Supported Versions (Latest Code)
We focus all development and support on the version of the TitanFusion cBot found directly in the repository's main branch.

The most current and supported version will always be the one available directly in the repository's main branch.

Reporting a Risk Vulnerability
We rely on our community of enthusiasts to identify and report issues that compromise the capital management or code integrity of the bot.

📝 Where to Report (Recommended)
All risk vulnerabilities, critical bugs, or logic failures should be reported using the GitHub Issues tracker.

Navigate to the Issues tab on the repository.

Click "New Issue".

Use a clear title starting with [CRITICAL RISK] or [EXECUTION BUG].

What to Include in Your Report
For rapid diagnosis of the problem, please provide:

Bot Version/Tag: The version tag you are using (e.g., v3.3).

Description: A clear step-by-step description of the unexpected behavior (e.g., "The Partial TP failed to move the SL to breakeven").

Log Output: Copy and paste the relevant log messages from cTrader, especially any lines showing FAILED with error (this is essential debugging data).

Configuration: Mention the Operation Mode and the settings used (e.g., ScalperOnly, RiskPerTrade = 3.0).

⏱️ Our Response Timeline
We treat severe risk vulnerabilities (e.g., bugs that disable the Stop Loss or lead to over-leverages) with high priority.

Acknowledgement: You can expect confirmation of receipt within 24 hours.

Assessment: Our team will assess the severity and determine a fix within 3 business days.

Fix & Patch: Critical fixes will be released in a new patch version as quickly as possible.

🤝 Open Source Philosophy
This project is open to modification and contribution without restriction under the MIT License. We encourage users to adapt the code and share improvements with the community. Your responsible disclosure helps us build a more robust and transparent trading system.
