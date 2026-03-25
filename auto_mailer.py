import pandas as pd
from fpdf import FPDF
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# --- CONFIGURAÇÕES ---
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")

def enviar_relatorio():
    # 1. Carregar Dados
    df = pd.read_csv('Livro1.csv', sep=';')
    df['ocupacao_perc'] = (df['quartos_ocupados'] / df['capacidade']) * 100
    hoje = df.iloc[-1]
    
    # --- CÁLCULOS DE INTELIGÊNCIA ---
    # Sensibilidade: Se aumentarmos 10€, quanto cai a ocupação? (Simulação)
    sensibilidade = "Alta" if hoje['ocupacao_perc'] > 80 else "Média"
    
    # Benchmark: Comparação com o mercado (Simulado: Mercado está a 72%)
    mercado_avg = 72.0
    benchmark_status = "Acima" if hoje['ocupacao_perc'] > mercado_avg else "Abaixo"
    
    # Scoring Rate (0-100): Saúde do dia
    # Fórmula: (Ocupação * 0.7) + (Tendência * 0.3)
    scoring_rate = round((hoje['ocupacao_perc'] * 0.8) + 15, 1)

    # Lógica de Decisão
    if hoje['ocupacao_perc'] < 60:
        cor, rec, acao = "#e74c3c", "Baixar Preços 12%", "Criar Oferta Flash"
    elif hoje['ocupacao_perc'] > 85:
        cor, rec, acao = "#2ecc71", "Subir Preços 15%", "Maximizar ADR"
    else:
        cor, rec, acao = "#f1c40f", "Manter Estável", "Focar em Upselling"

    # --- CORPO DO EMAIL EM HTML ---
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: auto; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">
            <h2 style="color: #2c3e50; text-align: center;">🏨 InsightKube Revenue AI</h2>
            <p style="text-align: center; font-size: 14px; color: #7f8c8d;">Relatório de Performance: {hoje['data']}</p>
            <hr>
            
            <div style="background-color: {cor}; color: white; padding: 15px; border-radius: 5px; text-align: center; margin: 20px 0;">
                <h3 style="margin: 0;">RECOMENDAÇÃO: {rec}</h3>
                <p style="margin: 5px 0 0 0;">Ação: {acao}</p>
            </div>

            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;"><b>Scoring Rate:</b></td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right; color: #2980b9;"><b>{scoring_rate}/100</b></td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;"><b>Benchmark Mercado:</b></td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right;">{benchmark_status} da Média</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;"><b>Sensibilidade Preço:</b></td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right;">{sensibilidade}</td>
                </tr>
                <tr>
                    <td style="padding: 10px;"><b>Ocupação Atual:</b></td>
                    <td style="padding: 10px; text-align: right;">{hoje['ocupacao_perc']:.1f}%</td>
                </tr>
            </table>

            <p style="font-size: 12px; color: #95a5a6; margin-top: 20px; text-align: center;">
                Este relatório foi gerado automaticamente pelo Intelligent Core da InsightKube.
            </p>
        </div>
    </body>
    </html>
    """

    # --- ENVIO ---
    msg = MIMEMultipart()
    msg['Subject'] = f"📊 InsightKube: Relatório {hoje['data']} (Score: {scoring_rate})"
    msg['From'] = GMAIL_USER
    msg['To'] = GMAIL_USER
    msg.attach(MIMEText(html_body, 'html'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.send_message(msg)
    
    print("✅ Email Premium enviado!")

if __name__ == "__main__":
    enviar_relatorio()
