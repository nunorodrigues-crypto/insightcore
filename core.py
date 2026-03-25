import pandas as pd

def processar_revenue_ai(ficheiro_csv):
    # 1. Ingestão
    df = pd.read_csv(ficheiro_csv)
    
    # 2. Inteligência (Cálculos Simples)
    df['ocupacao_perc'] = (df['quartos_ocupados'] / df['capacidade']) * 100
    
    # Pegamos nos dados de "Hoje" (última linha do ficheiro)
    hoje = df.iloc[-1]
    ocupacao = hoje['ocupacao_perc']
    preco = hoje['preco_atual']
    
    # 3. Regras de Decisão (O teu Segredo)
    if ocupacao < 60:
        alerta = "⚠️ Baixa Procura"
        recomendacao = "Baixar preços 12%"
        acao = "Criar promoção 2 noites no Airbnb/Booking"
    elif ocupacao > 85:
        alerta = "🚀 Alta Procura"
        recomendacao = "Aumentar preço 15%"
        acao = "Fechar canais externos, priorizar venda direta"
    else:
        alerta = "🟢 Estável"
        recomendacao = "Manter preço"
        acao = "Monitorizar concorrência próxima"
        
    return {
        "data": hoje['data'],
        "ocupacao": ocupacao,
        "alerta": alerta,
        "rec": recomendacao,
        "acao": acao
    }

# Exemplo de uso:
# resultado = processar_revenue_ai('dados_hotel.csv')
