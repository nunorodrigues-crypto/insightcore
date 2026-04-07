"""
InsightKube — Auto Mailer v2
Lê dados do Google Sheets do cliente, calcula KPI de hotelaria,
e envia email diário rico com análise completa.

Variáveis de ambiente necessárias (GitHub Secrets):
  GMAIL_USER         — email remetente
  GMAIL_PASSWORD     — app password Gmail
  SHEET_URL_CLIENTE  — URL público do Google Sheets em CSV (um por cliente)
  CLIENTE_EMAIL      — email do cliente destinatário
  CLIENTE_NOME       — nome do alojamento
  MERCADO_AVG        — ocupação média do mercado (default: 72)
"""

import os, smtplib, requests
from io import StringIO
from datetime import datetime, timedelta
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ── CONFIG ──────────────────────────────────────────────────────────
GMAIL_USER      = os.getenv("GMAIL_USER")
GMAIL_PASSWORD  = os.getenv("GMAIL_PASSWORD")
SHEET_URL       = os.getenv("SHEET_URL_CLIENTE")        # URL CSV do Google Sheets
CLIENTE_EMAIL   = os.getenv("CLIENTE_EMAIL")
CLIENTE_NOME    = os.getenv("CLIENTE_NOME", "Alojamento")
MERCADO_AVG     = float(os.getenv("MERCADO_AVG", "72"))
APP_URL         = "https://insightcore-fdctr3i6ssvwyxwdzilc7b.streamlit.app"

# ── CORES ────────────────────────────────────────────────────────────
TEAL      = "#0F9E8A"
TEAL_DARK = "#085041"
YELLOW    = "#F5C518"
RED       = "#F85149"
GREEN     = "#3FB950"
DARK      = "#0D1117"
CARD_BG   = "#161B22"
BORDER    = "#30363D"

# ── CARREGAR DADOS ───────────────────────────────────────────────────
def carregar_dados():
    """Lê Google Sheets exportado como CSV público."""
    if SHEET_URL:
        # Converter URL do Sheets para CSV export
        if "spreadsheets/d/" in SHEET_URL:
            sheet_id = SHEET_URL.split("spreadsheets/d/")[1].split("/")[0]
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        else:
            csv_url = SHEET_URL
        resp = requests.get(csv_url, timeout=30)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.text))
    else:
        # Fallback local para testes
        df = pd.read_csv("Livro1.csv", sep=";")

    df.columns = df.columns.str.strip().str.lower()

    # Normalizar nomes de colunas comuns
    col_map = {
        "quartos_ocupados": ["quartos_ocupados", "rooms_occupied", "ocupados", "sold"],
        "capacidade":       ["capacidade", "capacity", "total_rooms", "rooms_available"],
        "preco_atual":      ["preco_atual", "adr", "price", "tarifa", "preco"],
        "data":             ["data", "date", "dia"],
    }
    for standard, variants in col_map.items():
        for v in variants:
            if v in df.columns and standard not in df.columns:
                df.rename(columns={v: standard}, inplace=True)
                break

    required = ["data", "quartos_ocupados", "capacidade", "preco_atual"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas em falta no Google Sheets: {missing}")

    df["data"] = pd.to_datetime(df["data"], dayfirst=True)
    df["quartos_ocupados"] = pd.to_numeric(df["quartos_ocupados"], errors="coerce")
    df["capacidade"]       = pd.to_numeric(df["capacidade"], errors="coerce")
    df["preco_atual"]      = pd.to_numeric(df["preco_atual"], errors="coerce")
    df.dropna(subset=required, inplace=True)
    df.sort_values("data", inplace=True)
    return df

# ── CALCULAR KPI ─────────────────────────────────────────────────────
def calcular_kpi(df):
    df = df.copy()
    df["ocupacao_perc"] = (df["quartos_ocupados"] / df["capacidade"]) * 100
    df["revpar"]        = df["preco_atual"] * (df["ocupacao_perc"] / 100)
    df["receita"]       = df["quartos_ocupados"] * df["preco_atual"]

    hoje       = df.iloc[-1]
    ontem      = df.iloc[-2] if len(df) > 1 else hoje
    sem_passada = df.iloc[-8] if len(df) > 7 else df.iloc[0]
    ultimos7   = df.tail(7)
    ultimos30  = df.tail(30)

    ocup       = hoje["ocupacao_perc"]
    adr        = hoje["preco_atual"]
    revpar     = hoje["revpar"]
    receita    = hoje["receita"]

    # Variações
    ocup_d     = ocup - ontem["ocupacao_perc"]
    adr_d      = adr - ontem["preco_atual"]
    revpar_d   = ((revpar - ontem["revpar"]) / ontem["revpar"] * 100) if ontem["revpar"] else 0

    # Médias
    ocup_7     = ultimos7["ocupacao_perc"].mean()
    ocup_30    = ultimos30["ocupacao_perc"].mean()
    adr_7      = ultimos7["preco_atual"].mean()
    revpar_7   = ultimos7["revpar"].mean()
    receita_7  = ultimos7["receita"].sum()
    receita_30 = ultimos30["receita"].sum()

    # Margem estimada (estrutura típica de AL/hotel pequeno)
    custo_fixo_pct  = 45   # % da receita em custos fixos
    custo_var_pct   = 15   # % da receita em custos variáveis
    margem          = max(5, 100 - custo_fixo_pct - custo_var_pct - max(0, (ocup - 75) * 0.2))
    custo_pessoal   = 32 + max(0, (ocup - 85) * 0.5)

    # Scores de risco
    health_score   = round(min(100, (ocup * 0.45) + (margem * 0.35) + 15), 0)
    revenue_risk   = round(max(0, (75 - ocup) * 1.3), 1) if ocup < 75 else max(0, round((ocup - 92) * 0.8, 1))
    churn_risk     = round(max(10, 55 - (ocup - 50) * 0.6), 1)

    # Sensibilidade de preço
    sens = "Alta" if ocup > 80 else "Média" if ocup > 60 else "Baixa"
    bench = "Acima" if ocup > MERCADO_AVG else "Abaixo"

    # Decisão
    if ocup < 55:
        rec, acao, cor_rec, urgencia = "Baixar Preços 12-15%", "Criar promoção flash no Booking/Airbnb para os próximos 3 dias", RED, "URGENTE"
    elif ocup < 70:
        rec, acao, cor_rec, urgencia = "Baixar Preços 8%", "Activar descontos de last-minute nos canais OTA", "#F5A623", "ATENÇÃO"
    elif ocup > 90:
        rec, acao, cor_rec, urgencia = "Subir Preços 15-20%", "Fechar canais externos — priorizar reservas directas e upselling", GREEN, "OPORTUNIDADE"
    elif ocup > 80:
        rec, acao, cor_rec, urgencia = "Subir Preços 8-10%", "Maximizar ADR — activar tarifas de fim de semana", TEAL, "OPORTUNIDADE"
    else:
        rec, acao, cor_rec, urgencia = "Manter Preço Estável", "Focar em upselling: early check-in, late check-out, serviços extras", YELLOW, "ESTÁVEL"

    # Alertas
    alertas = []
    if ocup < 60:
        alertas.append(("red", "🔴 Ocupação crítica", f"Ocupação de {ocup:.1f}% está abaixo do limiar de rentabilidade (60%). Acção imediata necessária."))
    if abs(ocup_d) > 10:
        tipo = "red" if ocup_d < 0 else "green"
        alertas.append((tipo, f"{'📉' if ocup_d<0 else '📈'} Variação brusca", f"Ocupação variou {ocup_d:+.1f}pp face a ontem. Verificar cancelamentos ou reservas de grupo."))
    if custo_pessoal > 42:
        alertas.append(("yellow", "⚠️ Custo de pessoal elevado", f"Rácio pessoal/faturação estimado em {custo_pessoal:.1f}% — acima do benchmark de 38%."))
    if ocup < MERCADO_AVG - 10:
        alertas.append(("yellow", "📊 Abaixo do mercado", f"Ocupação {MERCADO_AVG - ocup:.1f}pp abaixo da média de mercado ({MERCADO_AVG}%). Rever estratégia de pricing."))
    alertas.append(("yellow", "🌍 Pressão externa", "Guerra no Golfo: combustíveis +10 cêntimos, peixe e carne +6%, transportes +10%. Impacto nos custos operacionais."))
    if not alertas:
        alertas.append(("green", "✅ Tudo normal", "Todos os indicadores dentro dos parâmetros esperados. Continuar a monitorizar."))

    return {
        "hoje_fmt":    hoje["data"].strftime("%d/%m/%Y"),
        "dia_semana":  hoje["data"].strftime("%A"),
        "ocup": ocup, "adr": adr, "revpar": revpar, "receita": receita,
        "ocup_d": ocup_d, "adr_d": adr_d, "revpar_d": revpar_d,
        "ocup_7": ocup_7, "ocup_30": ocup_30,
        "adr_7": adr_7, "revpar_7": revpar_7,
        "receita_7": receita_7, "receita_30": receita_30,
        "margem": margem, "custo_pessoal": custo_pessoal,
        "health_score": health_score, "revenue_risk": revenue_risk, "churn_risk": churn_risk,
        "sens": sens, "bench": bench,
        "rec": rec, "acao": acao, "cor_rec": cor_rec, "urgencia": urgencia,
        "alertas": alertas,
        "df": df,
    }

# ── MINI SPARKLINE EM ASCII ──────────────────────────────────────────
def sparkline(values, width=20):
    if len(values) < 2:
        return "—"
    mn, mx = min(values), max(values)
    rng = mx - mn if mx != mn else 1
    chars = "▁▂▃▄▅▆▇█"
    bars = [chars[int((v - mn) / rng * 7)] for v in values]
    return "".join(bars[-width:])

# ── CONSTRUIR EMAIL HTML ─────────────────────────────────────────────
def build_email(k):
    hoje = k["hoje_fmt"]
    spark_ocup  = sparkline(k["df"].tail(14)["ocupacao_perc"].tolist())
    spark_revpar = sparkline(k["df"].tail(14)["revpar"].tolist())

    def delta_badge(val, unit="pp", inverse=False):
        pos = val >= 0 if not inverse else val <= 0
        col = GREEN if pos else RED
        arrow = "▲" if val >= 0 else "▼"
        return f'<span style="color:{col};font-size:13px;font-weight:600">{arrow} {abs(val):.1f}{unit}</span>'

    def health_color(score):
        if score >= 70: return GREEN
        if score >= 50: return YELLOW
        return RED

    def risk_color(risk):
        if risk < 20: return GREEN
        if risk < 40: return YELLOW
        return RED

    alertas_html = ""
    for tipo, titulo, texto in k["alertas"]:
        border = {"red": RED, "green": GREEN, "yellow": YELLOW}.get(tipo, TEAL)
        alertas_html += f"""
        <tr>
          <td style="padding:8px 0">
            <div style="border-left:4px solid {border};padding:10px 14px;background:#1C1F26;border-radius:0 6px 6px 0">
              <div style="font-size:13px;font-weight:700;color:#E6EDF3;margin-bottom:3px">{titulo}</div>
              <div style="font-size:12px;color:#8B949E">{texto}</div>
            </div>
          </td>
        </tr>"""

    # KPI rows para tabela
    kpi_rows = [
        ("Ocupação hoje",    f"{k['ocup']:.1f}%",    delta_badge(k['ocup_d'])),
        ("ADR (preço médio)",f"{k['adr']:.0f}€",     delta_badge(k['adr_d'], "€")),
        ("RevPAR",           f"{k['revpar']:.0f}€",  delta_badge(k['revpar_d'], "%")),
        ("Receita do dia",   f"{k['receita']:.0f}€", ""),
        ("Ocupação 7 dias",  f"{k['ocup_7']:.1f}%",  f'<span style="color:#8B949E;font-size:12px">média</span>'),
        ("Receita 7 dias",   f"{k['receita_7']:.0f}€",""),
        ("Receita 30 dias",  f"{k['receita_30']:.0f}€",""),
        ("Benchmark mercado",f"{k['bench']} ({MERCADO_AVG:.0f}%)", ""),
        ("Margem estimada",  f"{k['margem']:.1f}%",  ""),
        ("Custo pessoal",    f"{k['custo_pessoal']:.1f}%", ""),
    ]
    kpi_html = ""
    for i, (label, val, extra) in enumerate(kpi_rows):
        bg = "#161B22" if i % 2 == 0 else "#1C1F26"
        kpi_html += f"""
        <tr style="background:{bg}">
          <td style="padding:10px 14px;font-size:13px;color:#8B949E;border-bottom:1px solid #30363D">{label}</td>
          <td style="padding:10px 14px;font-size:14px;font-weight:700;color:#E6EDF3;text-align:right;border-bottom:1px solid #30363D">{val}</td>
          <td style="padding:10px 14px;text-align:right;border-bottom:1px solid #30363D">{extra}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0D1117;font-family:'Segoe UI',Arial,sans-serif;color:#E6EDF3">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0D1117;padding:20px 0">
<tr><td align="center">
<table width="620" cellpadding="0" cellspacing="0" style="max-width:620px;width:100%">

  <!-- HEADER -->
  <tr><td style="background:linear-gradient(90deg,{TEAL} 0%,{TEAL_DARK} 100%);padding:22px 28px;border-radius:12px 12px 0 0">
    <table width="100%"><tr>
      <td>
        <div style="font-size:22px;font-weight:800;color:#fff">
          <span style="color:#fff">Insight</span><span style="color:{YELLOW}">Kube</span>
        </div>
        <div style="font-size:12px;color:#A8D5CE;margin-top:3px">Business powered by Data · Relatório Diário</div>
      </td>
      <td align="right">
        <div style="font-size:13px;color:#fff;font-weight:600">{CLIENTE_NOME}</div>
        <div style="font-size:11px;color:#A8D5CE">{hoje} · {k["dia_semana"]}</div>
      </td>
    </tr></table>
  </td></tr>

  <!-- HEALTH SCORE BANNER -->
  <tr><td style="background:#161B22;padding:20px 28px;border-bottom:1px solid {BORDER}">
    <table width="100%"><tr>
      <td width="80">
        <div style="width:70px;height:70px;border-radius:50%;background:{DARK};border:4px solid {health_color(k['health_score'])};display:flex;align-items:center;justify-content:center;text-align:center;padding-top:14px">
          <div style="font-size:24px;font-weight:800;color:{health_color(k['health_score'])}">{k['health_score']:.0f}</div>
          <div style="font-size:9px;color:#8B949E;margin-top:-4px">SCORE</div>
        </div>
      </td>
      <td style="padding-left:18px">
        <div style="font-size:11px;color:#8B949E;text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px">Health Score do dia</div>
        <div style="font-size:15px;font-weight:700;color:#E6EDF3">
          {"✅ Negócio saudável" if k['health_score']>=70 else "⚠️ Atenção necessária" if k['health_score']>=50 else "🔴 Situação crítica"}
        </div>
        <div style="font-size:12px;color:#8B949E;margin-top:3px">
          Revenue Risk: <span style="color:{risk_color(k['revenue_risk'])};font-weight:600">{k['revenue_risk']:.1f}%</span> &nbsp;|&nbsp;
          Churn Risk: <span style="color:{risk_color(k['churn_risk'])};font-weight:600">{k['churn_risk']:.1f}%</span> &nbsp;|&nbsp;
          Sensibilidade: <span style="color:{YELLOW};font-weight:600">{k['sens']}</span>
        </div>
      </td>
    </tr></table>
  </td></tr>

  <!-- DECISÃO DO DIA -->
  <tr><td style="background:{CARD_BG};padding:20px 28px;border-left:4px solid {k['cor_rec']};border-bottom:1px solid {BORDER}">
    <div style="font-size:10px;color:{k['cor_rec']};text-transform:uppercase;letter-spacing:.1em;font-weight:700;margin-bottom:6px">
      🎯 DECISÃO DO DIA — {k['urgencia']}
    </div>
    <div style="font-size:20px;font-weight:800;color:{k['cor_rec']};margin-bottom:6px">{k['rec']}</div>
    <div style="font-size:13px;color:#A8D5CE">▶ Acção imediata: {k['acao']}</div>
  </td></tr>

  <!-- KPI CARDS 4x -->
  <tr><td style="background:{DARK};padding:16px 28px;border-bottom:1px solid {BORDER}">
    <table width="100%" cellspacing="8"><tr>
      <td width="25%" style="background:{CARD_BG};border:1px solid {BORDER};border-radius:8px;padding:14px;text-align:center">
        <div style="font-size:10px;color:#8B949E;text-transform:uppercase;margin-bottom:4px">Ocupação</div>
        <div style="font-size:26px;font-weight:800;color:{'#3FB950' if k['ocup']>75 else '#F85149' if k['ocup']<60 else '#F5C518'}">{k['ocup']:.1f}%</div>
        <div style="font-size:11px;color:#8B949E">{delta_badge(k['ocup_d'])} vs ontem</div>
        <div style="font-size:11px;color:#555;margin-top:4px;letter-spacing:1px">{spark_ocup}</div>
      </td>
      <td width="25%" style="background:{CARD_BG};border:1px solid {BORDER};border-radius:8px;padding:14px;text-align:center">
        <div style="font-size:10px;color:#8B949E;text-transform:uppercase;margin-bottom:4px">ADR</div>
        <div style="font-size:26px;font-weight:800;color:{TEAL}">{k['adr']:.0f}€</div>
        <div style="font-size:11px;color:#8B949E">{delta_badge(k['adr_d'], '€')} vs ontem</div>
        <div style="font-size:11px;color:#8B949E;margin-top:4px">7d: {k['adr_7']:.0f}€</div>
      </td>
      <td width="25%" style="background:{CARD_BG};border:1px solid {BORDER};border-radius:8px;padding:14px;text-align:center">
        <div style="font-size:10px;color:#8B949E;text-transform:uppercase;margin-bottom:4px">RevPAR</div>
        <div style="font-size:26px;font-weight:800;color:{YELLOW}">{k['revpar']:.0f}€</div>
        <div style="font-size:11px;color:#8B949E">{delta_badge(k['revpar_d'], '%')} vs ontem</div>
        <div style="font-size:11px;color:#555;margin-top:4px;letter-spacing:1px">{spark_revpar}</div>
      </td>
      <td width="25%" style="background:{CARD_BG};border:1px solid {BORDER};border-radius:8px;padding:14px;text-align:center">
        <div style="font-size:10px;color:#8B949E;text-transform:uppercase;margin-bottom:4px">Receita dia</div>
        <div style="font-size:26px;font-weight:800;color:#E6EDF3">{k['receita']:.0f}€</div>
        <div style="font-size:11px;color:#8B949E">7d: {k['receita_7']:.0f}€</div>
        <div style="font-size:11px;color:#8B949E;margin-top:2px">30d: {k['receita_30']:.0f}€</div>
      </td>
    </tr></table>
  </td></tr>

  <!-- ALERTAS -->
  <tr><td style="background:{DARK};padding:0 28px 8px 28px">
    <div style="font-size:11px;color:#8B949E;text-transform:uppercase;letter-spacing:.06em;padding:16px 0 8px 0;font-weight:600">Alertas do dia</div>
    <table width="100%">{alertas_html}</table>
  </td></tr>

  <!-- KPI TABELA COMPLETA -->
  <tr><td style="background:{DARK};padding:0 28px 8px 28px">
    <div style="font-size:11px;color:#8B949E;text-transform:uppercase;letter-spacing:.06em;padding:16px 0 8px 0;font-weight:600">Análise completa</div>
    <table width="100%" style="border:1px solid {BORDER};border-radius:8px;overflow:hidden;border-collapse:collapse">
      {kpi_html}
    </table>
  </td></tr>

  <!-- BENCHMARK -->
  <tr><td style="background:{CARD_BG};padding:16px 28px;border:1px solid {BORDER};border-radius:8px;margin:0 28px">
  </td></tr>
  <tr><td style="background:{DARK};padding:8px 28px 16px 28px">
    <table width="100%" style="background:{CARD_BG};border:1px solid {BORDER};border-radius:8px;padding:16px">
    <tr><td colspan="3" style="padding:12px 14px 6px 14px">
      <div style="font-size:11px;color:#8B949E;text-transform:uppercase;letter-spacing:.06em;font-weight:600">Benchmark de Mercado</div>
    </td></tr>
    <tr>
      <td style="padding:8px 14px;text-align:center">
        <div style="font-size:11px;color:#8B949E">O seu negócio</div>
        <div style="font-size:22px;font-weight:800;color:{TEAL}">{k['ocup']:.1f}%</div>
      </td>
      <td style="padding:8px 14px;text-align:center">
        <div style="font-size:20px;font-weight:800;color:{'#3FB950' if k['bench']=='Acima' else '#F85149'}">{k['bench']}</div>
        <div style="font-size:11px;color:#8B949E">do mercado</div>
      </td>
      <td style="padding:8px 14px;text-align:center">
        <div style="font-size:11px;color:#8B949E">Média mercado</div>
        <div style="font-size:22px;font-weight:800;color:#8B949E">{MERCADO_AVG:.0f}%</div>
      </td>
    </tr>
    </table>
  </td></tr>

  <!-- CTA BUTTON -->
  <tr><td style="background:{DARK};padding:16px 28px 24px 28px;text-align:center">
    <a href="{APP_URL}"
       style="display:inline-block;background:linear-gradient(90deg,{TEAL} 0%,{TEAL_DARK} 100%);color:#fff;padding:16px 36px;text-decoration:none;border-radius:8px;font-weight:700;font-size:15px;letter-spacing:.02em">
      📊 Abrir Análise Completa na Plataforma →
    </a>
    <div style="font-size:11px;color:#555;margin-top:10px">
      Gráficos · Tendências · Revenue Intelligence · Lifecycle Intelligence
    </div>
  </td></tr>

  <!-- FOOTER -->
  <tr><td style="background:#161B22;padding:16px 28px;border-radius:0 0 12px 12px;border-top:1px solid {BORDER}">
    <table width="100%"><tr>
      <td><div style="font-size:11px;color:#555">InsightKube · Business powered by Data</div></td>
      <td align="right"><div style="font-size:11px;color:#555">Relatório gerado automaticamente · {hoje}</div></td>
    </tr></table>
  </td></tr>

</table>
</td></tr></table>
</body></html>"""
    return html


# ── ENVIAR EMAIL ─────────────────────────────────────────────────────
def enviar_email(html, kpi):
    score = kpi["health_score"]
    ocup  = kpi["ocup"]
    hoje  = kpi["hoje_fmt"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"InsightKube · {CLIENTE_NOME} · {hoje} · Score {score:.0f}/100 · Ocup. {ocup:.1f}%"
    msg["From"]    = f"InsightKube <{GMAIL_USER}>"
    msg["To"]      = CLIENTE_EMAIL

    # Versão texto simples
    texto = f"""InsightKube — Relatório Diário
{CLIENTE_NOME} · {hoje}

Health Score: {score:.0f}/100
Ocupação: {ocup:.1f}%
ADR: {kpi['adr']:.0f}€
RevPAR: {kpi['revpar']:.0f}€
Receita: {kpi['receita']:.0f}€

Decisão do dia: {kpi['rec']}
Acção: {kpi['acao']}

Ver análise completa: {APP_URL}

InsightKube · Business powered by Data
"""
    msg.attach(MIMEText(texto, "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.send_message(msg)

    print(f"✅ Email enviado para {CLIENTE_EMAIL} — Score: {score:.0f} | Ocup: {ocup:.1f}%")


# ── MAIN ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("InsightKube Auto Mailer v2 — a iniciar...")

    df   = carregar_dados()
    print(f"✅ Dados carregados: {len(df)} registos")

    kpi  = calcular_kpi(df)
    print(f"✅ KPI calculados — Score: {kpi['health_score']:.0f} | Ocup: {kpi['ocup']:.1f}%")

    html = build_email(kpi)
    enviar_email(html, kpi)
