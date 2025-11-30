# LISTA DE ARQUIVOS PARA MANTER
KEEP = [
    'launcher.py',
    'titan_hybrid.py',
    'data_manager.py',
    'deriv_client.py',
    'deriv_downloader.py',
    'dukascopy_downloader.py',
    'dashboard.html',
    'check_cuda.py',
    'data_cache.json',
    # Dados baixados (padrão)
    'dukascopy_*.csv',
    'deriv_*.csv'
]

# ARQUIVOS OBSOLETOS PARA REMOVER
REMOVE_FILES = [
    '../bridge',  # cTrader connector (obsoleto)
    '../ctrader_settings.md',  # Configurações antigas
    'titan_strategy.py',  # Versão antiga
    'titan_portfolio.py',  # Versão antiga
    'titan_wfo.py',  # Versão antiga
    'optimizer.py',  # Versão antiga integrada no titan_hybrid
]

print("="*70)
print("TITAN PRO - CLEANUP SCRIPT")
print("="*70)
print("\n✅ ARQUIVOS ESSENCIAIS (Mantidos):")
for f in KEEP:
    print(f"   {f}")

print("\n❌ ARQUIVOS OBSOLETOS (Para remover):")
for f in REMOVE_FILES:
    print(f"   {f}")

print("\n📁 LOCALIZAÇÃO DOS DADOS:")
print(f"   Pasta: Titan pro/")
print(f"   Padrão: dukascopy_[SYMBOL]_M1_3months.csv")
print(f"   Padrão: deriv_[SYMBOL]_M1_3months.csv")
print(f"   Cache: data_cache.json")

print("\n" + "="*70)
print("Execute os comandos manualmente para confirmar!")
print("="*70)
