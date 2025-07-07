# 🌤️ API de Previsão do Clima - Capitais Brasileiras

Este projeto realiza a coleta de dados meteorológicos (como temperatura, vento e chuva) para **capitais brasileiras**, utilizando uma API pública de clima.

Construção de pipeline de dados meteorológicos via API, com foco em boas práticas de engenharia de dados e tratamento robusto de dados JSON

A proposta é extrair dados estruturados de forma automática, organizá-los em JSON e abrir caminho para análises posteriores, como tendências regionais, previsões semanais ou visualizações.

---

## 🚧 Estrutura do Projeto

```text
projeto_clima/
├── clima.py            # funções reutilizáveis (módulo principal)
├── main.py             # script principal que roda a coleta de dados
├── gerar_capitais.py   # cria/atualiza o arquivo capitais.json
└── capitais.json       # contém os nomes e dados das capitais brasileiras

```text
📁 projeto_clima/
│
├── 📄 clima.py  ← Funções reutilizáveis
│     ├── def busca_coordenada(cidade)
│     │     ↪ Requisição para API Nominatim (coordenadas)
│     │     ↪ Retorna: lat, lon, regiao
│     │
│     ├── def previsao_temp(lat, lon, cidade)
│     │     ↪ Requisição para OpenMeteo (temperatura e vento por hora)
│     │     ↪ Cria DataFrame com mínimas e máximas por data
│     │
│     └── def chuva_total(lat, lon, cidade)
│           ↪ Requisição para OpenMeteo (chuva diária)
│           ↪ Cria DataFrame com soma diária da chuva
│
├── 📄 main.py  ← Onde o código roda
│     ├── Carrega capitais do arquivo JSON
│     ├── Loop 1: busca coordenadas (e região) de cada cidade
│     ├── Loop 2: previsões de temperatura para cada cidade
│     ├── Loop 3: previsões de chuva para cada cidade
│     └── Junta tudo em df_completo e imprime resultado final
│
└── 📄 capitais.json  ← Lista com as 27 capitais brasileiras
