import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime


st.set_page_config(page_title="InsightKube — Command Center", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp{background-color:#0D1117;color:#E6EDF3}
[data-testid="stSidebar"]{background-color:#161B22;border-right:1px solid #30363D}
.ik-header{background:linear-gradient(90deg,#0F9E8A 0%,#085041 100%);padding:18px 28px;border-radius:10px;display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}
.ik-header-title{font-size:22px;font-weight:700;color:#fff}
.ik-header-sub{font-size:12px;color:#A8D5CE;margin-top:2px}
.ik-header-meta{font-size:12px;color:#A8D5CE;text-align:right}
.ik-card{background:#161B22;border:1px solid #30363D;border-radius:10px;padding:18px 20px;margin-bottom:12px}
.ik-card-label{font-size:12px;color:#8B949E;text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px}
.ik-card-value{font-size:32px;font-weight:700;color:#E6EDF3}
.ik-card-delta{font-size:13px;margin-top:4px}
.ik-card-delta.up{color:#3FB950}
.ik-card-delta.down{color:#F85149}
.ik-card-delta.neutral{color:#F5C518}
.ik-section{font-size:16px;font-weight:600;color:#E6EDF3;margin:20px 0 10px 0;border-left:3px solid #0F9E8A;padding-left:10px}
.ik-decision{background:#161B22;border:1px solid #0F9E8A;border-radius:10px;padding:20px 24px;margin:10px 0}
.ik-decision-label{font-size:11px;color:#0F9E8A;text-transform:uppercase;letter-spacing:.08em;font-weight:600;margin-bottom:8px}
.ik-decision-text{font-size:18px;font-weight:700;color:#F5C518}
.ik-decision-action{font-size:14px;color:#A8D5CE;margin-top:6px}
.ik-alert{background:#1C1F26;border-left:4px solid #F85149;border-radius:6px;padding:12px 16px;margin:8px 0;font-size:13px;color:#E6EDF3}
.ik-alert-green{border-left-color:#3FB950}
.ik-alert-yellow{border-left-color:#F5C518}
.ik-score{text-align:center;padding:20px;background:#161B22;border:1px solid #30363D;border-radius:10px}
.ik-score-num{font-size:52px;font-weight:800;color:#0F9E8A}
.ik-score-label{font-size:12px;color:#8B949E;margin-top:4px}
.stTabs [data-baseweb="tab-list"]{background:#161B22;border-radius:8px;padding:4px;border:1px solid #30363D}
.stTabs [data-baseweb="tab"]{color:#8B949E;font-size:13px;font-weight:500;border-radius:6px;padding:8px 16px}
.stTabs [aria-selected="true"]{background:#0F9E8A!important;color:#fff!important}
hr{border-color:#30363D}
</style>
""", unsafe_allow_html=True)

def card(label, value, delta="", delta_type="neutral"):
    delta_html = f'<div class="ik-card-delta {delta_type}">{delta}</div>' if delta else ""
    st.markdown(f'<div class="ik-card"><div class="ik-card-label">{label}</div><div class="ik-card-value">{value}</div>{delta_html}</div>', unsafe_allow_html=True)

def alert(text, tipo="red"):
    cls = "ik-alert" + ("" if tipo == "red" else f" ik-alert-{tipo}")
    st.markdown(f'<div class="{cls}">{text}</div>', unsafe_allow_html=True)

def section(title):
    st.markdown(f'<div class="ik-section">{title}</div>', unsafe_allow_html=True)

def gerar_pdf(d):
    pdf = FPDF(); pdf.add_page()
    pdf.set_font("Arial",'B',16); pdf.cell(200,10,"INSIGHTKUBE COMMAND CENTER",ln=True,align='C')
    pdf.set_font("Arial",size=11); pdf.cell(200,8,f"Relatorio: {d['data']}",ln=True,align='C'); pdf.ln(6)
    pdf.set_font("Arial",'B',12)
    for k,v in [("Health Score",f"{d['score']:.0f}/100"),("Ocupacao",f"{d['ocupacao']:.1f}%"),("RevPAR",f"{d['revpar']:.0f} EUR"),("Margem",f"{d['margem']:.1f}%")]:
        pdf.cell(200,8,f"{k}: {v}",ln=True)
    pdf.ln(6); pdf.set_text_color(255,75,75)
    pdf.cell(200,10,f"RECOMENDACAO: {d['rec'].encode('ascii','ignore').decode()}",ln=True)
    pdf.set_text_color(0,0,0); pdf.set_font("Arial",size=11)
    pdf.cell(200,8,f"Acao: {d['acao'].encode('ascii','ignore').decode()}",ln=True)
    return pdf.output(dest='S').encode('latin-1','ignore')

PLOTLY_LAYOUT = dict(plot_bgcolor="#161B22", paper_bgcolor="#161B22", font_color="#8B949E", margin=dict(t=20,b=20,l=20,r=20))

with st.sidebar:
    st.markdown('<div style="text-align:center;padding:16px 0 8px 0"><span style="font-size:22px;font-weight:800;color:#0F9E8A">Insight</span><span style="font-size:22px;font-weight:800;color:#F5C518">Kube</span><div style="font-size:11px;color:#8B949E;margin-top:2px">Business powered by Data</div></div>', unsafe_allow_html=True)
    st.divider()
    st.caption("MÓDULO DE DADOS")
    uploaded_file = st.file_uploader("CSV de Reservas", type=['csv'], label_visibility="collapsed")
    st.caption("Colunas: data, quartos_ocupados, capacidade, preco_atual")
    st.divider()
    st.caption("CLIENTE")
    nome_cliente = st.text_input("Nome do alojamento", placeholder="Ex: Hotel Douro Porto", label_visibility="collapsed")
    st.divider()
    st.caption("BENCHMARK")
    mercado_avg = st.slider("Ocupação média do mercado (%)", 50, 90, 72)

agora = datetime.now().strftime("%d %b %Y | %H:%M")
cliente_label = nome_cliente if nome_cliente else "Sem cliente carregado"
st.markdown(f'<div class="ik-header"><div><div class="ik-header-title">📊 InsightKube — Command Center</div><div class="ik-header-sub">AI-Driven Decision Intelligence · Hotelaria & Restauração</div></div><div class="ik-header-meta"><div style="color:#fff;font-weight:600">{cliente_label}</div><div>Actualizado: {agora}</div></div></div>', unsafe_allow_html=True)

if not uploaded_file:
    for c in st.columns(4): 
        with c: card("—", "—/—", "Carregue o CSV", "neutral")
    st.markdown('<div style="text-align:center;padding:60px 20px;color:#8B949E"><div style="font-size:48px;margin-bottom:16px">📂</div><div style="font-size:18px;font-weight:600;color:#E6EDF3;margin-bottom:8px">Carregue o CSV de reservas para começar</div><div style="font-size:14px">Formato: <code>data, quartos_ocupados, capacidade, preco_atual</code></div></div>', unsafe_allow_html=True)
    st.stop()

try:
    df = pd.read_csv(uploaded_file, sep=None, engine='python')
    df.columns = df.columns.str.strip()
    required = ['data','quartos_ocupados','capacidade','preco_atual']
    if not all(c in df.columns for c in required):
        st.error(f"O CSV precisa das colunas: {required}"); st.stop()

    df['data'] = pd.to_datetime(df['data'], format='mixed', dayfirst=False)
    df['ocupacao_perc'] = (df['quartos_ocupados'] / df['capacidade']) * 100
    df['revpar'] = df['preco_atual'] * (df['ocupacao_perc'] / 100)
    df['data_fmt'] = df['data'].dt.strftime('%d/%m/%Y')

    hoje = df.iloc[-1]
    ocupacao = hoje['ocupacao_perc']; preco = hoje['preco_atual']; revpar = hoje['revpar']
    revpar_ant = df.iloc[-2]['revpar'] if len(df) > 1 else revpar
    revpar_delta = ((revpar - revpar_ant) / revpar_ant * 100) if revpar_ant else 0
    margem = max(10, 100 - 55 - (max(0, ocupacao - 75) * 0.3))
    revenue_risk = round(max(0,(75-ocupacao)*1.2),1) if ocupacao < 75 else round((ocupacao-90)*0.8,1) if ocupacao > 90 else 8.0
    churn_risk = round(50-(ocupacao-50)*0.5,1)
    health_score = round(min(100,(ocupacao*0.5)+(margem*0.3)+20),0)
    custo_pessoal_pct = 35 + max(0,(ocupacao-85)*0.5)

    if ocupacao < 60: rec, acao = "Baixar Preços 12%", "Criar promoção flash no Booking/Airbnb"
    elif ocupacao > 85: rec, acao = "Subir Preços 15%", "Fechar canais externos — priorizar venda directa"
    else: rec, acao = "Manter Preço Estável", "Focar em upselling e early check-in"

    benchmark_tipo = "up" if ocupacao > mercado_avg else "down"

    c1,c2,c3,c4 = st.columns(4)
    with c1: card("Health Score",f"{health_score:.0f}/100","✅ Saudável" if health_score>=70 else "⚠️ Atenção","up" if health_score>=70 else "down")
    with c2: card("Revenue Risk",f"{revenue_risk:.1f}%","Baixo risco" if revenue_risk<20 else "Risco elevado","up" if revenue_risk<20 else "down")
    with c3: card("Ocupação Hoje",f"{ocupacao:.1f}%",f"{'Acima' if ocupacao>mercado_avg else 'Abaixo'} do mercado ({mercado_avg}%)",benchmark_tipo)
    with c4: card("RevPAR",f"{revpar:.0f}€",f"{'▲' if revpar_delta>=0 else '▼'} {abs(revpar_delta):.1f}% vs ontem","up" if revpar_delta>=0 else "down")

    st.divider()
    tab1,tab2,tab3,tab4 = st.tabs(["🧠 Command Center","📈 Revenue & Ocupação","💰 Custos & Margem","👥 Equipa & Operação"])

    with tab1:
        cl,cr = st.columns([2,1])
        with cl:
            section("Decisão do Dia")
            st.markdown(f'<div class="ik-decision"><div class="ik-decision-label">🎯 Recomendação Imediata</div><div class="ik-decision-text">{rec}</div><div class="ik-decision-action">▶ Acção: {acao}</div></div>', unsafe_allow_html=True)
            section("Alertas Activos")
            if ocupacao < 60: alert(f"🔴 Ocupação crítica: {ocupacao:.1f}% — abaixo do limiar de rentabilidade (60%)","red")
            elif ocupacao > 85: alert(f"🟢 Alta procura: {ocupacao:.1f}% — oportunidade de maximizar ADR","green")
            else: alert(f"🟡 Ocupação estável: {ocupacao:.1f}% — monitorizar concorrência","yellow")
            alert("🟡 Custos de fornecedores sob pressão — guerra no Golfo +10% combustíveis","yellow")
            if margem < 25: alert(f"🔴 Margem sob pressão: {margem:.1f}% — rever estrutura de custos","red")
            else: alert(f"🟢 Margem operacional: {margem:.1f}% — dentro do esperado","green")
        with cr:
            st.markdown(f'<div class="ik-score"><div class="ik-score-num">{health_score:.0f}</div><div style="font-size:14px;color:#E6EDF3;font-weight:600">Health Score</div><div class="ik-score-label">Índice de saúde operacional</div></div>', unsafe_allow_html=True)
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            fig_risk = go.Figure(go.Bar(x=["Revenue","Churn"],y=[revenue_risk,churn_risk],marker_color=["#F85149" if revenue_risk>30 else "#F5C518","#F85149" if churn_risk>40 else "#F5C518"],text=[f"{revenue_risk:.1f}%",f"{churn_risk:.1f}%"],textposition="outside"))
            fig_risk.update_layout(**PLOTLY_LAYOUT, title="Risk Distribution", title_font_color="#E6EDF3", height=220, yaxis=dict(gridcolor="#30363D",range=[0,100]), xaxis=dict(gridcolor="#30363D"), showlegend=False)
            st.plotly_chart(fig_risk, use_container_width=True)

    with tab2:
        section("Evolução da Ocupação")
        fig_o = px.line(df,x='data',y='ocupacao_perc',labels={'ocupacao_perc':'Ocupação (%)','data':''},color_discrete_sequence=["#0F9E8A"])
        fig_o.add_hline(y=mercado_avg,line_dash="dash",line_color="#F5C518",annotation_text=f"Benchmark: {mercado_avg}%")
        fig_o.add_hline(y=60,line_dash="dot",line_color="#F85149",annotation_text="Limiar crítico: 60%")
        fig_o.update_layout(**PLOTLY_LAYOUT, height=300, yaxis=dict(gridcolor="#30363D",range=[0,105]), xaxis=dict(gridcolor="#30363D"))
        st.plotly_chart(fig_o,use_container_width=True)
        c1,c2 = st.columns(2)
        with c1:
            section("RevPAR Diário")
            fig_r = px.bar(df,x='data',y='revpar',color_discrete_sequence=["#0F9E8A"],labels={'revpar':'RevPAR (€)','data':''})
            fig_r.update_layout(**PLOTLY_LAYOUT,height=250,yaxis=dict(gridcolor="#30363D"),xaxis=dict(gridcolor="#30363D"))
            st.plotly_chart(fig_r,use_container_width=True)
        with c2:
            section("ADR Diário")
            fig_a = px.line(df,x='data',y='preco_atual',color_discrete_sequence=["#F5C518"],labels={'preco_atual':'ADR (€)','data':''})
            fig_a.update_layout(**PLOTLY_LAYOUT,height=250,yaxis=dict(gridcolor="#30363D"),xaxis=dict(gridcolor="#30363D"))
            st.plotly_chart(fig_a,use_container_width=True)
        section("KPI do Período")
        k1,k2,k3,k4 = st.columns(4)
        with k1: card("Ocupação Média",f"{df['ocupacao_perc'].mean():.1f}%")
        with k2: card("RevPAR Médio",f"{df['revpar'].mean():.0f}€")
        with k3: card("ADR Médio",f"{df['preco_atual'].mean():.0f}€")
        with k4: card("Dias Analisados",str(len(df)))

    with tab3:
        c1,c2 = st.columns(2)
        with c1:
            section("Margem & Custos")
            card("Margem Líquida",f"{margem:.1f}%","✅ Saudável" if margem>=30 else "⚠️ Sob pressão","up" if margem>=30 else "down")
            card("Breakeven Ocupação","42%","Estável","neutral")
            card("Custo por Quarto",f"{preco*0.55:.0f}€","Estimado","neutral")
        with c2:
            section("Distribuição de Custos")
            fig_c = go.Figure(go.Pie(labels=["Pessoal","Operacional","Fornecedores","Margem"],values=[35,20,15,round(margem)],hole=0.5,marker_colors=["#0F9E8A","#F5C518","#30363D","#3FB950"]))
            fig_c.update_layout(**PLOTLY_LAYOUT,height=280,legend=dict(font=dict(color="#8B949E")))
            st.plotly_chart(fig_c,use_container_width=True)
        section("Alertas de Custos")
        if margem < 25: alert("🔴 Margem abaixo de 25% — rever contratos de fornecedores","red")
        else: alert(f"🟢 Margem de {margem:.1f}% — dentro do esperado","green")
        alert("🟡 Guerra no Golfo: peixe e carne +6%, combustíveis +10 cêntimos — monitorizar food cost","yellow")

    with tab4:
        c1,c2,c3 = st.columns(3)
        with c1: card("Rácio Staff/Quartos",f"1:{ocupacao/25:.0f}","✅ Eficiente" if ocupacao<90 else "⚠️ Sobrecarga","up" if ocupacao<90 else "down")
        with c2: card("Produtividade/Colaborador",f"{preco*(ocupacao/100)*0.8:.0f}€/dia","Estimado","neutral")
        with c3: card("Custo Pessoal / Fat.",f"{custo_pessoal_pct:.1f}%","✅ Normal" if custo_pessoal_pct<40 else "⚠️ Elevado","up" if custo_pessoal_pct<40 else "down")
        section("Eficiência Operacional")
        df['eficiencia'] = df['ocupacao_perc']*0.8+10
        fig_e = px.area(df,x='data',y='eficiencia',color_discrete_sequence=["#0F9E8A"],labels={'eficiencia':'Índice de Eficiência','data':''})
        fig_e.update_layout(**PLOTLY_LAYOUT,height=250,yaxis=dict(gridcolor="#30363D"),xaxis=dict(gridcolor="#30363D"))
        st.plotly_chart(fig_e,use_container_width=True)
        section("Alertas de Equipa")
        if ocupacao > 85: alert("⚠️ Alta ocupação — verificar adequação de pessoal nos turnos de pico","yellow")
        else: alert("✅ Níveis de ocupação dentro do normal — sem pressão na equipa","green")

    st.divider()
    c_dl, c_tb = st.columns([1,2])
    with c_dl:
        section("Exportar PDF")
        pdf_bytes = gerar_pdf({"data":hoje['data_fmt'],"score":health_score,"ocupacao":ocupacao,"revpar":revpar,"margem":margem,"rec":rec,"acao":acao})
        st.download_button("📄 Descarregar Relatório PDF", data=pdf_bytes, file_name=f"InsightKube_{hoje['data_fmt'].replace('/','')}.pdf", mime="application/pdf", use_container_width=True)
    with c_tb:
        section("Dados do Período")
        st.dataframe(df[['data_fmt','quartos_ocupados','capacidade','ocupacao_perc','preco_atual','revpar']].rename(columns={'data_fmt':'Data','quartos_ocupados':'Ocup.','capacidade':'Cap.','ocupacao_perc':'Ocup. %','preco_atual':'ADR €','revpar':'RevPAR €'}).style.format({'Ocup. %':'{:.1f}','ADR €':'{:.0f}','RevPAR €':'{:.0f}'}), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erro ao processar o ficheiro: {e}")
    st.info("Verifica se o CSV tem as colunas: data, quartos_ocupados, capacidade, preco_atual")
