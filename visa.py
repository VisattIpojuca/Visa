import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from datetime import datetime

# ===============================
# 🎨 Configuração da página
# ===============================
st.set_page_config(page_title="Painel VISA Ipojuca", layout="wide")

# ===============================
# 🔐 LOGIN SIMPLES
# ===============================
def login():
    st.title("🔐 Painel da Vigilância Sanitária de Ipojuca")
    st.subheader("Acesso Restrito")

    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")

    if submit:
        if username == "admin" and password == "Ipojuca@2025*":
            st.session_state["autenticado"] = True
            st.success("✅ Login realizado com sucesso!")
            st.rerun()
        else:
            st.error("❌ Usuário ou senha incorretos.")

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    login()
    st.stop()

st.title("🦠 Painel de Produção - Vigilância Sanitária de Ipojuca")

# ===============================
# 📥 Fonte de dados
# ===============================
URL_DADOS = "https://docs.google.com/spreadsheets/d/1CP6RD8UlHzB6FB7x8fhS3YZB0rVGPyf6q99PNp4iAGQ/export?format=csv"

@st.cache_data
def carregar_dados(url: str) -> pd.DataFrame:
    df = pd.read_csv(url, dtype=str)
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    # Remove carimbo se existir
    if "Carimbo de data/hora" in df.columns:
        df = df.drop(columns=["Carimbo de data/hora"])

    # Identifica coluna de data
    col_data = [c for c in df.columns if "data" in c.lower()][0]
    df[col_data] = pd.to_datetime(df[col_data], dayfirst=True, errors="coerce")

    # Cria colunas auxiliares de tempo
    df["DATA"] = df[col_data]
    df["ANO"] = df["DATA"].dt.year
    df["MES"] = df["DATA"].dt.month
    df["ANO_MES"] = df["DATA"].dt.to_period("M").astype(str)  # ex: 2025-01

    # Trata lista de inspetores
    df["INSPETOR_LISTA"] = df["EQUIPE/INSPETOR"].apply(extrair_inspetores)

    return df, col_data

def extrair_inspetores(texto):
    if pd.isna(texto):
        return []
    return [nome.strip().upper() for nome in str(texto).split(",") if nome.strip()]

df, col_data = carregar_dados(URL_DADOS)

# ===============================
# 🧠 Barra lateral - Filtros
# ===============================
st.sidebar.header("Filtros")

# 📅 Filtro de datas com pré-seleção do ano atual
data_min = df[col_data].min()
data_max = df[col_data].max()

ano_atual = datetime.now().year
data_inicio_ano = pd.to_datetime(f"{ano_atual}-01-01")
data_fim_ano = pd.to_datetime(f"{ano_atual}-12-31")

data_inicio_default = max(data_min, data_inicio_ano)
data_fim_default = min(data_max, data_fim_ano)

data_range = st.sidebar.date_input(
    "📅 Período",
    value=(data_inicio_default, data_fim_default),
    min_value=data_min,
    max_value=data_max
)

# 🔗 Filtros adicionais
turno = st.sidebar.multiselect("🕑 Turno", sorted(df["TURNO"].dropna().unique()))
localidade = st.sidebar.multiselect("📍 Localidade", sorted(df["LOCALIDADE"].dropna().unique()))
estabelecimento = st.sidebar.multiselect("🏢 Estabelecimento", sorted(df["ESTABELECIMENTO"].dropna().unique()))
coordenacao = st.sidebar.multiselect("👥 Coordenação", sorted(df["COORDENAÇÃO"].dropna().unique()))
class_risco = st.sidebar.multiselect("⚠️ Classificação de Risco", sorted(df["CLASSIFICAÇÃO DE RISCO"].dropna().unique()))
motivacao = st.sidebar.multiselect("🎯 Motivação", sorted(df["MOTIVAÇÃO"].dropna().unique()))
status = st.sidebar.multiselect("✅ Status do Estabelecimento", sorted(df["O ESTABELECIMENTO FOI LIBERADO"].dropna().unique()))

todos_inspetores = sorted(set(sum(df["INSPETOR_LISTA"].tolist(), [])))
inspetores = st.sidebar.multiselect("🕵️‍♂️ Inspetor", todos_inspetores)

# ===============================
# 🔍 Aplicar filtros
# ===============================
df_filtrado = df.copy()

if data_range:
    df_filtrado = df_filtrado[
        (df_filtrado[col_data] >= pd.to_datetime(data_range[0])) &
        (df_filtrado[col_data] <= pd.to_datetime(data_range[1]))
    ]
if turno:
    df_filtrado = df_filtrado[df_filtrado["TURNO"].isin(turno)]
if localidade:
    df_filtrado = df_filtrado[df_filtrado["LOCALIDADE"].isin(localidade)]
if estabelecimento:
    df_filtrado = df_filtrado[df_filtrado["ESTABELECIMENTO"].isin(estabelecimento)]
if coordenacao:
    df_filtrado = df_filtrado[df_filtrado["COORDENAÇÃO"].isin(coordenacao)]
if class_risco:
    df_filtrado = df_filtrado[df_filtrado["CLASSIFICAÇÃO DE RISCO"].isin(class_risco)]
if motivacao:
    df_filtrado = df_filtrado[df_filtrado["MOTIVAÇÃO"].isin(motivacao)]
if status:
    df_filtrado = df_filtrado[df_filtrado["O ESTABELECIMENTO FOI LIBERADO"].isin(status)]
if inspetores:
    df_filtrado = df_filtrado[
        df_filtrado["INSPETOR_LISTA"].apply(lambda x: any(i in x for i in inspetores))
    ]

# ===============================
# 📌 Resumo da seleção
# ===============================
if len(estabelecimento) == 1:
    st.sidebar.subheader("📌 Resumo da Seleção")
    est = estabelecimento[0]
    dados_est = df_filtrado[df_filtrado["ESTABELECIMENTO"] == est]
    local = dados_est["LOCALIDADE"].dropna().unique()
    coord = dados_est["COORDENAÇÃO"].dropna().unique()
    risco = dados_est["CLASSIFICAÇÃO DE RISCO"].dropna().unique()

    st.sidebar.markdown(
        f"""
    - **Estabelecimento:** {est}
    - **Localidade:** {", ".join(local) if len(local) > 0 else "Não informado"}
    - **Coordenação:** {", ".join(coord) if len(coord) > 0 else "Não informado"}
    - **Classificação de Risco:** {", ".join(risco) if len(risco) > 0 else "Não informado"}
    """
    )

# ===============================
# 🧮 Indicadores Gerais
# ===============================
st.subheader("📊 Indicadores Gerais do Período")

total_inspecoes = len(df_filtrado)
total_estabelecimentos = df_filtrado["ESTABELECIMENTO"].nunique()
total_inspetores_env = len(set(sum(df_filtrado["INSPETOR_LISTA"].tolist(), [])))

liberados = df_filtrado["O ESTABELECIMENTO FOI LIBERADO"].str.upper().fillna("")
taxa_liberacao = (
    (liberados == "SIM").sum() / total_inspecoes * 100 if total_inspecoes > 0 else 0
)

col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
col_kpi1.metric("Total de Inspeções", f"{total_inspecoes}")
col_kpi2.metric("Estabelecimentos Únicos", f"{total_estabelecimentos}")
col_kpi3.metric("Inspetores Envolvidos", f"{total_inspetores_env}")
col_kpi4.metric("Taxa de Liberação (%)", f"{taxa_liberacao:.1f}%")

# ===============================
# 🧮 Indicadores por Inspetor
# ===============================
st.subheader("🕵️‍♂️ Indicadores de Desempenho por Inspetor")

# Explodir a lista de inspetores
df_inspetores = df_filtrado.explode("INSPETOR_LISTA")
df_inspetores = df_inspetores[df_inspetores["INSPETOR_LISTA"].notna() & (df_inspetores["INSPETOR_LISTA"] != "")]

if not df_inspetores.empty:
    # Dias distintos no período para produtividade média
    dias_periodo = df_filtrado["DATA"].dt.date.nunique()
    dias_periodo = dias_periodo if dias_periodo > 0 else 1

    # Agrupamento por inspetor
    grp = df_inspetores.groupby("INSPETOR_LISTA")

    desempenho_insp = grp.agg(
        INSPECOES=("INSPETOR_LISTA", "count"),
        LIBERADOS=("O ESTABELECIMENTO FOI LIBERADO", lambda x: (x.str.upper() == "SIM").sum())
    ).reset_index()

    desempenho_insp["TAXA_LIBERACAO_%"] = (
        desempenho_insp["LIBERADOS"] / desempenho_insp["INSPECOES"] * 100
    ).round(1)

    desempenho_insp["INSPECOES_DIA_MEDIO"] = (
        desempenho_insp["INSPECOES"] / dias_periodo
    ).round(2)

    # Participação percentual no total de inspeções
    desempenho_insp["PARTICIPACAO_%"] = (
        desempenho_insp["INSPECOES"] / desempenho_insp["INSPECOES"].sum() * 100
    ).round(1)

    # Ordena por produção
    desempenho_insp = desempenho_insp.sort_values("INSPECOES", ascending=False)

    # Tabela
    st.dataframe(desempenho_insp, use_container_width=True)

    # Gráfico de barras - produção por inspetor
    fig_insp = px.bar(
        desempenho_insp,
        x="INSPETOR_LISTA",
        y="INSPECOES",
        title="🏆 Produção por Inspetor (Período Selecionado)",
        text="INSPECOES"
    )
    fig_insp.update_traces(textposition="outside")
    fig_insp.update_layout(xaxis_title="Inspetor", yaxis_title="Nº de inspeções")
    st.plotly_chart(fig_insp, use_container_width=True)

else:
    st.info("Nenhum dado de inspetor encontrado para o filtro atual.")

# ===============================
# 🏆 Ranking Mensal de Produção
# ===============================
st.subheader("📆 Ranking Mensal de Produção dos Inspetores")

if not df_inspetores.empty:
    prod_mensal = (
        df_inspetores
        .groupby(["ANO_MES", "INSPETOR_LISTA"])
        .size()
        .reset_index(name="INSPECOES")
    )

    # Seletor de mês/ano
    meses_disponiveis = sorted(prod_mensal["ANO_MES"].unique())
    mes_selecionado = st.selectbox("Selecione o Ano-Mês para ver o ranking:", meses_disponiveis)

    ranking_mes = (
        prod_mensal[prod_mensal["ANO_MES"] == mes_selecionado]
        .sort_values("INSPECOES", ascending=False)
        .reset_index(drop=True)
    )
    ranking_mes["POSICAO"] = ranking_mes.index + 1

    col_r1, col_r2 = st.columns([1, 1.5])

    with col_r1:
        st.markdown(f"**Ranking de Inspetores - {mes_selecionado}**")
        st.dataframe(
            ranking_mes[["POSICAO", "INSPETOR_LISTA", "INSPECOES"]],
            use_container_width=True
        )

    with col_r2:
        fig_rank = px.bar(
            ranking_mes,
            x="INSPETOR_LISTA",
            y="INSPECOES",
            title=f"🏅 Ranking de Produção - {mes_selecionado}",
            text="INSPECOES"
        )
        fig_rank.update_traces(textposition="outside")
        fig_rank.update_layout(xaxis_title="Inspetor", yaxis_title="Nº de inspeções")
        st.plotly_chart(fig_rank, use_container_width=True)

    # Evolução mensal (todos meses x inspetor)
    fig_evol = px.line(
        prod_mensal,
        x="ANO_MES",
        y="INSPECOES",
        color="INSPETOR_LISTA",
        markers=True,
        title="📈 Evolução Mensal de Produção por Inspetor"
    )
    fig_evol.update_layout(xaxis_title="Ano-Mês", yaxis_title="Nº de inspeções")
    st.plotly_chart(fig_evol, use_container_width=True)

else:
    st.info("Não há dados suficientes para montar o ranking mensal de inspetores.")

# ===============================
# 📊 Gráficos Gerais
# ===============================
st.subheader("📈 Análises Gráficas")

col1, col2 = st.columns(2)

# 📅 Produção ao longo do período
with col1:
    prod_por_data = df_filtrado.groupby(col_data).size().reset_index(name="Inspeções")
    if not prod_por_data.empty:
        graf1 = px.bar(
            prod_por_data,
            x=col_data,
            y="Inspeções",
            title="📅 Produção ao Longo do Período"
        )
        st.plotly_chart(graf1, use_container_width=True)
    else:
        st.info("Sem dados para o período selecionado.")

# 🎯 Distribuição por Motivação
with col2:
    motiv_counts = df_filtrado["MOTIVAÇÃO"].value_counts().reset_index()
    motiv_counts.columns = ["Motivação", "Quantidade"]
    if not motiv_counts.empty:
        graf2 = px.pie(
            motiv_counts,
            names="Motivação",
            values="Quantidade",
            title="🎯 Distribuição por Motivação"
        )
        st.plotly_chart(graf2, use_container_width=True)
    else:
        st.info("Sem dados de motivação para o filtro atual.")

# ✔️ Status do Estabelecimento
col3, col4 = st.columns(2)

with col3:
    status_counts = df_filtrado["O ESTABELECIMENTO FOI LIBERADO"].value_counts().reset_index()
    status_counts.columns = ["Status", "Quantidade"]
    if not status_counts.empty:
        graf3 = px.pie(
            status_counts,
            names="Status",
            values="Quantidade",
            title="✔️ Status do Estabelecimento"
        )
        st.plotly_chart(graf3, use_container_width=True)
    else:
        st.info("Sem dados de status para o filtro atual.")

# 🏙️ Classificação de Risco por Localidade
with col4:
    risco_local = (
        df_filtrado
        .groupby(["LOCALIDADE", "CLASSIFICAÇÃO DE RISCO"])
        .size()
        .reset_index(name="Quantidade")
    )
    if not risco_local.empty:
        graf4 = px.bar(
            risco_local,
            x="LOCALIDADE",
            y="Quantidade",
            color="CLASSIFICAÇÃO DE RISCO",
            title="🏙️ Classificação de Risco por Localidade",
            barmode="stack"
        )
        st.plotly_chart(graf4, use_container_width=True)
    else:
        st.info("Sem dados de risco/localidade para o filtro atual.")

# ===============================
# 📑 Visualização dos Dados
# ===============================
st.subheader("📑 Visualização dos Dados")

colunas_tabela = [
    "DATA",
    "TURNO",
    "ESTABELECIMENTO",
    "LOCALIDADE",
    "COORDENAÇÃO",
    "CLASSIFICAÇÃO DE RISCO",
    "MOTIVAÇÃO",
    "O ESTABELECIMENTO FOI LIBERADO",
    "NÚMERO DA VISITA",
    "EQUIPE/INSPETOR"
]

colunas_existentes = [c for c in colunas_tabela if c in df_filtrado.columns]
st.dataframe(df_filtrado[colunas_existentes], use_container_width=True)

# ===============================
# 📥 Download dos Dados
# ===============================
def gerar_excel_download(dataframe):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        dataframe.to_excel(writer, index=False, sheet_name="Dados Filtrados")
    return output.getvalue()

st.download_button(
    label="📥 Download dos Dados Filtrados",
    data=gerar_excel_download(df_filtrado.drop(columns=["INSPETOR_LISTA"], errors="ignore")),
    file_name="dados_filtrados_visa.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
