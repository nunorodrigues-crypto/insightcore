import pandas as pd
import os

print("--- INICIANDO SCRIPT ---")

# Verificar se os Secrets existem
user = os.getenv("GMAIL_USER")
pw = os.getenv("GMAIL_PASSWORD")

if not user or not pw:
    print("❌ ERRO: Secrets GMAIL_USER ou GMAIL_PASSWORD nao encontrados!")
else:
    print(f"✅ Secrets detectados para: {user}")

# Verificar se o CSV existe
if not os.path.exists('Livro1.csv'):
    print("❌ ERRO: Ficheiro Livro1.csv nao encontrado na raiz!")
else:
    print("✅ Ficheiro Livro1.csv encontrado!")

# Tentar ler o ficheiro
try:
    df = pd.read_csv('Livro1.csv', sep=';')
    print(f"✅ CSV lido com sucesso. Linhas: {len(df)}")
    
    # Aqui entraria o resto do código de envio...
    # Por agora, foca em ver se estas mensagens aparecem no log!
    
except Exception as e:
    print(f"❌ ERRO ao ler CSV: {e}")

print("--- FIM DO SCRIPT ---")
