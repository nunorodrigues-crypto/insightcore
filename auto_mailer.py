"""
InsightKube — Auto Mailer v3 com Gemini AI
Calcula KPI de hotelaria e usa Gemini para interpretação inteligente.

GitHub Secrets necessários:
  GMAIL_USER, GMAIL_PASSWORD
  SHEET_URL_CLIENTE, CLIENTE_EMAIL, CLIENTE_NOME
  GEMINI_API_KEY
  MERCADO_AVG (opcional, default 72)
"""

import os, smtplib, requests, json
from io import StringIO
from datetime import datetime
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ── CONFIG ──────────────────────────────────────────────────────────
GMAIL_USER     = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")
SHEET_URL      = os.getenv("SHEET_URL_CLIENTE")
CLIENTE_EMAIL  = os.getenv("CLIENTE_EMAIL")
CLIENTE_NOME   = os.getenv("CLIENTE_NOME", "Alojamento")
MERCADO_AVG    = float(os.getenv("MERCADO_AVG", "72"))
GEMINI_API_KEY = os.getenv("AIzaSyC_bzk-cFi5SxJQrI1G3WmPT63Pi1bQrAE")
APP_URL        = "https://insightcore-fdctr3i6ssvwyxwdzilc7b.streamlit.app"

TEAL="0F9E8A"; TEAL_DARK="085041"; YELLOW="F5C518"
RED="F85149"; GREEN="3FB950"; DARK="0D1117"; CARD_BG="161B22"; BORDER="30363D"

# ── CARREGAR DADOS ───────────────────────────────────────────────────
def carregar_dados():
    if SHEET_URL:
        if "spreadsheets/d/" in SHEET_URL:
            sid = SHEET_URL.split("spreadsheets/d/")[1].split("/")[0]
            url = f"https://docs.google.com/spreadsheets/d/1WIHg5olaxpAD0hVw59ttC5HoEycObPM0_4c0p6gucpo/edit?gid=0#gid=0"
        else:
            url = SHEET_URL
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.text))
    else:
        df = pd.read_csv("Livro1.csv", sep=";")

    df.columns = df.columns.str.strip().str.lower()
    col_map = {
        "quartos_ocupados": ["quartos_ocupados","rooms_occupied","ocupados","sold"],
        "capacidade":       ["capacidade","capacity","total_rooms","rooms_available"],
        "preco_atual":      ["preco_atual","adr","price","tarifa","preco"],
        "data":             ["data","date","dia"],
    }
    for std, variants in col_map.items():
        for v in variants:
            if v in df.columns and std not in df.columns:
                df.rename(columns={v: std}, inplace=True)
                break

    df["data"] = pd.to_datetime(df["data"], format="mixed", dayfirst=False)
    for col in ["capacidade", "preco_atual"]:
        df[col] = (df[col].astype(str)
                   .str.replace("€","",regex=False).str.replace("\xa0","",regex=False)
                   .str.replace("\u202f","",regex=False).str.strip()
                   .str.replace(r"\s+","",regex=True).str.replace(",",".",regex=False))
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["quartos_ocupados"] = pd.to_numeric(df["quartos_ocupados"], errors="coerce")
    df.dropna(subset=["data","quartos_ocupados","capacidade","preco_atual"], inplace=True)
    df.sort_values("data", inplace=True)
    return df

# ── CALCULAR KPI ─────────────────────────────────────────────────────
def calcular_kpi(df):
    df = df.copy()
    df["ocupacao_perc"] = (df["quartos_ocupados"] / df["capacidade"]) * 100
    df["revpar"]        = df["preco_atual"] * (df["ocupacao_perc"] / 100)
    df["receita"]       = df["quartos_ocupados"] * df["preco_atual"]

    hoje    = df.iloc[-1]
    ontem   = df.iloc[-2] if len(df) > 1 else hoje
    u7      = df.tail(7)
    u30     = df.tail(30)

    ocup    = hoje["ocupacao_perc"]
    adr     = hoje["preco_atual"]
    revpar  = hoje["revpar"]
    receita = hoje["receita"]

    ocup_d  = ocup - ontem["ocupacao_perc"]
    adr_d   = adr  - ontem["preco_atual"]
    revpar_d = ((revpar - ontem["revpar"]) / ontem["revpar"] * 100) if ontem["revpar"] else 0

    ocup_7    = u7["ocupacao_perc"].mean()
    ocup_30   = u30["ocupacao_perc"].mean()
    adr_7     = u7["preco_atual"].mean()
    revpar_7  = u7["revpar"].mean()
    rec_7     = u7["receita"].sum()
    rec_30    = u30["receita"].sum()
    tendencia = "subida" if u7["ocupacao_perc"].iloc[-1] > u7["ocupacao_perc"].iloc[0] else "descida" if u7["ocupacao_perc"].iloc[-1] < u7["ocupacao_perc"].iloc[0] else "estável"

    health_score = round(min(100, (ocup * 0.5) + 20), 0)
    revenue_risk = round(max(0, (75 - ocup) * 1.3), 1) if ocup < 75 else max(0, round((ocup - 92) * 0.8, 1))

    return {
        "hoje_fmt":   hoje["data"].strftime("%d/%m/%Y"),
        "dia_semana": hoje["data"].strftime("%A"),
        "ocup": ocup, "adr": adr, "revpar": revpar, "receita": receita,
        "ocup_d": ocup_d, "adr_d": adr_d, "revpar_d": revpar_d,
        "ocup_7": ocup_7, "ocup_30": ocup_30,
        "adr_7": adr_7, "revpar_7": revpar_7,
        "rec_7": rec_7, "rec_30": rec_30,
        "tendencia": tendencia,
        "health_score": health_score,
        "revenue_risk": revenue_risk,
        "benchmark": "Acima" if ocup > MERCADO_AVG else "Abaixo",
        "df": df,
    }

# ── GEMINI AI — INTERPRETAÇÃO ────────────────────────────────────────
def interpretar_com_gemini(k):
    """Envia os KPI ao Gemini e pede análise inteligente em JSON."""

    prompt = f"""És o analista sénior da InsightKube, uma consultoria de dados para hotelaria.
Analisa os seguintes KPI do alojamento "{CLIENTE_NOME}" para o dia {k['hoje_fmt']} e responde APENAS com um objecto JSON válido, sem texto antes ou depois, sem markdown, sem backticks.

KPI DO DIA:
- Ocupação: {k['ocup']:.1f}% (variação vs ontem: {k['ocup_d']:+.1f}pp)
- ADR (preço médio): {k['adr']:.0f}€ (variação: {k['adr_d']:+.1f}€)
- RevPAR: {k['revpar']:.0f}€ (variação: {k['revpar_d']:+.1f}%)
- Receita do dia: {k['receita']:.0f}€
- Ocupação média 7 dias: {k['ocup_7']:.1f}%
- Ocupação média 30 dias: {k['ocup_30']:.1f}%
- Receita 7 dias: {k['rec_7']:.0f}€
- Receita 30 dias: {k['rec_30']:.0f}€
- Tendência da semana: {k['tendencia']}
- Benchmark de mercado: {k['benchmark']} da média ({MERCADO_AVG:.0f}%)
- Health Score: {k['health_score']:.0f}/100
- Revenue Risk: {k['revenue_risk']:.1f}%
- Dia da semana: {k['dia_semana']}

Contexto de mercado: Guerra no Golfo está a pressionar custos — combustíveis +10 cêntimos, transportes +10%, fornecedores alimentares +6%.

Responde com este JSON exacto:
{{
  "decisao_titulo": "frase curta e directa com a recomendação principal (máx 8 palavras)",
  "decisao_acao": "acção concreta e específica que o gestor deve tomar hoje (máx 20 palavras)",
  "urgencia": "URGENTE|ATENÇÃO|OPORTUNIDADE|ESTÁVEL",
  "cor_hex": "#F85149|#F5A623|#3FB950|#F5C518",
  "analise_narrativa": "parágrafo de 3-4 frases com análise aprofundada: o que está a acontecer, porquê, e o que significa para o negócio. Tom profissional mas directo.",
  "alertas": [
    {{"tipo": "red|yellow|green", "titulo": "título curto", "texto": "explicação de 1-2 frases"}},
    {{"tipo": "red|yellow|green", "titulo": "título curto", "texto": "explicação de 1-2 frases"}},
    {{"tipo": "red|yellow|green", "titulo": "título curto", "texto": "explicação de 1-2 frases"}}
  ],
  "insight_semana": "observação inteligente sobre a tendência da semana (1-2 frases)",
  "previsao_amanha": "previsão breve para amanhã baseada nos padrões identificados (1 frase)"
}}"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1000}
    }

    try:
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        texto = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        # Limpar markdown se existir
        texto = texto.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(texto)
    except Exception as e:
        print(f"⚠️ Gemini falhou ({e}) — usando fallback")
        return fallback_analise(k)

def fallback_analise(k):
    """Análise de fallback se Gemini falhar."""
    ocup = k["ocup"]
    if ocup < 55:
        dec, acao, urg, cor = "Baixar Preços 12-15% — Urgente", "Criar promoção flash no Booking/Airbnb para os próximos 3 dias", "URGENTE", f"#{RED}"
    elif ocup < 70:
        dec, acao, urg, cor = "Baixar Preços 8% — Procura Fraca", "Activar descontos last-minute nos canais OTA", "ATENÇÃO", "#F5A623"
    elif ocup > 90:
        dec, acao, urg, cor = "Subir Preços 15-20% — Alta Procura", "Fechar canais externos e priorizar venda directa", "OPORTUNIDADE", f"#{GREEN}"
    elif ocup > 80:
        dec, acao, urg, cor = "Subir Preços 8-10% — Boa Procura", "Maximizar ADR e activar tarifas de fim de semana", "OPORTUNIDADE", f"#{TEAL}"
    else:
        dec, acao, urg, cor = "Manter Preço Estável", "Focar em upselling: early check-in e serviços extras", "ESTÁVEL", f"#{YELLOW}"
    return {
        "decisao_titulo": dec, "decisao_acao": acao, "urgencia": urg, "cor_hex": cor,
        "analise_narrativa": f"Ocupação de {ocup:.1f}% com tendência {k['tendencia']}. RevPAR de {k['revpar']:.0f}€. A monitorizar.",
        "alertas": [{"tipo": "yellow", "titulo": "🌍 Pressão de custos", "texto": "Guerra no Golfo: combustíveis e fornecedores sob pressão. Monitorizar margens."}],
        "insight_semana": f"Ocupação média de {k['ocup_7']:.1f}% nos últimos 7 dias.",
        "previsao_amanha": "Continuar a monitorizar os padrões de reserva."
    }

# ── SPARKLINE ────────────────────────────────────────────────────────
def sparkline(values):
    if len(values) < 2: return "—"
    mn, mx = min(values), max(values)
    rng = mx - mn if mx != mn else 1
    chars = "▁▂▃▄▅▆▇█"
    return "".join(chars[int((v-mn)/rng*7)] for v in values[-14:])

# ── BUILD EMAIL ──────────────────────────────────────────────────────
def build_email(k, ai):
    hoje = k["hoje_fmt"]
    spark_o = sparkline(k["df"]["ocupacao_perc"].tolist())
    spark_r = sparkline(k["df"]["revpar"].tolist())

    def delta_badge(val, unit="pp"):
        col = f"#{GREEN}" if val >= 0 else f"#{RED}"
        arrow = "▲" if val >= 0 else "▼"
        return f'<span style="color:{col};font-size:13px;font-weight:600">{arrow} {abs(val):.1f}{unit}</span>'

    def hcol(s): return f"#{GREEN}" if s>=70 else f"#{YELLOW}" if s>=50 else f"#{RED}"

    alertas_html = ""
    for a in ai.get("alertas", []):
        border = {"red": f"#{RED}", "green": f"#{GREEN}", "yellow": f"#{YELLOW}"}.get(a["tipo"], f"#{TEAL}")
        alertas_html += f"""
        <tr><td style="padding:6px 0">
          <div style="border-left:4px solid {border};padding:10px 14px;background:#1C1F26;border-radius:0 6px 6px 0">
            <div style="font-size:13px;font-weight:700;color:#E6EDF3;margin-bottom:3px">{a['titulo']}</div>
            <div style="font-size:12px;color:#8B949E">{a['texto']}</div>
          </div>
        </td></tr>"""

    kpi_rows = [
        ("Ocupação hoje",     f"{k['ocup']:.1f}%",   delta_badge(k['ocup_d'])),
        ("ADR",               f"{k['adr']:.0f}€",    delta_badge(k['adr_d'], "€")),
        ("RevPAR",            f"{k['revpar']:.0f}€", delta_badge(k['revpar_d'], "%")),
        ("Receita do dia",    f"{k['receita']:.0f}€",""),
        ("Ocupação 7 dias",   f"{k['ocup_7']:.1f}%", "média"),
        ("Ocupação 30 dias",  f"{k['ocup_30']:.1f}%","média"),
        ("Receita 7 dias",    f"{k['rec_7']:.0f}€",  ""),
        ("Receita 30 dias",   f"{k['rec_30']:.0f}€", ""),
        ("Benchmark mercado", k['benchmark'],         f"{MERCADO_AVG:.0f}% média"),
        ("Tendência semana",  k['tendencia'].upper(), ""),
    ]
    kpi_html = ""
    for i, (label, val, extra) in enumerate(kpi_rows):
        bg = f"#{CARD_BG}" if i%2==0 else "#1C1F26"
        kpi_html += f"""
        <tr style="background:{bg}">
          <td style="padding:10px 14px;font-size:13px;color:#8B949E;border-bottom:1px solid #{BORDER}">{label}</td>
          <td style="padding:10px 14px;font-size:14px;font-weight:700;color:#E6EDF3;text-align:right;border-bottom:1px solid #{BORDER}">{val}</td>
          <td style="padding:10px 14px;font-size:12px;color:#8B949E;text-align:right;border-bottom:1px solid #{BORDER}">{extra}</td>
        </tr>"""

    cor_dec = ai.get("cor_hex", f"#{TEAL}")

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#{DARK};font-family:'Segoe UI',Arial,sans-serif;color:#E6EDF3">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#{DARK};padding:20px 0">
<tr><td align="center">
<table width="620" cellpadding="0" cellspacing="0" style="max-width:620px;width:100%">

  <tr><td style="background:linear-gradient(90deg,#{TEAL} 0%,#{TEAL_DARK} 100%);padding:22px 28px;border-radius:12px 12px 0 0">
    <table width="100%"><tr>
      <td><div style="font-size:22px;font-weight:800;color:#fff">Insight<span style="color:#{YELLOW}">Kube</span></div>
          <div style="font-size:12px;color:#A8D5CE;margin-top:3px">Business powered by Data · Relatório Diário</div></td>
      <td align="right"><div style="font-size:13px;color:#fff;font-weight:600">{CLIENTE_NOME}</div>
          <div style="font-size:11px;color:#A8D5CE">{hoje} · {k['dia_semana']}</div></td>
    </tr></table>
  </td></tr>

  <tr><td style="background:#{CARD_BG};padding:20px 28px;border-bottom:1px solid #{BORDER}">
    <table width="100%"><tr>
      <td width="80" style="text-align:center">
        <div style="font-size:42px;font-weight:800;color:{hcol(k['health_score'])}">{k['health_score']:.0f}</div>
        <div style="font-size:9px;color:#8B949E;text-transform:uppercase">Health Score</div>
      </td>
      <td style="padding-left:18px">
        <div style="font-size:11px;color:#8B949E;text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px">Análise InsightKube · AI</div>
        <div style="font-size:14px;color:#E6EDF3;line-height:1.5">{ai.get('analise_narrativa','')}</div>
      </td>
    </tr></table>
  </td></tr>

  <tr><td style="background:#{CARD_BG};padding:20px 28px;border-left:4px solid {cor_dec};border-bottom:1px solid #{BORDER}">
    <div style="font-size:10px;color:{cor_dec};text-transform:uppercase;letter-spacing:.1em;font-weight:700;margin-bottom:6px">
      🎯 DECISÃO DO DIA — {ai.get('urgencia','ESTÁVEL')}
    </div>
    <div style="font-size:20px;font-weight:800;color:{cor_dec};margin-bottom:6px">{ai.get('decisao_titulo','')}</div>
    <div style="font-size:13px;color:#A8D5CE">▶ {ai.get('decisao_acao','')}</div>
  </td></tr>

  <tr><td style="background:#{DARK};padding:16px 28px;border-bottom:1px solid #{BORDER}">
    <table width="100%" cellspacing="8"><tr>
      <td width="25%" style="background:#{CARD_BG};border:1px solid #{BORDER};border-radius:8px;padding:14px;text-align:center">
        <div style="font-size:10px;color:#8B949E;text-transform:uppercase;margin-bottom:4px">Ocupação</div>
        <div style="font-size:26px;font-weight:800;color:{'#3FB950' if k['ocup']>75 else '#F85149' if k['ocup']<60 else '#F5C518'}">{k['ocup']:.1f}%</div>
        <div style="font-size:11px;color:#8B949E">{delta_badge(k['ocup_d'])} vs ontem</div>
        <div style="font-size:11px;color:#555;margin-top:4px;letter-spacing:1px">{spark_o}</div>
      </td>
      <td width="25%" style="background:#{CARD_BG};border:1px solid #{BORDER};border-radius:8px;padding:14px;text-align:center">
        <div style="font-size:10px;color:#8B949E;text-transform:uppercase;margin-bottom:4px">ADR</div>
        <div style="font-size:26px;font-weight:800;color:#{TEAL}">{k['adr']:.0f}€</div>
        <div style="font-size:11px;color:#8B949E">{delta_badge(k['adr_d'],'€')} vs ontem</div>
        <div style="font-size:11px;color:#8B949E;margin-top:4px">7d: {k['adr_7']:.0f}€</div>
      </td>
      <td width="25%" style="background:#{CARD_BG};border:1px solid #{BORDER};border-radius:8px;padding:14px;text-align:center">
        <div style="font-size:10px;color:#8B949E;text-transform:uppercase;margin-bottom:4px">RevPAR</div>
        <div style="font-size:26px;font-weight:800;color:#{YELLOW}">{k['revpar']:.0f}€</div>
        <div style="font-size:11px;color:#8B949E">{delta_badge(k['revpar_d'],'%')} vs ontem</div>
        <div style="font-size:11px;color:#555;margin-top:4px;letter-spacing:1px">{spark_r}</div>
      </td>
      <td width="25%" style="background:#{CARD_BG};border:1px solid #{BORDER};border-radius:8px;padding:14px;text-align:center">
        <div style="font-size:10px;color:#8B949E;text-transform:uppercase;margin-bottom:4px">Receita dia</div>
        <div style="font-size:26px;font-weight:800;color:#E6EDF3">{k['receita']:.0f}€</div>
        <div style="font-size:11px;color:#8B949E">7d: {k['rec_7']:.0f}€</div>
        <div style="font-size:11px;color:#8B949E;margin-top:2px">30d: {k['rec_30']:.0f}€</div>
      </td>
    </tr></table>
  </td></tr>

  <tr><td style="background:#{DARK};padding:0 28px 8px 28px">
    <div style="font-size:11px;color:#8B949E;text-transform:uppercase;letter-spacing:.06em;padding:16px 0 8px 0;font-weight:600">Alertas do dia</div>
    <table width="100%">{alertas_html}</table>
  </td></tr>

  <tr><td style="background:#{DARK};padding:0 28px 8px 28px">
    <div style="font-size:11px;color:#8B949E;text-transform:uppercase;letter-spacing:.06em;padding:16px 0 8px 0;font-weight:600">Análise completa</div>
    <table width="100%" style="border:1px solid #{BORDER};border-radius:8px;overflow:hidden;border-collapse:collapse">{kpi_html}</table>
  </td></tr>

  <tr><td style="background:#{DARK};padding:0 28px 16px 28px">
    <table width="100%" style="background:#{CARD_BG};border:1px solid #{BORDER};border-radius:8px">
    <tr><td colspan="2" style="padding:12px 14px 4px 14px">
      <div style="font-size:11px;color:#8B949E;text-transform:uppercase;letter-spacing:.06em;font-weight:600">Insight da Semana · AI</div>
    </td></tr>
    <tr><td style="padding:6px 14px 8px 14px;font-size:13px;color:#E6EDF3">{ai.get('insight_semana','')}</td></tr>
    <tr><td style="padding:4px 14px 12px 14px">
      <div style="font-size:11px;color:#{TEAL};font-weight:600;margin-bottom:3px">Previsão para amanhã</div>
      <div style="font-size:13px;color:#8B949E">{ai.get('previsao_amanha','')}</div>
    </td></tr>
    </table>
  </td></tr>

  <tr><td style="background:#{DARK};padding:8px 28px 24px 28px;text-align:center">
    <a href="{APP_URL}" style="display:inline-block;background:linear-gradient(90deg,#{TEAL} 0%,#{TEAL_DARK} 100%);color:#fff;padding:16px 36px;text-decoration:none;border-radius:8px;font-weight:700;font-size:15px">
      📊 Abrir Análise Completa na Plataforma →
    </a>
    <div style="font-size:11px;color:#555;margin-top:10px">Gráficos · Tendências · Revenue Intelligence</div>
  </td></tr>

  <tr><td style="background:#{CARD_BG};padding:16px 28px;border-radius:0 0 12px 12px;border-top:1px solid #{BORDER}">
    <table width="100%"><tr>
      <td><div style="font-size:11px;color:#555">InsightKube · Business powered by Data · Análise por Gemini AI</div></td>
      <td align="right"><div style="font-size:11px;color:#555">{hoje}</div></td>
    </tr></table>
  </td></tr>

</table></td></tr></table>
</body></html>"""
    return html

# ── ENVIAR ───────────────────────────────────────────────────────────
def enviar_email(html, k, ai):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"InsightKube · {CLIENTE_NOME} · {k['hoje_fmt']} · Score {k['health_score']:.0f}/100 · {ai.get('urgencia','')}"
    msg["From"]    = f"InsightKube <{GMAIL_USER}>"
    msg["To"]      = CLIENTE_EMAIL
    msg.attach(MIMEText(f"InsightKube — {CLIENTE_NOME} — {k['hoje_fmt']}\n\n{ai.get('analise_narrativa','')}\n\nDecisão: {ai.get('decisao_titulo','')}\nAcção: {ai.get('decisao_acao','')}\n\nVer análise: {APP_URL}", "plain"))
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP("smtp.gmail.com", 587) as s:
        s.starttls(); s.login(GMAIL_USER, GMAIL_PASSWORD); s.send_message(msg)
    print(f"✅ Email enviado para {CLIENTE_EMAIL}")

# ── MAIN ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("InsightKube Auto Mailer v3 — Gemini AI")
    df  = carregar_dados()
    print(f"✅ {len(df)} registos carregados")
    kpi = calcular_kpi(df)
    print(f"✅ KPI: Ocup {kpi['ocup']:.1f}% | RevPAR {kpi['revpar']:.0f}€ | Score {kpi['health_score']:.0f}")
    print("🤖 A chamar Gemini AI para interpretação...")
    ai  = interpretar_com_gemini(kpi)
    print(f"✅ AI: {ai.get('urgencia','')} — {ai.get('decisao_titulo','')}")
    html = build_email(kpi, ai)
    enviar_email(html, kpi, ai)
