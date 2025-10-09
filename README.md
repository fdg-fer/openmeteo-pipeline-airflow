# 🌤️ API de Previsão do Clima - Capitais Brasileiras

Este projeto realiza a coleta de dados meteorológicos (como temperatura, vento e chuva) para **capitais brasileiras**, utilizando uma API pública de clima.

Construção de pipeline de dados meteorológicos via API, com foco em boas práticas de engenharia de dados e tratamento robusto de dados JSON

A proposta é extrair dados estruturados de forma automática, organizá-los em JSON e abrir caminho para análises posteriores, como tendências regionais, previsões semanais ou visualizações.

---

## 🚧 Estrutura do Projeto



---

# ☁️ Meteo Pipeline Airflow

Este projeto implementa um **pipeline de dados meteorológicos** desenvolvido em **Python e Apache Airflow**, com integração à **API Open-Meteo** para coleta de informações de **temperatura e precipitação** em capitais brasileiras.

A arquitetura foi projetada para simular um fluxo **real de engenharia de dados**, com:
- **Orquestração de tarefas** via Airflow (usando Docker)
- **Ingestão incremental** e carga histórica automatizada
- **Persistência de dados** no banco PostgreSQL
- **Armazenamento intermediário** em formato Parquet

O objetivo é demonstrar, de forma prática, como construir uma DAG completa — desde a **extração de dados brutos via API**, até a **carga estruturada em banco de dados relacional**, dentro de um ambiente **containerizado e reproduzível**.

---
