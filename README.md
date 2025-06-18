📊 Painel de Produção - Vigilância Sanitária de Ipojuca
📝 Descrição
Este projeto é um painel interativo desenvolvido com Streamlit para visualizar e filtrar os dados de produção da Vigilância Sanitária de Ipojuca, alimentados por uma planilha do Google Sheets que recebe informações via Google Forms.

O painel permite:

Filtrar por múltiplos campos: Estabelecimento, Turno, Localidade, Coordenação, Classificação de risco e Inspetor.

Visualizar resumo da seleção para um único estabelecimento.

Visualize tabelas e gráficos interativos.

Fazer download dos dados filtrados em arquivo Excel.

Hospedagem via GitHub e publicação no Streamlit Cloud .

🚀 Como usar
Pré-requisitos
Python 3.8 ou superior instalado

Instalar as dependências pessoais emrequisitos.txt

Passos para rodar localmente
Clone o repositório ou copie os arquivos visa.pye requisitos.txt.

Instalar as dependências:

festança

Cópia

Editar
pip install -r requisitos.txt
Execute o painel:

festança

Cópia

Editar
streamlit run visa.py
O painel abrirá automaticamente no navegador padrão, ou acesse http://localhost:8501.

🛠️ Estrutura dos arquivos
visa.py: Script principal do painel com toda a lógica de carregamento, filtros, gráficos e download.

requisitos.txt: Lista de bibliotecas Python que permitem rodar o projeto.

⚙️ Configuração da Planilha Google Sheets
A planilha precisa ser configurada para permitir a exportação em CSV público via URL (exemplo usado no código).

As colunas obrigatórias (em caixa alta) são:

ESTABELECIMENTO

TURNO

LOCALIDADE

COORDENAÇÃO

CLASSIFICAÇÃO DE RISCO

EQUIPE/INSPETOR

📥 Baixe os dados filtrados
O botão de download permite exportar a seleção atual para um arquivo Excel, utilizando uma biblioteca xlsxwriterpara gerar o arquivo.

🌐 Publicação no Streamlit Cloud
Para publicar seu painel online:

Faça um push do repositório com os arquivos para o GitHub.

Acesse https://share.streamlit.io/ .

Conecte-se à sua conta do GitHub.

Importe seu repositório e selecione o arquivo visa.pypara iniciar o deploy.

O Streamlit Cloud será instalado automaticamente conforme as dependências declaradas no requisitos.txt.

Contato
Desenvolvido por: Vigilância em Saúde de Ipojuca
E-mail: exemplo@ipojuca.pe.gov.br