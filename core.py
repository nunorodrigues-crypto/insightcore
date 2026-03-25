import streamlit as st
import pandas as pd
from fpdf import FPDF

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

def gerar_pdf_report(res):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    
    # Cabeçalho
    pdf.cell(200, 10, txt="INSIGHTKUBE REVENUE AI - RELATÓRIO DIÁRIO", ln=True, align='C')
    pdf.ln(10)
    
    # Dados
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Data da Analise: {res['data']}", ln=True)
    pdf.cell(200, 10, txt=f"Ocupacao Prevista: {res['ocupacao']:.1f}%", ln=True)
    pdf.cell(200, 10, txt=f"Preco Recomendado: {res['rec']}", ln=True)
    
    # O "Dinheiro"
    pdf.ln(5)
    pdf.set_text_color(255, 0, 0) # Vermelho para a Ação
    pdf.cell(200, 10, txt=f"ACAO IMEDIATA: {res['acao']}", ln=True)
    
    return pdf.output(dest='S').encode('latin-1') # Retorna o PDF como bytes

# ... (teu código anterior igual até à parte do 'Ação')

        st.divider()
        st.subheader("📄 Relatório Executivo")
        
        # Preparar os dados para a função do PDF
        dados_report = {
            "data": hoje["data"],
            "ocupacao": ocupacao,
            "rec": rec,
            "acao": acao
        }
        
        # Gerar o PDF
        pdf_bytes = gerar_pdf_report(dados_report)
        
        # Botão para o utilizador descarregar
        st.download_button(
            label="Descarregar Relatório PDF",
            data=pdf_bytes,
            file_name=f"Relatorio_InsightKube_{hoje['data'].replace('/', '-')}.pdf",
            mime="application/pdf"
        )
        
    except Exception as e:
        st.error(f"Erro técnico: {e}")
# ...

# FUNÇÃO DO PDF MELHORADA (dentro ou fora do bloco, mas definida)
def gerar_pdf_report(res):
    pdf = FPDF()
    pdf.add_page()
    
    # Título
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="INSIGHTKUBE REVENUE AI", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Relatorio Diario de Tomada de Decisao", ln=True, align='C')
    pdf.ln(10)
    
    # Bloco de Dados
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt=f"Data da Analise: {res['data']}", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Ocupacao Prevista: {res['ocupacao']:.1f}%", ln=True)
    pdf.cell(200, 10, txt=f"Recomendacao: {res['rec']}", ln=True)
    
    # Bloco de Ação (Destaque)
    pdf.ln(10)
    pdf.set_fill_color(240, 242, 246)
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(255, 0, 0)
    pdf.cell(200, 15, txt=f"ACAO IMEDIATA: {res['acao']}", ln=True, align='C', fill=True)
    
    # Nota de Rodapé
    pdf.set_y(-30)
    pdf.set_font("Arial", 'I', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, txt="InsightKube - Business Powered by Data. Confidencial.", align='C')
    
    # "S" retorna string, mas em Python 3 fpdf precisa de encode para bytes
    return pdf.output(dest='S').encode('latin-1', 'ignore')
