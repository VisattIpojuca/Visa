import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from io import BytesIO

# 🚀 Configuração da página
st.set_page_config(page_title="Painel VISA - Ipojuca", layout="wide")
st.title("📊 Painel de Produção - Vigilância Sanitária de Ipojuca")

# 🔗 URL da planilha Google Sheets
url = 'https://docs.google.com/spreadsheets/d/1CP6RD8UlHzB6FB7x8fhS3YZB0rVGPyf6q99PNp4iAGQ/export?format=csv'

# 🔄 Carregar dados
@st.cache_data
def carregar_dados():
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip().str.upper()

    df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce', dayfirst=True)
    df['MÊS'] = df['DATA'].dt.to_period('M').astype(str)

    df['INSPETOR_LISTA'] = df['EQUIPE/INSPETOR'].fillna('').str.upper().str.split(r',\s*')

    df_inspetores = df.explode('INSPETOR_LISTA')
    df_inspetores['INSPETOR_LISTA'] = df_inspetores['INSPETOR_LISTA'].str.strip()

    return df, df_inspetores

# Carregar dados
df_equipes, df_inspetores = carregar_dados()

# 🔍 Sidebar - Filtros
st.sidebar.header("Filtros")
todos_inspetores = sorted(set([i.strip() for sub in df_equipes['INSPETOR_LISTA'] for i in sub if i]))

filtros = {
    'MÊS': st.sidebar.multiselect("📅 Mês", sorted(df_equipes['MÊS'].dropna().unique())),
    'DATA': st.sidebar.multiselect("📆 Data", sorted(df_equipes['DATA'].dropna().dt.strftime('%d/%m/%Y').unique())),
    'ESTABELECIMENTO': st.sidebar.multiselect("🏢 Estabelecimento", sorted(df_equipes['ESTABELECIMENTO'].dropna().unique())),
    'TURNO': st.sidebar.multiselect("🕑 Turno", sorted(df_equipes['TURNO'].dropna().unique())),
    'LOCALIDADE': st.sidebar.multiselect("📍 Localidade", sorted(df_equipes['LOCALIDADE'].dropna().unique())),
    'COORDENAÇÃO': st.sidebar.multiselect("👥 Coordenação", sorted(df_equipes['COORDENAÇÃO'].dropna().unique())),
    'CLASSIFICAÇÃO DE RISCO': st.sidebar.multiselect("⚠️ Classificação de Risco", sorted(df_equipes['CLASSIFICAÇÃO DE RISCO'].dropna().unique())),
    'MOTIVAÇÃO': st.sidebar.multiselect("🎯 Motivação", sorted(df_equipes['MOTIVAÇÃO'].dropna().unique())),
    'STATUS': st.sidebar.multiselect("✅ Status do Estabelecimento", sorted(df_equipes['O ESTABELECIMENTO FOI LIBERADO'].dropna().unique())),
    'INSPETOR': st.sidebar.multiselect("🕵️‍♂️ Inspetor", todos_inspetores)
}

def aplicar_filtros(df):
    df_filtrado = df.copy()

    if filtros['MÊS']:
        df_filtrado = df_filtrado[df_filtrado['MÊS'].isin(filtros['MÊS'])]

    if filtros['DATA']:
        datas_convertidas = pd.to_datetime(filtros['DATA'], format='%d/%m/%Y', errors='coerce')
        df_filtrado = df_filtrado[df_filtrado['DATA'].isin(datas_convertidas)]

    for coluna in ['ESTABELECIMENTO', 'TURNO', 'LOCALIDADE', 'COORDENAÇÃO', 'CLASSIFICAÇÃO DE RISCO', 'MOTIVAÇÃO', 'STATUS']:
        filtro_col = 'O ESTABELECIMENTO FOI LIBERADO' if coluna == 'STATUS' else coluna
        if filtros[coluna]:
            df_filtrado = df_filtrado[df_filtrado[filtro_col].isin(filtros[coluna])]

    if filtros['INSPETOR']:
        df_filtrado = df_filtrado[df_filtrado['INSPETOR_LISTA'].apply(
            lambda x: any(i in x for i in filtros['INSPETOR'])
        )]

    return df_filtrado

# Aplicar filtros
df_equipes_filtrado = aplicar_filtros(df_equipes)
df_inspetores_filtrado = aplicar_filtros(df_inspetores)

# 🔹 Resumo da Seleção
if len(filtros['ESTABELECIMENTO']) == 1:
    dados_resumo = df_equipes_filtrado[['ESTABELECIMENTO', 'LOCALIDADE', 'COORDENAÇÃO', 'CLASSIFICAÇÃO DE RISCO']].drop_duplicates()
    st.sidebar.subheader("📌 Resumo da Seleção")
    st.sidebar.dataframe(dados_resumo)

# 🔹 Visualização de Dados (Por Equipe)
st.subheader("📑 Visualização dos Dados (Por Equipe)")
st.dataframe(df_equipes_filtrado[['DATA', 'ESTABELECIMENTO', 'LOCALIDADE', 'TURNO', 'COORDENAÇÃO',
                                  'CLASSIFICAÇÃO DE RISCO', 'MOTIVAÇÃO', 'O ESTABELECIMENTO FOI LIBERADO',
                                  'NÚMERO DA VISITA', 'EQUIPE/INSPETOR']])

# 🔹 Gráficos - Produção por Equipe
st.subheader("📊 Análise Gráfica - Produção por Equipe")

col1, col2 = st.columns(2)

with col1:
    if not df_equipes_filtrado.empty:
        fig_local = px.bar(df_equipes_filtrado['LOCALIDADE'].value_counts().reset_index(),
                            x='index', y='LOCALIDADE',
                            labels={'index':'Localidade', 'LOCALIDADE':'Número de Visitas'},
                            title='Visitas por Localidade')
        st.plotly_chart(fig_local, use_container_width=True)
    else:
        st.warning("Nenhum dado para gerar gráfico de Localidade.")

with col2:
    if not df_equipes_filtrado.empty:
        fig_risco = px.bar(df_equipes_filtrado['CLASSIFICAÇÃO DE RISCO'].value_counts().reset_index(),
                            x='index', y='CLASSIFICAÇÃO DE RISCO',
                            labels={'index':'Classificação de Risco', 'CLASSIFICAÇÃO DE RISCO':'Número de Visitas'},
                            title='Visitas por Classificação de Risco')
        st.plotly_chart(fig_risco, use_container_width=True)
    else:
        st.warning("Nenhum dado para gerar gráfico de Classificação de Risco.")

# 🔹 Produção por Inspetor
st.subheader("🕵️‍♂️ Produção por Inspetor (Individual)")

if not df_inspetores_filtrado.empty:
    df_insp = df_inspetores_filtrado['INSPETOR_LISTA'].value_counts().reset_index()
    df_insp.columns = ['Inspetor', 'Número de Visitas']
    fig_insp = px.bar(df_insp, x='Inspetor', y='Número de Visitas', color='Inspetor',
                       title="Produção Individual dos Inspetores")
    st.plotly_chart(fig_insp, use_container_width=True)
else:
    st.warning("Nenhum dado para gerar gráfico de Produção por Inspetor.")

# 🔽 Download dos Dados
def gerar_excel_download(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados Filtrados')
    output.seek(0)
    return output.getvalue()

st.subheader("📥 Download dos Dados")

st.download_button(
    label="📥 Baixar Dados Filtrados (Por Equipe)",
    data=gerar_excel_download(df_equipes_filtrado),
    file_name="dados_filtrados_equipes.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.download_button(
    label="📥 Baixar Dados Produção por Inspetor",
    data=gerar_excel_download(df_inspetores_filtrado),
    file_name="dados_filtrados_inspetores.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
