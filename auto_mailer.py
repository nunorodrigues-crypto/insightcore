import pandas as pd
from fpdf import FPDF
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

print("--- INICIANDO MOTOR DE ENVIO ---")

# 1. Puxar credenciais
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")

def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="INSIGHTKUBE REVENUE AI", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Data do Relatorio: {dados['data']}", ln=True)
    pdf.cell(200, 10, txt=f"Ocupacao Calculada: {dados['ocupacao']:.1f}%", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt=f"RECOMENDACAO: {dados['rec']}", ln=True)
    pdf.cell(200, 10, txt=f"ACAO IMEDIATA: {dados['acao']}", ln=True)
    return pdf.output(dest='S').encode('latin-1', 'ignore')

try:
    # 2. Ler Dados
    df = pd.read_csv('Livro1.csv', sep=';')
    df['ocupacao_perc'] = (df['quartos_ocupados'] / df['capacidade']) * 100
    hoje = df.iloc[-1]
    
    # Lógica de Receita
    if hoje['ocupacao_perc'] < 60:
        rec, acao = "Baixar precos 12%", "Criar promocao 2 noites"
    elif hoje['ocupacao_perc'] > 85:
        rec, acao = "Aumentar preco 15%", "Fechar canais externos"
    else:
        rec, acao = "Manter preco atual", "Monitorizar concorrencia"

    dados = {"data": hoje['data'], "ocupacao": hoje['ocupacao_perc'], "rec": rec, "acao": acao}
    print(f"✅ Analise concluida para {dados['data']}")

    # 3. Preparar Email
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = GMAIL_USER 
    msg['Subject'] = f"🏨 InsightKube: Decisao {dados['data']}"
    
    corpo = f"Bom dia,\n\nO sistema analisou os dados e recomenda: {rec}.\n\nDetalhes no PDF em anexo."
    msg.attach(MIMEText(corpo, 'plain'))
    
    pdf_content = gerar_pdf(dados)
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(pdf_content)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f"attachment; filename= Relatorio_Revenue.pdf")
    msg.attach(part)

    # 4. Enviar
    print("--- A CONECTAR AO GMAIL ---")
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.send_message(msg)
    
    print("✅ SUCESSO: Email enviado com o PDF!")

except Exception as e:
    print(f"❌ ERRO CRITICO: {str(e)}")
