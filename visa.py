import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# Configurações da página
st.set_page_config(page_title="Painel de Produção - Vigilância Sanitária de Ipojuca", layout="wide")
st.title("📊 Painel de Produção - Vigilância Sanitária de Ipojuca")

# URL da planilha do Google Sheets
url = 'https://docs.google.com/spreadsheets/d/1CP6RD8UlHzB6FB7x8fhS3YZB0rVGPyf6q99PNp4iAGQ/export?format=csv'

# Carregar dados
@st.cache_data
def carregar_dados():
    df = pd.read_csv(url, dtype=str)
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    return df

df = carregar_dados()

# Padronizar e tratar dados
for coluna in ['DATAS', 'TURNO', 'ESTABELECIMENTO', 'LOCALIDADE', 'COORDENAÇÃO',
               'CLASSIFICAÇÃO DE RISCO', 'EQUIPE/INSPETOR', 'MOTIVAÇÃO', 
               'O ESTABELECIMENTO FOI LIBERADO', 'NÚMERO DA VISITA']:
    if coluna not in df.columns:
        df[coluna] = ''

# Criar lista de inspetores individuais
def extrair_inspetores(texto):
    if pd.isna(texto):
        return []
    return [nome.strip().upper() for nome in str(texto).split(',')]

df['INSPETOR_LISTA'] = df['EQUIPE/INSPETOR'].apply(extrair_inspetores)

# -------------------------------
# BARRA LATERAL COM FILTROS
# -------------------------------
st.sidebar.header("Filtros")

# Filtros principais
datas = st.sidebar.multiselect("📅 Data", sorted(df['DATAS'].dropna().unique()))
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
# APLICAR FILTROS
# -------------------------------
df_filtrado = df.copy()

if datas:
    df_filtrado = df_filtrado[df_filtrado['DATAS'].isin(datas)]
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
# RESUMO DA SELEÇÃO
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
# VISUALIZAÇÃO DE DADOS
# -------------------------------
st.subheader("📑 Visualização dos Dados")

st.dataframe(
    df_filtrado[['DATAS', 'TURNO', 'ESTABELECIMENTO', 'LOCALIDADE', 'COORDENAÇÃO',
                 'CLASSIFICAÇÃO DE RISCO', 'MOTIVAÇÃO', 'O ESTABELECIMENTO FOI LIBERADO',
                 'NÚMERO DA VISITA', 'EQUIPE/INSPETOR']]
)

# -------------------------------
# GRÁFICOS
# -------------------------------
st.subheader("📊 Análise Gráfica")

col1, col2 = st.columns(2)

with col1:
    graf1 = px.histogram(df_filtrado, x='LOCALIDADE', color='CLASSIFICAÇÃO DE RISCO',
                          title="Distribuição por Localidade e Risco")
    st.plotly_chart(graf1, use_container_width=True)

with col2:
    graf2 = px.histogram(df_filtrado, x='COORDENAÇÃO', color='CLASSIFICAÇÃO DE RISCO',
                          title="Distribuição por Coordenação e Risco")
    st.plotly_chart(graf2, use_container_width=True)

# -------------------------------
# DOWNLOAD DOS DADOS
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
