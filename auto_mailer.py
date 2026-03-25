import pandas as pd
from fpdf import FPDF
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# 1. Configurações de Email (Puxa dos Secrets do GitHub)
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")
DESTINATARIO = GMAIL_USER  # Podes mudar para o email do cliente

def gerar_pdf_bytes(res):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="INSIGHTKUBE REVENUE AI - RELATORIO AUTOMATICO", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Data: {res['data']}", ln=True)
    pdf.cell(200, 10, txt=f"Ocupacao: {res['ocupacao']:.1f}%", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt=f"RECOMENDACAO: {res['rec']}", ln=True)
    pdf.cell(200, 10, txt=f"ACAO: {res['acao']}", ln=True)
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# 2. Processamento dos Dados
try:
    df = pd.read_csv('Livro1.csv', sep=';') # Usa o teu ficheiro que já está no GitHub
    df['ocupacao_perc'] = (df['quartos_ocupados'] / df['capacidade']) * 100
    hoje = df.iloc[-1]
    
    # Regras Simples
    if hoje['ocupacao_perc'] < 60:
        rec, acao = "Baixar precos 12%", "Criar promocao 2 noites"
    else:
        rec, acao = "Manter preco", "Monitorizar"

    dados = {
        "data": hoje['data'],
        "ocupacao": hoje['ocupacao_perc'],
        "rec": rec,
        "acao": acao
    }

    # 3. Gerar PDF e Enviar Email
    pdf_content = gerar_pdf_bytes(dados)
    
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = DESTINATARIO
    msg['Subject'] = f"🏨 InsightKube: Decisao do Dia {dados['data']}"
    
    msg.attach(MIMEText(f"Bom dia Nuno,\n\nAqui esta a analise automatica para hoje: {rec}.\nVerifica o PDF em anexo.", 'plain'))
    
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(pdf_content)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f"attachment; filename= Relatorio_{dados['data'].replace('/','-')}.pdf")
    msg.attach(part)

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.send_message(msg)
    
    print("✅ Email enviado com sucesso!")

except Exception as e:
    print(f"❌ Erro: {e}")
