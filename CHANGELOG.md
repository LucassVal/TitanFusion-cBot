# Changelog

## [2.1.0] - 2025-12-01
### Added
- **Full Revolution Optimization Engine**: Expanded from 15 to 40 parameters per strategy combination.
- **New Indicators**: Added ADX (Average Directional Index) for trend strength filtering.
- **Advanced Metrics**: Added Sortino Ratio, Max Favorable Excursion (MFE), and Max Adverse Excursion (MAE) to fitness calculation.
- **Volume Optimization**: Fitness function now rewards optimal trade frequency (50-200 trades/day).
- **Expanded Parameter Ranges**: Ranges now cover all market types (Scalper, Breakout, Pullback) with independent settings.
- **Mega Grid**: Increased optimization sampling from 100k to 500k combinations.

### Changed
- **Fitness Function**: Completely rewritten "Ultra-Robust Fitness" with multi-factor scoring.
- **Drawdown Limits**: Relaxed training DD to 25% and validation to 30% to allow for more aggressive discovery (controlled by fitness penalties).
- **Launcher**: Updated to support new market selection workflow.

## [2.0.0] - 2025-11-30
### Added
- **Hybrid GPU/CPU Engine**: Dual-engine architecture for simultaneous trading and optimization.
- **OpenCL Kernel**: High-performance C kernel for portfolio simulation.
- **Tiered Drawdown**: 15% (Train) -> 20% (Val) -> 12% (Live) risk layering.
- **Data Manager**: Automated data handling for Dukascopy and Deriv.
- **Dashboard**: HTML5 dashboard with real-time health monitoring.

### Fixed
- **Fitness Function Bug**: Fixed hardcoded $10 drawdown limit that was rejecting all parameters.
- **Indentation Errors**: Resolved persistent Python indentation issues in `titan_hybrid.py`.

## [1.0.0] - 2025-11-29
- Initial Release
