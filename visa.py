import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# Configurações da página
st.set_page_config(page_title="Painel VISA - Ipojuca", layout="wide")

st.title("Painel de Produção da Vigilância Sanitária - Ipojuca")

# URL da planilha
sheet_url = 'https://docs.google.com/spreadsheets/d/1CP6RD8UlHzB6FB7x8fhS3YZB0rVGPyf6q99PNp4iAGQ/export?format=csv'
df = pd.read_csv(sheet_url)

# Padronização dos nomes das colunas
df.columns = df.columns.str.upper()

# Tratamento de data
df['DATA'] = pd.to_datetime(df['DATA'], dayfirst=True, errors='coerce')

# Tratamento do campo INSPETOR
df['INSPETOR_LISTA'] = df['EQUIPE/INSPETOR'].fillna('').str.upper().str.split(',')
df = df.explode('INSPETOR_LISTA')
df['INSPETOR_LISTA'] = df['INSPETOR_LISTA'].str.strip()

# Sidebar - Filtros
st.sidebar.header("Filtros")

datas = st.sidebar.multiselect("Data", sorted(df['DATA'].dropna().dt.strftime('%d/%m/%Y').unique()))
turno = st.sidebar.multiselect("Turno", sorted(df['TURNO'].dropna().unique()))
localidade = st.sidebar.multiselect("Localidade", sorted(df['LOCALIDADE'].dropna().unique()))
estabelecimento = st.sidebar.multiselect("Estabelecimento", sorted(df['ESTABELECIMENTO'].dropna().unique()))
coordenacao = st.sidebar.multiselect("Coordenação", sorted(df['COORDENAÇÃO'].dropna().unique()))
risco = st.sidebar.multiselect("Classificação de Risco", sorted(df['CLASSIFICAÇÃO DE RISCO'].dropna().unique()))
inspetor = st.sidebar.multiselect("Inspetor", sorted(df['INSPETOR_LISTA'].dropna().unique()))
motivacao = st.sidebar.multiselect("Motivação", sorted(df['MOTIVAÇÃO'].dropna().unique()))
status = st.sidebar.multiselect("Status do Estabelecimento", sorted(df['O ESTABELECIMENTO FOI LIBERADO'].dropna().unique()))

# Aplicação dos filtros
df_filtrado = df.copy()

if datas:
    datas_convertidas = pd.to_datetime(datas, dayfirst=True)
    df_filtrado = df_filtrado[df_filtrado['DATA'].isin(datas_convertidas)]

if turno:
    df_filtrado = df_filtrado[df_filtrado['TURNO'].isin(turno)]

if localidade:
    df_filtrado = df_filtrado[df_filtrado['LOCALIDADE'].isin(localidade)]

if estabelecimento:
    df_filtrado = df_filtrado[df_filtrado['ESTABELECIMENTO'].isin(estabelecimento)]

if coordenacao:
    df_filtrado = df_filtrado[df_filtrado['COORDENAÇÃO'].isin(coordenacao)]

if risco:
    df_filtrado = df_filtrado[df_filtrado['CLASSIFICAÇÃO DE RISCO'].isin(risco)]

if inspetor:
    df_filtrado = df_filtrado[df_filtrado['INSPETOR_LISTA'].isin(inspetor)]

if motivacao:
    df_filtrado = df_filtrado[df_filtrado['MOTIVAÇÃO'].isin(motivacao)]

if status:
    df_filtrado = df_filtrado[df_filtrado['O ESTABELECIMENTO FOI LIBERADO'].isin(status)]

# Resumo da seleção
if len(estabelecimento) == 1 and not df_filtrado.empty:
    est_info = df_filtrado.iloc[0]
    st.sidebar.subheader("Resumo da Seleção")
    st.sidebar.markdown(f"""
    **Estabelecimento:** {est_info['ESTABELECIMENTO']}  
    **Localidade:** {est_info['LOCALIDADE']}  
    **Coordenação:** {est_info['COORDENAÇÃO']}  
    **Classificação de Risco:** {est_info['CLASSIFICAÇÃO DE RISCO']}  
    """)

# Gráficos
if not df_filtrado.empty:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Produção por Inspetor")
        df_insp = df_filtrado['INSPETOR_LISTA'].value_counts().reset_index()
        df_insp.columns = ['Inspetor', 'Número de Visitas']
        fig_insp = px.bar(df_insp, x='Inspetor', y='Número de Visitas', color='Inspetor')
        st.plotly_chart(fig_insp, use_container_width=True)

    with col2:
        st.subheader("Produção ao Longo do Tempo")
        df_tempo = df_filtrado.groupby(df_filtrado['DATA'].dt.strftime('%d/%m/%Y')).size().reset_index(name='Visitas')
        fig_tempo = px.bar(df_tempo, x='DATA', y='Visitas')
        st.plotly_chart(fig_tempo, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Distribuição por Motivação")
        fig_mot = px.pie(df_filtrado, names='MOTIVAÇÃO', title='Motivações')
        st.plotly_chart(fig_mot, use_container_width=True)

    with col4:
        st.subheader("Status dos Estabelecimentos")
        fig_status = px.pie(df_filtrado, names='O ESTABELECIMENTO FOI LIBERADO', title='Status')
        st.plotly_chart(fig_status, use_container_width=True)

    st.subheader("Classificação de Risco por Localidade")
    fig_risco = px.histogram(df_filtrado, x='LOCALIDADE', color='CLASSIFICAÇÃO DE RISCO', barmode='group')
    st.plotly_chart(fig_risco, use_container_width=True)

    # Visualização dos Dados
    st.subheader("Visualização de Dados")
    st.dataframe(df_filtrado[['DATA', 'TURNO', 'ESTABELECIMENTO', 'LOCALIDADE', 'COORDENAÇÃO', 'CLASSIFICAÇÃO DE RISCO',
                               'INSPETOR_LISTA', 'MOTIVAÇÃO', 'O ESTABELECIMENTO FOI LIBERADO', 'NÚMERO DA VISITA']])

    # Download dos Dados Filtrados
    def gerar_excel_download(dataframe):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            dataframe.to_excel(writer, index=False, sheet_name='Dados')
        output.seek(0)
        return output

    st.download_button(
        label="📥 Download dos Dados Filtrados",
        data=gerar_excel_download(df_filtrado.drop(columns=['INSPETOR_LISTA'], errors='ignore')),
        file_name='dados_filtrados.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
else:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
