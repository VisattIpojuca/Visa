# 🦠 Painel de Produção da Vigilância Sanitária de Ipojuca

Este painel tem como objetivo monitorar, analisar e visualizar os dados de produção da Vigilância Sanitária de Ipojuca, a partir das informações preenchidas no formulário oficial da VISA, que alimenta uma planilha online.

## 🔗 Acesse o painel online:
👉 [Clique aqui para acessar o painel no Streamlit](https://painelvisa.streamlit.app/)

---

## 🚀 Funcionalidades

- 📅 Filtro de período (seleção de datas em formato de calendário)
- 🕑 Filtro por turno
- 📍 Filtro por localidade
- 🏢 Filtro por estabelecimento
- 👥 Filtro por coordenação
- ⚠️ Filtro por classificação de risco
- 🎯 Filtro por motivação
- ✅ Filtro por status do estabelecimento (liberado ou não)
- 🕵️‍♂️ Filtro por inspetor (identifica automaticamente os nomes, mesmo quando há mais de um por inspeção)
- 📥 Download dos dados filtrados
- 📊 Análises gráficas:
  - 📅 Produção ao longo do período
  - 🎯 Distribuição por motivação
  - ✔️ Status do estabelecimento
  - 🏙️ Classificação de risco por localidade

---

## 🗂️ Dados de entrada

A planilha é gerada automaticamente pelo Google Forms e está hospedada no Google Sheets, que serve como fonte de dados dinâmica para o painel.

## 📦 Como executar localmente

1. Clone este repositório:
```bash
git clone https://github.com/seuusuario/nome-do-repositorio.git
cd nome-do-repositorio
