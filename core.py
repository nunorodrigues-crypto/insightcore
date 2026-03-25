import streamlit as st
import pandas as pd

# 1. Configuração de Marca e Título
st.set_page_config(page_title="InsightKube Revenue AI", layout="centered")

# Estilo Simples e Profissional
st.markdown("""
    <style>
    .big-font { font-size:24px !important; font-weight: bold; }
    .rec-font { font-size:20px !important; color: #FF4B4B; font-weight: bold;}
    .action-font { font-size:18px !important; color: #2E8B57;}
    </style>
    """, unsafe_allow_html=True)

st.title("🏨 Revenue AI para Hotelaria")
st.subheader("Dizemos-te diariamente o que fazer para aumentar receitas e reduzir custos")

# 🔹 1. INGESTÃO DE DADOS (O Upload CSV do Cliente)
st.sidebar.header("Módulo de Dados")
uploaded_file = st.sidebar.file_uploader("Carregar CSV de Reservas", type=['csv'])

if uploaded_file:
    # Ler o CSV do cliente
    try:
        df = pd.read_csv(uploaded_file)
        # Garanter que as colunas obrigatórias existem
        required_columns = ['data', 'quartos_ocupados', 'capacidade', 'preco_atual']
        if not all(col in df.columns for col in required_columns):
            st.error(f"O CSV deve conter as colunas: {', '.join(required_columns)}")
            st.stop()
            
        # Converter data
        df['data'] = pd.to_csv(df['data'])
        
        # 🔹 2. MOTOR DE INTELIGÊNCIA (O teu Core Inteligente)
        # Cálculos Simples
        df['ocupacao_perc'] = (df['quartos_ocupados'] / df['capacidade']) * 100
        
        # Pegamos nos dados de "Hoje" (última linha do ficheiro para simular o dia atual)
        hoje = df.iloc[-1]
        data_hoje = hoje['data']
        ocupacao = hoje['ocupacao_perc']
        preco = hoje['preco_atual']
        
        # 🧠 Regras Inteligentes (O teu Segredo)
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
            
        # 🔹 3. OUTPUT DE VALOR (A Recomendação Direta)
        st.divider()
        st.markdown(f'<p class="big-font">📅 Previsão para: {data_hoje}</p>', unsafe_allow_html=True)
        
        # Exibir Métricas Clave
        col1, col2 = st.columns(2)
        col1.metric("Ocupação Prevista", f"{ocupacao:.0f}%", alerta)
        col2.metric("Preço Atual", f"{preco:.2f} €")
        
        st.divider()
        st.subheader("💡 Decisão do Dia")
        
        # Exibir a Recomendação de forma Destacada (O que o cliente compra)
        st.markdown(f'<p class="rec-font">👉 Recomendação: {recomendacao}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="action-font">👉 Ação: {acao}</p>', unsafe_allow_html=True)
        
        st.info("Isto é uma recomendação gerada automaticamente para maximizar a sua receita com base no seu histórico e tendências atuais.")

    except Exception as e:
        st.error(f"Erro ao processar o ficheiro: {e}")

else:
    # Mensagem inicial quando não há ficheiro
    st.info("Por favor, carregue o CSV de reservas no menu lateral para obter a sua recomendação diária.")
    
    # Exemplo de formato de CSV para o cliente saber o que carregar
    st.divider()
    st.subheader("Exemplo de Formato de CSV Aceite")
    exemplo_df = pd.DataFrame({
        'data': ['2024-03-20', '2024-03-21', '2024-03-22'],
        'quartos_ocupados': [15, 20, 12],
        'capacidade': [25, 25, 25],
        'preco_atual': [120.00, 130.00, 115.00]
    })
    st.dataframe(exemplo_df)
