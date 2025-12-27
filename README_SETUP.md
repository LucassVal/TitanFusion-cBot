# 🚀 Gold Emperor AI - Setup Guide

## ⚠️ SEGURANÇA PRIMEIRO!

**NUNCA compartilhe suas chaves de API!** As chaves que você mostrou devem ser **REVOGADAS IMEDIATAMENTE**:

1. **Google Cloud Console**: https://console.cloud.google.com/apis/credentials
   - Encontre a chave do Gemini
   - Clique em "Excluir" ou "Revogar"
   - Crie uma NOVA chave

2. **Deriv**: https://app.deriv.com/account/api-token
   - Revogue o token `98L08GjOewqA8M5`
   - Crie um novo token

---

## 📦 Instalação

### 1. Instalar Python (se não tiver)
- Download: https://www.python.org/downloads/
- **IMPORTANTE**: Marque "Add Python to PATH" durante instalação

### 2. Instalar bibliotecas necessárias
Abra o CMD/PowerShell e rode:

```bash
pip install requests websocket-client
```

### 3. Configurar chaves de API (SEGURO)

**Opção A - Variáveis de Ambiente (Recomendado):**

Windows PowerShell:
```powershell
$env:GEMINI_API_KEY = "SUA_NOVA_CHAVE_GEMINI"
$env:DERIV_API_KEY = "SUA_NOVA_CHAVE_DERIV"
```

Windows CMD:
```cmd
set GEMINI_API_KEY=SUA_NOVA_CHAVE_GEMINI
set DERIV_API_KEY=SUA_NOVA_CHAVE_DERIV
```

**Opção B - Editar o código (NÃO recomendado):**
- Abra `gemini_trader.py`
- Substitua nas linhas 17-18

---

## ▶️ Como Usar

### 1. Rodar o script Python
```bash
cd "C:\Users\Lucas Valério\Desktop\Titan pro"
python gemini_trader.py
```

Você verá:
```
🚀 Gold Emperor AI - Iniciando...
📊 Símbolo: frxXAUUSD
⏱️  Intervalo: 30s
✅ Conectado à Deriv API
📈 Preço atual: $2758.50
✅ Previsão salva: BUY (85% confiança)
```

### 2. Adicionar indicador ao cTrader
1. Abra cTrader
2. Menu: Automate → Manage cBots
3. Clique "New" → Cole o código de `GoldEmperor_AI.cs`
4. Compile
5. Adicione ao gráfico XAUUSD

### 3. Pronto! 🎉
- Python atualiza previsões a cada 30 segundos
- cTrader lê e mostra no painel a cada 5 segundos

---

## 🔧 Problemas Comuns

**"Erro ao ler JSON"**
- Certifique-se que `python gemini_trader.py` está rodando
- Verifique o caminho do arquivo em `GoldEmperor_AI.cs` (parâmetro)

**"Erro de autorização Deriv"**
- Chave incorreta ou revogada
- Gere nova chave em https://app.deriv.com/account/api-token

**"Erro Gemini API"**
- Chave incorreta
- Limite de requisições excedido (aguarde alguns minutos)

---

## 📊 Arquitetura

```
Deriv API → Python Script → Gemini AI → predictions.json → cTrader Indicator
```

1. **Python** busca dados do mercado a cada 30s
2. **Gemini AI** analisa e gera previsão
3. **JSON** armazena resultado
4. **cTrader** lê e exibe no painel

---

## ⚙️ Personalização

**Alterar intervalo de atualização:**
- `gemini_trader.py` linha 15: `UPDATE_INTERVAL = 30` (segundos)
- `GoldEmperor_AI.cs` parâmetro: "Update Interval"

**Mudar símbolo:**
- `gemini_trader.py` linha 14: `SYMBOL = "frxXAUUSD"`

---

## 📞 Suporte

Se tiver problemas, verifique:
1. Python está instalado e no PATH
2. Bibliotecas instaladas (`pip list`)
3. Chaves de API válidas e com permissões
4. Script Python rodando em background
5. Caminho do JSON correto no indicador

Bons trades! 📈🚀
