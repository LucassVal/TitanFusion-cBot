import requests
import os
import json

# API Key do Lucas
API_KEY = "AIzaSyCWyaHwLI3zeUsKNJlSmiHt3dA4Nz88Hzw"

def list_models():
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    
    print(f"🔍 Colsultando modelos disponíveis para a chave {API_KEY[:10]}...")
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print("\n✅ MODELOS DISPONÍVEIS:")
            print("="*60)
            print(f"{'NAME (ID)':<40} | {'DISPLAY NAME'}")
            print("="*60)
            
            found_flash = False
            for model in data.get('models', []):
                name = model['name'].replace('models/', '')
                display = model['displayName']
                
                # Filtrar apenas modelos de geração de texto/chat
                if "generateContent" in model.get('supportedGenerationMethods', []):
                    print(f"{name:<40} | {display}")
                    if "flash" in name: found_flash = True
            
            print("="*60)
            if found_flash:
                print("\n🚀 BOA NOTÍCIA: Modelos 'Flash' (Rápidos) foram encontrados!")
            else:
                print("\n⚠️ AVISO: Nenhum modelo 'Flash' encontrado. Use 'gemini-pro'.")
                
        else:
            print(f"❌ ERRO: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ ERRO DE CONEXÃO: {e}")

if __name__ == "__main__":
    list_models()
    input("\nPressione Enter para sair...")
