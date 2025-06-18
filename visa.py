import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# Configuração da página
st.set_page_config(page_title="Painel de Produção - Vigilância Sanitária de Ipojuca", layout="wide")

st.title("📊 Painel de Produção - Vigilância Sanitária de Ipojuca")

# --- FUNÇÃO PARA CARREGAR OS DADOS ---
@st.cache_data
def carregar_dados():
    url = 'https://docs.google.com/spreadsheets/d/1CP6RD8UlHzB6FB7x8fhS3YZB0rVGPyf6q99PNp4iAGQ/export?format=csv'
    df = pd.read_csv(url)
    return df


# --- CARREGAR OS DADOS ---
try:
    df = carregar_dados()
    df.columns = df.columns.str.strip().str.upper()  # Remove espaços e deixa tudo em caixa alta
except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")
    st.stop()

# --- VERIFICAR COLUNAS NECESSÁRIAS ---
colunas_necessarias = ["ESTABELECIMENTO", "TURNO", "LOCALIDADE", "COORDENAÇÃO", "CLASSIFICAÇÃO DE RISCO", "EQUIPE/INSPETOR"]

faltando = [col for col in colunas_necessarias if col not in df.columns]

if faltando:
    st.error(f"🚨 As seguintes colunas estão faltando na planilha: {', '.join(faltando)}")
    st.subheader("🔍 Nomes encontrados na planilha:")
    st.write(df.columns.tolist())
    st.stop()

# --- AJUSTES NA COLUNA DE INSPETOR ---
# Expandir os nomes de inspetores que estão separados por vírgula
df_inspetores = df.copy()

df_inspetores['INSPETOR_LISTA'] = df_inspetores['EQUIPE/INSPETOR'].fillna('').apply(
    lambda x: [nome.strip() for nome in str(x).split(',') if nome.strip() != '']
)

inspetores_unicos = sorted(set([nome for sublist in df_inspetores['INSPETOR_LISTA'] for nome in sublist]))

# --- DEFINIR OS FILTROS ---
st.sidebar.header("🎯 Filtros")

filtro_estabelecimento = st.sidebar.multiselect("Estabelecimento", sorted(df['ESTABELECIMENTO'].dropna().unique()))
filtro_turno = st.sidebar.multiselect("Turno", sorted(df['TURNO'].dropna().unique()))
filtro_localidade = st.sidebar.multiselect("Localidade", sorted(df['LOCALIDADE'].dropna().unique()))
filtro_coordenacao = st.sidebar.multiselect("Coordenação", sorted(df['COORDENAÇÃO'].dropna().unique()))
filtro_classificacao = st.sidebar.multiselect("Classificação de risco", sorted(df['CLASSIFICAÇÃO DE RISCO'].dropna().unique()))
filtro_inspetor = st.sidebar.multiselect("Inspetor", inspetores_unicos)

# --- APLICAR FILTROS ---
df_filtrado = df_inspetores.copy()

if filtro_estabelecimento:
    df_filtrado = df_filtrado[df_filtrado['ESTABELECIMENTO'].isin(filtro_estabelecimento)]
if filtro_turno:
    df_filtrado = df_filtrado[df_filtrado['TURNO'].isin(filtro_turno)]
if filtro_localidade:
    df_filtrado = df_filtrado[df_filtrado['LOCALIDADE'].isin(filtro_localidade)]
if filtro_coordenacao:
    df_filtrado = df_filtrado[df_filtrado['COORDENAÇÃO'].isin(filtro_coordenacao)]
if filtro_classificacao:
    df_filtrado = df_filtrado[df_filtrado['CLASSIFICAÇÃO DE RISCO'].isin(filtro_classificacao)]
if filtro_inspetor:
    df_filtrado = df_filtrado[df_filtrado['INSPETOR_LISTA'].apply(lambda x: any(i in x for i in filtro_inspetor))]

# --- RESUMO DA SELEÇÃO ---
if len(filtro_estabelecimento) == 1:
    est = filtro_estabelecimento[0]
    dados_est = df[df['ESTABELECIMENTO'] == est].iloc[0]

    with st.sidebar.expander("📌 Resumo da Seleção", expanded=True):
        st.write(f"**Estabelecimento:** {dados_est.get('ESTABELECIMENTO', 'Não informado')}")
        st.write(f"**Localidade:** {dados_est.get('LOCALIDADE', 'Não informado')}")
        st.write(f"**Coordenação:** {dados_est.get('COORDENAÇÃO', 'Não informado')}")
        st.write(f"**Classificação de risco:** {dados_est.get('CLASSIFICAÇÃO DE RISCO', 'Não informado')}")

# --- BOTÃO DE DOWNLOAD DA TABELA FILTRADA ---
def gerar_excel_download(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados Filtrados')
    processed_data = output.getvalue()
    return processed_data

st.sidebar.download_button(
    label="📥 Baixar dados filtrados",
    data=gerar_excel_download(df_filtrado.drop(columns=['INSPETOR_LISTA'], errors='ignore')),
    file_name='dados_filtrados.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)

# --- ÁREA PRINCIPAL ---
st.subheader("📑 Visualização dos Dados")

st.dataframe(df_filtrado.drop(columns=['INSPETOR_LISTA'], errors='ignore'), use_container_width=True)

# --- GRÁFICOS ---

col1, col2 = st.columns(2)

with col1:
    grafico_localidade = df_filtrado['LOCALIDADE'].value_counts().reset_index()
    grafico_localidade.columns = ['Localidade', 'Quantidade']
    fig1 = px.bar(grafico_localidade, x='Localidade', y='Quantidade',
                  title='Atendimentos por Localidade', text_auto=True)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    grafico_classificacao = df_filtrado['CLASSIFICAÇÃO DE RISCO'].value_counts().reset_index()
    grafico_classificacao.columns = ['Classificação de risco', 'Quantidade']
    fig2 = px.pie(grafico_classificacao, names='Classificação de risco', values='Quantidade',
                  title='Distribuição por Classificação de risco')
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")
st.caption("Desenvolvido pela Vigilância em Saúde de Ipojuca - 2025")
