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

# Simulação de status para os outros departamentos (baseado no teu slide)
    status_custos = "⚠️ Margem Sob Pressão" if scoring_rate < 70 else "✅ Margem Estável"
    status_equipa = "✅ Eficiência Ótima" if hoje['ocupacao_perc'] < 90 else "⚠️ Sobrecarga"

    html_body = f"""
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; color: #333; line-height: 1.6;">
        <div style="max-width: 600px; margin: auto; border: 1px solid #eee; padding: 25px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
            <h2 style="color: #2c3e50; text-align: center; margin-bottom: 5px;">🏨 InsightKube Revenue AI</h2>
            <p style="text-align: center; font-size: 13px; color: #95a5a6; margin-top: 0;">Relatório Executivo • {hoje['data']}</p>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
            
            <div style="background-color: {cor}; color: white; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                <h3 style="margin: 0; font-size: 18px;">RECOMENDAÇÃO: {rec}</h3>
                <p style="margin: 8px 0 0 0; font-size: 15px; opacity: 0.9;">Próximo Passo: {acao}</p>
            </div>

            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <tr>
                    <td style="padding: 12px; border-bottom: 1px solid #f9f9f9;"><b>Scoring Rate:</b></td>
                    <td style="padding: 12px; border-bottom: 1px solid #f9f9f9; text-align: right; color: #2980b9; font-size: 18px;"><b>{scoring_rate}/100</b></td>
                </tr>
                <tr>
                    <td style="padding: 12px; border-bottom: 1px solid #f9f9f9;"><b>Benchmark Mercado:</b></td>
                    <td style="padding: 12px; border-bottom: 1px solid #f9f9f9; text-align: right;">{benchmark_status} da Média</td>
                </tr>
                <tr>
                    <td style="padding: 12px; border-bottom: 1px solid #f9f9f9;"><b>Sensibilidade Preço:</b></td>
                    <td style="padding: 12px; border-bottom: 1px solid #f9f9f9; text-align: right;">{sensibilidade}</td>
                </tr>
                <tr>
                    <td style="padding: 12px;"><b>Ocupação Atual:</b></td>
                    <td style="padding: 12px; text-align: right;">{hoje['ocupacao_perc']:.1f}%</td>
                </tr>
            </table>

            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 25px;">
                <p style="margin: 0 0 10px 0; font-weight: bold; font-size: 14px; color: #7f8c8d;">OUTROS INDICADORES:</p>
                <div style="font-size: 13px;">
                    <span style="display: inline-block; margin-right: 15px;">{status_custos}</span>
                    <span style="display: inline-block;">{status_equipa}</span>
                </div>
            </div>

            <div style="text-align: center;">
                <a href="https://insightcore-fdctr3i6ssvwyxwdzilc7b.streamlit.app" 
                   style="background-color: #2c3e50; color: white; padding: 15px 30px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block; font-size: 15px;">
                   Abrir Painel Completo na Plataforma →
                </a>
                <p style="font-size: 11px; color: #bdc3c7; margin-top: 15px;">
                    *Análise detalhada de Custos, Margens e Eficiência de Equipa disponível na App.
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    # --- ENVIO ---
    msg = MIMEMultipart()
    msg['Subject'] = f"InsightKube: Relatório {hoje['data']} (Score: {scoring_rate})"
    msg['From'] = GMAIL_USER
    msg['To'] = GMAIL_USER
    msg.attach(MIMEText(html_body, 'html'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.send_message(msg)
    
    print("Email Premium enviado!")

if __name__ == "__main__":
    enviar_relatorio()
