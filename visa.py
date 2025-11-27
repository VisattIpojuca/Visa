import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from datetime import datetime

# ======================================================
# 🎨 CONFIGURAÇÃO DA PÁGINA
# ======================================================
st.set_page_config(
    page_title="Painel VISA Ipojuca",
    layout="wide",
    page_icon="🦠"
)

# ======================================================
# 🔐 LOGIN SIMPLES
# ======================================================
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

# Título principal após login
st.title("🦠 Painel de Produção - Vigilância Sanitária de Ipojuca")

# ======================================================
# 📥 FONTE E CARREGAMENTO DOS DADOS
# ======================================================
URL_DADOS = "https://docs.google.com/spreadsheets/d/1CP6RD8UlHzB6FB7x8fhS3YZB0rVGPyf6q99PNp4iAGQ/export?format=csv"

def extrair_inspetores(texto):
    if pd.isna(texto):
        return []
    return [nome.strip().upper() for nome in str(texto).split(",") if nome.strip()]

@st.cache_data
def carregar_dados(url: str):
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
    df["MES_ANO_LABEL"] = df["DATA"].dt.strftime("%b/%Y")     # ex: Jan/2025

    # Trata lista de inspetores
    df["INSPETOR_LISTA"] = df["EQUIPE/INSPETOR"].apply(extrair_inspetores)

    # Normaliza campo de liberação para facilitar análise
    df["LIBERADO_FLAG"] = df["O ESTABELECIMENTO FOI LIBERADO"].str.upper().fillna("")
    df["LIBERADO_BIN"] = df["LIBERADO_FLAG"].apply(lambda x: 1 if x == "SIM" else 0)

    return df, col_data

df, col_data = carregar_dados(URL_DADOS)

# ======================================================
# 🧠 BARRA LATERAL - FILTROS
# ======================================================
st.sidebar.header("🧠 Filtros")

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
inspetores_sel = st.sidebar.multiselect("🕵️‍♂️ Inspetor", todos_inspetores)

# ======================================================
# 🔍 APLICAR FILTROS
# ======================================================
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
if inspetores_sel:
    df_filtrado = df_filtrado[
        df_filtrado["INSPETOR_LISTA"].apply(lambda x: any(i in x for i in inspetores_sel))
    ]

# ======================================================
# 📌 RESUMO DA SELEÇÃO (SIDEBAR)
# ======================================================
st.sidebar.markdown("---")
st.sidebar.subheader("📌 Resumo da Seleção")

st.sidebar.markdown(
    f"""
- **Período:** {data_range[0].strftime("%d/%m/%Y")} a {data_range[1].strftime("%d/%m/%Y")}
- **Total de Registros Filtrados:** {len(df_filtrado)}
"""
)

if len(estabelecimento) == 1:
    est = estabelecimento[0]
    dados_est = df_filtrado[df_filtrado["ESTABELECIMENTO"] == est]
    local = dados_est["LOCALIDADE"].dropna().unique()
    coord = dados_est["COORDENAÇÃO"].dropna().unique()
    risco = dados_est["CLASSIFICAÇÃO DE RISCO"].dropna().unique()

    st.sidebar.markdown(
        f"""
**Estabelecimento Focado:**
- 🏢 {est}
- 📍 Localidade: {", ".join(local) if len(local) > 0 else "Não informado"}
- 👥 Coordenação: {", ".join(coord) if len(coord) > 0 else "Não informado"}
- ⚠️ Classificação de Risco: {", ".join(risco) if len(risco) > 0 else "Não informado"}
"""
    )

# ======================================================
# 🧱 LAYOUT PRINCIPAL EM ABAS
# ======================================================
aba_geral, aba_inspetores, aba_coordenacao, aba_detalhes, aba_download = st.tabs(
    ["📊 Visão Geral", "🕵️‍♂️ Painel dos Inspetores", "👥 Coordenações", "📑 Tabelas Detalhadas", "📥 Download"]
)

# ======================================================
# 📊 VISÃO GERAL
# ======================================================
with aba_geral:
    st.subheader("📊 Indicadores Gerais do Período Selecionado")

    total_inspecoes = len(df_filtrado)
    total_estabelecimentos = df_filtrado["ESTABELECIMENTO"].nunique()
    total_inspetores_env = len(set(sum(df_filtrado["INSPETOR_LISTA"].tolist(), [])))
    dias_periodo = df_filtrado["DATA"].dt.date.nunique()
    dias_periodo = dias_periodo if dias_periodo > 0 else 1

    taxa_liberacao = (
        df_filtrado["LIBERADO_BIN"].sum() / total_inspecoes * 100
        if total_inspecoes > 0 else 0
    )

    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    col_kpi1.metric("Total de Inspeções", f"{total_inspecoes}")
    col_kpi2.metric("Estabelecimentos Únicos", f"{total_estabelecimentos}")
    col_kpi3.metric("Inspetores Envolvidos", f"{total_inspetores_env}")
    col_kpi4.metric("Taxa de Liberação (%)", f"{taxa_liberacao:.1f}%")

    st.markdown("### 📈 Tendências e Distribuições")

    col1, col2 = st.columns(2)

    # 📅 Produção ao longo do período (por dia)
    with col1:
        prod_por_data = df_filtrado.groupby("DATA").size().reset_index(name="Inspeções")
        if not prod_por_data.empty:
            graf1 = px.bar(
                prod_por_data,
                x="DATA",
                y="Inspeções",
                title="📅 Produção Diária no Período"
            )
            graf1.update_layout(xaxis_title="Data", yaxis_title="Nº de inspeções")
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

    col3, col4 = st.columns(2)

    # ✔️ Status do Estabelecimento
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
            graf4.update_layout(xaxis_title="Localidade", yaxis_title="Nº de inspeções")
            st.plotly_chart(graf4, use_container_width=True)
        else:
            st.info("Sem dados de risco/localidade para o filtro atual.")

    # ⚠️ Top estabelecimentos mais visitados
    st.markdown("### 🏢 Estabelecimentos Mais Fiscalizados no Período")
    top_estab = (
        df_filtrado["ESTABELECIMENTO"]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "Estabelecimento", "ESTABELECIMENTO": "Inspeções"})
        .head(10)
    )
    if not top_estab.empty:
        graf_top = px.bar(
            top_estab,
            x="Estabelecimento",
            y="Inspeções",
            title="🏢 Top 10 Estabelecimentos Mais Fiscalizados",
            text="Inspeções"
        )
        graf_top.update_traces(textposition="outside")
        graf_top.update_layout(xaxis_title="Estabelecimento", yaxis_title="Nº de inspeções")
        st.plotly_chart(graf_top, use_container_width=True)
    else:
        st.info("Sem dados de estabelecimentos para o filtro atual.")

# ======================================================
# 🕵️‍♂️ PAINEL DOS INSPETORES
# ======================================================
with aba_inspetores:
    st.subheader("🕵️‍♂️ Indicadores de Desempenho por Inspetor")

    # Explodir a lista de inspetores
    df_insp = df_filtrado.explode("INSPETOR_LISTA")
    df_insp = df_insp[
        df_insp["INSPETOR_LISTA"].notna() & (df_insp["INSPETOR_LISTA"] != "")
    ]

    if df_insp.empty:
        st.info("Nenhum dado de inspetor encontrado para o filtro atual.")
    else:
        dias_periodo = df_filtrado["DATA"].dt.date.nunique()
        dias_periodo = dias_periodo if dias_periodo > 0 else 1

        grp = df_insp.groupby("INSPETOR_LISTA")

        desempenho_insp = grp.agg(
            INSPECOES=("INSPETOR_LISTA", "count"),
            LIBERADOS=("LIBERADO_BIN", "sum"),
            ESTAB_UNICOS=("ESTABELECIMENTO", "nunique")
        ).reset_index()

        desempenho_insp["TAXA_LIBERACAO_%"] = (
            desempenho_insp["LIBERADOS"] / desempenho_insp["INSPECOES"] * 100
        ).round(1)

        desempenho_insp["INSPECOES_DIA_MEDIO"] = (
            desempenho_insp["INSPECOES"] / dias_periodo
        ).round(2)

        desempenho_insp["PARTICIPACAO_%"] = (
            desempenho_insp["INSPECOES"] / desempenho_insp["INSPECOES"].sum() * 100
        ).round(1)

        desempenho_insp = desempenho_insp.sort_values("INSPECOES", ascending=False)

        # KPIs gerais dos inspetores
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Total de Inspetores Ativos no Período", f"{desempenho_insp['INSPETOR_LISTA'].nunique()}")
        col_b.metric("Maior Produção (Inspetor)", f"{desempenho_insp.iloc[0]['INSPECOES']} insp.")
        col_c.metric(
            "Média de Inspeções por Inspetor",
            f"{desempenho_insp['INSPECOES'].mean():.1f}"
        )

        st.markdown("### 📋 Tabela de Desempenho por Inspetor")
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

        # --------------------------------------------------
        # 📆 Ranking Mensal de Produção dos Inspetores
        # --------------------------------------------------
        st.markdown("### 📆 Ranking Mensal de Produção dos Inspetores")

        prod_mensal = (
            df_insp
            .groupby(["ANO_MES", "MES_ANO_LABEL", "INSPETOR_LISTA"])
            .size()
            .reset_index(name="INSPECOES")
        )

        if not prod_mensal.empty:
            meses_disponiveis = prod_mensal["MES_ANO_LABEL"].unique().tolist()
            meses_disponiveis = sorted(
                meses_disponiveis,
                key=lambda x: datetime.strptime(x, "%b/%Y")
            )

            mes_label_selecionado = st.selectbox(
                "Selecione o Mês/Ano para ver o ranking:",
                meses_disponiveis
            )

            prod_mes_sel = prod_mensal[prod_mensal["MES_ANO_LABEL"] == mes_label_selecionado]
            ranking_mes = (
                prod_mes_sel
                .sort_values("INSPECOES", ascending=False)
                .reset_index(drop=True)
            )
            ranking_mes["POSICAO"] = ranking_mes.index + 1

            col_r1, col_r2 = st.columns([1, 1.5])

            with col_r1:
                st.markdown(f"**Ranking de Inspetores - {mes_label_selecionado}**")
                st.dataframe(
                    ranking_mes[["POSICAO", "INSPETOR_LISTA", "INSPECOES"]],
                    use_container_width=True
                )

            with col_r2:
                fig_rank = px.bar(
                    ranking_mes,
                    x="INSPETOR_LISTA",
                    y="INSPECOES",
                    title=f"🏅 Ranking de Produção - {mes_label_selecionado}",
                    text="INSPECOES"
                )
                fig_rank.update_traces(textposition="outside")
                fig_rank.update_layout(xaxis_title="Inspetor", yaxis_title="Nº de inspeções")
                st.plotly_chart(fig_rank, use_container_width=True)

            # Evolução mensal (todos meses x inspetor)
            fig_evol = px.line(
                prod_mensal.sort_values("ANO_MES"),
                x="MES_ANO_LABEL",
                y="INSPECOES",
                color="INSPETOR_LISTA",
                markers=True,
                title="📈 Evolução Mensal de Produção por Inspetor"
            )
            fig_evol.update_layout(xaxis_title="Mês/Ano", yaxis_title="Nº de inspeções")
            st.plotly_chart(fig_evol, use_container_width=True)

        # --------------------------------------------------
        # 🧍‍♂️ Painel Individual do Inspetor
        # --------------------------------------------------
        st.markdown("### 🧍‍♂️ Painel Individual do Inspetor")

        insp_escolha = st.selectbox(
            "Selecione um inspetor para visualizar detalhes:",
            sorted(desempenho_insp["INSPETOR_LISTA"].unique())
        )

        df_insp_ind = df_insp[df_insp["INSPETOR_LISTA"] == insp_escolha]

        if not df_insp_ind.empty:
            total_insp_ind = len(df_insp_ind)
            estab_unicos_ind = df_insp_ind["ESTABELECIMENTO"].nunique()
            taxa_lib_ind = (
                df_insp_ind["LIBERADO_BIN"].sum() / total_insp_ind * 100
                if total_insp_ind > 0 else 0
            )

            col_i1, col_i2, col_i3 = st.columns(3)
            col_i1.metric("Total de Inspeções (Inspetor)", f"{total_insp_ind}")
            col_i2.metric("Estabelecimentos Atendidos", f"{estab_unicos_ind}")
            col_i3.metric("Taxa de Liberação (%)", f"{taxa_lib_ind:.1f}%")

            # Linha do tempo de inspeções do inspetor
            prod_insp_data = (
                df_insp_ind.groupby("DATA").size().reset_index(name="Inspeções")
            )
            fig_timeline = px.bar(
                prod_insp_data,
                x="DATA",
                y="Inspeções",
                title=f"📅 Linha do Tempo de Inspeções - {insp_escolha}"
            )
            fig_timeline.update_layout(xaxis_title="Data", yaxis_title="Nº de inspeções")
            st.plotly_chart(fig_timeline, use_container_width=True)

            # Distribuição por risco do inspetor
            risco_insp = (
                df_insp_ind["CLASSIFICAÇÃO DE RISCO"]
                .value_counts()
                .reset_index()
                .rename(columns={"index": "Risco", "CLASSIFICAÇÃO DE RISCO": "Quantidade"})
            )
            if not risco_insp.empty:
                fig_risco_insp = px.pie(
                    risco_insp,
                    names="Risco",
                    values="Quantidade",
                    title=f"⚠️ Perfil de Risco Atendido - {insp_escolha}"
                )
                st.plotly_chart(fig_risco_insp, use_container_width=True)

            # Distribuição de motivação do inspetor
            motiv_insp = (
                df_insp_ind["MOTIVAÇÃO"]
                .value_counts()
                .reset_index()
                .rename(columns={"index": "Motivação", "MOTIVAÇÃO": "Quantidade"})
            )
            if not motiv_insp.empty:
                fig_motiv_insp = px.bar(
                    motiv_insp,
                    x="Motivação",
                    y="Quantidade",
                    title=f"🎯 Distribuição de Motivação - {insp_escolha}",
                    text="Quantidade"
                )
                fig_motiv_insp.update_traces(textposition="outside")
                fig_motiv_insp.update_layout(xaxis_title="Motivação", yaxis_title="Nº de inspeções")
                st.plotly_chart(fig_motiv_insp, use_container_width=True)

# ======================================================
# 👥 VISÃO POR COORDENAÇÃO
# ======================================================
with aba_coordenacao:
    st.subheader("👥 Indicadores por Coordenação")

    if df_filtrado.empty:
        st.info("Sem dados para o filtro atual.")
    else:
        grp_coord = df_filtrado.groupby("COORDENAÇÃO").agg(
            INSPECOES=("COORDENAÇÃO", "count"),
            ESTAB_UNICOS=("ESTABELECIMENTO", "nunique"),
            LIBERADOS=("LIBERADO_BIN", "sum")
        ).reset_index()

        grp_coord["TAXA_LIBERACAO_%"] = (
            grp_coord["LIBERADOS"] / grp_coord["INSPECOES"] * 100
        ).round(1)

        grp_coord = grp_coord.sort_values("INSPECOES", ascending=False)

        st.markdown("### 📋 Tabela de Coordenações")
        st.dataframe(grp_coord, use_container_width=True)

        fig_coord = px.bar(
            grp_coord,
            x="COORDENAÇÃO",
            y="INSPECOES",
            title="👥 Produção por Coordenação",
            text="INSPECOES"
        )
        fig_coord.update_traces(textposition="outside")
        fig_coord.update_layout(xaxis_title="Coordenação", yaxis_title="Nº de inspeções")
        st.plotly_chart(fig_coord, use_container_width=True)

        # Coordenação x Classificação de risco
        risco_coord = (
            df_filtrado
            .groupby(["COORDENAÇÃO", "CLASSIFICAÇÃO DE RISCO"])
            .size()
            .reset_index(name="Quantidade")
        )
        if not risco_coord.empty:
            fig_risco_coord = px.bar(
                risco_coord,
                x="COORDENAÇÃO",
                y="Quantidade",
                color="CLASSIFICAÇÃO DE RISCO",
                title="⚠️ Mix de Risco por Coordenação",
                barmode="stack"
            )
            fig_risco_coord.update_layout(xaxis_title="Coordenação", yaxis_title="Nº de inspeções")
            st.plotly_chart(fig_risco_coord, use_container_width=True)

# ======================================================
# 📑 TABELAS DETALHADAS
# ======================================================
with aba_detalhes:
    st.subheader("📑 Visualização Completa dos Dados Filtrados")

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
    st.dataframe(df_filtrado[colunas_existentes].sort_values("DATA", ascending=False), use_container_width=True)

# ======================================================
# 📥 DOWNLOAD
# ======================================================
with aba_download:
    st.subheader("📥 Download dos Dados")

    def gerar_excel_download(dataframe):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            dataframe.to_excel(writer, index=False, sheet_name="Dados Filtrados")
        return output.getvalue()

    st.markdown("Faça o download dos dados filtrados para análise mais detalhada em Excel/Power BI:")

    st.download_button(
        label="📥 Download dos Dados Filtrados (Excel)",
        data=gerar_excel_download(df_filtrado.drop(columns=["INSPETOR_LISTA"], errors="ignore")),
        file_name="dados_filtrados_visa.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
