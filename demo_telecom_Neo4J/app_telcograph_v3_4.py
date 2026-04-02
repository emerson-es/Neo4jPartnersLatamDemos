import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import geopandas as gpd
import contextily as ctx
import matplotlib.pyplot as plt
import seaborn as sns
import os
import requests
from neo4j import GraphDatabase

from app_config import (
    NEO4J_URI,
    NEO4J_USER,
    NEO4J_PASSWORD,
    NEO4J_DATABASE,
    AURA_API_CLIENT_ID,
    AURA_API_CLIENT_SECRET,
    AURA_API_TEXT2CYPHER_ENDPOINT,
    AURA_TOKEN_URL,
    LOGO_NEO4J_URL,
    LOGO_EMPRESA_URL,
    KAGGLE_DATASET_URL,
)

from neo4j_analysis import Neo4jAnalysis
from neo4j_viz.neo4j import from_neo4j, ColorSpace
from neo4j_viz import Layout

# ── Paleta de cores dos nós ────────────────────────────────────────────────────
colors = {
    "Customer": "#F00B47",
    "Location": "#00AEEF",
    "PaymentMethod": "#702082",
    "Contract": "#002E5D",
    "Service": "#616AB1",
    "Movie": "#E6007E",
}

# ── Paleta de cores para topologia de rede ────────────────────────────────────
network_colors = {
    "CoreNetwork": "#D62828",
    "RegionalHub": "#F77F00",
    "CentralOffice": "#FCBF49",
    "DistributionCabinet": "#003049",
    "AccessNode": "#0097D7",
    "CPE": "#2A9D8F",
    "Customer": "#F00B47",
    "MaintenanceEvent": "#E63946",
}

label_to_property = {
    "Customer": "customer_id",
    "Location": "city",
    "PaymentMethod": "payment_method",
    "Contract": "contract",
    "Service": "service_type",
    "Movie": "title",
}

network_label_to_property = {
    "CoreNetwork": "name",
    "RegionalHub": "name",
    "CentralOffice": "name",
    "DistributionCabinet": "name",
    "AccessNode": "name",
    "CPE": "cpe_id",
    "Customer": "customer_id",
    "MaintenanceEvent": "title",
}

NETWORK_GRAPH_HEIGHT = 560

# ── Configuração da página ─────────────────────────────────────────────────────
st.set_page_config(page_title="Análise de Grafos · Neo4j", layout="wide")

# ── CSS Global ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Base ─────────────────────────────────────────────── */
[data-testid="stAppViewContainer"] {
    background-color: #EEF2F8 !important;
}
[data-testid="block-container"] {
    padding: 1.5rem 2.75rem 3rem !important;
    max-width: 1440px;
}
/* Aplica Inter SOMENTE em elementos de texto puros — NUNCA em span/div para
   não quebrar as fontes de ícones do Streamlit (seta do expander, etc.)     */
[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] label,
[data-testid="stAppViewContainer"] a,
[data-testid="stAppViewContainer"] li,
[data-testid="stAppViewContainer"] input,
[data-testid="stAppViewContainer"] textarea,
[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] h4,
[data-testid="stAppViewContainer"] h5,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] a,
[data-testid="stSidebar"] li {
    font-family: 'Inter', sans-serif !important;
}

/* Protege TODAS as fontes de ícones do Streamlit de qualquer override */
[data-testid="stExpanderToggleIcon"],
[data-testid="stExpanderToggleIcon"] *,
.material-icons,
.material-icons-outlined,
.material-symbols-outlined,
.material-symbols-rounded,
.material-symbols-sharp,
[class*="material-symbols"],
[class*="material-icons"] {
    font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
}

/* ── Tipografia ───────────────────────────────────────── */
h1 {
    font-size: 1.85rem !important;
    font-weight: 700 !important;
    color: #002E5D !important;
    letter-spacing: -0.025em !important;
    margin-bottom: 0.15rem !important;
    line-height: 1.2 !important;
}
h2 {
    font-size: 1.4rem !important;
    font-weight: 700 !important;
    color: #002E5D !important;
    margin-top: 0.5rem !important;
    letter-spacing: -0.015em !important;
}
h3 {
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    color: #1A365D !important;
}
p {
    color: #2D3748;
}

/* ── Sidebar ──────────────────────────────────────────── */
[data-testid="stSidebar"] > div:first-child {
    background: #002E5D !important;
}
[data-testid="stSidebarContent"] {
    padding: 1.25rem 0.9rem !important;
}
/* Centraliza as imagens (logos) dentro da sidebar */
[data-testid="stSidebar"] [data-testid="stImage"],
[data-testid="stSidebar"] [data-testid="stImage"] > div,
[data-testid="stSidebar"] [data-testid="stImage"] img {
    display: block !important;
    margin-left: auto !important;
    margin-right: auto !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] small {
    color: #A8C8E8 !important;
    font-size: 11.5px !important;
    font-family: 'Inter', sans-serif !important;
}
/* Labels dos itens de navegação */
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] p {
    color: #C8DFF2 !important;
    font-size: 13px !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.15) !important;
    margin: 10px 0 14px !important;
}

/* ── Divisores ────────────────────────────────────────── */
hr {
    border-color: #CBD5E0 !important;
    margin: 1.5rem 0 !important;
}

/* ── Formulários ─────────────────────────────────────── */
[data-testid="stForm"] {
    background: #FFFFFF !important;
    border-radius: 14px !important;
    padding: 1.2rem 1.25rem !important;
    border: 1px solid #DDE4EF !important;
    box-shadow: 0 2px 10px rgba(0, 46, 93, 0.06) !important;
}

/* ── Botões ───────────────────────────────────────────── */
.stFormSubmitButton > button,
.stButton > button {
    background: linear-gradient(135deg, #002E5D 0%, #0082BF 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 13.5px !important;
    font-family: 'Inter', sans-serif !important;
    padding: 0.45rem 1.3rem !important;
    letter-spacing: 0.02em !important;
    transition: opacity 0.18s, transform 0.18s !important;
    box-shadow: 0 2px 8px rgba(0, 46, 93, 0.28) !important;
    width: 100% !important;
}
/* Força texto branco em todos os filhos do botão */
.stFormSubmitButton > button *,
.stButton > button * {
    color: #FFFFFF !important;
    font-family: 'Inter', sans-serif !important;
}
.stFormSubmitButton > button:hover,
.stButton > button:hover {
    opacity: 0.87 !important;
    transform: translateY(-1px) !important;
}

/* ── Expanders ────────────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid #DDE4EF !important;
    border-radius: 10px !important;
    overflow: hidden !important;
    margin-bottom: 0.65rem !important;
    background: #FAFBFD !important;
}
/* Usa o seletor de label do expander — NÃO usa summary para não quebrar ícone de seta */
[data-testid="stExpander"] [data-testid="stExpanderToggleIcon"] {
    color: #4A5568 !important;
}
[data-testid="stExpander"] > details > summary > span,
[data-testid="stExpander"] > details > summary p {
    font-weight: 500 !important;
    color: #4A5568 !important;
    font-size: 13.5px !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Dataframe ────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid #DDE4EF !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

/* ── Captions ─────────────────────────────────────────── */
[data-testid="stCaptionContainer"] p {
    color: #718096 !important;
    font-size: 12px !important;
}

/* ── Form labels ──────────────────────────────────────── */
[data-testid="stSlider"] label,
[data-testid="stTextInput"] label,
[data-testid="stSelectbox"] label {
    font-weight: 500 !important;
    color: #2D3748 !important;
    font-size: 13px !important;
}

/* ══════════════════════════════════════════════════════
   KPI CARDS
══════════════════════════════════════════════════════ */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 14px;
    margin: 0.75rem 0 1.5rem;
}
.kpi-card {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 20px 16px 16px;
    box-shadow: 0 1px 4px rgba(0,46,93,0.07), 0 4px 14px rgba(0,46,93,0.04);
    display: flex;
    flex-direction: column;
    gap: 9px;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    cursor: default;
}
.kpi-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 26px rgba(0,46,93,0.12);
}
.kpi-card::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--kc, #002E5D);
    border-radius: 14px 14px 0 0;
}
.kpi-icon-wrap {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    background: var(--kb, #EBF4FF);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 19px;
}
.kpi-value {
    font-size: 23px;
    font-weight: 700;
    color: #1A202C;
    line-height: 1.1;
    letter-spacing: -0.02em;
}
.kpi-label {
    font-size: 11px;
    font-weight: 600;
    color: #718096;
    text-transform: uppercase;
    letter-spacing: 0.07em;
}

/* ══════════════════════════════════════════════════════
   INTRO CARDS (3 colunas)
══════════════════════════════════════════════════════ */
.intro-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
    margin: 0.75rem 0 1.5rem;
}
.intro-card {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 18px 20px 16px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    border-left: 4px solid var(--ic, #002E5D);
    display: flex;
    flex-direction: column;
    gap: 5px;
}
.intro-icon { font-size: 19px; margin-bottom: 2px; }
.intro-label {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    color: var(--ic, #002E5D);
}
.intro-text {
    font-size: 13px;
    color: #4A5568;
    line-height: 1.55;
}

/* ══════════════════════════════════════════════════════
   PAGE HEADER BANNER
══════════════════════════════════════════════════════ */
.page-header {
    background: linear-gradient(135deg, #001F45 0%, #003370 50%, #005FA3 100%);
    border-radius: 16px;
    padding: 28px 32px 24px;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.page-header::before {
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(0,174,239,0.18) 0%, transparent 70%);
    border-radius: 50%;
}
.page-header h1 {
    color: #FFFFFF !important;
    font-size: 1.7rem !important;
    margin: 0 0 6px !important;
}
.page-header-sub {
    color: #93C6E8;
    font-size: 14px;
    margin: 0;
    font-weight: 400;
}
</style>
""", unsafe_allow_html=True)


# ── Conexão (importada de config.py) ──────────────────────────────────────────


# ── Helpers ────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_aura_access_token(client_id: str, client_secret: str) -> str:
    response = requests.post(
        AURA_TOKEN_URL,
        data={"grant_type": "client_credentials"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        auth=(client_id, client_secret),
        timeout=15,
    )
    try:
        response.raise_for_status()
    except Exception as exc:
        raise RuntimeError(
            f"Falha ao obter token da Aura API: {response.status_code} {response.text}"
        ) from exc
    token = response.json().get("access_token")
    if not token:
        raise RuntimeError("Resposta da Aura API não contém access_token")
    return token


def invoke_aura_agent(endpoint: str, bearer_token: str, prompt: str) -> dict:
    response = requests.post(
        endpoint,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {bearer_token}",
        },
        json={"input": prompt},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


@st.cache_resource
def get_analysis_client():
    return Neo4jAnalysis(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE)


@st.cache_data(show_spinner=False)
def load_kpi_summary():
    query = """
        MATCH (c:Customer)
        WITH count(c) AS total_customers,
             sum(CASE WHEN c.churn_label = 'Yes' THEN 1 ELSE 0 END) AS churned_customers,
             avg(c.tenure_months) AS avg_tenure_months,
             avg(coalesce(toFloat(c.monthly_charges), 0.0) * coalesce(toFloat(c.tenure_months), 0.0)) AS avg_customer_lifetime_value
        CALL() {
            MATCH (c2:Customer)
            WHERE c2.louvain_community_id IS NOT NULL
            WITH c2.louvain_community_id AS community_id, count(*) AS community_size
            WHERE community_size >= 10
            RETURN count(*) AS unique_communities
        }
        OPTIONAL MATCH (:Customer)-[:WATCHED_MOVIE]->(:Movie)
        RETURN total_customers,
               churned_customers,
               round((toFloat(churned_customers) / CASE WHEN total_customers = 0 THEN 1 ELSE total_customers END) * 100, 2) AS churn_rate_pct,
               round(coalesce(avg_tenure_months, 0), 1) AS avg_tenure_months,
               round(coalesce(avg_customer_lifetime_value, 0), 2) AS avg_customer_lifetime_value,
               unique_communities,
               count(*) AS total_movie_watches
    """
    return analysis.run_query_df(query)


def render_kpi_cards(kpis):
    """Renderiza uma grade de KPI cards com ícone, valor e rótulo."""
    cards = [
        {"icon": "👥", "label": "Total de Clientes",    "value": f"{int(kpis['total_customers']):,}",                      "color": "#002E5D", "bg": "#EBF4FF"},
        {"icon": "📉", "label": "Taxa de Churn",        "value": f"{float(kpis['churn_rate_pct']):.2f}%",                  "color": "#F00B47", "bg": "#FFF0F3"},
        {"icon": "📅", "label": "Tempo Médio (meses)",  "value": f"{float(kpis['avg_tenure_months']):.1f}",                "color": "#0097D7", "bg": "#E6F7FF"},
        {"icon": "🎬", "label": "Filmes Assistidos",    "value": f"{int(kpis['total_movie_watches']):,}",                  "color": "#E6007E", "bg": "#FFF0FA"},
        {"icon": "💰", "label": "CLV Médio",            "value": f"${float(kpis['avg_customer_lifetime_value']):,.2f}",    "color": "#16A085", "bg": "#E8F8F5"},
        {"icon": "🔗", "label": "Comunidades Únicas",   "value": f"{int(kpis['unique_communities']):,}",                   "color": "#702082", "bg": "#F3E8FF"},
    ]
    inner = "".join(
        f"""<div class="kpi-card" style="--kc:{c['color']};--kb:{c['bg']};">
                <div class="kpi-icon-wrap">{c['icon']}</div>
                <div class="kpi-value">{c['value']}</div>
                <div class="kpi-label">{c['label']}</div>
            </div>"""
        for c in cards
    )
    st.markdown(f'<div class="kpi-grid">{inner}</div>', unsafe_allow_html=True)


def render_section_intro(what: str, how: str, takeaway: str):
    """Renderiza 3 cards informativos no topo de cada seção."""
    st.markdown(f"""
    <div class="intro-grid">
        <div class="intro-card" style="--ic:#0097D7;">
            <div class="intro-icon">🔍</div>
            <div class="intro-label">O que mostra</div>
            <div class="intro-text">{what}</div>
        </div>
        <div class="intro-card" style="--ic:#702082;">
            <div class="intro-icon">💡</div>
            <div class="intro-label">Como usar</div>
            <div class="intro-text">{how}</div>
        </div>
        <div class="intro-card" style="--ic:#16A085;">
            <div class="intro-icon">📈</div>
            <div class="intro-label">Impacto no negócio</div>
            <div class="intro-text">{takeaway}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_styled_table(df: pd.DataFrame):
    st.dataframe(df, hide_index=True, use_container_width=True)


# ── Bootstrap ──────────────────────────────────────────────────────────────────
analysis = get_analysis_client()

try:
    kpi_df = load_kpi_summary()
except Exception:
    kpi_df = pd.DataFrame()

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.markdown(
    f"""
    <div style="text-align:center; padding:0.75rem 0 0.25rem;">
        <img
            src="{LOGO_NEO4J_URL}"
            style="width:120px; display:inline-block;"
        >
    </div>
    <p style="
        text-align:center;
        color:#FFFFFF;
        font-size:12px;
        margin:8px 0 12px;
        font-family:'Inter',sans-serif;
        font-weight:500;
        letter-spacing:0.02em;
        opacity:0.90;
    ">Análise de Grafos · Customer 360</p>
    <div style="text-align:center; padding:0 0 0.5rem;">
        <img
            src="{LOGO_EMPRESA_URL}"
            style="width:140px; display:inline-block;"
        >
    </div>
    <hr style="border-color:rgba(255,255,255,0.15); margin:10px 0 140px;">
    """,
    unsafe_allow_html=True,
)

section_options = [
    "O que os Dados Representam",
    "A Geografia",
    "Entendendo o Grafo Customer 360",
    "Redes de Similaridade",
    "Combinações de Serviços com Alto Churn",
    "GDS: Comunidades de Churn",
    "Falhas Geo-Espaciais",
    "Heatmap de Churn",
    "Recomendações de Filmes",
    "Previsão de Risco com KNN",
    "── Topologia de Rede ──",
    "Visão Hierárquica da Rede",
    "Rastreamento de Caminho do Cliente",
    "Capacidade e Utilização",
    "Análise de Impacto de Falhas",
    "Manutenção e SLA",
    "Custos de Manutenção",
    "Análise de Causa Raiz",
    "Linha do Tempo de Incidentes",
]

selected_section = st.sidebar.radio("Navegação", section_options)

# ── Header da página ───────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <h1>Análise de Assinantes em Telecom com Neo4j: da Rede ao Comportamento do Cliente</h1>
    <p class="page-header-sub">Da tabela relacional ao Grafo: insights acionáveis para o negócio.</p>
</div>
""", unsafe_allow_html=True)

# ── KPI Cards ─────────────────────────────────────────────────────────────────
if not kpi_df.empty:
    render_kpi_cards(kpi_df.iloc[0])

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# SEÇÕES
# ══════════════════════════════════════════════════════════════════════════════

if selected_section == "O que os Dados Representam":
    st.header("O que os Dados Representam")
    render_section_intro(
        "Como entidades de cliente, produto, geografia e comportamento cinematográfico são representadas no grafo.",
        "Leia o resumo do schema e, em seguida, navegue pelas seções na barra lateral para explorar cada análise.",
        "O modelo em grafo torna junções entre domínios e insights baseados em relacionamentos muito mais rápidos.",
    )
    st.markdown(f"""
Este demo utiliza o [dataset de churn do Kaggle]({KAGGLE_DATASET_URL}) modelado como um grafo **Customer 360** no Neo4j.
Exploraremos como a abordagem de grafo permite percorrer relações complexas entre clientes, dados demográficos, planos e comportamentos para revelar insights difíceis de obter com métodos tabulares tradicionais.

**Principais Entidades:**
- **Clientes**: Atributos demográficos e de assinatura, incluindo a classificação de churn.
- **Localidades**: Cidades onde os clientes residem, habilitando análise geo-espacial.
- **Métodos de Pagamento**: Formas de pagamento utilizadas, que podem estar associadas ao risco de churn.
- **Contratos**: Tipos de contratos dos clientes (mensal, anual ou bienal).
- **Serviços**: Serviços assinados por cada cliente (internet, suporte técnico, etc.).
- **Filmes**: Para clientes com streaming, enriquecemos o grafo com filmes sintéticos assistidos, permitindo análises de similaridade e recomendações.
- **Relacionamentos**: Definem como clientes se conectam às suas localidades, pagamentos, contratos, serviços e outros clientes via similaridade.
    """)

elif selected_section == "A Geografia":
    st.header("A Geografia")
    render_section_intro(
        "Onde os clientes estão concentrados e quais localidades têm maiores taxas de churn.",
        "Observe o tamanho das bolhas para a concentração de clientes e a cor para o risco de churn.",
        "Equipes podem priorizar intervenções por localidade em vez de ações genéricas de retenção.",
    )
    st.markdown("Distribuição física da base de clientes usando coordenadas geo-espaciais armazenadas no Neo4j.")

    @st.cache_data
    def load_geography():
        query = """
        MATCH (c:Customer)-[:LIVES_AT]->(l:Location)
        WITH l, count(c) AS total_customers,
             sum(CASE WHEN c.churn_label = 'Yes' THEN 1 ELSE 0 END) AS churned_customers
        RETURN l.city AS city,
               l.longitude AS longitude,
               l.latitude AS latitude,
               total_customers,
               round((toFloat(churned_customers) / total_customers) * 100, 2) AS churn_rate_pct
        """
        return analysis.run_query_df(query)

    with st.spinner("Carregando dados espaciais..."):
        results_df = load_geography()

    if not results_df.empty:
        gdf = gpd.GeoDataFrame(
            results_df,
            geometry=gpd.points_from_xy(results_df.longitude, results_df.latitude),
            crs="EPSG:4326",
        )
        gdf_wm = gdf.to_crs(epsg=3857)

        fig, ax = plt.subplots(figsize=(6, 4))
        sizes = gdf_wm["total_customers"].fillna(0) * 2 + 20
        gdf_wm.plot(
            ax=ax, column="churn_rate_pct", cmap="YlOrRd",
            markersize=sizes, alpha=0.7, edgecolors="black", linewidth=0.5,
            legend=True, legend_kwds={"label": "Churn %", "shrink": 0.6},
        )
        ctx.add_basemap(ax, crs=gdf_wm.crs.to_string(), source=ctx.providers.OpenStreetMap.Mapnik)
        ax.set_axis_off()
        ax.set_title("Distribuição de Clientes por Taxa de Churn", fontsize=12, fontweight="light", pad=15, color="#333333")
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        st.caption("Cor da bolha reflete % de churn; tamanho reflete o total de clientes na localidade.")
    else:
        st.warning("Nenhum dado geo-espacial encontrado no grafo.")

elif selected_section == "Entendendo o Grafo Customer 360":
    st.header("O Perfil Estrutural de um Cliente")
    render_section_intro(
        "Vizinhança estrutural amostrada ao redor dos nós de clientes nas principais dimensões.",
        "Escolha o tamanho da amostra à esquerda, execute a consulta e inspecione o contexto conectado à direita.",
        "O contexto de grafo por cliente evidencia rapidamente oportunidades de retenção e venda cruzada.",
    )
    st.markdown("""
Em um banco de dados relacional, esta visão requer a junção de 5 tabelas diferentes.
No Neo4j, simplesmente percorremos a partir do cliente para ver seu contexto completo de produtos e identidade.
    """)

    controls_col, output_col = st.columns([1, 2])

    with controls_col:
        with st.form("customer_lookup_form"):
            customers = st.slider("Número de Clientes para Amostrar", min_value=1, max_value=10, value=2, help="Quantos clientes devemos carregar?")
            submitted = st.form_submit_button("Gerar Grafo do Cliente")

    if submitted:
        query = f"""
            MATCH (c:Customer)
            LIMIT {customers}
            MATCH p=(c)-[rels*..1]-()
            WHERE NONE(r IN rels WHERE type(r) = 'SIMILAR_TO' OR type(r) = 'WATCHED_MOVIE')
            RETURN p
            """
        with output_col:
            with st.expander("Ver Consulta Cypher"):
                st.code(query, language="cypher")
            with st.spinner("Percorrendo o grafo..."):
                results = analysis.run_query_viz(query)
                if results:
                    st.success("Grafo do cliente gerado com sucesso.")
                    VG = from_neo4j(results)
                    VG.color_nodes(field="caption", color_space=ColorSpace.DISCRETE, colors=colors)
                    VG.resize_nodes(property="monthly_charges", node_radius_min_max=(10, 30))
                    analysis.set_caption_by_label(VG, label_to_property)
                    generated_html = VG.render(layout=Layout.FORCE_DIRECTED)
                    components.html(generated_html.data, height=NETWORK_GRAPH_HEIGHT)
                else:
                    st.warning("Cliente não encontrado ou sem conexões.")

elif selected_section == "Redes de Similaridade":
    st.header("Redes de Similaridade e Comunidades")
    render_section_intro(
        "Grafo local de similaridade de clientes baseado em atributos compartilhados.",
        "Selecione um cliente e a profundidade de travessia à esquerda, depois inspecione os clusters vizinhos à direita.",
        "Vizinhanças de similaridade ajudam a direcionar intervenções para grupos de risco com perfis comuns.",
    )

    st.markdown("### Como as Redes de Similaridade e Comunidades foram criadas?")

    st.markdown("""
<div class="intro-grid">
    <div class="intro-card" style="--ic:#0097D7;">
        <div class="intro-icon">1️⃣</div>
        <div class="intro-label">Passo 1 — Conexões de Similaridade</div>
        <div class="intro-text">
            Conectamos dois clientes como "similares" <b>somente quando</b> eles têm o <b>mesmo contrato</b>,
            o <b>mesmo método de pagamento</b>, pelo menos <b>3 de 4 características demográficas iguais</b>
            (gênero, parceiro, dependentes, idoso) e pelo menos <b>3 serviços em comum</b>.
            Quanto mais coisas em comum, mais forte a conexão (peso da aresta).
        </div>
    </div>
    <div class="intro-card" style="--ic:#702082;">
        <div class="intro-icon">2️⃣</div>
        <div class="intro-label">Passo 2 — Algoritmo de Louvain</div>
        <div class="intro-text">
            Rodamos o <b>algoritmo de Louvain</b>, que olha toda essa rede de conexões e identifica automaticamente
            <b>grupos (comunidades)</b> de clientes que são mais conectados entre si do que com o restante.
            Cada cliente recebe um <b>"ID de comunidade"</b> — seu grupo de pertencimento.
        </div>
    </div>
    <div class="intro-card" style="--ic:#16A085;">
        <div class="intro-icon">3️⃣</div>
        <div class="intro-label">Como Usar</div>
        <div class="intro-text">
            Se dentro de uma comunidade vários clientes já cancelaram, os demais membros daquele mesmo grupo são
            <b>candidatos fortes a cancelar também</b>. A equipe de retenção pode priorizar ações para
            comunidades com alta taxa de churn. Explore abaixo a rede de um cliente específico.
        </div>
    </div>
</div>
    """, unsafe_allow_html=True)

    st.divider()

    controls_col, output_col = st.columns([1, 2])

    with controls_col:
        with st.form("similarity_network_form"):
            customer_id = st.text_input("ID do Cliente para Explorar", value="7517-SAWMO", help="Experimente '7517-SAWMO' como perfil de exemplo")
            customers = st.slider("Número de Clientes Similares", min_value=3, max_value=10, value=10, help="Quantos clientes similares buscar?")
            depth = st.slider("Graus de Similaridade para Percorrer", min_value=1, max_value=4, value=2, help="Quantos graus de similaridade explorar?")
            max_customers = st.slider("Máx. Clientes por Grau", min_value=5, max_value=20, value=10, help="Quantos clientes por grau de similaridade?")
            submitted_sim = st.form_submit_button("Mostrar Rede de Similaridade")

    if submitted_sim:
        query = f"""
            MATCH l1 = (source:Customer {{customer_id: '{customer_id}'}})-[:SIMILAR_TO]-(target:Customer)
            WITH l1, target LIMIT {customers}
            CALL(target) {{
                WITH target
                MATCH l2 = (target)-[:SIMILAR_TO*..{depth}]-(other:Customer)
                WHERE other.customer_id <> '{customer_id}'
                RETURN l2 LIMIT {max_customers}
            }}
            RETURN l1, l2
            """
        with output_col:
            with st.expander("Ver Consulta Cypher"):
                st.code(query, language="cypher")
            with st.spinner("Extraindo rede de similaridade..."):
                results_sim = analysis.run_query_viz(query)
                if results_sim:
                    st.success("Rede de similaridade gerada.")
                    VG = from_neo4j(results_sim)
                    VG.color_nodes(field="caption", color_space=ColorSpace.DISCRETE, colors=colors)
                    VG.resize_nodes(property="monthly_charges", node_radius_min_max=(10, 30))
                    analysis.set_caption_by_label(VG, label_to_property)
                    html_sim = VG.render(layout=Layout.FORCE_DIRECTED, initial_zoom=0.75)
                    components.html(html_sim.data, height=NETWORK_GRAPH_HEIGHT)
                else:
                    st.warning("Nenhum relacionamento de similaridade encontrado no grafo.")

elif selected_section == "Combinações de Serviços com Alto Churn":
    st.header("Combinações Tóxicas de Serviços")
    render_section_intro(
        "Combinações de serviços associadas a maior churn e um subgrafo amostral dos clientes impactados.",
        "Defina o número de pares e o tamanho da amostra à esquerda, depois inspecione métricas e a rede à direita.",
        "Combinações de alto risco informam estratégias de empacotamento, precificação e campanhas de retenção proativa.",
    )
    st.markdown("""
Consultamos o grafo para identificar quais pares de serviços impulsionam as maiores taxas de churn
e exploramos uma amostra estrutural dos clientes afetados.
Da mesma forma, podemos identificar triplas ou combinações de ordem superior.
    """)

    controls_col, output_col = st.columns([1, 2])

    with controls_col:
        with st.form("service_pair_form"):
            top_n = st.slider("Número de Pares de Serviços", min_value=1, max_value=5, value=3, help="Quantos pares analisar?")
            customers = st.slider("Clientes Afetados para Amostrar", min_value=5, max_value=20, value=5, help="Quantos clientes afetados por par?")
            submitted_service_pairs = st.form_submit_button("Analisar Pares de Serviços")

    if submitted_service_pairs:
        query_metrics = f"""
            MATCH (s1:Service)<-[:SUBSCRIBES_TO]-(c:Customer)-[:SUBSCRIBES_TO]->(s2:Service)
            WHERE s1.service_type < s2.service_type
            WITH s1.service_type AS Service_A,
                 s2.service_type AS Service_B,
                 count(c) AS Total_Subscribers,
                 sum(CASE WHEN c.churn_label = 'Yes' THEN 1.0 ELSE 0.0 END) AS Churned,
                 sum(CASE WHEN c.churn_label = 'No' THEN 1.0 ELSE 0.0 END) AS Retained
            WHERE Total_Subscribers > 50 AND Retained > 0
            RETURN Service_A, Service_B, Total_Subscribers,
                   round((Churned / Total_Subscribers) * 100, 1) AS Churn_Rate_Pct
            ORDER BY Churn_Rate_Pct DESC
            LIMIT {top_n}
            """
        query_graph = f"""
            MATCH (s1:Service)<-[:SUBSCRIBES_TO]-(c:Customer)-[:SUBSCRIBES_TO]->(s2:Service)
            WHERE s1.service_type < s2.service_type
            WITH s1, s2, count(c) AS Total_Subscribers,
                 sum(CASE WHEN c.churn_label = 'Yes' THEN 1.0 ELSE 0.0 END) AS Churned
            WHERE Total_Subscribers > 50
            WITH s1, s2, (Churned / Total_Subscribers) AS Churn_Rate
            ORDER BY Churn_Rate DESC
            LIMIT {top_n}
            CALL(s1, s2) {{
                WITH s1, s2
                MATCH p=(s1)<-[:SUBSCRIBES_TO]-(c:Customer)-[:SUBSCRIBES_TO]->(s2)
                RETURN p
                LIMIT {customers}
            }}
            RETURN p
            """
        with output_col:
            with st.expander("Ver Consulta Cypher — Métricas"):
                st.code(query_metrics, language="cypher")
            with st.expander("Ver Consulta Cypher — Grafo"):
                st.code(query_graph, language="cypher")

            with st.spinner("Calculando métricas de risco por combinação..."):
                metrics_df = analysis.run_query_df(query_metrics)
                if not metrics_df.empty:
                    st.success("Métricas de combinação de serviços geradas.")
                    render_styled_table(metrics_df)
                else:
                    st.warning("Sem dados de métricas para os parâmetros selecionados.")

            with st.spinner("Extraindo subgrafos visuais para os pares..."):
                results_pairs = analysis.run_query_viz(query_graph)
                if results_pairs:
                    VG = from_neo4j(results_pairs)
                    VG.color_nodes(field="caption", color_space=ColorSpace.DISCRETE, colors=colors)
                    VG.resize_nodes(property="monthly_charges", node_radius_min_max=(10, 30))
                    analysis.set_caption_by_label(VG, label_to_property)
                    st.info("O tamanho dos nós é proporcional ao valor da mensalidade.")
                    html_pairs = VG.render(layout=Layout.FORCE_DIRECTED, initial_zoom=0.8)
                    components.html(html_pairs.data, height=NETWORK_GRAPH_HEIGHT)
                else:
                    st.warning("Não foi possível extrair um subgrafo para esses serviços.")

elif selected_section == "GDS: Comunidades de Churn":
    st.header("Comunidades Comportamentais e Risco Estrutural")
    render_section_intro(
        "Estrutura de comunidades do algoritmo Louvain sobre relacionamentos de similaridade entre clientes.",
        "Ajuste o número de clusters e o tamanho mínimo, depois compare estrutura e risco lado a lado.",
        "O risco por comunidade ajuda a priorizar intervenções para grupos com padrões comuns de produto e comportamento.",
    )
    st.markdown("""
Usando o **algoritmo Louvain**, agrupamos clientes pela similaridade estrutural (serviços compartilhados, contratos, métodos de pagamento e dados demográficos).
Em seguida, sobrepomos as taxas reais de churn para encontrar combinações tóxicas de produtos — um exemplo de como o clustering em grafo revela padrões ocultos de risco invisíveis a métodos tabulares.
    """)

    controls_col, output_col = st.columns([1, 2])

    with controls_col:
        with st.form("louvain_form"):
            clusters_to_show = st.slider("Número de Clusters Louvain", min_value=3, max_value=15, value=8, help="Quantos clusters visualizar?")
            min_cluster_size = st.slider("Mínimo de Clientes por Cluster", min_value=5, max_value=30, value=20, help="Tamanho mínimo para inclusão na análise?")
            submitted_louvain = st.form_submit_button("Mostrar Clusters e Perfis de Risco")

    if submitted_louvain:
        query_louvain = f"""
                MATCH (c:Customer)
                WHERE c.louvain_community_id IS NOT NULL
                WITH c.louvain_community_id AS comm_id, count(c) AS comm_size
                ORDER BY comm_size DESC LIMIT {clusters_to_show}
                CALL(comm_id) {{
                    WITH comm_id
                    MATCH p=(c1:Customer)-[rel:SIMILAR_TO]->(c2:Customer)
                    WHERE c1.louvain_community_id = comm_id AND c2.louvain_community_id = comm_id
                    RETURN p LIMIT 100
                }}
                RETURN p
                """
        profile_query = f"""
                MATCH (c:Customer)
                WHERE c.louvain_community_id IS NOT NULL
                WITH c.louvain_community_id AS community_id,
                    count(c) AS total_customers,
                    sum(CASE WHEN c.churn_label = 'Yes' THEN 1 ELSE 0 END) AS churned_customers
                WHERE total_customers > {min_cluster_size}
                RETURN toString(community_id) AS community_id,
                    total_customers,
                    round((toFloat(churned_customers) / total_customers) * 100, 1) AS churn_rate_pct
                ORDER BY total_customers DESC LIMIT {clusters_to_show}
                """
        with output_col:
            with st.expander("Ver Consulta Cypher — Clusters Louvain"):
                st.code(query_louvain, language="cypher")
            with st.expander("Ver Consulta Cypher — Perfis de Risco"):
                st.code(profile_query, language="cypher")

            col1, col2 = st.columns([1, 1])

            with col1:
                st.subheader("Topologia do Subgrafo")
                with st.spinner("Renderizando clusters Louvain..."):
                    results_louvain = analysis.run_query_viz(query_louvain)
                    if results_louvain:
                        st.success("Topologia de comunidades gerada.")
                        VG = from_neo4j(results_louvain)
                        VG.color_nodes(
                            property="louvain_community_id",
                            color_space=ColorSpace.DISCRETE,
                            colors=[
                                "#F00B47", "#00AEEF", "#702082", "#002E5D",
                                "#616AB1", "#9A4F9F", "#007BBF", "#E6007E",
                            ]
                        )
                        VG.resize_relationships(property="weight")
                        html_louvain = VG.render(layout=Layout.FORCE_DIRECTED, initial_zoom=0.15)
                        components.html(html_louvain.data, height=NETWORK_GRAPH_HEIGHT)
                    else:
                        st.warning("Nenhuma topologia Louvain encontrada para os parâmetros selecionados.")

            with col2:
                st.subheader("Panorama de Risco")
                with st.spinner("Agregando perfis de risco..."):
                    comm_df = analysis.run_query_df(profile_query)
                    if comm_df.empty:
                        st.warning("Sem dados de perfil de risco para os filtros selecionados.")
                    else:
                        sky_palette_12 = [
                            "#F00B47", "#E6007E", "#9A4F9F", "#702082",
                            "#533285", "#616AB1", "#002E5D", "#005B9A",
                            "#007BBF", "#0097D7", "#00AEEF", "#80D6F7",
                        ]
                        fig, ax = plt.subplots(figsize=(6, 4))
                        sns.scatterplot(
                            data=comm_df, x="community_id", y="churn_rate_pct",
                            size="total_customers", sizes=(100, 1500), hue="churn_rate_pct",
                            palette=sns.color_palette(sky_palette_12, as_cmap=True),
                            edgecolor="black", alpha=0.8, ax=ax,
                        )
                        ax.set_xlabel("ID da Comunidade Louvain")
                        ax.set_ylabel("Taxa de Churn (%)")
                        ax.axhline(26.5, color='red', linestyle='--', linewidth=1, label="Churn Médio")
                        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1))
                        st.pyplot(fig, use_container_width=True)

            # ── Clientes da comunidade com maior churn ────────────────────
            if not comm_df.empty:
                st.divider()
                st.subheader("Clientes da Comunidade com Maior Taxa de Churn")
                worst_comm = comm_df.sort_values("churn_rate_pct", ascending=False).iloc[0]
                worst_comm_id = worst_comm["community_id"]
                worst_churn_pct = worst_comm["churn_rate_pct"]
                worst_total = int(worst_comm["total_customers"])

                st.markdown(f"""
A comunidade **{worst_comm_id}** possui a maior taxa de churn: **{worst_churn_pct}%** entre {worst_total} clientes.
Abaixo estão os membros dessa comunidade — priorize ações de retenção para os clientes ativos deste grupo.
                """)

                worst_customers_query = f"""
                    MATCH (c:Customer)
                    WHERE c.louvain_community_id = toInteger('{worst_comm_id}')
                    RETURN c.customer_id AS CustomerID,
                           c.churn_label AS Churn,
                           c.macro_reason AS Motivo_Churn,
                           c.contract AS Contrato,
                           c.monthly_charges AS Mensalidade,
                           c.tenure_months AS Meses_Cliente,
                           c.internet_service AS Internet,
                           c.payment_method AS Pagamento,
                           c.city AS Cidade
                    ORDER BY c.churn_label DESC, c.monthly_charges DESC
                """
                with st.expander("Ver Consulta Cypher — Clientes da Comunidade"):
                    st.code(worst_customers_query, language="cypher")
                with st.spinner("Carregando clientes da comunidade..."):
                    worst_cust_df = analysis.run_query_df(worst_customers_query)
                if not worst_cust_df.empty:
                    # KPIs da comunidade
                    total_comm = len(worst_cust_df)
                    churned_comm = len(worst_cust_df[worst_cust_df["Churn"] == "Yes"])
                    active_comm = total_comm - churned_comm
                    avg_charge = worst_cust_df["Mensalidade"].mean()
                    comm_cards = [
                        {"icon": "👥", "label": "Total na Comunidade",   "value": str(total_comm),                     "color": "#002E5D", "bg": "#EBF4FF"},
                        {"icon": "📉", "label": "Já Churned",           "value": str(churned_comm),                    "color": "#D62828", "bg": "#FDECEA"},
                        {"icon": "✅", "label": "Ainda Ativos",          "value": str(active_comm),                     "color": "#2A9D8F", "bg": "#E8F5E9"},
                        {"icon": "💰", "label": "Mensalidade Média",    "value": f"${avg_charge:.2f}",                 "color": "#F77F00", "bg": "#FFF3E0"},
                    ]
                    cc_inner = "".join(
                        f"""<div class="kpi-card" style="--kc:{c['color']};--kb:{c['bg']};">
                                <div class="kpi-icon-wrap">{c['icon']}</div>
                                <div class="kpi-value">{c['value']}</div>
                                <div class="kpi-label">{c['label']}</div>
                            </div>"""
                        for c in comm_cards
                    )
                    st.markdown(f'<div class="kpi-grid" style="grid-template-columns: repeat(4, 1fr);">{cc_inner}</div>', unsafe_allow_html=True)

                    render_styled_table(worst_cust_df)
                else:
                    st.info("Nenhum cliente encontrado para essa comunidade.")

elif selected_section == "Falhas Geo-Espaciais":
    st.header("Hotspots Geo-Espaciais de Risco")
    render_section_intro(
        "Localidades onde clientes ativos de Suporte Técnico estão próximos a clientes que já cancelaram pelo mesmo motivo.",
        "Ajuste o raio de proximidade e veja no mapa quais CEPs concentram risco de churn por problemas técnicos.",
        "Equipes de campo priorizam manutenção preventiva nas áreas com maior densidade de risco.",
    )

    st.markdown("### Por que grafos são essenciais aqui?")
    st.markdown("""
<div class="intro-grid">
    <div class="intro-card" style="--ic:#0097D7;">
        <div class="intro-icon">🔗</div>
        <div class="intro-label">Travessia de Relacionamentos</div>
        <div class="intro-text">
            A consulta parte dos <b>clientes que já cancelaram</b> e que assinavam Suporte Técnico,
            percorre até sua <b>localização</b> via <code>LIVES_AT</code>, e então busca
            <b>clientes ativos</b> próximos com o mesmo serviço — tudo em uma única query.
        </div>
    </div>
    <div class="intro-card" style="--ic:#702082;">
        <div class="intro-icon">📍</div>
        <div class="intro-label">Funções Espaciais Nativas</div>
        <div class="intro-text">
            O Neo4j calcula <code>point.distance()</code> entre coordenadas geográficas nativamente,
            sem precisar de extensões GIS externas. Filtramos por <b>raio configurável</b> para
            encontrar apenas vizinhos dentro da zona de risco.
        </div>
    </div>
    <div class="intro-card" style="--ic:#16A085;">
        <div class="intro-icon">🎯</div>
        <div class="intro-label">Resultado Acionável</div>
        <div class="intro-text">
            O resultado é uma <b>lista de CEPs</b> com contagem de churners técnicos próximos e
            clientes ativos em risco — pronta para ser enviada à equipe de campo para
            <b>manutenção preventiva</b> ou <b>contato proativo</b>.
        </div>
    </div>
</div>
    """, unsafe_allow_html=True)

    st.divider()

    controls_col, output_col = st.columns([1, 2])

    with controls_col:
        with st.form("geo_hotspot_form"):
            km_radius = st.slider("Raio de Proximidade (km)", min_value=0.5, max_value=5.0, value=2.0, step=0.5, help="Distância máxima para considerar dois clientes como 'vizinhos geográficos'.")
            submitted_geo = st.form_submit_button("Identificar Hotspots")

    if submitted_geo:
        geo_query = f"""
            MATCH (churned:Customer {{churn_label: 'Yes'}})-[:SUBSCRIBES_TO]->(:Service {{service_type: 'tech_support'}})
            MATCH (churned)-[:LIVES_AT]->(bad_loc:Location)
            MATCH (active:Customer {{churn_label: 'No'}})-[:SUBSCRIBES_TO]->(:Service {{service_type: 'tech_support'}})
            MATCH (active)-[:LIVES_AT]->(nearby_loc:Location)
            WITH churned, bad_loc, active, nearby_loc,
                point.distance(bad_loc.location_point, nearby_loc.location_point) AS distance_meters
            WHERE distance_meters > 0 AND distance_meters < {km_radius} * 1000
            RETURN nearby_loc.zip_code AS CEP,
                nearby_loc.city AS Cidade,
                nearby_loc.latitude AS latitude,
                nearby_loc.longitude AS longitude,
                count(DISTINCT churned) AS Churners_Proximos,
                count(DISTINCT active) AS Ativos_em_Risco,
                round(avg(distance_meters)) AS Distancia_Media_m
            ORDER BY Churners_Proximos DESC, Ativos_em_Risco DESC
            """
        with output_col:
            with st.expander("Ver Consulta Cypher"):
                st.code(geo_query, language="cypher")
            with st.spinner("Calculando proximidade espacial..."):
                geo_df = analysis.run_query_df(geo_query)

            if not geo_df.empty:
                st.success(f"{len(geo_df)} hotspots identificados em um raio de {km_radius} km.")

                # KPIs
                total_ativos_risco = int(geo_df["Ativos_em_Risco"].sum())
                total_churners = int(geo_df["Churners_Proximos"].sum())
                top_city = geo_df.sort_values("Ativos_em_Risco", ascending=False).iloc[0]["Cidade"]
                geo_cards = [
                    {"icon": "📍", "label": "Hotspots Encontrados",   "value": str(len(geo_df)),        "color": "#D62828", "bg": "#FDECEA"},
                    {"icon": "👥", "label": "Ativos em Risco",        "value": f"{total_ativos_risco}",  "color": "#F77F00", "bg": "#FFF3E0"},
                    {"icon": "📉", "label": "Churners Próximos",      "value": f"{total_churners}",      "color": "#002E5D", "bg": "#EBF4FF"},
                    {"icon": "🏙️", "label": "Cidade Mais Crítica",    "value": str(top_city),            "color": "#0097D7", "bg": "#E6F7FF"},
                ]
                gc_inner = "".join(
                    f"""<div class="kpi-card" style="--kc:{c['color']};--kb:{c['bg']};">
                            <div class="kpi-icon-wrap">{c['icon']}</div>
                            <div class="kpi-value">{c['value']}</div>
                            <div class="kpi-label">{c['label']}</div>
                        </div>"""
                    for c in geo_cards
                )
                st.markdown(f'<div class="kpi-grid" style="grid-template-columns: repeat(4, 1fr);">{gc_inner}</div>', unsafe_allow_html=True)

                # Mapa
                gdf = gpd.GeoDataFrame(
                    geo_df,
                    geometry=gpd.points_from_xy(geo_df.longitude, geo_df.latitude),
                    crs="EPSG:4326",
                )
                gdf_wm = gdf.to_crs(epsg=3857)
                fig, ax = plt.subplots(figsize=(6, 4))
                gdf_wm.plot(
                    ax=ax,
                    column="Ativos_em_Risco",
                    cmap="YlOrRd",
                    markersize=gdf_wm["Ativos_em_Risco"] * 50,
                    alpha=0.8,
                    edgecolors="#000000",
                    linewidth=1.0,
                    legend=True,
                    legend_kwds={"label": "Ativos em Risco", "shrink": 0.6},
                )
                ctx.add_basemap(ax, crs=gdf_wm.crs.to_string(), source=ctx.providers.OpenStreetMap.Mapnik)
                ax.set_axis_off()
                ax.set_title("Hotspots Geo-Espaciais de Risco Técnico", fontsize=12, fontweight="light", pad=15, color="#333333")
                plt.tight_layout()
                st.pyplot(fig, use_container_width=True)
                st.caption(f"Tamanho e cor indicam o número de clientes ativos em risco dentro de {km_radius} km de churners técnicos.")

                # Tabela
                st.subheader("Detalhamento por Localidade")
                render_styled_table(geo_df.drop(columns=["latitude", "longitude"]))
            else:
                st.warning("Nenhum hotspot encontrado com os parâmetros selecionados. Tente aumentar o raio.")

elif selected_section == "Heatmap de Churn":
    st.header("Heatmap de Churn por Segmento")
    render_section_intro(
        "Taxas de churn por segmento de contrato e método de pagamento, com filtro opcional por cidade.",
        "Escolha a cidade e o tamanho mínimo do segmento à esquerda, depois inspecione as células de alto risco no heatmap.",
        "Padrões de churn por segmento refinam ofertas, incentivos de pagamento e estratégias de migração de contrato.",
    )

    st.markdown("### Por que esta análise demonstra o poder dos grafos?")
    st.markdown("""
<div class="intro-grid">
    <div class="intro-card" style="--ic:#D62828;">
        <div class="intro-icon">🔄</div>
        <div class="intro-label">SQL: 3 JOINs + GROUP BY</div>
        <div class="intro-text">
            Em SQL tradicional, cruzar contrato × pagamento × cidade × churn requer
            <b>3 JOINs</b> entre tabelas separadas (customers, contracts, payments, locations)
            com <b>GROUP BY</b> complexo e subqueries para calcular taxas.
        </div>
    </div>
    <div class="intro-card" style="--ic:#2A9D8F;">
        <div class="intro-icon">🕸️</div>
        <div class="intro-label">Grafo: Travessia Natural</div>
        <div class="intro-text">
            No Neo4j, simplesmente <b>percorremos</b> de Customer para Contract via <code>HAS_CONTRACT</code>,
            para PaymentMethod via <code>PAYS_WITH</code>, e para Location via <code>LIVES_AT</code>.
            A consulta é <b>declarativa e legível</b>, sem JOINs explícitos.
        </div>
    </div>
    <div class="intro-card" style="--ic:#002E5D;">
        <div class="intro-icon">⚡</div>
        <div class="intro-label">Vantagem: Flexibilidade</div>
        <div class="intro-text">
            Adicionar uma nova dimensão (ex: serviços, filme assistido) é apenas <b>mais uma travessia</b>,
            sem redesenhar tabelas ou criar novos JOINs. O modelo de grafo escala naturalmente
            com a complexidade do negócio.
        </div>
    </div>
</div>
    """, unsafe_allow_html=True)

    st.divider()

    @st.cache_data(show_spinner=False)
    def load_cities():
        city_df = analysis.run_query_df(
            """
            MATCH (:Customer)-[:LIVES_AT]->(l:Location)
            WHERE l.city IS NOT NULL
            RETURN DISTINCT l.city AS city
            ORDER BY city
            """
        )
        return ["Todas as Cidades"] + city_df["city"].tolist() if not city_df.empty else ["Todas as Cidades"]

    city_options = load_cities()

    controls_col, output_col = st.columns([1, 2])

    with controls_col:
        with st.form("heatmap_form"):
            selected_city = st.selectbox("Cidade", city_options, help="Filtre o heatmap por cidade ou exiba todas.")
            minimum_customers = st.slider("Mínimo de Clientes por Segmento", min_value=10, max_value=50, value=20, step=10, help="Tamanho mínimo para inclusão no heatmap?")
            submitted_heatmap = st.form_submit_button("Gerar Heatmap de Churn")

    if submitted_heatmap:
        sanitized_city = selected_city.replace("'", "\\'")
        city_filter = "" if selected_city == "Todas as Cidades" else f"WHERE l.city = '{sanitized_city}'"

        churn_heatmap_query = f"""
            MATCH (c:Customer)-[:HAS_CONTRACT]->(ct:Contract)
            MATCH (c)-[:PAYS_WITH]->(p:PaymentMethod)
            MATCH (c)-[:LIVES_AT]->(l:Location)
            {city_filter}
            WITH ct.contract AS contract, p.payment_method AS payment_method,
                count(c) AS total_customers,
                sum(CASE WHEN c.churn_label = 'Yes' THEN 1 ELSE 0 END) AS churned_customers
            WHERE contract IS NOT NULL AND payment_method IS NOT NULL AND total_customers > {minimum_customers}
            RETURN contract, payment_method, total_customers,
                round((toFloat(churned_customers) / total_customers) * 100, 2) AS churn_rate_pct
            ORDER BY churn_rate_pct DESC
        """

        with output_col:
            with st.expander("Ver Consulta Cypher"):
                st.code(churn_heatmap_query, language="cypher")

            with st.spinner("Construindo heatmap de churn..."):
                heatmap_df = analysis.run_query_df(churn_heatmap_query)

            if heatmap_df.empty:
                st.warning("Sem dados de churn para os segmentos selecionados.")
            else:
                st.success("Heatmap de churn gerado.")
                pivot_df = heatmap_df.pivot(index="contract", columns="payment_method", values="churn_rate_pct")
                fig, ax = plt.subplots(figsize=(6, 4))
                sns.heatmap(pivot_df, annot=True, fmt=".1f", cmap="YlOrRd", linewidths=0.5, cbar_kws={"label": "Churn %"}, ax=ax)
                ax.set_xlabel("Método de Pagamento")
                ax.set_ylabel("Tipo de Contrato")
                ax.set_title("Taxa de Churn: Contrato × Método de Pagamento")
                st.pyplot(fig, use_container_width=True)
                st.caption(f"Células mostram % de churn para segmentos com mais de {minimum_customers} clientes.")

elif selected_section == "Recomendações de Filmes":
    st.header("Recomendações de Filmes")
    render_section_intro(
        "Principais filmes candidatos baseados no histórico de clientes similares.",
        "Insira o customer_id e a quantidade de recomendações à esquerda, depois revise a lista ranqueada à direita.",
        "O ranqueamento combina similaridade comportamental e sinal de preferência para maior relevância.",
    )
    st.markdown("""
Recomendação baseada no que clientes similares assistiram e avaliaram,
excluindo filmes que este cliente já assistiu ou avaliou.
    """)

    controls_col, output_col = st.columns([1, 2])

    with controls_col:
        with st.form("movie_recommendation_form"):
            customer_id = st.text_input(
                "ID do Cliente",
                value="7517-SAWMO",
                help="Informe um customer_id para obter recomendações.",
            )
            recommendation_count = st.slider(
                "Número de Recomendações",
                min_value=1, max_value=10, value=5,
                help="Quantas recomendações retornar?",
            )
            submitted_recommendations = st.form_submit_button("Recomendar Filmes")

    if submitted_recommendations:
        sanitized_customer_id = customer_id.replace("'", "\\'")
        recommendation_query = f"""
            MATCH (c:Customer {{customer_id: '{sanitized_customer_id}'}})
            OPTIONAL MATCH (c)-[:WATCHED_MOVIE]->(seen:Movie)
            OPTIONAL MATCH (c)-[:RATED]->(rated_seen:Movie)
            WITH c, collect(DISTINCT seen) + collect(DISTINCT rated_seen) AS seen_movies
            MATCH (c)-[:SIMILAR_TO]-(sim:Customer)-[:WATCHED_MOVIE]->(m:Movie)
            OPTIONAL MATCH (sim)-[r:RATED]->(m)
            WHERE NOT m IN seen_movies
            RETURN m.title AS movie_title,
                   count(DISTINCT sim) AS similar_customers_who_watched,
                   count(r) AS ratings_count,
                   round(avg(r.rating), 2) AS avg_rating
            ORDER BY similar_customers_who_watched DESC,
                     avg_rating DESC,
                     ratings_count DESC,
                     movie_title ASC
            LIMIT {recommendation_count}
        """

        with output_col:
            with st.expander("Ver Consulta Cypher"):
                st.code(recommendation_query, language="cypher")
            with st.spinner("Gerando recomendações..."):
                recommendations_df = analysis.run_query_df(recommendation_query)
            if recommendations_df.empty:
                st.warning("Nenhuma recomendação encontrada. Tente um ID diferente.")
            else:
                st.success("Recomendações de filmes geradas.")
                render_styled_table(recommendations_df)

elif selected_section == "Previsão de Risco com KNN":
    st.header("Previsão de Risco de Churn com KNN")
    render_section_intro(
        "Razão macro de churn prevista para clientes ativos com base nas relações NEAREST_NEIGHBOR.",
        "Revise a tabela de previsões, depois selecione um customer_id para inspecionar o subgrafo NEAREST_NEIGHBOR.",
        "Sinais baseados em vizinhança apoiam a priorização de retenção com explicabilidade.",
    )

    # ── Explicação do método ─────────────────────────────────────────────
    st.markdown("### Como funciona o KNN em Grafo?")
    st.markdown("""
**Objetivo:** Encontrar para cada cliente os 5 clientes mais parecidos com ele,
levando em conta tanto o perfil individual quanto **todas as suas conexões** no grafo.
    """)
    st.markdown("""
<div class="intro-grid">
    <div class="intro-card" style="--ic:#0097D7;">
        <div class="intro-icon">1️⃣</div>
        <div class="intro-label">Passo 1 — Embedding com FastRP</div>
        <div class="intro-text">
            Um algoritmo (<b>FastRP</b>) percorre toda a rede de relacionamentos de cada cliente —
            onde mora, como paga, que contrato tem, que serviços usa — e transforma tudo isso em uma
            <b>"impressão digital" numérica</b> (embedding). Dois clientes com conexões parecidas
            terão impressões digitais parecidas, mesmo que não se conheçam diretamente.
        </div>
    </div>
    <div class="intro-card" style="--ic:#702082;">
        <div class="intro-icon">2️⃣</div>
        <div class="intro-label">Passo 2 — Features Híbridas</div>
        <div class="intro-text">
            Combinamos essa impressão digital (embedding estrutural) com dados que sabemos que importam:
            <b>valor da mensalidade</b>, <b>tempo como cliente</b>, se é <b>idoso</b>, se tem <b>parceiro</b>
            e se tem <b>dependentes</b>. Essa combinação (hybrid features) captura tanto a estrutura do grafo
            quanto atributos individuais.
        </div>
    </div>
    <div class="intro-card" style="--ic:#16A085;">
        <div class="intro-icon">3️⃣</div>
        <div class="intro-label">Passo 3 — KNN e Predição</div>
        <div class="intro-text">
            O <b>KNN (K-Nearest Neighbors)</b> compara todos os clientes usando essas features combinadas
            e conecta cada um aos <b>5 mais parecidos</b> via a relação <code>NEAREST_NEIGHBOR</code>
            com uma nota de similaridade. Para prever risco: se a maioria dos 5 vizinhos já cancelou,
            o cliente está em alto risco — e o <b>motivo dos vizinhos direciona a oferta de retenção</b>.
        </div>
    </div>
</div>
    """, unsafe_allow_html=True)

    st.info("""
**Como usar na prática:** Para qualquer cliente ativo, basta olhar seus 5 vizinhos mais próximos.
Se a maioria já cancelou, esse cliente está em alto risco. O motivo do churn dos vizinhos
(ex: preço, concorrência, atendimento) indica qual oferta de retenção tem maior chance de sucesso.
    """)

    st.divider()
    st.markdown("### Resultados da Previsão por Votação de Vizinhos")
    st.markdown("""
A consulta abaixo executa uma **votação majoritária** entre os vizinhos KNN de cada cliente ativo:
para cada cliente, conta quantos dos seus vizinhos churned compartilham cada motivo de churn
e retorna o motivo mais votado como predição, com um score de confiança (proporção de votos).
    """)

    prediction_query = """
MATCH (active:Customer {churn_label: 'No'})
MATCH (active)-[rel:NEAREST_NEIGHBOR]->(churned:Customer {churn_label: 'Yes'})
WHERE churned.macro_reason IS NOT NULL
WITH active, churned.macro_reason AS predicted_reason, count(*) AS votes
ORDER BY active.customer_id, votes DESC
WITH active, collect({reason: predicted_reason, votes: votes})[0] AS top_prediction
RETURN active.customer_id AS CustomerID,
       top_prediction.reason AS PredictedFlightRisk,
       (toFloat(top_prediction.votes) / 5.0) AS ConfidenceScore
ORDER BY ConfidenceScore DESC, CustomerID
"""

    with st.expander("Ver Consulta Cypher"):
        st.code(prediction_query, language="cypher")

    with st.spinner("Executando consulta de previsão KNN..."):
        results_df = analysis.run_query_df(prediction_query)

    if results_df.empty:
        st.warning("Nenhum resultado de previsão encontrado.")
    else:
        st.success("Resultados de previsão gerados.")
        left_col, right_col = st.columns([1, 1])

        with left_col:
            st.subheader("Resultados de Previsão")
            render_styled_table(results_df)

            # Distribuição de riscos previstos
            st.subheader("Distribuição dos Riscos Previstos")
            risk_dist = results_df.groupby("PredictedFlightRisk").agg(
                Clientes=("CustomerID", "count"),
                Confianca_Media=("ConfidenceScore", "mean"),
            ).reset_index().sort_values("Clientes", ascending=False)
            render_styled_table(risk_dist)

            risk_palette = ["#D62828", "#F77F00", "#FCBF49", "#002E5D", "#0097D7", "#2A9D8F", "#702082", "#616AB1"]
            fig_risk, ax_risk = plt.subplots(figsize=(6, 3.5))
            ax_risk.barh(
                risk_dist["PredictedFlightRisk"],
                risk_dist["Clientes"],
                color=risk_palette[:len(risk_dist)],
                edgecolor="white",
            )
            ax_risk.set_xlabel("Nº de Clientes")
            ax_risk.set_title("Clientes em Risco por Motivo Previsto")
            ax_risk.invert_yaxis()
            plt.tight_layout()
            st.pyplot(fig_risk, use_container_width=True)

        ranked_df = results_df.sort_values(
            by=["ConfidenceScore", "CustomerID"],
            ascending=[False, True],
        )
        customer_options = ranked_df["CustomerID"].dropna().astype(str).tolist()
        default_customer_id = str(ranked_df.iloc[0]["CustomerID"])

        with right_col:
            st.subheader("Grafo NEAREST_NEIGHBOR")
            selected_customer_id = st.selectbox(
                "Selecione um customer_id para visualizar",
                options=customer_options,
                index=customer_options.index(default_customer_id),
            )

            graph_query = f"""
                MATCH p=(active:Customer {{customer_id: '{selected_customer_id}'}})-[:NEAREST_NEIGHBOR]->(churned:Customer {{churn_label: 'Yes'}})
                WHERE churned.macro_reason IS NOT NULL
                RETURN p
                """

            with st.expander("Ver Consulta do Grafo NEAREST_NEIGHBOR"):
                st.code(graph_query, language="cypher")

            with st.spinner("Renderizando grafo de vizinhança..."):
                results_knn_graph = analysis.run_query_viz(graph_query)

            if results_knn_graph:
                st.success("Grafo NEAREST_NEIGHBOR gerado.")
                VG = from_neo4j(results_knn_graph)
                VG.color_nodes(field="caption", color_space=ColorSpace.DISCRETE, colors=colors)
                VG.resize_nodes(property="monthly_charges", node_radius_min_max=(10, 30))
                analysis.set_caption_by_label(VG, label_to_property)
                html_knn = VG.render(layout=Layout.FORCE_DIRECTED, initial_zoom=0.75)
                components.html(html_knn.data, height=NETWORK_GRAPH_HEIGHT)
            else:
                st.warning("Nenhum dado NEAREST_NEIGHBOR encontrado para o cliente selecionado.")

            # Detalhes dos vizinhos
            if selected_customer_id:
                neighbor_detail_query = f"""
                    MATCH (active:Customer {{customer_id: '{selected_customer_id}'}})-[rel:NEAREST_NEIGHBOR]->(neighbor:Customer)
                    RETURN neighbor.customer_id AS Vizinho,
                           neighbor.churn_label AS Churn,
                           neighbor.macro_reason AS Motivo_Churn,
                           round(rel.similarity_score, 4) AS Similaridade,
                           neighbor.monthly_charges AS Mensalidade,
                           neighbor.tenure_months AS Meses_Cliente,
                           neighbor.contract AS Contrato,
                           neighbor.internet_service AS Internet
                    ORDER BY rel.similarity_score DESC
                """
                with st.spinner("Carregando detalhes dos vizinhos..."):
                    neighbor_df = analysis.run_query_df(neighbor_detail_query)
                if not neighbor_df.empty:
                    st.subheader("Detalhes dos 5 Vizinhos Mais Próximos")
                    render_styled_table(neighbor_df)

elif selected_section == "── Topologia de Rede ──":
    st.header("O Poder dos Grafos na Topologia de Rede Telco")
    render_section_intro(
        "Visão geral de como o grafo modela a infraestrutura física da rede, do Core ao CPE do cliente.",
        "Navegue pelas subseções de topologia na barra lateral para explorar cada camada da rede.",
        "Grafos revelam dependências, caminhos críticos e impacto de falhas que são invisíveis em tabelas.",
    )
    st.markdown("""
A topologia de rede de telecomunicações é inerentemente um **grafo hierárquico**. Cada camada se conecta
à próxima através de relações `CONNECTS_TO`, formando o caminho completo que os dados percorrem
desde o backbone até o equipamento do cliente.

**Hierarquia da Rede:**
- **CoreNetwork** → Backbone DWDM de alta capacidade (400 Gbps), nível Tier-1
- **RegionalHub** → Hubs OTN regionais que agregam tráfego de múltiplas cidades
- **CentralOffice** → Escritórios centrais (OLT/DSLAM) que servem bairros
- **DistributionCabinet** → Armários de distribuição com splitters ópticos
- **AccessNode** → Nós de acesso (GPON/VDSL2) que atendem assinantes diretamente
- **CPE** → Equipamento na casa do cliente (ONT ou Modem DSL)
- **Customer** → O assinante final

**Por que grafos são ideais aqui?**

Em um banco de dados relacional, rastrear o caminho completo de um cliente até o Core requer
múltiplos JOINs entre 7 tabelas. No Neo4j, é uma simples travessia de relacionamentos.
Além disso, consultas como "quais clientes são impactados por uma falha neste equipamento?"
ou "existe um caminho alternativo?" tornam-se triviais com grafos.
    """)

    # KPIs de infraestrutura
    infra_kpi_query = """
        MATCH (cn:CoreNetwork) WITH count(cn) AS cores
        MATCH (rh:RegionalHub) WITH cores, count(rh) AS hubs
        MATCH (co:CentralOffice) WITH cores, hubs, count(co) AS offices
        MATCH (dc:DistributionCabinet) WITH cores, hubs, offices, count(dc) AS cabinets
        MATCH (an:AccessNode) WITH cores, hubs, offices, cabinets, count(an) AS access_nodes
        MATCH (cpe:CPE) WITH cores, hubs, offices, cabinets, access_nodes, count(cpe) AS cpes
        RETURN cores, hubs, offices, cabinets, access_nodes, cpes
    """
    with st.spinner("Carregando KPIs de infraestrutura..."):
        infra_df = analysis.run_query_df(infra_kpi_query)
    if not infra_df.empty:
        row = infra_df.iloc[0]
        infra_cards = [
            {"icon": "🌐", "label": "Core Networks",          "value": f"{int(row['cores'])}",         "color": "#D62828", "bg": "#FDECEA"},
            {"icon": "🏢", "label": "Hubs Regionais",         "value": f"{int(row['hubs'])}",          "color": "#F77F00", "bg": "#FFF3E0"},
            {"icon": "🏭", "label": "Escritórios Centrais",   "value": f"{int(row['offices'])}",       "color": "#FCBF49", "bg": "#FFFDE7"},
            {"icon": "📦", "label": "Armários Distribuição",   "value": f"{int(row['cabinets'])}",      "color": "#003049", "bg": "#E3F2FD"},
            {"icon": "📡", "label": "Nós de Acesso",          "value": f"{int(row['access_nodes'])}",  "color": "#0097D7", "bg": "#E6F7FF"},
            {"icon": "📶", "label": "CPEs (ONT/Modem)",       "value": f"{int(row['cpes']):,}",        "color": "#2A9D8F", "bg": "#E8F5E9"},
        ]
        inner = "".join(
            f"""<div class="kpi-card" style="--kc:{c['color']};--kb:{c['bg']};">
                    <div class="kpi-icon-wrap">{c['icon']}</div>
                    <div class="kpi-value">{c['value']}</div>
                    <div class="kpi-label">{c['label']}</div>
                </div>"""
            for c in infra_cards
        )
        st.markdown(f'<div class="kpi-grid">{inner}</div>', unsafe_allow_html=True)

elif selected_section == "Visão Hierárquica da Rede":
    st.header("Visão Hierárquica da Rede")
    render_section_intro(
        "Topologia completa da rede, do CoreNetwork até os AccessNodes, visualizada como grafo interativo.",
        "Selecione a profundidade e a região para explorar a hierarquia. Clique nos nós para ver propriedades.",
        "A visão hierárquica revela pontos únicos de falha e dependências críticas entre camadas.",
    )
    st.markdown("""
Visualize a árvore de infraestrutura da rede. Cada nível da hierarquia é colorido de forma distinta,
permitindo identificar rapidamente a estrutura e as dependências entre camadas.
Com grafos, podemos percorrer toda a topologia com uma única consulta Cypher.
    """)

    controls_col, output_col = st.columns([1, 2])

    with controls_col:
        with st.form("network_topology_form"):
            depth_options = {
                "Core → Hubs Regionais": 1,
                "Core → Escritórios Centrais": 2,
                "Core → Armários de Distribuição": 3,
                "Core → Nós de Acesso": 4,
            }
            selected_depth_label = st.selectbox(
                "Profundidade da Hierarquia",
                options=list(depth_options.keys()),
                index=1,
                help="Quantas camadas da rede exibir a partir do Core?",
            )
            selected_depth = depth_options[selected_depth_label]
            submitted_topo = st.form_submit_button("Visualizar Topologia")

    if submitted_topo:
        topo_query = f"""
            MATCH path = (cn:CoreNetwork)-[:CONNECTS_TO*1..{selected_depth}]->(target)
            WHERE NOT target:CPE AND NOT target:Customer
            RETURN path
        """
        with output_col:
            with st.expander("Ver Consulta Cypher"):
                st.code(topo_query, language="cypher")
            with st.spinner("Renderizando topologia da rede..."):
                results_topo = analysis.run_query_viz(topo_query)
            if results_topo:
                st.success("Topologia da rede gerada com sucesso.")
                VG = from_neo4j(results_topo)
                VG.color_nodes(
                    field="caption",
                    color_space=ColorSpace.DISCRETE,
                    colors=network_colors,
                )
                analysis.set_caption_by_label(VG, network_label_to_property)
                html_topo = VG.render(layout=Layout.HIERARCHICAL, initial_zoom=0.5)
                components.html(html_topo.data, height=NETWORK_GRAPH_HEIGHT + 100)

                # Tabela resumo por camada
                summary_query = f"""
                    MATCH path = (cn:CoreNetwork)-[:CONNECTS_TO*1..{selected_depth}]->(target)
                    WHERE NOT target:CPE AND NOT target:Customer
                    WITH target, labels(target)[0] AS camada, target.status AS status
                    RETURN camada AS Camada,
                           count(*) AS Total,
                           sum(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) AS Ativos,
                           sum(CASE WHEN status <> 'Active' THEN 1 ELSE 0 END) AS Inativos
                    ORDER BY CASE camada
                        WHEN 'CoreNetwork' THEN 0
                        WHEN 'RegionalHub' THEN 1
                        WHEN 'CentralOffice' THEN 2
                        WHEN 'DistributionCabinet' THEN 3
                        WHEN 'AccessNode' THEN 4
                        ELSE 5 END
                """
                summary_df = analysis.run_query_df(summary_query)
                if not summary_df.empty:
                    st.subheader("Resumo por Camada")
                    render_styled_table(summary_df)
            else:
                st.warning("Nenhum dado de topologia encontrado.")

elif selected_section == "Rastreamento de Caminho do Cliente":
    st.header("Rastreamento de Caminho: Cliente → Core")
    render_section_intro(
        "O caminho físico completo de um cliente até o backbone da rede, passando por todas as camadas.",
        "Insira um customer_id e visualize toda a cadeia de equipamentos que o conecta à rede.",
        "Essencial para troubleshooting: identifica exatamente quais equipamentos servem cada cliente.",
    )
    st.markdown("""
Uma das consultas mais poderosas em grafos para telcos: dado um cliente, qual é o caminho completo
até o core da rede? No Neo4j, isso é uma simples travessia de caminho variável.
Em SQL, seria necessário um encadeamento de 6+ JOINs com condições complexas.
    """)

    controls_col, output_col = st.columns([1, 2])

    with controls_col:
        with st.form("path_trace_form"):
            trace_customer_id = st.text_input(
                "Customer ID",
                value="3668-QPYBK",
                help="Informe um customer_id para rastrear o caminho até o Core.",
            )
            submitted_trace = st.form_submit_button("Rastrear Caminho")

    if submitted_trace:
        sanitized_trace_id = trace_customer_id.replace("'", "\\'")
        path_query = f"""
            MATCH path = (cust:Customer {{customer_id: '{sanitized_trace_id}'}})<-[:CONNECTS_TO]-(cpe:CPE)<-[:CONNECTS_TO]-(an:AccessNode)<-[:CONNECTS_TO]-(dc:DistributionCabinet)<-[:CONNECTS_TO]-(co:CentralOffice)<-[:CONNECTS_TO]-(rh:RegionalHub)<-[:CONNECTS_TO]-(cn:CoreNetwork)
            RETURN path
        """
        with output_col:
            with st.expander("Ver Consulta Cypher"):
                st.code(path_query, language="cypher")
            with st.spinner("Rastreando caminho na rede..."):
                results_path = analysis.run_query_viz(path_query)
            if results_path:
                st.success("Caminho rastreado com sucesso.")
                VG = from_neo4j(results_path)
                VG.color_nodes(
                    field="caption",
                    color_space=ColorSpace.DISCRETE,
                    colors=network_colors,
                )
                analysis.set_caption_by_label(VG, network_label_to_property)
                html_path = VG.render(layout=Layout.HIERARCHICAL, initial_zoom=0.8)
                components.html(html_path.data, height=NETWORK_GRAPH_HEIGHT)

                # Detalhes do caminho em tabela
                detail_query = f"""
                    MATCH (cust:Customer {{customer_id: '{sanitized_trace_id}'}})<-[:CONNECTS_TO]-(cpe:CPE)<-[:CONNECTS_TO]-(an:AccessNode)<-[:CONNECTS_TO]-(dc:DistributionCabinet)<-[:CONNECTS_TO]-(co:CentralOffice)<-[:CONNECTS_TO]-(rh:RegionalHub)<-[:CONNECTS_TO]-(cn:CoreNetwork)
                    RETURN cn.name AS Core,
                           rh.name AS Hub_Regional,
                           co.name AS Escritorio_Central,
                           dc.name AS Armario_Distribuicao,
                           an.name AS No_Acesso,
                           an.technology AS Tecnologia,
                           cpe.cpe_id AS CPE,
                           cpe.model AS Modelo_CPE,
                           cust.customer_id AS Cliente
                """
                detail_df = analysis.run_query_df(detail_query)
                if not detail_df.empty:
                    st.subheader("Detalhes do Caminho")
                    render_styled_table(detail_df)

                    # Métricas do caminho
                    metrics_query = f"""
                        MATCH (cust:Customer {{customer_id: '{sanitized_trace_id}'}})<-[r1:CONNECTS_TO]-(cpe:CPE)<-[r2:CONNECTS_TO]-(an:AccessNode)<-[r3:CONNECTS_TO]-(dc:DistributionCabinet)<-[r4:CONNECTS_TO]-(co:CentralOffice)<-[r5:CONNECTS_TO]-(rh:RegionalHub)<-[r6:CONNECTS_TO]-(cn:CoreNetwork)
                        RETURN round(coalesce(r2.distance_km, 0) + coalesce(r3.distance_km, 0) + coalesce(r4.distance_km, 0) + coalesce(r5.distance_km, 0) + coalesce(r6.distance_km, 0), 2) AS distancia_total_km,
                               coalesce(r2.latency_ms, 0) + coalesce(r3.latency_ms, 0) + coalesce(r4.latency_ms, 0) + coalesce(r5.latency_ms, 0) + coalesce(r6.latency_ms, 0) AS latencia_total_ms,
                               r1.connection_type AS tipo_conexao_cpe,
                               an.technology AS tecnologia_acesso
                    """
                    metrics_df = analysis.run_query_df(metrics_query)
                    if not metrics_df.empty:
                        m = metrics_df.iloc[0]
                        m_cards = [
                            {"icon": "📏", "label": "Distância Total",   "value": f"{m.get('distancia_total_km', 0)} km",  "color": "#003049", "bg": "#E3F2FD"},
                            {"icon": "⚡", "label": "Latência Total",    "value": f"{m.get('latencia_total_ms', 0)} ms",   "color": "#D62828", "bg": "#FDECEA"},
                            {"icon": "🔌", "label": "Conexão CPE",      "value": str(m.get('tipo_conexao_cpe', 'N/A')),   "color": "#2A9D8F", "bg": "#E8F5E9"},
                            {"icon": "📡", "label": "Tecnologia Acesso", "value": str(m.get('tecnologia_acesso', 'N/A')),  "color": "#F77F00", "bg": "#FFF3E0"},
                        ]
                        m_inner = "".join(
                            f"""<div class="kpi-card" style="--kc:{c['color']};--kb:{c['bg']};">
                                    <div class="kpi-icon-wrap">{c['icon']}</div>
                                    <div class="kpi-value">{c['value']}</div>
                                    <div class="kpi-label">{c['label']}</div>
                                </div>"""
                            for c in m_cards
                        )
                        st.markdown(f'<div class="kpi-grid" style="grid-template-columns: repeat(4, 1fr);">{m_inner}</div>', unsafe_allow_html=True)
            else:
                st.warning(f"Caminho não encontrado para o cliente '{trace_customer_id}'. Verifique o ID.")

elif selected_section == "Capacidade e Utilização":
    st.header("Capacidade e Utilização dos Nós de Acesso")
    render_section_intro(
        "Taxa de ocupação de cada Access Node, identificando gargalos e nós sobrecarregados.",
        "Revise a tabela de utilização e o gráfico de barras. Nós acima de 80% indicam risco operacional.",
        "Planejamento de capacidade proativo evita degradação de serviço e reduz churn por problemas técnicos.",
    )
    st.markdown("""
A análise de capacidade dos nós de acesso é fundamental para planejamento de rede.
No grafo, cada AccessNode possui `active_subscribers` e `capacity_subscribers`,
permitindo calcular a taxa de utilização instantaneamente.
Nós sobrecarregados (>80%) são candidatos prioritários para upgrade ou divisão de área.
    """)

    utilization_query = """
        MATCH (an:AccessNode)
        WHERE an.capacity_subscribers > 0
        RETURN an.name AS Nome,
               an.city AS Cidade,
               an.technology AS Tecnologia,
               an.vendor AS Vendor,
               an.active_subscribers AS Assinantes_Ativos,
               an.capacity_subscribers AS Capacidade,
               round(toFloat(an.active_subscribers) / an.capacity_subscribers * 100, 1) AS Utilizacao_Pct,
               an.status AS Status
        ORDER BY Utilizacao_Pct DESC
    """

    with st.expander("Ver Consulta Cypher"):
        st.code(utilization_query, language="cypher")

    with st.spinner("Carregando dados de utilização..."):
        util_df = analysis.run_query_df(utilization_query)

    if not util_df.empty:
        st.success("Dados de utilização carregados.")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("Tabela de Utilização")
            render_styled_table(util_df)

        with col2:
            st.subheader("Utilização por Nó de Acesso")
            fig, ax = plt.subplots(figsize=(6, max(4, len(util_df) * 0.35)))

            bar_colors = []
            for pct in util_df["Utilizacao_Pct"]:
                if pct >= 100:
                    bar_colors.append("#D62828")
                elif pct >= 80:
                    bar_colors.append("#F77F00")
                elif pct >= 60:
                    bar_colors.append("#FCBF49")
                else:
                    bar_colors.append("#2A9D8F")

            bars = ax.barh(
                util_df["Nome"],
                util_df["Utilizacao_Pct"],
                color=bar_colors,
                edgecolor="white",
                linewidth=0.5,
            )
            ax.axvline(x=80, color="#D62828", linestyle="--", linewidth=1.2, alpha=0.7, label="Limite 80%")
            ax.axvline(x=100, color="#000000", linestyle="-", linewidth=1, alpha=0.4, label="Capacidade 100%")
            ax.set_xlabel("Utilização (%)")
            ax.set_title("Taxa de Utilização dos Nós de Acesso")
            ax.legend(loc="lower right", fontsize=9)
            ax.invert_yaxis()
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)

            # KPIs de capacidade
            total_nodes = len(util_df)
            critical_nodes = len(util_df[util_df["Utilizacao_Pct"] >= 100])
            warning_nodes = len(util_df[(util_df["Utilizacao_Pct"] >= 80) & (util_df["Utilizacao_Pct"] < 100)])
            healthy_nodes = total_nodes - critical_nodes - warning_nodes
            cap_cards = [
                {"icon": "🔴", "label": "Críticos (≥100%)", "value": str(critical_nodes), "color": "#D62828", "bg": "#FDECEA"},
                {"icon": "🟡", "label": "Alerta (80-99%)",  "value": str(warning_nodes),  "color": "#F77F00", "bg": "#FFF3E0"},
                {"icon": "🟢", "label": "Saudáveis (<80%)", "value": str(healthy_nodes),  "color": "#2A9D8F", "bg": "#E8F5E9"},
            ]
            cap_inner = "".join(
                f"""<div class="kpi-card" style="--kc:{c['color']};--kb:{c['bg']};">
                        <div class="kpi-icon-wrap">{c['icon']}</div>
                        <div class="kpi-value">{c['value']}</div>
                        <div class="kpi-label">{c['label']}</div>
                    </div>"""
                for c in cap_cards
            )
            st.markdown(f'<div class="kpi-grid" style="grid-template-columns: repeat(3, 1fr);">{cap_inner}</div>', unsafe_allow_html=True)
    else:
        st.warning("Nenhum dado de Access Nodes encontrado.")

elif selected_section == "Análise de Impacto de Falhas":
    st.header("Análise de Impacto de Falhas em Cascata")
    render_section_intro(
        "Como falhas em equipamentos de rede se propagam e afetam clientes downstream via relações CAUSED e CONTRIBUTED_TO.",
        "Visualize o grafo de propagação de falhas, selecione um evento para ver o impacto completo até o cliente.",
        "Entender cascatas permite investir em resiliência nos pontos certos, reduzindo o impacto total em clientes.",
    )
    st.markdown("""
O grafo de manutenção modela **eventos de manutenção** ligados aos equipamentos que os originaram.
As relações `CAUSED` e `CONTRIBUTED_TO` entre eventos revelam como uma falha em um equipamento
pode causar degradação em outros — algo que só é possível modelar eficientemente com grafos.

**Exemplo real no grafo:** Uma falha de HVAC em um Escritório Central causou superaquecimento
nos equipamentos OLT downstream, gerando throttling térmico que afetou 137 clientes adicionais.
    """)

    controls_col, output_col = st.columns([1, 2])

    with controls_col:
        with st.form("impact_form"):
            show_cascades = st.checkbox("Mostrar apenas eventos com cascata", value=False, help="Filtrar apenas eventos que causaram outros eventos")
            submitted_impact = st.form_submit_button("Analisar Impacto de Falhas")

    if submitted_impact:
        # Grafo de falhas com cascatas
        cascade_graph_query = """
            MATCH (equip)-[hm:HAS_MAINTENANCE]->(m:MaintenanceEvent)
            OPTIONAL MATCH (m)-[caused:CAUSED]->(m2:MaintenanceEvent)
            OPTIONAL MATCH (m)-[contrib:CONTRIBUTED_TO]->(m3:MaintenanceEvent)
            WITH equip, hm, m, caused, m2, contrib, m3
            RETURN equip, hm, m, caused, m2, contrib, m3
        """

        if show_cascades:
            cascade_graph_query = """
                MATCH (equip)-[hm:HAS_MAINTENANCE]->(m:MaintenanceEvent)-[caused:CAUSED]->(m2:MaintenanceEvent)<-[hm2:HAS_MAINTENANCE]-(equip2)
                RETURN equip, hm, m, caused, m2, hm2, equip2
                UNION
                MATCH (equip)-[hm:HAS_MAINTENANCE]->(m:MaintenanceEvent)-[contrib:CONTRIBUTED_TO]->(m2:MaintenanceEvent)<-[hm2:HAS_MAINTENANCE]-(equip2)
                RETURN equip, hm, m, contrib AS caused, m2, hm2, equip2
            """

        with output_col:
            with st.expander("Ver Consulta Cypher"):
                st.code(cascade_graph_query, language="cypher")

            with st.spinner("Carregando grafo de impacto..."):
                results_impact = analysis.run_query_viz(cascade_graph_query)

            if results_impact:
                st.success("Grafo de impacto de falhas gerado.")
                VG = from_neo4j(results_impact)
                VG.color_nodes(
                    field="caption",
                    color_space=ColorSpace.DISCRETE,
                    colors=network_colors,
                )
                analysis.set_caption_by_label(VG, network_label_to_property)
                html_impact = VG.render(layout=Layout.FORCE_DIRECTED, initial_zoom=0.6)
                components.html(html_impact.data, height=NETWORK_GRAPH_HEIGHT + 60)
            else:
                st.warning("Nenhum grafo de impacto encontrado.")

            # Tabela de eventos
            events_query = """
                MATCH (equip)-[:HAS_MAINTENANCE]->(m:MaintenanceEvent)
                OPTIONAL MATCH (m)-[:CAUSED]->(cascaded:MaintenanceEvent)
                RETURN m.title AS Evento,
                       m.priority AS Prioridade,
                       m.status AS Status,
                       labels(equip)[0] AS Tipo_Equipamento,
                       equip.name AS Equipamento,
                       m.customers_affected AS Clientes_Afetados,
                       m.duration_hours AS Duracao_Horas,
                       m.sla_met AS SLA_Cumprido,
                       m.root_cause AS Causa_Raiz,
                       count(cascaded) AS Eventos_Cascata
                ORDER BY m.customers_affected DESC
            """
            st.subheader("Detalhamento de Eventos de Manutenção")
            with st.spinner("Carregando detalhamento..."):
                events_df = analysis.run_query_df(events_query)
            if not events_df.empty:
                render_styled_table(events_df)
            else:
                st.info("Nenhum evento de manutenção registrado.")

            # Relações de cascata
            cascade_detail_query = """
                MATCH (m1:MaintenanceEvent)-[r:CAUSED]->(m2:MaintenanceEvent)
                RETURN m1.title AS Evento_Origem,
                       m2.title AS Evento_Causado,
                       r.impact AS Descricao_Impacto,
                       m1.customers_affected AS Clientes_Origem,
                       m2.customers_affected AS Clientes_Cascata
                UNION
                MATCH (m1:MaintenanceEvent)-[r:CONTRIBUTED_TO]->(m2:MaintenanceEvent)
                RETURN m1.title AS Evento_Origem,
                       m2.title AS Evento_Causado,
                       r.reason AS Descricao_Impacto,
                       m1.customers_affected AS Clientes_Origem,
                       m2.customers_affected AS Clientes_Cascata
            """
            st.subheader("Cadeia de Causalidade entre Eventos")
            with st.spinner("Carregando cadeias de causalidade..."):
                cascade_df = analysis.run_query_df(cascade_detail_query)
            if not cascade_df.empty:
                render_styled_table(cascade_df)
            else:
                st.info("Nenhuma relação de cascata encontrada.")

    # ═══════════════════════════════════════════════════════════════════════
    # IMPACTO COMPLETO: Evento → Topologia → CPE → Cliente
    # ═══════════════════════════════════════════════════════════════════════
    st.divider()
    st.header("Impacto Completo: do Evento até o Cliente")
    render_section_intro(
        "Selecione um evento de manutenção e veja o grafo completo: equipamento → camadas da rede → CPEs → clientes afetados.",
        "Escolha o evento e o número de clientes amostrais para visualizar. O grafo mostra o caminho físico completo.",
        "Esta é a análise mais poderosa dos grafos para telco: rastrear o impacto real de uma falha até cada cliente.",
    )
    st.markdown("""
Em um banco de dados relacional, determinar quais clientes são afetados por uma falha em um
DistributionCabinet requer múltiplos JOINs encadeados (cabinet → access_nodes → cpes → customers).
No Neo4j, é uma **simples travessia de caminho variável** — e o resultado pode ser visualizado
como grafo, mostrando exatamente a cadeia física de impacto.

Selecione um evento de manutenção para visualizar:
- O **equipamento** onde ocorreu a falha e o **evento** de manutenção
- Todos os **AccessNodes** downstream conectados
- Uma **amostra de CPEs e Clientes** afetados em cada nó de acesso
- Eventuais **cascatas** (CAUSED/CONTRIBUTED_TO) desse evento
    """)

    # Carregar lista de eventos com clientes afetados
    event_list_query = """
        MATCH (equip)-[:HAS_MAINTENANCE]->(m:MaintenanceEvent)
        WHERE m.customers_affected > 0
        WITH m.title AS titulo, m.event_id AS event_id,
             m.customers_affected AS clientes, m.cost AS custo,
             m.priority AS prioridade, m.category AS categoria,
             collect(DISTINCT equip.name) AS equipamentos
        RETURN titulo, event_id, clientes, custo, prioridade, categoria, equipamentos
        ORDER BY clientes DESC
    """
    with st.spinner("Carregando lista de eventos..."):
        event_list_df = analysis.run_query_df(event_list_query)

    if not event_list_df.empty:
        event_display = [
            f"{row['titulo']}  ({row['prioridade']} · {row['clientes']} clientes · ${row['custo']:,})"
            for _, row in event_list_df.iterrows()
        ]

        controls_col2, output_col2 = st.columns([1, 2])

        with controls_col2:
            with st.form("full_impact_form"):
                selected_event_idx = st.selectbox(
                    "Evento de Manutenção",
                    range(len(event_display)),
                    format_func=lambda i: event_display[i],
                    help="Selecione um evento para ver o impacto completo na topologia até os clientes.",
                )
                sample_cpes_per_an = st.slider(
                    "CPEs/Clientes amostrais por Access Node",
                    min_value=1, max_value=10, value=3,
                    help="Quantos CPEs e clientes exibir por nó de acesso? (limita o tamanho do grafo)",
                )
                show_upstream = st.checkbox(
                    "Incluir caminho upstream (até o Core)",
                    value=False,
                    help="Mostrar também os equipamentos acima do equipamento que falhou (hub, core).",
                )
                submitted_full_impact = st.form_submit_button("Visualizar Impacto Completo")

        if submitted_full_impact:
            selected_event = event_list_df.iloc[selected_event_idx]
            event_title = selected_event["titulo"].replace("'", "\\'")
            event_id = selected_event["event_id"]

            # Construir query do grafo de impacto completo
            # 1. Equipamento → Evento (+ cascatas)
            # 2. Equipamento → AccessNodes downstream
            # 3. AccessNodes → amostra de CPEs → Clientes
            full_impact_query = f"""
                // Evento e equipamento afetado
                MATCH (equip)-[hm:HAS_MAINTENANCE]->(m:MaintenanceEvent {{event_id: '{event_id}'}})
                WITH equip, hm, m

                // Cascatas desse evento
                OPTIONAL MATCH (m)-[caused:CAUSED]->(m2:MaintenanceEvent)<-[hm2:HAS_MAINTENANCE]-(equip2)
                WITH equip, hm, m, caused, m2, hm2, equip2

                // AccessNodes downstream (direto ou via camadas intermediárias)
                OPTIONAL MATCH (equip)-[:CONNECTS_TO*0..3]->(an:AccessNode)
                WITH equip, hm, m, caused, m2, hm2, equip2, collect(DISTINCT an) AS all_ans

                // Amostrar CPEs e Customers por AccessNode
                UNWIND all_ans AS an
                OPTIONAL MATCH (an)-[c1:CONNECTS_TO]->(cpe:CPE)-[c2:CONNECTS_TO]->(cust:Customer)
                WITH equip, hm, m, caused, m2, hm2, equip2, an,
                     collect({{cpe: cpe, c1: c1, cust: cust, c2: c2}})[0..{sample_cpes_per_an}] AS samples

                // Retornar tudo
                UNWIND samples AS s
                RETURN equip, hm, m, caused, m2, hm2, equip2,
                       an, s.c1 AS c1, s.cpe AS cpe, s.c2 AS c2, s.cust AS cust
            """

            # Query upstream opcional
            if show_upstream:
                full_impact_query = f"""
                    // Evento e equipamento afetado
                    MATCH (equip)-[hm:HAS_MAINTENANCE]->(m:MaintenanceEvent {{event_id: '{event_id}'}})
                    WITH equip, hm, m

                    // Cascatas desse evento
                    OPTIONAL MATCH (m)-[caused:CAUSED]->(m2:MaintenanceEvent)<-[hm2:HAS_MAINTENANCE]-(equip2)
                    WITH equip, hm, m, caused, m2, hm2, equip2

                    // Caminho upstream até o Core
                    OPTIONAL MATCH upstream = (core)-[:CONNECTS_TO*1..5]->(equip)
                    WHERE core:CoreNetwork OR core:RegionalHub
                    WITH equip, hm, m, caused, m2, hm2, equip2, upstream

                    // AccessNodes downstream
                    OPTIONAL MATCH (equip)-[:CONNECTS_TO*0..3]->(an:AccessNode)
                    WITH equip, hm, m, caused, m2, hm2, equip2, upstream, collect(DISTINCT an) AS all_ans

                    // Amostrar CPEs e Customers
                    UNWIND all_ans AS an
                    OPTIONAL MATCH (an)-[c1:CONNECTS_TO]->(cpe:CPE)-[c2:CONNECTS_TO]->(cust:Customer)
                    WITH equip, hm, m, caused, m2, hm2, equip2, upstream, an,
                         collect({{cpe: cpe, c1: c1, cust: cust, c2: c2}})[0..{sample_cpes_per_an}] AS samples

                    UNWIND samples AS s
                    RETURN equip, hm, m, caused, m2, hm2, equip2, upstream,
                           an, s.c1 AS c1, s.cpe AS cpe, s.c2 AS c2, s.cust AS cust
                """

            with output_col2:
                with st.expander("Ver Consulta Cypher — Impacto Completo"):
                    st.code(full_impact_query, language="cypher")

                with st.spinner("Renderizando grafo de impacto completo até o cliente..."):
                    results_full = analysis.run_query_viz(full_impact_query)

                if results_full:
                    st.success(f"Grafo de impacto gerado para: {selected_event['titulo']}")

                    VG_full = from_neo4j(results_full)
                    VG_full.color_nodes(
                        field="caption",
                        color_space=ColorSpace.DISCRETE,
                        colors=network_colors,
                    )
                    VG_full.resize_nodes(property="customers_affected", node_radius_min_max=(8, 35))
                    analysis.set_caption_by_label(VG_full, network_label_to_property)
                    html_full = VG_full.render(layout=Layout.HIERARCHICAL, initial_zoom=0.35)
                    components.html(html_full.data, height=NETWORK_GRAPH_HEIGHT + 200)
                    st.caption("Grafo hierárquico: Evento → Equipamento → AccessNodes → CPEs → Clientes. Cores indicam o tipo de nó na topologia.")

                    # KPIs do evento
                    kpi_impact_query = f"""
                        MATCH (equip)-[:HAS_MAINTENANCE]->(m:MaintenanceEvent {{event_id: '{event_id}'}})
                        WITH equip, m
                        OPTIONAL MATCH (equip)-[:CONNECTS_TO*0..3]->(an:AccessNode)
                        WITH equip, m, count(DISTINCT an) AS access_nodes_afetados
                        OPTIONAL MATCH (equip)-[:CONNECTS_TO*0..4]->(cpe:CPE)
                        WITH equip, m, access_nodes_afetados, count(DISTINCT cpe) AS cpes_totais
                        OPTIONAL MATCH (equip)-[:CONNECTS_TO*0..5]->(cust:Customer)
                        WITH equip, m, access_nodes_afetados, cpes_totais, count(DISTINCT cust) AS clientes_potenciais
                        OPTIONAL MATCH (m)-[:CAUSED]->(cascaded:MaintenanceEvent)
                        RETURN m.title AS evento,
                               m.priority AS prioridade,
                               m.category AS categoria,
                               m.cost AS custo,
                               coalesce(m.revenue_at_risk, 0) AS receita_risco,
                               m.customers_affected AS clientes_reportados,
                               m.duration_hours AS duracao_h,
                               m.outage_duration_hours AS outage_h,
                               m.root_cause AS causa_raiz,
                               access_nodes_afetados,
                               cpes_totais AS cpes_potenciais,
                               clientes_potenciais,
                               count(cascaded) AS eventos_cascata
                    """
                    with st.spinner("Calculando métricas de impacto..."):
                        kpi_imp_df = analysis.run_query_df(kpi_impact_query)

                    if not kpi_imp_df.empty:
                        ki = kpi_imp_df.iloc[0]

                        impact_cards = [
                            {"icon": "🎯", "label": "Prioridade",             "value": str(ki.get('prioridade', 'N/A')),                  "color": "#D62828", "bg": "#FDECEA"},
                            {"icon": "💰", "label": "Custo Direto",           "value": f"${float(ki.get('custo', 0)):,.0f}",              "color": "#002E5D", "bg": "#EBF4FF"},
                            {"icon": "⚠️", "label": "Receita em Risco",      "value": f"${float(ki.get('receita_risco', 0)):,.0f}",      "color": "#F77F00", "bg": "#FFF3E0"},
                            {"icon": "👥", "label": "Clientes Reportados",    "value": f"{int(ki.get('clientes_reportados', 0)):,}",      "color": "#D62828", "bg": "#FDECEA"},
                            {"icon": "📡", "label": "Access Nodes Afetados",  "value": str(int(ki.get('access_nodes_afetados', 0))),      "color": "#0097D7", "bg": "#E6F7FF"},
                            {"icon": "📶", "label": "CPEs Potenciais",        "value": f"{int(ki.get('cpes_potenciais', 0)):,}",          "color": "#2A9D8F", "bg": "#E8F5E9"},
                        ]
                        ik_inner = "".join(
                            """<div class="kpi-card" style="--kc:{color};--kb:{bg};">
                                    <div class="kpi-icon-wrap">{icon}</div>
                                    <div class="kpi-value">{value}</div>
                                    <div class="kpi-label">{label}</div>
                                </div>""".format(**c)
                            for c in impact_cards
                        )
                        st.markdown(f'<div class="kpi-grid">{ik_inner}</div>', unsafe_allow_html=True)

                        # Causa raiz e detalhes
                        st.markdown(f"""
**Causa Raiz:** {ki.get('causa_raiz', 'N/A')}

**Duração:** {ki.get('duracao_h', 'N/A')} horas | **Outage:** {ki.get('outage_h', 'N/A')} horas | **Eventos em cascata:** {int(ki.get('eventos_cascata', 0))}
                        """)

                    # Tabela de clientes afetados (amostra real)
                    st.subheader("Amostra de Clientes Afetados")
                    affected_customers_query = f"""
                        MATCH (equip)-[:HAS_MAINTENANCE]->(m:MaintenanceEvent {{event_id: '{event_id}'}})
                        WITH equip
                        MATCH (equip)-[:CONNECTS_TO*0..3]->(an:AccessNode)-[:CONNECTS_TO]->(cpe:CPE)-[:CONNECTS_TO]->(cust:Customer)
                        RETURN DISTINCT cust.customer_id AS Customer_ID,
                               cust.city AS Cidade,
                               cust.contract AS Contrato,
                               cust.monthly_charges AS Mensalidade,
                               cust.churn_label AS Churn,
                               cust.internet_service AS Internet,
                               an.name AS Access_Node,
                               cpe.model AS Modelo_CPE
                        ORDER BY cust.monthly_charges DESC
                        LIMIT 20
                    """
                    with st.expander("Ver Consulta Cypher — Clientes Afetados"):
                        st.code(affected_customers_query, language="cypher")
                    with st.spinner("Carregando clientes afetados..."):
                        affected_df = analysis.run_query_df(affected_customers_query)
                    if not affected_df.empty:
                        render_styled_table(affected_df)

                        # Métricas de receita dos afetados
                        revenue_query = f"""
                            MATCH (equip)-[:HAS_MAINTENANCE]->(m:MaintenanceEvent {{event_id: '{event_id}'}})
                            WITH equip
                            MATCH (equip)-[:CONNECTS_TO*0..3]->(an:AccessNode)-[:CONNECTS_TO]->(cpe:CPE)-[:CONNECTS_TO]->(cust:Customer)
                            RETURN count(DISTINCT cust) AS total_clientes,
                                   sum(CASE WHEN cust.churn_label = 'Yes' THEN 1 ELSE 0 END) AS clientes_churned,
                                   round(avg(cust.monthly_charges), 2) AS mensalidade_media,
                                   round(sum(cust.monthly_charges), 2) AS receita_mensal_total,
                                   round(sum(cust.monthly_charges * cust.tenure_months), 2) AS clv_total
                        """
                        with st.spinner("Calculando métricas de receita..."):
                            rev_df = analysis.run_query_df(revenue_query)
                        if not rev_df.empty:
                            rv = rev_df.iloc[0]
                            total_c = int(rv.get('total_clientes', 0))
                            churned_c = int(rv.get('clientes_churned', 0))
                            churn_pct = round((churned_c / total_c) * 100, 1) if total_c > 0 else 0
                            rev_cards = [
                                {"icon": "👥", "label": "Clientes na Área",   "value": f"{total_c:,}",                                         "color": "#002E5D", "bg": "#EBF4FF"},
                                {"icon": "📉", "label": "Já Churned",         "value": f"{churned_c} ({churn_pct}%)",                           "color": "#D62828", "bg": "#FDECEA"},
                                {"icon": "💳", "label": "Mensalidade Média",  "value": f"${float(rv.get('mensalidade_media', 0)):.2f}",         "color": "#0097D7", "bg": "#E6F7FF"},
                                {"icon": "💰", "label": "Receita Mensal",     "value": f"${float(rv.get('receita_mensal_total', 0)):,.2f}",     "color": "#2A9D8F", "bg": "#E8F5E9"},
                            ]
                            rv_inner = "".join(
                                """<div class="kpi-card" style="--kc:{color};--kb:{bg};">
                                        <div class="kpi-icon-wrap">{icon}</div>
                                        <div class="kpi-value">{value}</div>
                                        <div class="kpi-label">{label}</div>
                                    </div>""".format(**c)
                                for c in rev_cards
                            )
                            st.markdown(f'<div class="kpi-grid" style="grid-template-columns: repeat(4, 1fr);">{rv_inner}</div>', unsafe_allow_html=True)
                    else:
                        st.info("Nenhum cliente encontrado via topologia downstream.")
                else:
                    st.warning("Não foi possível renderizar o grafo de impacto completo. Tente outro evento.")

elif selected_section == "Manutenção e SLA":
    st.header("Dashboard de Manutenção e Conformidade SLA")
    render_section_intro(
        "Visão consolidada dos eventos de manutenção, prioridades, durações e conformidade com SLA.",
        "Analise o dashboard para identificar padrões de falha, equipamentos problemáticos e violações de SLA.",
        "Monitorar SLA e padrões de manutenção permite ação preventiva e reduz o impacto em receita.",
    )
    st.markdown("""
O grafo armazena eventos de manutenção conectados aos equipamentos afetados, incluindo causa raiz,
duração, clientes impactados e se o SLA foi cumprido. Essa estrutura permite consultas poderosas
como "quais equipamentos concentram mais violações de SLA?" ou "qual a receita em risco por tipo de evento?".
    """)

    # KPIs de manutenção
    maint_kpi_query = """
        MATCH (m:MaintenanceEvent)
        RETURN count(m) AS total_eventos,
               sum(m.customers_affected) AS total_clientes_afetados,
               round(avg(m.duration_hours), 1) AS duracao_media_horas,
               sum(CASE WHEN m.sla_met = true THEN 1 ELSE 0 END) AS sla_cumprido,
               sum(CASE WHEN m.sla_met = false THEN 1 ELSE 0 END) AS sla_violado,
               round(sum(coalesce(m.revenue_at_risk, 0)), 2) AS receita_em_risco_total
    """

    with st.spinner("Carregando KPIs de manutenção..."):
        maint_kpi_df = analysis.run_query_df(maint_kpi_query)

    if not maint_kpi_df.empty:
        mk = maint_kpi_df.iloc[0]
        total_events = int(mk.get('total_eventos', 0))
        sla_ok = int(mk.get('sla_cumprido', 0))
        sla_fail = int(mk.get('sla_violado', 0))
        sla_pct = round((sla_ok / total_events) * 100, 1) if total_events > 0 else 0

        maint_cards = [
            {"icon": "🔧", "label": "Total de Eventos",        "value": str(total_events),                                      "color": "#003049", "bg": "#E3F2FD"},
            {"icon": "👥", "label": "Clientes Afetados",       "value": f"{int(mk.get('total_clientes_afetados', 0)):,}",        "color": "#D62828", "bg": "#FDECEA"},
            {"icon": "⏱️", "label": "Duração Média (h)",       "value": str(mk.get('duracao_media_horas', 0)),                   "color": "#F77F00", "bg": "#FFF3E0"},
            {"icon": "✅", "label": "SLA Cumprido",             "value": f"{sla_pct}%",                                           "color": "#2A9D8F", "bg": "#E8F5E9"},
            {"icon": "❌", "label": "SLA Violado",              "value": str(sla_fail),                                           "color": "#D62828", "bg": "#FDECEA"},
            {"icon": "💸", "label": "Receita em Risco (Total)", "value": f"${float(mk.get('receita_em_risco_total', 0)):,.2f}",   "color": "#702082", "bg": "#F3E8FF"},
        ]
        m_inner = "".join(
            f"""<div class="kpi-card" style="--kc:{c['color']};--kb:{c['bg']};">
                    <div class="kpi-icon-wrap">{c['icon']}</div>
                    <div class="kpi-value">{c['value']}</div>
                    <div class="kpi-label">{c['label']}</div>
                </div>"""
            for c in maint_cards
        )
        st.markdown(f'<div class="kpi-grid">{m_inner}</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Eventos por Prioridade e Tipo")
        priority_query = """
            MATCH (m:MaintenanceEvent)
            RETURN m.priority AS Prioridade,
                   m.type AS Tipo,
                   count(*) AS Qtd,
                   sum(m.customers_affected) AS Clientes_Afetados,
                   round(avg(m.duration_hours), 1) AS Duracao_Media_h,
                   sum(CASE WHEN m.sla_met = false THEN 1 ELSE 0 END) AS SLA_Violados
            ORDER BY CASE m.priority
                WHEN 'P1-Critical' THEN 0
                WHEN 'P2-High' THEN 1
                WHEN 'P3-Medium' THEN 2
                WHEN 'P4-Low' THEN 3
                ELSE 4 END
        """
        with st.expander("Ver Consulta Cypher"):
            st.code(priority_query, language="cypher")
        with st.spinner("Carregando..."):
            prio_df = analysis.run_query_df(priority_query)
        if not prio_df.empty:
            render_styled_table(prio_df)

            # Gráfico de clientes afetados por prioridade
            fig, ax = plt.subplots(figsize=(6, 3.5))
            prio_colors_map = {
                "P1-Critical": "#D62828",
                "P2-High": "#F77F00",
                "P3-Medium": "#FCBF49",
                "P4-Low": "#2A9D8F",
            }
            bar_cols = [prio_colors_map.get(p, "#999999") for p in prio_df["Prioridade"]]
            ax.bar(prio_df["Prioridade"], prio_df["Clientes_Afetados"], color=bar_cols, edgecolor="white")
            ax.set_ylabel("Clientes Afetados")
            ax.set_title("Impacto por Prioridade do Evento")
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)

    with col2:
        st.subheader("Equipamentos Mais Afetados")
        equip_query = """
            MATCH (equip)-[:HAS_MAINTENANCE]->(m:MaintenanceEvent)
            RETURN labels(equip)[0] AS Tipo,
                   equip.name AS Equipamento,
                   count(m) AS Total_Eventos,
                   sum(m.customers_affected) AS Clientes_Afetados_Total,
                   sum(CASE WHEN m.sla_met = false THEN 1 ELSE 0 END) AS SLA_Violados,
                   round(sum(coalesce(m.revenue_at_risk, 0)), 2) AS Receita_em_Risco
            ORDER BY Total_Eventos DESC
        """
        with st.expander("Ver Consulta Cypher"):
            st.code(equip_query, language="cypher")
        with st.spinner("Carregando..."):
            equip_df = analysis.run_query_df(equip_query)
        if not equip_df.empty:
            render_styled_table(equip_df)

            # Gráfico horizontal de receita em risco
            fig2, ax2 = plt.subplots(figsize=(6, max(3, len(equip_df) * 0.4)))
            ax2.barh(
                equip_df["Equipamento"],
                equip_df["Receita_em_Risco"],
                color="#702082",
                edgecolor="white",
                linewidth=0.5,
            )
            ax2.set_xlabel("Receita em Risco ($)")
            ax2.set_title("Receita em Risco por Equipamento")
            ax2.invert_yaxis()
            plt.tight_layout()
            st.pyplot(fig2, use_container_width=True)

elif selected_section == "Custos de Manutenção":
    st.header("Análise de Custos de Manutenção")
    render_section_intro(
        "Visão detalhada dos custos operacionais de manutenção por categoria, tipo de evento e equipamento.",
        "Compare custos por categoria, identifique onde o orçamento é gasto e onde há retorno em prevenção.",
        "Otimizar alocação de CAPEX/OPEX com base em dados reais de custo reduz TCO e melhora o ROI da rede.",
    )
    st.markdown("""
Cada evento de manutenção no grafo possui `cost` (custo direto), `revenue_at_risk` (receita em risco),
`crew_size`, `vendor_involved` e `duration_hours`. Cruzando esses dados com a topologia da rede,
conseguimos responder perguntas como: *"Quanto custa manter cada camada da rede?"*
ou *"Qual é o retorno do investimento em manutenção preventiva vs. corretiva?"*.
    """)

    # KPIs financeiros
    cost_kpi_query = """
        MATCH (m:MaintenanceEvent)
        RETURN round(sum(m.cost), 2) AS custo_total,
               round(avg(m.cost), 2) AS custo_medio,
               round(max(m.cost), 2) AS custo_maximo,
               round(sum(coalesce(m.revenue_at_risk, 0)), 2) AS receita_risco_total,
               round(sum(CASE WHEN m.type = 'Preventive' THEN m.cost ELSE 0 END), 2) AS custo_preventivo,
               round(sum(CASE WHEN m.type = 'Emergency' THEN m.cost ELSE 0 END), 2) AS custo_emergencia,
               round(sum(CASE WHEN m.type = 'Corrective' THEN m.cost ELSE 0 END), 2) AS custo_corretivo,
               sum(CASE WHEN m.vendor_involved = true THEN 1 ELSE 0 END) AS eventos_com_vendor
    """
    with st.spinner("Carregando KPIs financeiros..."):
        cost_kpi_df = analysis.run_query_df(cost_kpi_query)

    if not cost_kpi_df.empty:
        ck = cost_kpi_df.iloc[0]
        cost_cards = [
            {"icon": "💰", "label": "Custo Total",            "value": f"${float(ck.get('custo_total', 0)):,.0f}",        "color": "#002E5D", "bg": "#EBF4FF"},
            {"icon": "📊", "label": "Custo Médio/Evento",     "value": f"${float(ck.get('custo_medio', 0)):,.0f}",        "color": "#0097D7", "bg": "#E6F7FF"},
            {"icon": "🔺", "label": "Custo Máximo (Evento)",  "value": f"${float(ck.get('custo_maximo', 0)):,.0f}",       "color": "#D62828", "bg": "#FDECEA"},
            {"icon": "⚠️", "label": "Receita em Risco Total", "value": f"${float(ck.get('receita_risco_total', 0)):,.0f}","color": "#F77F00", "bg": "#FFF3E0"},
            {"icon": "🛡️", "label": "Custo Preventivo",       "value": f"${float(ck.get('custo_preventivo', 0)):,.0f}",   "color": "#2A9D8F", "bg": "#E8F5E9"},
            {"icon": "🚨", "label": "Custo Emergência",       "value": f"${float(ck.get('custo_emergencia', 0)):,.0f}",   "color": "#D62828", "bg": "#FDECEA"},
        ]
        c_inner = "".join(
            f"""<div class="kpi-card" style="--kc:{c['color']};--kb:{c['bg']};">
                    <div class="kpi-icon-wrap">{c['icon']}</div>
                    <div class="kpi-value">{c['value']}</div>
                    <div class="kpi-label">{c['label']}</div>
                </div>"""
            for c in cost_cards
        )
        st.markdown(f'<div class="kpi-grid">{c_inner}</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Custo por Categoria de Evento")
        cat_cost_query = """
            MATCH (m:MaintenanceEvent)
            RETURN m.category AS Categoria,
                   count(*) AS Qtd_Eventos,
                   round(sum(m.cost), 2) AS Custo_Total,
                   round(avg(m.cost), 2) AS Custo_Medio,
                   round(sum(coalesce(m.revenue_at_risk, 0)), 2) AS Receita_em_Risco,
                   sum(m.customers_affected) AS Clientes_Afetados
            ORDER BY Custo_Total DESC
        """
        with st.expander("Ver Consulta Cypher"):
            st.code(cat_cost_query, language="cypher")
        with st.spinner("Carregando custos por categoria..."):
            cat_df = analysis.run_query_df(cat_cost_query)
        if not cat_df.empty:
            render_styled_table(cat_df)

            fig, ax = plt.subplots(figsize=(6, 4))
            cat_palette = ["#002E5D", "#003049", "#0097D7", "#2A9D8F", "#F77F00",
                           "#FCBF49", "#D62828", "#702082", "#616AB1", "#E6007E"]
            wedges, texts, autotexts = ax.pie(
                cat_df["Custo_Total"],
                labels=cat_df["Categoria"],
                autopct="%1.1f%%",
                colors=cat_palette[:len(cat_df)],
                pctdistance=0.82,
                startangle=90,
            )
            for t in texts:
                t.set_fontsize(9)
            for at in autotexts:
                at.set_fontsize(8)
                at.set_color("white")
                at.set_fontweight("bold")
            ax.set_title("Distribuição de Custo por Categoria", fontsize=12, pad=12)
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)

    with col2:
        st.subheader("Custo: Preventivo vs. Corretivo vs. Emergência")
        type_cost_query = """
            MATCH (m:MaintenanceEvent)
            RETURN m.type AS Tipo,
                   count(*) AS Qtd_Eventos,
                   round(sum(m.cost), 2) AS Custo_Total,
                   round(avg(m.cost), 2) AS Custo_Medio,
                   round(sum(coalesce(m.revenue_at_risk, 0)), 2) AS Receita_em_Risco,
                   sum(m.customers_affected) AS Clientes_Afetados,
                   sum(CASE WHEN m.sla_met = false THEN 1 ELSE 0 END) AS SLA_Violados
            ORDER BY Custo_Total DESC
        """
        with st.expander("Ver Consulta Cypher"):
            st.code(type_cost_query, language="cypher")
        with st.spinner("Carregando custos por tipo..."):
            type_df = analysis.run_query_df(type_cost_query)
        if not type_df.empty:
            render_styled_table(type_df)

            type_color_map = {"Preventive": "#2A9D8F", "Corrective": "#F77F00", "Emergency": "#D62828"}
            fig2, ax2 = plt.subplots(figsize=(6, 4))
            x_pos = range(len(type_df))
            bar_width = 0.35
            bars1 = ax2.bar(
                [p - bar_width / 2 for p in x_pos],
                type_df["Custo_Total"],
                bar_width,
                label="Custo Total ($)",
                color=[type_color_map.get(t, "#999") for t in type_df["Tipo"]],
                edgecolor="white",
            )
            bars2 = ax2.bar(
                [p + bar_width / 2 for p in x_pos],
                type_df["Receita_em_Risco"],
                bar_width,
                label="Receita em Risco ($)",
                color=[type_color_map.get(t, "#999") for t in type_df["Tipo"]],
                edgecolor="white",
                alpha=0.5,
            )
            ax2.set_xticks(list(x_pos))
            ax2.set_xticklabels(type_df["Tipo"])
            ax2.set_ylabel("Valor ($)")
            ax2.set_title("Custo vs. Receita em Risco por Tipo")
            ax2.legend(fontsize=9)
            plt.tight_layout()
            st.pyplot(fig2, use_container_width=True)

    st.divider()

    # Custo por camada da rede
    st.subheader("Custo de Manutenção por Camada da Rede")
    layer_cost_query = """
        MATCH (equip)-[:HAS_MAINTENANCE]->(m:MaintenanceEvent)
        RETURN labels(equip)[0] AS Camada,
               count(m) AS Qtd_Eventos,
               round(sum(m.cost), 2) AS Custo_Total,
               round(avg(m.cost), 2) AS Custo_Medio,
               round(sum(coalesce(m.revenue_at_risk, 0)), 2) AS Receita_em_Risco,
               sum(m.customers_affected) AS Clientes_Afetados,
               round(sum(m.cost) * 1.0 / count(m), 2) AS Custo_Por_Evento,
               sum(CASE WHEN m.vendor_involved = true THEN 1 ELSE 0 END) AS Eventos_com_Vendor,
               sum(CASE WHEN m.vendor_involved = true THEN m.cost ELSE 0 END) AS Custo_Vendor
        ORDER BY Custo_Total DESC
    """
    with st.expander("Ver Consulta Cypher"):
        st.code(layer_cost_query, language="cypher")
    with st.spinner("Carregando custos por camada..."):
        layer_df = analysis.run_query_df(layer_cost_query)
    if not layer_df.empty:
        render_styled_table(layer_df)

        col_a, col_b = st.columns([1, 1])
        with col_a:
            fig3, ax3 = plt.subplots(figsize=(6, 4))
            layer_colors = {"CoreNetwork": "#D62828", "RegionalHub": "#F77F00", "CentralOffice": "#FCBF49",
                            "DistributionCabinet": "#003049", "AccessNode": "#0097D7"}
            l_colors = [layer_colors.get(l, "#999") for l in layer_df["Camada"]]
            ax3.barh(layer_df["Camada"], layer_df["Custo_Total"], color=l_colors, edgecolor="white")
            ax3.set_xlabel("Custo Total ($)")
            ax3.set_title("Custo por Camada da Rede")
            ax3.invert_yaxis()
            plt.tight_layout()
            st.pyplot(fig3, use_container_width=True)

        with col_b:
            fig4, ax4 = plt.subplots(figsize=(6, 4))
            ax4.barh(layer_df["Camada"], layer_df["Custo_Vendor"], color=l_colors, edgecolor="white", alpha=0.6, label="Custo Vendor")
            ax4.barh(layer_df["Camada"], layer_df["Custo_Total"] - layer_df["Custo_Vendor"], left=layer_df["Custo_Vendor"], color=l_colors, edgecolor="white", label="Custo Interno")
            ax4.set_xlabel("Custo ($)")
            ax4.set_title("Interno vs. Vendor por Camada")
            ax4.legend(fontsize=9)
            ax4.invert_yaxis()
            plt.tight_layout()
            st.pyplot(fig4, use_container_width=True)

    st.divider()

    # Top 10 eventos mais caros
    st.subheader("Top 10 Eventos Mais Caros")
    top_cost_query = """
        MATCH (equip)-[:HAS_MAINTENANCE]->(m:MaintenanceEvent)
        RETURN m.title AS Evento,
               m.category AS Categoria,
               m.type AS Tipo,
               m.priority AS Prioridade,
               equip.name AS Equipamento,
               m.cost AS Custo,
               coalesce(m.revenue_at_risk, 0) AS Receita_em_Risco,
               m.cost + coalesce(m.revenue_at_risk, 0) AS Impacto_Total,
               m.customers_affected AS Clientes_Afetados,
               m.crew_size AS Equipe,
               CASE WHEN m.vendor_involved THEN 'Sim' ELSE 'Não' END AS Vendor
        ORDER BY Impacto_Total DESC
        LIMIT 10
    """
    with st.expander("Ver Consulta Cypher"):
        st.code(top_cost_query, language="cypher")
    with st.spinner("Carregando top eventos..."):
        top_df = analysis.run_query_df(top_cost_query)
    if not top_df.empty:
        render_styled_table(top_df)

elif selected_section == "Análise de Causa Raiz":
    st.header("Análise de Causa Raiz e Padrões de Falha")
    render_section_intro(
        "Agrupamento de eventos por causa raiz, com grafos de equipamentos reincidentes, cascatas e impacto downstream.",
        "Explore os grafos para identificar padrões recorrentes, cadeias de causalidade e raio de impacto na topologia.",
        "Eliminar causas raiz sistêmicas reduz eventos futuros e o custo total de operação.",
    )
    st.markdown("""
O grafo é a ferramenta ideal para análise de causa raiz em redes telco. Diferente de tabelas,
ele permite visualizar simultaneamente: o equipamento que falhou, quais outros eventos essa falha
causou (`CAUSED`), quais manutenções perdidas contribuíram (`CONTRIBUTED_TO`), e qual o raio de
impacto na topologia downstream (`CONNECTS_TO`).

Nesta seção exploramos **4 visões de grafo complementares** que revelam padrões invisíveis em dados tabulares.
    """)

    # ═══════════════════════════════════════════════════════════════════════
    # 1. GRAFO DE EQUIPAMENTOS REINCIDENTES
    # ═══════════════════════════════════════════════════════════════════════
    st.subheader("1. Grafo de Equipamentos Reincidentes")
    st.markdown("""
Equipamentos com múltiplos eventos de manutenção são sinais de problemas sistêmicos.
O grafo abaixo mostra **apenas** equipamentos que tiveram 2+ eventos, conectados a cada um dos seus incidentes.
O tamanho dos nós de manutenção reflete o custo — revelando visualmente onde o investimento se concentra.
    """)

    reincident_graph_query = """
        MATCH (equip)-[hm:HAS_MAINTENANCE]->(m:MaintenanceEvent)
        WITH equip, collect(m) AS events, count(m) AS total_events
        WHERE total_events > 1
        UNWIND events AS m
        MATCH (equip)-[hm:HAS_MAINTENANCE]->(m)
        OPTIONAL MATCH (m)-[c:CAUSED]->(m2:MaintenanceEvent)
        OPTIONAL MATCH (m)-[ct:CONTRIBUTED_TO]->(m3:MaintenanceEvent)
        RETURN equip, hm, m, c, m2, ct, m3
    """
    with st.expander("Ver Consulta Cypher — Equipamentos Reincidentes"):
        st.code(reincident_graph_query, language="cypher")

    with st.spinner("Renderizando grafo de equipamentos reincidentes..."):
        results_reincident = analysis.run_query_viz(reincident_graph_query)

    if results_reincident:
        VG_re = from_neo4j(results_reincident)
        VG_re.color_nodes(field="caption", color_space=ColorSpace.DISCRETE, colors=network_colors)
        VG_re.resize_nodes(property="cost", node_radius_min_max=(10, 40))
        analysis.set_caption_by_label(VG_re, network_label_to_property)
        html_re = VG_re.render(layout=Layout.FORCE_DIRECTED, initial_zoom=0.6)
        components.html(html_re.data, height=NETWORK_GRAPH_HEIGHT + 40)
        st.caption("Nós grandes = eventos caros. Setas entre eventos indicam cascatas (CAUSED) ou contribuições (CONTRIBUTED_TO).")

    # Tabela de reincidentes
    reincident_table_query = """
        MATCH (equip)-[:HAS_MAINTENANCE]->(m:MaintenanceEvent)
        WITH equip, count(m) AS total_eventos,
             collect(m.category) AS categorias,
             sum(m.cost) AS custo_total,
             sum(m.customers_affected) AS clientes_total,
             sum(coalesce(m.revenue_at_risk, 0)) AS receita_risco_total
        WHERE total_eventos > 1
        RETURN equip.name AS Equipamento,
               labels(equip)[0] AS Camada,
               total_eventos AS Eventos,
               categorias AS Categorias,
               custo_total AS Custo_Total,
               clientes_total AS Clientes_Total,
               receita_risco_total AS Receita_em_Risco
        ORDER BY total_eventos DESC, custo_total DESC
    """
    with st.spinner("Carregando tabela de reincidentes..."):
        reincident_df = analysis.run_query_df(reincident_table_query)
    if not reincident_df.empty:
        render_styled_table(reincident_df)

    st.divider()

    # ═══════════════════════════════════════════════════════════════════════
    # 2. GRAFO DE CADEIA DE CAUSALIDADE COMPLETA
    # ═══════════════════════════════════════════════════════════════════════
    st.subheader("2. Cadeia de Causalidade Completa (CAUSED + CONTRIBUTED_TO)")
    st.markdown("""
Este grafo mostra **todas** as relações de causalidade entre eventos: `CAUSED` (falha direta)
e `CONTRIBUTED_TO` (manutenção perdida que agravou outro evento). Inclui também os equipamentos
envolvidos em cada ponta da cadeia, revelando como problemas se propagam entre camadas da rede.
    """)

    causality_graph_query = """
        MATCH (equip1)-[hm1:HAS_MAINTENANCE]->(m1:MaintenanceEvent)-[rel]->(m2:MaintenanceEvent)<-[hm2:HAS_MAINTENANCE]-(equip2)
        WHERE type(rel) IN ['CAUSED', 'CONTRIBUTED_TO']
        RETURN equip1, hm1, m1, rel, m2, hm2, equip2
    """
    with st.expander("Ver Consulta Cypher — Cadeia de Causalidade"):
        st.code(causality_graph_query, language="cypher")

    with st.spinner("Renderizando grafo de causalidade..."):
        results_causality = analysis.run_query_viz(causality_graph_query)

    if results_causality:
        VG_caus = from_neo4j(results_causality)
        VG_caus.color_nodes(field="caption", color_space=ColorSpace.DISCRETE, colors=network_colors)
        VG_caus.resize_nodes(property="cost", node_radius_min_max=(12, 45))
        analysis.set_caption_by_label(VG_caus, network_label_to_property)
        html_caus = VG_caus.render(layout=Layout.FORCE_DIRECTED, initial_zoom=0.7)
        components.html(html_caus.data, height=NETWORK_GRAPH_HEIGHT + 40)

        # Tabela detalhada das cadeias
        causality_detail_query = """
            MATCH (equip1)-[:HAS_MAINTENANCE]->(m1:MaintenanceEvent)-[rel]->(m2:MaintenanceEvent)<-[:HAS_MAINTENANCE]-(equip2)
            WHERE type(rel) IN ['CAUSED', 'CONTRIBUTED_TO']
            RETURN type(rel) AS Relacao,
                   equip1.name AS Equip_Origem,
                   labels(equip1)[0] AS Camada_Origem,
                   m1.title AS Evento_Origem,
                   m1.category AS Cat_Origem,
                   m1.cost AS Custo_Origem,
                   CASE WHEN type(rel) = 'CAUSED' THEN rel.impact ELSE rel.reason END AS Descricao,
                   equip2.name AS Equip_Destino,
                   labels(equip2)[0] AS Camada_Destino,
                   m2.title AS Evento_Destino,
                   m2.category AS Cat_Destino,
                   m2.cost AS Custo_Destino,
                   m2.customers_affected AS Clientes_Cascata
        """
        with st.spinner("Carregando detalhamento de causalidade..."):
            caus_detail_df = analysis.run_query_df(causality_detail_query)
        if not caus_detail_df.empty:
            render_styled_table(caus_detail_df)
    else:
        st.info("Nenhuma cadeia de causalidade encontrada.")

    st.divider()

    # ═══════════════════════════════════════════════════════════════════════
    # 3. RAIO DE IMPACTO — Upstream e Downstream de um equipamento
    # ═══════════════════════════════════════════════════════════════════════
    st.subheader("3. Raio de Impacto na Topologia (Upstream + Downstream)")
    st.markdown("""
Quando um equipamento falha, é fundamental entender **duas direções**:
- **Downstream** (para baixo): quais AccessNodes, CPEs e Clientes são impactados?
- **Upstream** (para cima): de quem esse equipamento depende? Se o Core ou Hub acima falhar, este equipamento também cai.

Selecione o equipamento, a direção e a profundidade de travessia para explorar o grafo.
    """)

    # Carregar lista de equipamentos com manutenção
    equip_list_query = """
        MATCH (equip)-[:HAS_MAINTENANCE]->(m:MaintenanceEvent)
        WHERE m.customers_affected > 0
        RETURN DISTINCT equip.name AS nome, labels(equip)[0] AS tipo,
               sum(m.customers_affected) AS total_clientes
        ORDER BY total_clientes DESC
    """
    equip_list_df = analysis.run_query_df(equip_list_query)

    if not equip_list_df.empty:
        equip_display = [
            f"{row['nome']}  ({row['tipo']} · {int(row['total_clientes'])} clientes afetados)"
            for _, row in equip_list_df.iterrows()
        ]
        equip_options = equip_list_df["nome"].tolist()

        controls_col_impact, output_col_impact = st.columns([1, 2])
        with controls_col_impact:
            with st.form("blast_radius_form"):
                selected_equip_idx = st.selectbox(
                    "Equipamento",
                    range(len(equip_display)),
                    format_func=lambda i: equip_display[i],
                    help="Selecione um equipamento para explorar o raio de impacto.",
                )
                selected_equip = equip_options[selected_equip_idx]

                direction = st.radio(
                    "Direção da Exploração",
                    ["Downstream (impacto nos clientes)", "Upstream (dependências acima)", "Ambos (visão completa)"],
                    index=2,
                    help="Downstream mostra o que é afetado. Upstream mostra de quem depende.",
                )

                blast_depth = st.slider(
                    "Profundidade de Travessia",
                    min_value=1, max_value=4, value=2,
                    help="Quantas camadas na direção escolhida?",
                )
                submitted_blast = st.form_submit_button("Visualizar Raio de Impacto")

        if submitted_blast:
            sanitized_equip = selected_equip.replace("'", "\\'")

            if direction == "Downstream (impacto nos clientes)":
                blast_graph_query = f"""
                    MATCH (equip {{name: '{sanitized_equip}'}})-[hm:HAS_MAINTENANCE]->(m:MaintenanceEvent)
                    WHERE m.customers_affected > 0
                    WITH equip, hm, m
                    OPTIONAL MATCH downstream_path = (equip)-[:CONNECTS_TO*1..{blast_depth}]->(down)
                    WHERE NOT down:CPE AND NOT down:Customer
                    RETURN equip, hm, m, downstream_path
                """
            elif direction == "Upstream (dependências acima)":
                blast_graph_query = f"""
                    MATCH (equip {{name: '{sanitized_equip}'}})-[hm:HAS_MAINTENANCE]->(m:MaintenanceEvent)
                    WHERE m.customers_affected > 0
                    WITH equip, hm, m
                    OPTIONAL MATCH upstream_path = (up)-[:CONNECTS_TO*1..{blast_depth}]->(equip)
                    WHERE NOT up:CPE AND NOT up:Customer
                    RETURN equip, hm, m, upstream_path
                """
            else:
                blast_graph_query = f"""
                    MATCH (equip {{name: '{sanitized_equip}'}})-[hm:HAS_MAINTENANCE]->(m:MaintenanceEvent)
                    WHERE m.customers_affected > 0
                    WITH equip, hm, m
                    OPTIONAL MATCH downstream_path = (equip)-[:CONNECTS_TO*1..{blast_depth}]->(down)
                    WHERE NOT down:CPE AND NOT down:Customer
                    WITH equip, hm, m, collect(downstream_path) AS dp
                    OPTIONAL MATCH upstream_path = (up)-[:CONNECTS_TO*1..{blast_depth}]->(equip)
                    WHERE NOT up:CPE AND NOT up:Customer
                    RETURN equip, hm, m, dp, upstream_path
                """

            with output_col_impact:
                with st.expander("Ver Consulta Cypher — Raio de Impacto"):
                    st.code(blast_graph_query, language="cypher")

                with st.spinner("Renderizando raio de impacto..."):
                    results_blast = analysis.run_query_viz(blast_graph_query)

                if results_blast:
                    st.success(f"Raio de impacto de '{selected_equip}' gerado.")
                    VG_blast = from_neo4j(results_blast)
                    VG_blast.color_nodes(field="caption", color_space=ColorSpace.DISCRETE, colors=network_colors)
                    VG_blast.resize_nodes(property="customers_affected", node_radius_min_max=(10, 35))
                    analysis.set_caption_by_label(VG_blast, network_label_to_property)
                    html_blast = VG_blast.render(layout=Layout.HIERARCHICAL, initial_zoom=0.5)
                    components.html(html_blast.data, height=NETWORK_GRAPH_HEIGHT + 60)

                    # Métricas de impacto (sempre downstream para contagem de clientes)
                    blast_metrics_query = f"""
                        MATCH (equip {{name: '{sanitized_equip}'}})-[:HAS_MAINTENANCE]->(m:MaintenanceEvent)
                        WHERE m.customers_affected > 0
                        WITH equip, m
                        OPTIONAL MATCH (equip)-[:CONNECTS_TO*1..{blast_depth}]->(down)
                        WHERE NOT down:CPE AND NOT down:Customer
                        WITH equip, m, count(DISTINCT down) AS downstream_elements
                        OPTIONAL MATCH (equip)-[:CONNECTS_TO*1..5]->(cpe:CPE)
                        WITH equip, m, downstream_elements, count(DISTINCT cpe) AS cpes_afetados
                        OPTIONAL MATCH (up)-[:CONNECTS_TO*1..{blast_depth}]->(equip)
                        WHERE NOT up:CPE AND NOT up:Customer
                        RETURN m.title AS Evento,
                               m.category AS Categoria,
                               m.cost AS Custo,
                               m.customers_affected AS Clientes_Reportados,
                               downstream_elements AS Elementos_Downstream,
                               cpes_afetados AS CPEs_Potencialmente_Afetados,
                               count(DISTINCT up) AS Elementos_Upstream,
                               m.root_cause AS Causa_Raiz
                    """
                    blast_met_df = analysis.run_query_df(blast_metrics_query)
                    if not blast_met_df.empty:
                        render_styled_table(blast_met_df)
                else:
                    st.warning("Nenhum dado de impacto encontrado.")

    st.divider()

    # ═══════════════════════════════════════════════════════════════════════
    # 4. GRAFO POR CATEGORIA — Exploração interativa
    # ═══════════════════════════════════════════════════════════════════════
    st.subheader("4. Exploração de Grafo por Categoria de Evento")
    st.markdown("""
Selecione uma categoria de evento (Power, Fiber, Equipment, etc.) para visualizar o grafo de
todos os equipamentos e eventos daquela categoria. Útil para identificar se uma categoria
específica se concentra em determinadas regiões ou camadas da rede.
    """)

    cat_list_query = """
        MATCH (m:MaintenanceEvent)
        RETURN DISTINCT m.category AS categoria
        ORDER BY categoria
    """
    cat_list_df = analysis.run_query_df(cat_list_query)
    cat_options = cat_list_df["categoria"].tolist() if not cat_list_df.empty else []

    controls_col_cat, output_col_cat = st.columns([1, 2])
    with controls_col_cat:
        with st.form("category_graph_form"):
            selected_cat = st.selectbox(
                "Categoria",
                cat_options,
                index=0 if cat_options else 0,
                help="Selecione uma categoria de manutenção.",
            )
            submitted_cat_graph = st.form_submit_button("Visualizar Grafo da Categoria")

    if submitted_cat_graph and selected_cat:
        sanitized_cat = selected_cat.replace("'", "\\'")
        cat_graph_query = f"""
            MATCH (equip)-[hm:HAS_MAINTENANCE]->(m:MaintenanceEvent {{category: '{sanitized_cat}'}})
            OPTIONAL MATCH (m)-[c:CAUSED]->(m2:MaintenanceEvent)
            OPTIONAL MATCH (m)-[ct:CONTRIBUTED_TO]->(m3:MaintenanceEvent)
            RETURN equip, hm, m, c, m2, ct, m3
        """
        with output_col_cat:
            with st.expander("Ver Consulta Cypher"):
                st.code(cat_graph_query, language="cypher")

            with st.spinner(f"Renderizando grafo de categoria '{selected_cat}'..."):
                results_cat_graph = analysis.run_query_viz(cat_graph_query)

            if results_cat_graph:
                st.success(f"Grafo da categoria '{selected_cat}' gerado.")
                VG_cat = from_neo4j(results_cat_graph)
                VG_cat.color_nodes(field="caption", color_space=ColorSpace.DISCRETE, colors=network_colors)
                VG_cat.resize_nodes(property="cost", node_radius_min_max=(10, 40))
                analysis.set_caption_by_label(VG_cat, network_label_to_property)
                html_cat = VG_cat.render(layout=Layout.FORCE_DIRECTED, initial_zoom=0.6)
                components.html(html_cat.data, height=NETWORK_GRAPH_HEIGHT)
            else:
                st.warning(f"Nenhum dado encontrado para a categoria '{selected_cat}'.")

            # Tabela resumo da categoria
            cat_summary_query = f"""
                MATCH (equip)-[:HAS_MAINTENANCE]->(m:MaintenanceEvent {{category: '{sanitized_cat}'}})
                RETURN equip.name AS Equipamento,
                       labels(equip)[0] AS Camada,
                       m.title AS Evento,
                       m.priority AS Prioridade,
                       m.cost AS Custo,
                       m.customers_affected AS Clientes,
                       m.outage_duration_hours AS Horas_Outage,
                       m.root_cause AS Causa_Raiz,
                       CASE WHEN m.sla_met THEN 'Sim' WHEN m.sla_met = false THEN 'Não' ELSE 'N/A' END AS SLA_OK
                ORDER BY m.cost DESC
            """
            with st.spinner("Carregando detalhamento..."):
                cat_sum_df = analysis.run_query_df(cat_summary_query)
            if not cat_sum_df.empty:
                render_styled_table(cat_sum_df)

    st.divider()

    # ═══════════════════════════════════════════════════════════════════════
    # 5. ANÁLISES TABULARES COMPLEMENTARES
    # ═══════════════════════════════════════════════════════════════════════
    st.subheader("5. Visão Consolidada: Categorias, Vendor e Manutenção Perdida")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("**Impacto por Categoria**")
        cat_impact_query = """
            MATCH (m:MaintenanceEvent)
            RETURN m.category AS Categoria,
                   count(*) AS Eventos,
                   sum(m.customers_affected) AS Clientes_Afetados,
                   round(sum(m.cost), 0) AS Custo_Total,
                   round(sum(coalesce(m.revenue_at_risk, 0)), 0) AS Receita_em_Risco,
                   round(avg(m.duration_hours), 1) AS Duracao_Media_h,
                   round(avg(m.outage_duration_hours), 1) AS Outage_Media_h,
                   sum(CASE WHEN m.sla_met = false THEN 1 ELSE 0 END) AS SLA_Violados
            ORDER BY Custo_Total DESC
        """
        with st.expander("Ver Consulta Cypher"):
            st.code(cat_impact_query, language="cypher")
        with st.spinner("Carregando..."):
            cat_imp_df = analysis.run_query_df(cat_impact_query)
        if not cat_imp_df.empty:
            render_styled_table(cat_imp_df)

            fig, ax = plt.subplots(figsize=(6, 4.5))
            scatter_colors = ["#002E5D", "#D62828", "#F77F00", "#2A9D8F", "#FCBF49",
                              "#0097D7", "#702082", "#616AB1", "#E6007E", "#003049"]
            for i, (_, row) in enumerate(cat_imp_df.iterrows()):
                ax.scatter(
                    row["Custo_Total"], row["Clientes_Afetados"],
                    s=max(row["Eventos"] * 80, 80),
                    c=scatter_colors[i % len(scatter_colors)],
                    alpha=0.8, edgecolors="black", linewidth=0.5,
                    label=row["Categoria"],
                )
            ax.set_xlabel("Custo Total ($)")
            ax.set_ylabel("Clientes Afetados")
            ax.set_title("Custo vs. Impacto por Categoria")
            ax.legend(fontsize=8, bbox_to_anchor=(1.02, 1), loc='upper left')
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)

    with col2:
        st.markdown("**Vendor vs. Equipe Interna**")
        vendor_query = """
            MATCH (m:MaintenanceEvent)
            RETURN CASE WHEN m.vendor_involved THEN 'Com Vendor' ELSE 'Equipe Interna' END AS Modo,
                   count(*) AS Eventos,
                   round(sum(m.cost), 0) AS Custo_Total,
                   round(avg(m.cost), 0) AS Custo_Medio,
                   round(avg(m.crew_size), 1) AS Equipe_Media,
                   round(avg(m.duration_hours), 1) AS Duracao_Media_h,
                   sum(m.customers_affected) AS Clientes_Afetados,
                   sum(CASE WHEN m.sla_met = false THEN 1 ELSE 0 END) AS SLA_Violados
            ORDER BY Custo_Total DESC
        """
        with st.expander("Ver Consulta Cypher"):
            st.code(vendor_query, language="cypher")
        with st.spinner("Carregando análise vendor..."):
            vendor_df = analysis.run_query_df(vendor_query)
        if not vendor_df.empty:
            render_styled_table(vendor_df)

            fig_v, ax_v = plt.subplots(figsize=(5, 3.5))
            v_colors = ["#002E5D", "#0097D7"]
            ax_v.bar(vendor_df["Modo"], vendor_df["Custo_Total"], color=v_colors, edgecolor="white")
            ax_v.set_ylabel("Custo Total ($)")
            ax_v.set_title("Custo Total: Vendor vs. Interno")
            plt.tight_layout()
            st.pyplot(fig_v, use_container_width=True)

    st.divider()

    # Manutenção perdida → impacto (com grafo)
    st.subheader("Manutenção Preventiva Perdida → Impacto Downstream")
    st.markdown("""
As relações `CONTRIBUTED_TO` revelam como manutenções preventivas que foram canceladas ou perdidas
contribuíram para incidentes futuros. O grafo abaixo mostra essa cadeia completa.
    """)

    missed_graph_query = """
        MATCH (equip1)-[hm1:HAS_MAINTENANCE]->(m1:MaintenanceEvent)-[r:CONTRIBUTED_TO]->(m2:MaintenanceEvent)<-[hm2:HAS_MAINTENANCE]-(equip2)
        RETURN equip1, hm1, m1, r, m2, hm2, equip2
    """
    with st.expander("Ver Consulta Cypher"):
        st.code(missed_graph_query, language="cypher")

    with st.spinner("Renderizando grafo de manutenção perdida..."):
        results_missed = analysis.run_query_viz(missed_graph_query)
    if results_missed:
        VG_missed = from_neo4j(results_missed)
        VG_missed.color_nodes(field="caption", color_space=ColorSpace.DISCRETE, colors=network_colors)
        VG_missed.resize_nodes(property="cost", node_radius_min_max=(10, 40))
        analysis.set_caption_by_label(VG_missed, network_label_to_property)
        html_missed = VG_missed.render(layout=Layout.FORCE_DIRECTED, initial_zoom=0.8)
        components.html(html_missed.data, height=NETWORK_GRAPH_HEIGHT)

    missed_query = """
        MATCH (m1:MaintenanceEvent)-[r:CONTRIBUTED_TO]->(m2:MaintenanceEvent)
        OPTIONAL MATCH (equip1)-[:HAS_MAINTENANCE]->(m1)
        OPTIONAL MATCH (equip2)-[:HAS_MAINTENANCE]->(m2)
        RETURN m1.title AS Evento_Perdido,
               equip1.name AS Equipamento_Origem,
               m2.title AS Evento_Consequente,
               equip2.name AS Equipamento_Afetado,
               r.reason AS Razao,
               m2.customers_affected AS Clientes_Impactados,
               m2.cost AS Custo_Consequente,
               coalesce(m2.revenue_at_risk, 0) AS Receita_em_Risco
    """
    with st.spinner("Carregando detalhamento..."):
        missed_df = analysis.run_query_df(missed_query)
    if not missed_df.empty:
        render_styled_table(missed_df)
        st.caption("CONTRIBUTED_TO mostra como manutenção preventiva perdida causa incidentes evitáveis.")
    else:
        st.info("Nenhuma relação CONTRIBUTED_TO encontrada.")

elif selected_section == "Linha do Tempo de Incidentes":
    st.header("Linha do Tempo de Incidentes — Grafo e Custos")
    render_section_intro(
        "Todos os eventos de manutenção visualizados como grafo: equipamentos, incidentes e cascatas com custos.",
        "Filtre por tipo e prioridade. O grafo mostra a rede de dependências, a tabela e os gráficos detalham custos.",
        "Visualizar incidentes como grafo revela padrões de propagação e equipamentos reincidentes invisíveis em tabelas.",
    )
    st.markdown("""
Nesta seção, além dos gráficos temporais de custo, visualizamos os incidentes como **grafo interativo**.
Cada nó de equipamento se conecta aos seus eventos de manutenção via `HAS_MAINTENANCE`,
e eventos conectam-se entre si via `CAUSED` e `CONTRIBUTED_TO` — revelando cadeias de falha,
equipamentos reincidentes e a "topologia" dos incidentes operacionais.

O tamanho dos nós de manutenção é proporcional ao custo do evento, facilitando a identificação visual
dos incidentes mais caros.
    """)

    controls_col, output_col = st.columns([1, 2])

    with controls_col:
        with st.form("timeline_form"):
            type_filter = st.multiselect(
                "Tipo de Evento",
                ["Emergency", "Corrective", "Preventive"],
                default=["Emergency", "Corrective", "Preventive"],
                help="Filtre por tipo de manutenção.",
            )
            priority_filter = st.multiselect(
                "Prioridade",
                ["P1-Critical", "P2-High", "P3-Medium", "P4-Low"],
                default=["P1-Critical", "P2-High", "P3-Medium", "P4-Low"],
                help="Filtre por prioridade do evento.",
            )
            submitted_timeline = st.form_submit_button("Gerar Linha do Tempo")

    if submitted_timeline:
        type_list = "[" + ", ".join(f"'{t}'" for t in type_filter) + "]"
        prio_list = "[" + ", ".join(f"'{p}'" for p in priority_filter) + "]"

        # ── Grafo de incidentes ──────────────────────────────────────────────
        graph_timeline_query = f"""
            MATCH (equip)-[hm:HAS_MAINTENANCE]->(m:MaintenanceEvent)
            WHERE m.start_time IS NOT NULL
              AND m.type IN {type_list}
              AND m.priority IN {prio_list}
            OPTIONAL MATCH (m)-[caused:CAUSED]->(m2:MaintenanceEvent)
            OPTIONAL MATCH (m)-[contrib:CONTRIBUTED_TO]->(m3:MaintenanceEvent)
            RETURN equip, hm, m, caused, m2, contrib, m3
        """

        # ── Tabela de dados ──────────────────────────────────────────────────
        timeline_query = f"""
            MATCH (equip)-[:HAS_MAINTENANCE]->(m:MaintenanceEvent)
            WHERE m.start_time IS NOT NULL
              AND m.type IN {type_list}
              AND m.priority IN {prio_list}
            RETURN m.title AS Evento,
                   m.type AS Tipo,
                   m.priority AS Prioridade,
                   m.category AS Categoria,
                   equip.name AS Equipamento,
                   m.start_time AS Data_Inicio,
                   m.cost AS Custo,
                   coalesce(m.revenue_at_risk, 0) AS Receita_em_Risco,
                   m.customers_affected AS Clientes_Afetados,
                   m.outage_duration_hours AS Horas_Outage,
                   CASE WHEN m.sla_met THEN 'Sim' WHEN m.sla_met = false THEN 'Não' ELSE 'N/A' END AS SLA_OK
            ORDER BY m.start_time
        """

        with output_col:
            with st.expander("Ver Consulta Cypher — Grafo de Incidentes"):
                st.code(graph_timeline_query, language="cypher")
            with st.expander("Ver Consulta Cypher — Tabela"):
                st.code(timeline_query, language="cypher")

            # ── Renderizar Grafo ─────────────────────────────────────────────
            st.subheader("Grafo de Incidentes: Equipamentos → Eventos → Cascatas")
            with st.spinner("Renderizando grafo de incidentes..."):
                results_tl_graph = analysis.run_query_viz(graph_timeline_query)

            if results_tl_graph:
                st.success("Grafo de incidentes gerado.")
                VG = from_neo4j(results_tl_graph)
                VG.color_nodes(
                    field="caption",
                    color_space=ColorSpace.DISCRETE,
                    colors=network_colors,
                )
                VG.resize_nodes(property="cost", node_radius_min_max=(8, 40))
                analysis.set_caption_by_label(VG, network_label_to_property)
                html_tl_graph = VG.render(layout=Layout.FORCE_DIRECTED, initial_zoom=0.5)
                components.html(html_tl_graph.data, height=NETWORK_GRAPH_HEIGHT + 100)
                st.caption("Tamanho dos nós de manutenção é proporcional ao custo. Setas `CAUSED` e `CONTRIBUTED_TO` indicam cascatas.")
            else:
                st.warning("Nenhum dado de grafo encontrado para os filtros selecionados.")

            st.divider()

            # ── Tabela e Gráficos Temporais ─────────────────────────────────
            with st.spinner("Carregando dados tabulares..."):
                tl_df = analysis.run_query_df(timeline_query)

            if not tl_df.empty:
                st.subheader("Detalhamento Tabular")
                st.success(f"{len(tl_df)} eventos encontrados.")
                render_styled_table(tl_df)

                # Converter datas
                tl_df["Data_Inicio"] = pd.to_datetime(tl_df["Data_Inicio"], errors="coerce")
                tl_valid = tl_df.dropna(subset=["Data_Inicio"]).copy()

                if not tl_valid.empty:
                    tl_valid = tl_valid.sort_values("Data_Inicio")
                    tl_valid["Custo_Acumulado"] = tl_valid["Custo"].cumsum()
                    tl_valid["Receita_Risco_Acumulada"] = tl_valid["Receita_em_Risco"].cumsum()

                    col_t1, col_t2 = st.columns([1, 1])

                    with col_t1:
                        st.subheader("Custo Acumulado ao Longo do Tempo")
                        fig, ax = plt.subplots(figsize=(6, 4))
                        ax.plot(tl_valid["Data_Inicio"], tl_valid["Custo_Acumulado"],
                                color="#002E5D", linewidth=2, label="Custo Acumulado")
                        ax.fill_between(tl_valid["Data_Inicio"], tl_valid["Custo_Acumulado"],
                                        alpha=0.15, color="#002E5D")
                        ax.plot(tl_valid["Data_Inicio"], tl_valid["Receita_Risco_Acumulada"],
                                color="#D62828", linewidth=2, linestyle="--", label="Receita em Risco Acumulada")
                        ax.fill_between(tl_valid["Data_Inicio"], tl_valid["Receita_Risco_Acumulada"],
                                        alpha=0.1, color="#D62828")
                        ax.set_xlabel("Data")
                        ax.set_ylabel("Valor ($)")
                        ax.set_title("Evolução dos Custos")
                        ax.legend(fontsize=9)
                        plt.xticks(rotation=30)
                        plt.tight_layout()
                        st.pyplot(fig, use_container_width=True)

                    with col_t2:
                        st.subheader("Eventos por Mês")
                        tl_valid["Mes"] = tl_valid["Data_Inicio"].dt.to_period("M").astype(str)
                        monthly = tl_valid.groupby("Mes").agg(
                            Eventos=("Evento", "count"),
                            Custo=("Custo", "sum"),
                            Clientes=("Clientes_Afetados", "sum"),
                        ).reset_index()

                        fig2, ax2 = plt.subplots(figsize=(6, 4))
                        ax2_twin = ax2.twinx()
                        bars = ax2.bar(monthly["Mes"], monthly["Custo"], color="#0097D7",
                                       edgecolor="white", alpha=0.8, label="Custo ($)")
                        ax2_twin.plot(monthly["Mes"], monthly["Eventos"], color="#D62828",
                                      marker="o", linewidth=2, label="Nº Eventos")
                        ax2.set_xlabel("Mês")
                        ax2.set_ylabel("Custo ($)", color="#0097D7")
                        ax2_twin.set_ylabel("Nº Eventos", color="#D62828")
                        ax2.set_title("Custo e Frequência Mensal")
                        plt.xticks(rotation=45)
                        lines1, labels1 = ax2.get_legend_handles_labels()
                        lines2, labels2 = ax2_twin.get_legend_handles_labels()
                        ax2.legend(lines1 + lines2, labels1 + labels2, fontsize=9, loc="upper left")
                        plt.tight_layout()
                        st.pyplot(fig2, use_container_width=True)

                    st.divider()

                    # Scatter: Custo vs Duração de Outage
                    st.subheader("Custo vs. Duração de Outage por Evento")
                    fig3, ax3 = plt.subplots(figsize=(10, 5))
                    type_color_scatter = {"Emergency": "#D62828", "Corrective": "#F77F00", "Preventive": "#2A9D8F"}
                    for t in tl_valid["Tipo"].unique():
                        subset = tl_valid[tl_valid["Tipo"] == t]
                        ax3.scatter(
                            subset["Horas_Outage"],
                            subset["Custo"],
                            s=subset["Clientes_Afetados"].clip(lower=20) * 3,
                            c=type_color_scatter.get(t, "#999"),
                            alpha=0.7,
                            edgecolors="black",
                            linewidth=0.5,
                            label=t,
                        )
                    ax3.set_xlabel("Duração do Outage (horas)")
                    ax3.set_ylabel("Custo ($)")
                    ax3.set_title("Custo vs. Outage (tamanho = clientes afetados)")
                    ax3.legend(fontsize=10)
                    plt.tight_layout()
                    st.pyplot(fig3, use_container_width=True)
                    st.caption("Tamanho dos pontos é proporcional ao número de clientes afetados.")

                    st.divider()

                    # ── Grafo por Mês Selecionado ────────────────────────────
                    st.subheader("Explorar Grafo de um Mês Específico")
                    st.markdown("Selecione um mês para visualizar apenas os incidentes daquele período como grafo interativo.")

                    month_options = sorted(tl_valid["Mes"].unique().tolist())
                    selected_month = st.selectbox("Mês", month_options, index=len(month_options) - 1)

                    if selected_month:
                        year_part, month_part = selected_month.split("-")
                        month_start = f"{year_part}-{month_part}-01"
                        next_month = int(month_part) + 1
                        if next_month > 12:
                            month_end = f"{int(year_part) + 1}-01-01"
                        else:
                            month_end = f"{year_part}-{next_month:02d}-01"

                        month_graph_query = f"""
                            MATCH (equip)-[hm:HAS_MAINTENANCE]->(m:MaintenanceEvent)
                            WHERE m.start_time >= datetime('{month_start}')
                              AND m.start_time < datetime('{month_end}')
                              AND m.type IN {type_list}
                              AND m.priority IN {prio_list}
                            OPTIONAL MATCH (m)-[caused:CAUSED]->(m2:MaintenanceEvent)
                            OPTIONAL MATCH (m)-[contrib:CONTRIBUTED_TO]->(m3:MaintenanceEvent)
                            RETURN equip, hm, m, caused, m2, contrib, m3
                        """

                        with st.expander("Ver Consulta Cypher — Grafo Mensal"):
                            st.code(month_graph_query, language="cypher")

                        with st.spinner(f"Renderizando grafo de {selected_month}..."):
                            results_month = analysis.run_query_viz(month_graph_query)

                        if results_month:
                            VG_month = from_neo4j(results_month)
                            VG_month.color_nodes(
                                field="caption",
                                color_space=ColorSpace.DISCRETE,
                                colors=network_colors,
                            )
                            VG_month.resize_nodes(property="cost", node_radius_min_max=(10, 40))
                            analysis.set_caption_by_label(VG_month, network_label_to_property)
                            html_month = VG_month.render(layout=Layout.FORCE_DIRECTED, initial_zoom=0.7)
                            components.html(html_month.data, height=NETWORK_GRAPH_HEIGHT)
                        else:
                            st.info(f"Nenhum evento encontrado em {selected_month} para os filtros selecionados.")
            else:
                st.warning("Nenhum evento encontrado para os filtros selecionados.")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.footer-bar {
    margin-top: 3rem;
    border-top: 1px solid #CBD5E0;
    padding: 18px 0 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
}
.footer-bar svg { opacity: 0.55; flex-shrink: 0; }
.footer-bar span {
    font-size: 12.5px;
    color: #8A96A8;
    font-family: 'Inter', sans-serif;
    letter-spacing: 0.01em;
}
</style>
<div class="footer-bar">
  <!-- Neo4j wordmark (simplified) -->
  <svg width="52" height="16" viewBox="0 0 52 16" fill="none" xmlns="http://www.w3.org/2000/svg">
    <text x="0" y="13" font-family="Inter,sans-serif" font-size="13" font-weight="700" fill="#002E5D">Neo4j</text>
  </svg>
  <span>© 2026 Neo4j, Inc. Todos os direitos reservados.</span>
</div>
""", unsafe_allow_html=True)
