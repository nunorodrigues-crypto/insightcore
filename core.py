import streamlit as st
import pandas as pd

st.set_page_config(page_title="InsightKube Revenue AI", layout="centered")

st.markdown("""
    <style>
    .big-font { font-size:24px !important; font-weight: bold; }
    .rec-font { font-size:24px !important; color: #FF4B4B; font-weight: bold; background-color: #f0f2f6; padding: 10px; border-radius: 10px;}
    .action-font { font-size:20px !important; color: #2E8B57; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

st.title("🏨 Revenue AI para Hotelaria")
st.subheader("Decisões diárias para aumentar receita")

st.sidebar.header("Módulo de Dados")
uploaded_file = st.sidebar.file_uploader("Carregar CSV de Reservas", type=['csv'])

if uploaded_file:
    try:
        # Tenta ler com ponto e vírgula (padrão Excel PT)
        df = pd.read_csv(uploaded_file, sep=None, engine='python')
        
        # Limpar nomes de colunas (remover espaços vazios)
        df.columns = df.columns.str.strip()
        
        required_columns = ['data', 'quartos_ocupados', 'capacidade', 'preco_atual']
        if not all(col in df.columns for col in required_columns):
            st.error(f"Colunas detectadas: {list(df.columns)}")
            st.error(f"O CSV deve conter exatamente: {required_columns}")
            st.stop()
            
        # Converter data (formato europeu DD/MM/YY)
        df['data'] = pd.to_datetime(df['data'], dayfirst=True).dt.strftime('%d/%m/%Y')
        
        # MOTOR DE INTELIGÊNCIA
        df['ocupacao_perc'] = (df['quartos_ocupados'] / df['capacidade']) * 100
        
        hoje = df.iloc[-1]
        ocupacao = hoje['ocupacao_perc']
        preco = hoje['preco_atual']
        
        # REGRAS INTELIGENTES
        if ocupacao < 60:
            alerta, rec, acao = "⚠️ Baixa Procura", "Baixar preços 12%", "Criar promoção 2 noites no Airbnb/Booking"
        elif ocupacao > 85:
            alerta, rec, acao = "🚀 Alta Procura", "Aumentar preço 15%", "Fechar canais externos, priorizar venda direta"
        else:
            alerta, rec, acao = "🟢 Estável", "Manter preço", "Monitorizar concorrência próxima"
            
        # OUTPUT DE VALOR
        st.divider()
        st.markdown(f'<p class="big-font">📅 Previsão para: {hoje["data"]}</p>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        col1.metric("Ocupação Prevista", f"{ocupacao:.1f}%", alerta)
        col2.metric("Preço Atual", f"{preco:.2f} €")
        
        st.divider()
        st.subheader("💡 Decisão do Dia")
        st.markdown(f'<p class="rec-font">👉 {rec}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="action-font">📍 Ação: {acao}</p>', unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Erro técnico: {e}")
else:
    st.info("Carregue o CSV para obter a recomendação.")
    # Exibe o formato esperado para ajudar o usuário
    st.write("Formato esperado:", pd.DataFrame(columns=['data', 'quartos_ocupados', 'capacidade', 'preco_atual']))
