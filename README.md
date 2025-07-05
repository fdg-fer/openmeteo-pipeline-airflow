# 🌤️ API de Previsão do Clima - Capitais Brasileiras

Este projeto realiza a coleta de dados meteorológicos (como temperatura, umidade e condição do tempo) para **capitais brasileiras**, utilizando uma API pública de clima.

A proposta é extrair dados estruturados de forma automática, organizá-los em JSON e abrir caminho para análises posteriores, como tendências regionais, previsões semanais ou visualizações.

---

## 🚧 Estrutura do Projeto

```text
projeto_clima/
├── clima.py            # funções reutilizáveis (módulo principal)
├── main.py             # script principal que roda a coleta de dados
├── gerar_capitais.py   # cria/atualiza o arquivo capitais.json
└── capitais.json       # contém os nomes e dados das capitais brasileiras
