# 🤝 Contributing to Titan Pro

Thank you for your interest in contributing! This project thrives on community collaboration.

## 💡 Philosophy

> "O conhecimento só cresce quando debatido" - Lucas Valério

We believe in open collaboration, knowledge sharing, and helping each other grow.

---

## 🚀 How to Contribute

### **1. Fork & Clone**
```bash
# Fork on GitHub, then:
git clone https://github.com/YOUR_USERNAME/TitanFusion-cBot.git
cd TitanFusion-cBot
```

### **2. Create Branch**
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### **3. Make Changes**
- Write clean, documented code
- Follow existing code style
- Test thoroughly
- Update README if needed

### **4. Commit**
```bash
git add .
git commit -m "feat: your descriptive message"
```

**Commit Message Format:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `perf:` Performance improvement
- `refactor:` Code restructuring
- `test:` Adding tests

### **5. Push & PR**
```bash
git push origin feature/your-feature-name
```

Then create Pull Request on GitHub!

---

## 📋 Contribution Ideas

### **High Priority**
- [ ] WebSocket backend for dashboard.html
- [ ] Trade execution implementation (Deriv API)
- [ ] Multi-pair portfolio management
- [ ] Backtesting visualization

### **Medium Priority**
- [ ] Machine Learning fitness scoring
- [ ] Automated testing suite
- [ ] Performance benchmarks
- [ ] Docker containerization

### **Code Quality**
- [ ] Type hints (Python 3.12)
- [ ] Unit tests
- [ ] Integration tests
- [ ] Documentation improvements

---

## 🧪 Testing

Before submitting PR:

```bash
# Test GPU detection
python "Titan pro/check_cuda.py"

# Test data download
python "Titan pro/dukascopy_downloader.py"

# Test launcher
python "Titan pro/launcher.py"
```

---

## 📝 Code Style

- **Python**: PEP 8
- **Line length**: 100 characters
- **Docstrings**: Google style
- **Type hints**: Preferred

Example:
```python
def calculate_fitness(net_profit: float, max_dd: float) -> float:
    """
    Calculate robust fitness score.
    
    Args:
        net_profit: Net profit in USD
        max_dd: Maximum drawdown in USD
        
    Returns:
        Fitness score (higher is better)
    """
    return net_profit - (max_dd * 2.0)
```

---

## 🐛 Reporting Bugs

**Use GitHub Issues with:**
- Clear title
- Steps to reproduce
- Expected vs actual behavior
- System info (OS, GPU, Python version)
- Error logs

---

## 💬 Questions

- **Discussions**: Use GitHub Discussions
- **Issues**: For bugs/features only
- **Email**: For private matters

---

## 🎯 Pull Request Guidelines

**Will be merged if:**
- ✅ Code works and is tested
- ✅ Follows project style
- ✅ Has clear description
- ✅ Doesn't break existing features
- ✅ Adds value to the project

**May need revision if:**
- ⚠️ Missing tests
- ⚠️ Unclear commit messages
- ⚠️ Breaking changes without discussion
- ⚠️ Performance regression

---

## 🏆 Recognition

Contributors will be:
- Listed in README.md
- Mentioned in release notes
- Part of a growing community!

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for helping make Titan Pro better! 🚀**
