# 🚀 Guia de Upload para GitHub - TITAN FUSION QUANTUM

## ⚠️ IMPORTANTE: Protegendo Suas APIs

Este guia mostra como fazer upload do projeto para o GitHub **SEM EXPOR** suas chaves de API.

---

## 📋 Checklist ANTES do Upload

### ✅ Passo 1: Verificar Arquivos Sensíveis

```powershell
# Abra PowerShell na pasta do projeto
cd "C:\Users\Lucas Valério\Desktop\Titan pro"

# Verifique se .gitignore existe
dir .gitignore

# Se não existir, PARE e crie primeiro!
```

### ✅ Passo 2: Limpar API do quantum_brain.py

**OPÇÃO A: Usar variável de ambiente (Recomendado)**
```python
# quantum_brain.py - LINHA 15
# ❌ ANTES (NÃO FAÇA COMMIT ASSIM!):
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyCWyaHwLI3zeUsKNJlSmiHt3dA4Nz88Hzw")

# ✅ DEPOIS (SEGURO para GitHub):
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
```

**OPÇÃO B: Usar config.py**
```python
# 1. Crie config.py (já ignorado pelo Git)
# 2. Coloque sua API lá:
GEMINI_API_KEY = "SUA_API_REAL_AQUI"

# 3. No quantum_brain.py, importe:
try:
    from config import GEMINI_API_KEY
except:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
```

### ✅ Passo 3: Inicializar Git

```bash
cd "C:\Users\Lucas Valério\Desktop\Titan pro"

# Inicializar repositório
git init

# Verificar status (NÃO deve mostrar arquivos sensíveis!)
git status

# VERIFICAÇÃO CRÍTICA:
# ❌ Se aparecer: config.py, *.json, data/ → PARE! O .gitignore não está funcionando
# ✅ Se NÃO aparecer: Seguro para continuar
```

---

## 🔒 Verificação de Segurança

### Teste se .gitignore está funcionando:

```bash
# Criar arquivo de teste
echo "teste" > config.py

# Verificar se Git ignora
git status

# Se config.py aparecer = PROBLEMA!
# Se config.py NÃO aparecer = OK!

# Limpar teste
del config.py
```

---

## 📤 Upload para GitHub

### Passo 1: Criar Repositório no GitHub
1. Ir em https://github.com/new
2. Nome: `TitanFusion-cBot`
3. Descrição: "AI-Powered Trading System for cTrader"
4. **NÃO** marcar "Initialize with README" (já temos)
5. Criar repositório

### Passo 2: Conectar Repositório Local

```bash
# Adicionar remote
git remote add origin https://github.com/LucassVal/TitanFusion-cBot.git

# Verificar remote
git remote -v
```

### Passo 3: Fazer Primeiro Commit

```bash
# Adicionar todos os arquivos (exceto os ignorados)
git add .

# Verificar o que será commitado
git status

# ⚠️ VERIFICAÇÃO FINAL:
# Se aparecer qualquer arquivo com API/senha → git reset e corrija!

# Fazer commit
git commit -m "Initial commit - Titan Fusion Quantum v1.0.0"

# Push para GitHub
git push -u origin main
```

---

## 🔐 Arquivos que DEVEM estar no .gitignore

Verifique se estes NÃO aparecem no `git status`:

```
❌ config.py (suas APIs reais)
❌ *.json (dados de trading)
❌ data/ (histórico de sinais)
❌ __pycache__/ (Python cache)
❌ *.log (logs do sistema)
```

Arquivos que DEVEM ir pro GitHub:
```
✅ README.md
✅ CHANGELOG.md
✅ .gitignore
✅ .version
✅ requirements.txt
✅ config.example.py
✅ TitanFusion_QuantumBot.cs
✅ quantum_brain.py (SEM sua API real)
```

---

## 🆘 Se Você Já Fez Commit com API Exposta

### SOLUÇÃO: Remover da História do Git

```bash
# 1. Remover arquivo do Git (mas manter local)
git rm --cached quantum_brain.py

# 2. Adicionar ao .gitignore temporariamente
echo "quantum_brain.py" >> .gitignore

# 3. Commit da remoção
git commit -m "Remove sensitive file"

# 4. Limpar histórico (CUIDADO!)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch quantum_brain.py" \
  --prune-empty --tag-name-filter cat -- --all

# 5. Force push
git push origin --force --all

# 6. DEPOIS: Limpar quantum_brain.py localmente, remover do .gitignore, adicionar de volta sem API
```

**⚠️ MELHOR OPÇÃO:** Revogar a API antiga em https://ai.google.dev/ e criar nova!

---

## 📝 Estrutura Final no GitHub

```
TitanFusion-cBot/
├── .gitignore ✅
├── .version ✅
├── README.md ✅
├── CHANGELOG.md ✅
├── LICENSE ✅
├── requirements.txt ✅
├── config.example.py ✅ (SEM suas APIs)
├── TitanFusion_QuantumBot.cs ✅
├── quantum_brain.py ✅ (SEM sua API real)
└── run_quantum.bat ✅
```

**NÃO deve aparecer:**
- ❌ config.py
- ❌ *.json
- ❌ data/
- ❌ __pycache__/

---

## ✅ Checklist Final

Antes de fazer push, confirme:

- [ ] Criei .gitignore
- [ ] Removi API hardcoded de quantum_brain.py
- [ ] Criei config.example.py (SEM minhas APIs)
- [ ] Testei `git status` (nenhum arquivo sensível)
- [ ] Li README.md (não tem APIs expostas)
- [ ] Arquivo config.py está em .gitignore
- [ ] Testei clone em pasta separada para confirmar

---

## 🎯 Para Colaboradores

Quando alguém clonar o repositório:

```bash
# 1. Clone
git clone https://github.com/LucassVal/TitanFusion-cBot.git

# 2. Entre na pasta
cd TitanFusion-cBot

# 3. Copiar exemplo de config
copy config.example.py config.py

# 4. Editar config.py e adicionar suas APIs
notepad config.py

# 5. Instalar dependências
pip install -r requirements.txt

# 6. Pronto para rodar!
python quantum_brain.py
```

---

## 📧 Suporte

Se tiver dúvidas sobre segurança ou upload:
- Abra uma Issue: https://github.com/LucassVal/TitanFusion-cBot/issues
- Contato: [@LucassVal](https://github.com/LucassVal)

---

**🔒 Lembre-se: NUNCA faça commit de senhas ou APIs reais!**
