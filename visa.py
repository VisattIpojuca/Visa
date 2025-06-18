import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# 🎨 Configurações da página
st.set_page_config(page_title="Painel VISA Ipojuca", layout="wide")
st.title("🦠 Painel de Produção - Vigilância Sanitária de Ipojuca")

# 📥 URL da planilha
url = 'https://docs.google.com/spreadsheets/d/1CP6RD8UlHzB6FB7x8fhS3YZB0rVGPyf6q99PNp4iAGQ/export?format=csv'

# 🚀 Carregar dados
@st.cache_data
def carregar_dados():
    df = pd.read_csv(url, dtype=str)
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    return df

df = carregar_dados()

# 🔧 Limpeza básica
if 'Carimbo de data/hora' in df.columns:
    df = df.drop(columns=['Carimbo de data/hora'])

# Identificar coluna de data
col_data = [c for c in df.columns if "data" in c.lower()][0]

# Transformar data em formato datetime
df[col_data] = pd.to_datetime(df[col_data], dayfirst=True, errors='coerce')

# Corrigir lista de inspetores
def extrair_inspetores(texto):
    if pd.isna(texto):
        return []
    return [nome.strip().upper() for nome in str(texto).split(',')]

df['INSPETOR_LISTA'] = df['EQUIPE/INSPETOR'].apply(extrair_inspetores)

# -------------------------------
# 🧠 Barra lateral - Filtros
# -------------------------------
st.sidebar.header("Filtros")

# Filtro de datas em formato de calendário
data_min = df[col_data].min()
data_max = df[col_data].max()

data_range = st.sidebar.date_input(
    "📅 Período",
    value=(data_min, data_max),
    min_value=data_min,
    max_value=data_max
)

# Filtros adicionais
turno = st.sidebar.multiselect("🕑 Turno", sorted(df['TURNO'].dropna().unique()))
localidade = st.sidebar.multiselect("📍 Localidade", sorted(df['LOCALIDADE'].dropna().unique()))
estabelecimento = st.sidebar.multiselect("🏢 Estabelecimento", sorted(df['ESTABELECIMENTO'].dropna().unique()))
coordenacao = st.sidebar.multiselect("👥 Coordenação", sorted(df['COORDENAÇÃO'].dropna().unique()))
class_risco = st.sidebar.multiselect("⚠️ Classificação de Risco", sorted(df['CLASSIFICAÇÃO DE RISCO'].dropna().unique()))
motivacao = st.sidebar.multiselect("🎯 Motivação", sorted(df['MOTIVAÇÃO'].dropna().unique()))
status = st.sidebar.multiselect("✅ Status do Estabelecimento", sorted(df['O ESTABELECIMENTO FOI LIBERADO'].dropna().unique()))

# Filtro por inspetor
todos_inspetores = sorted(set(sum(df['INSPETOR_LISTA'].tolist(), [])))
inspetores = st.sidebar.multiselect("🕵️‍♂️ Inspetor", todos_inspetores)

# -------------------------------
# 🔍 Aplicar filtros
# -------------------------------
df_filtrado = df.copy()

if data_range:
    df_filtrado = df_filtrado[
        (df_filtrado[col_data] >= pd.to_datetime(data_range[0])) &
        (df_filtrado[col_data] <= pd.to_datetime(data_range[1]))
    ]
if turno:
    df_filtrado = df_filtrado[df_filtrado['TURNO'].isin(turno)]
if localidade:
    df_filtrado = df_filtrado[df_filtrado['LOCALIDADE'].isin(localidade)]
if estabelecimento:
    df_filtrado = df_filtrado[df_filtrado['ESTABELECIMENTO'].isin(estabelecimento)]
if coordenacao:
    df_filtrado = df_filtrado[df_filtrado['COORDENAÇÃO'].isin(coordenacao)]
if class_risco:
    df_filtrado = df_filtrado[df_filtrado['CLASSIFICAÇÃO DE RISCO'].isin(class_risco)]
if motivacao:
    df_filtrado = df_filtrado[df_filtrado['MOTIVAÇÃO'].isin(motivacao)]
if status:
    df_filtrado = df_filtrado[df_filtrado['O ESTABELECIMENTO FOI LIBERADO'].isin(status)]
if inspetores:
    df_filtrado = df_filtrado[df_filtrado['INSPETOR_LISTA'].apply(lambda x: any(i in x for i in inspetores))]

# -------------------------------
# 📌 Resumo da seleção
# -------------------------------
if len(estabelecimento) == 1:
    st.sidebar.subheader("📌 Resumo da Seleção")
    est = estabelecimento[0]
    dados_est = df_filtrado[df_filtrado['ESTABELECIMENTO'] == est]
    local = dados_est['LOCALIDADE'].dropna().unique()
    coord = dados_est['COORDENAÇÃO'].dropna().unique()
    risco = dados_est['CLASSIFICAÇÃO DE RISCO'].dropna().unique()

    st.sidebar.markdown(f"""
    - **Estabelecimento:** {est}
    - **Localidade:** {', '.join(local) if len(local) > 0 else 'Não informado'}
    - **Coordenação:** {', '.join(coord) if len(coord) > 0 else 'Não informado'}
    - **Classificação de Risco:** {', '.join(risco) if len(risco) > 0 else 'Não informado'}
    """)

# -------------------------------
# 📑 Visualização dos Dados
# -------------------------------
st.subheader("📑 Visualização dos Dados")

st.dataframe(
    df_filtrado[[col_data, 'TURNO', 'ESTABELECIMENTO', 'LOCALIDADE', 'COORDENAÇÃO',
                 'CLASSIFICAÇÃO DE RISCO', 'MOTIVAÇÃO', 'O ESTABELECIMENTO FOI LIBERADO',
                 'NÚMERO DA VISITA', 'EQUIPE/INSPETOR']]
)

# -------------------------------
# 📊 Gráficos
# -------------------------------
st.subheader("📈 Análises Gráficas")

col1, col2 = st.columns(2)

# 📅 Produção ao longo do período
with col1:
    prod_por_data = df_filtrado.groupby(col_data).size().reset_index(name='Inspeções')
    graf1 = px.bar(prod_por_data, x=col_data, y='Inspeções',
                   title="📅 Produção ao Longo do Período")
    st.plotly_chart(graf1, use_container_width=True)

# 🎯 Distribuição por Motivação
with col2:
    motiv_counts = df_filtrado['MOTIVAÇÃO'].value_counts().reset_index()
    motiv_counts.columns = ['Motivação', 'Quantidade']
    graf2 = px.pie(motiv_counts, names='Motivação', values='Quantidade',
                   title="🎯 Distribuição por Motivação")
    st.plotly_chart(graf2, use_container_width=True)

# ✔️ Status do Estabelecimento
col3, col4 = st.columns(2)
with col3:
    status_counts = df_filtrado['O ESTABELECIMENTO FOI LIBERADO'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Quantidade']
    graf3 = px.pie(status_counts, names='Status', values='Quantidade',
                   title="✔️ Status do Estabelecimento")
    st.plotly_chart(graf3, use_container_width=True)

# 🏙️ Classificação de Risco por Localidade
with col4:
    risco_local = df_filtrado.groupby(['LOCALIDADE', 'CLASSIFICAÇÃO DE RISCO']).size().reset_index(name='Quantidade')
    graf4 = px.bar(risco_local, x='LOCALIDADE', y='Quantidade', color='CLASSIFICAÇÃO DE RISCO',
                   title="🏙️ Classificação de Risco por Localidade", barmode='stack')
    st.plotly_chart(graf4, use_container_width=True)

# -------------------------------
# 📥 Download dos Dados
# -------------------------------
def gerar_excel_download(dataframe):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        dataframe.to_excel(writer, index=False, sheet_name='Dados Filtrados')
    return output.getvalue()

st.download_button(
    label="📥 Download dos Dados Filtrados",
    data=gerar_excel_download(df_filtrado.drop(columns=['INSPETOR_LISTA'], errors='ignore')),
    file_name="dados_filtrados_visa.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
