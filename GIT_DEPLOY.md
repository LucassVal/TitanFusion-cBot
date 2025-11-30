# 📤 GIT DEPLOYMENT GUIDE - Titan Pro

## ✅ Limpeza Concluída

Arquivos removidos:
- ✓ bridge/ (cTrader connector obsoleto)
- ✓ ctrader_settings.md (obsoleto)
- ✓ Titan pro/deriv_data.csv (dados antigos)

Arquivos criados:
- ✓ README.md (documentação profissional)
- ✓ .gitignore (ignora dados/cache)

---

## 🚀 DEPLOY PARA GITHUB

### **Opção 1: Primeiro Commit (Repositório Novo)**

```bash
cd "c:/Users/Lucas Valério/.gemini/antigravity/playground/prismic-prominence"

# Inicializar Git
git init

# Adicionar arquivos
git add .

# Commit
git commit -m "feat: Titan Pro v2.0 - Hybrid GPU Trading System

- Dual GPU optimization (Intel + NVIDIA)
- 100k parameter combinations with Walk-Forward validation
- Multi-source data (Dukascopy + Deriv)
- Auto-update weekly re-calibration
- 8 markets support (4 real + 4 synthetic)
- Multi-timeframe (M1, M5, M15, M30, H1)"

# Conectar ao repositório existente
git remote add origin https://github.com/LucassVal/TitanFusion-cBot.git

# Push (forçado para sobrescrever)
git push -f origin main
```

---

### **Opção 2: Atualizar Repositório Existente**

```bash
cd "c:/Users/Lucas Valério/.gemini/antigravity/playground/prismic-prominence"

# Se já tem .git/ local
git add .

git commit -m "feat: Major upgrade to Titan Pro v2.0

Breaking Changes:
- Migrated from cTrader to direct API trading
- New architecture: CPU (live) + GPU (optimization)
- Data sources: Dukascopy (real) + Deriv (synthetic)

New Features:
- Dual GPU parallel processing
- 100k combinations grid search
- Walk-Forward validation (70/30)
- Auto-update system (weekly)
- Multi-market support (8 markets)
- Multi-timeframe support (M1-H1)

Technical:
- Python 3.12
- PyOpenCL for GPU
- pandas_ta for indicators
- WebSocket API connections"

# Push para GitHub
git push origin main
```

---

### **Opção 3: Clone Existente + Update**

```bash
# Se não tem repositório local ainda
cd "c:/Users/Lucas Valério/.gemini/antigravity/playground"

# Backup pasta atual
Rename-Item "prismic-prominence" "prismic-prominence-backup"

# Clone GitHub
git clone https://github.com/LucassVal/TitanFusion-cBot.git
cd TitanFusion-cBot

# Copiar arquivos novos
Copy-Item "../prismic-prominence-backup/Titan pro/*" ./ -Recurse
Copy-Item "../prismic-prominence-backup/README.md" ./
Copy-Item "../prismic-prominence-backup/.gitignore" ./

# Commit
git add .
git commit -m "feat: Titan Pro v2.0 complete rewrite"
git push origin main
```

---

## 📋 VERIFICAÇÕES PRÉ-COMMIT

Antes de fazer push, verificar:

```bash
# Ver status
git status

# Ver diff
git diff

# Ver arquivos que serão commitados
git ls-files

# Verificar se .gitignore está funcionando
git status --ignored
```

**Arquivos que NÃO devem aparecer:**
- ❌ `*.csv` (dados baixados)
- ❌ `data_cache.json`
- ❌ `__pycache__/`
- ❌ `.venv/`

**Arquivos que DEVEM aparecer:**
- ✅ `Titan pro/*.py` (todos os scripts)
- ✅ `Titan pro/dashboard.html`
- ✅ `README.md`
- ✅ `.gitignore`

---

## 🔧 TROUBLESHOOTING

### **Erro: "repository not found"**
```bash
# Verificar remote
git remote -v

# Reconfigurar
git remote set-url origin https://github.com/LucassVal/TitanFusion-cBot.git
```

### **Erro: "failed to push"**
```bash
# Forçar push (CUIDADO: sobrescreve histórico)
git push -f origin main
```

### **Arquivos grandes demais**
```bash
# Ver tamanho dos arquivos
Get-ChildItem -Recurse | Sort-Object Length -Descending | Select-Object -First 10

# Se tem CSVs grandes, adicionar ao .gitignore
echo "*.csv" >> .gitignore
git rm --cached "Titan pro/*.csv"
```

---

## 📝 RECOMENDAÇÕES

1. **Branching**: Crie branch antes de push
```bash
git checkout -b feature/titan-pro-v2
git push origin feature/titan-pro-v2
```

2. **Tags**: Marque versão
```bash
git tag -a v2.0.0 -m "Titan Pro v2.0 Release"
git push origin v2.0.0
```

3. **Releases**: Crie release no GitHub
   - GitHub → Repositório → Releases → New Release
   - Tag: v2.0.0
   - Title: "Titan Pro v2.0 - Hybrid GPU Trading System"
   - Description: Copie do README.md

---

## ✅ DEPLOY COMPLETO!

Após push bem-sucedido:
1. Verifique: https://github.com/LucassVal/TitanFusion-cBot
2. Atualize descrição do repositório
3. Adicione tópicos: `trading`, `gpu`, `python`, `algorithmic-trading`, `machine-learning`
4. Configure GitHub Actions (opcional para CI/CD)

**🎉 Repositório pronto para compartilhar!**
