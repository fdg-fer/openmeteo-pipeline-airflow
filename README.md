# 🌤️ API de Previsão do Clima - Capitais Brasileiras

Este projeto realiza a coleta de dados meteorológicos (como temperatura, vento e chuva) para **capitais brasileiras**, utilizando uma API pública de clima.

Construção de pipeline de dados meteorológicos via API, com foco em boas práticas de engenharia de dados e tratamento robusto de dados JSON

A proposta é extrair dados estruturados de forma automática, organizá-los em JSON e abrir caminho para análises posteriores, como tendências regionais, previsões semanais ou visualizações.

---

## 🚧 Estrutura do Projeto

```text
📁 projeto_clima/
│
├── 📄 clima.py  ← Funções reutilizáveis
│     ├── def busca_coordenada(cidade)
│     │     ↪ Requisição para API Nominatim (coordenadas)
│     │     ↪ Retorna: lat, lon, regiao
│     │
│     ├── def previsao_temperatura(lat, lon, cidade)
│     │     ↪ Requisição para OpenMeteo (temperatura e vento por hora)
│     │     ↪ Cria DataFrame com mínimas e máximas por data
│     │
│     ├── def chuva_total(lat, lon, cidade)
│     │     ↪ Requisição para OpenMeteo (chuva diária)
│     │     ↪ Cria DataFrame com soma diária da chuva
│     │
│     ├── def historico_temperatura(lat, lon, cidade)
│     │     ↪ Requisição para OpenMeteo (histórico de temperatura e vento por hora)
│     │     ↪ Cria DataFrame com mínimas e máximas por data
│     │
│     └── def historico_chuva(lat, lon, cidade)
│           ↪ Requisição para OpenMeteo (chuva histórica diária)
│           ↪ Cria DataFrame com soma da chuva por dia
│
├── 📄 main_previsao.py  ← Roda as previsões
│     ├── Carrega capitais do arquivo JSON
│     ├── Loop 1: busca coordenadas (e região) de cada cidade
│     ├── Loop 2: previsão de temperatura e vento
│     ├── Loop 3: previsão de chuva
│     └── Junta tudo em df_previsao e imprime/salva o resultado
│
├── 📄 main_historico.py  ← Roda o histórico
│     ├── Carrega capitais do arquivo JSON
│     ├── Loop 1: busca coordenadas
│     ├── Loop 2: histórico de temperatura e vento
│     ├── Loop 3: histórico de chuva
│     └── Junta tudo em df_historico e imprime/salva o resultado
│
└── 📄 capitais.json  ← Lista com as 27 capitais brasileiras
```

---

# 🔁 Pipeline de Coleta e Armazenamento de Dados Climáticos


| Etapa                    | Ferramenta               | Descrição                                                                 |
|--------------------------|--------------------------|---------------------------------------------------------------------------|
| 1. Coleta API            | Python (`clima.py`)      | Realiza requisições para APIs de clima (Nominatim e Open-Meteo).         |
| 2. Salvar Bronze         | Databricks File System   | Armazena os dados brutos no formato JSON para rastreabilidade.           |
| 3. Tratar Dados          | Pandas ou PySpark        | Processa os dados e organiza em DataFrames estruturados.                 |
| 4. Salvar Silver/Gold    | Delta Table ou Parquet   | Salva os dados tratados em formatos otimizados para consulta e análise.  |
| 5. Inserir em PostgreSQL | Pandas + SQLAlchemy      | Exporta os dados finais para uso externo via banco PostgreSQL.           |

---

