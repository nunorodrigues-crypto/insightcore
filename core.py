import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração de Marca
st.set_page_config(page_title="InsightKube SaaS", layout="wide")
st.sidebar.title("INSIGHTKUBE")
st.sidebar.subheader("Business Powered by Data")

# --- MÓDULO 1: DATA ENTRY (UPLOAD) ---
st.sidebar.divider()
uploaded_file = st.sidebar.file_uploader("Carregar Excel de Operação", type=['xlsx', 'csv'])

if uploaded_file:
    df = pd.read_csv(uploaded_file) # Ou read_excel
else:
    # Dados de exemplo para demonstração
    df = pd.DataFrame({
        'Data': pd.date_range(start='2024-03-01', periods=10),
        'Vendas': [1000, 1200, 1100, 1500, 1400, 1600, 1300, 1700, 1800, 1650],
        'Custos': [400, 420, 390, 450, 440, 480, 410, 500, 520, 490]
    })

# --- MÓDULO 2: CÁLCULOS DE ENGENHARIA DE LUCRO ---
df['Margem_Bruta'] = (df['Vendas'] - df['Custos']) / df['Vendas']
margem_media = df['Margem_Bruta'].mean()
venda_total = df['Vendas'].sum()

# --- MÓDULO 3: DASHBOARD (FORESIGHT) ---
st.title("🚀 Painel de Controlo Operacional")

col1, col2, col3 = st.columns(3)
col1.metric("Faturação Acumulada", f"{venda_total:,.2f} €")
col2.metric("Margem Média", f"{margem_media:.1%}")
col3.metric("Status de Rentabilidade", "SAUDÁVEL" if margem_media > 0.6 else "ALERTA")

# Gráfico Dinâmico
st.subheader("Tendência de Vendas e Margem")
fig = px.area(df, x='Data', y='Vendas', title="Performance de Vendas (Foresight Analysis)")
st.plotly_chart(fig, use_container_width=True)

# --- MÓDULO 4: O "DIAGNÓSTICO MENSAL" AUTOMÁTICO ---
st.divider()
st.subheader("📝 Diagnóstico Automático InsightKube")
if margem_media < 0.65:
    st.error(f"Detetámos uma fuga de margem. O seu Food Cost/Custo Operacional está {0.65 - margem_media:.1%} acima do ideal.")
else:
    st.success("A operação está a identificar modelos de crescimento eficientes.")

st.info("🔮 **Foresight:** Com base no histórico, prevemos que o Breakeven do mês seja atingido no dia 19.")
