# 🚧 Impedimentos e Aprendizados

Durante a configuração e execução do projeto, o ponto mais desafiador foi ajustar o arquivo **`docker-compose.yaml`**, responsável por definir toda a infraestrutura do **Airflow** — incluindo os serviços de **Webserver**, **Scheduler**, **Worker**, **Triggerer**, **Redis** e **PostgreSQL**.

Esse arquivo atua como o roteiro de inicialização e integração de todos os containers.  
Pequenas inconsistências na configuração (como volumes, variáveis de ambiente ou dependências entre serviços) podem impedir o funcionamento correto do pipeline.

---

## 🧩 Problema principal — DAG presa em **`queued`**

Um dos maiores entraves foi entender por que a DAG permanecia no status **`queued`**, mesmo após acionar manualmente o comando de trigger:

```bash
docker exec -it airflow-airflow-scheduler-1 bash -lc \
  "airflow dags trigger meteo_historico_nivel2 
```

Inicialmente, parecia um problema no **`worker`**, mas após investigar os logs e processos ativos, identifiquei que o **`scheduler`** estava travado e não processava as DAGs corretamente.
A solução foi simples, mas só clara depois de entender o papel de cada componente dentro da arquitetura:

```bash
docker restart airflow-airflow-scheduler-1
```

Após o restart do scheduler, as DAGs passaram a ser executadas normalmente.
Esse aprendizado reforçou a importância de **entender o funcionamento interno do Airflow e do Docker Compose**, não apenas executar comandos isolados.

## 💡 Outros aprendizados relevantes

- Diferença entre **imagem** e **container** — entender que a imagem é o modelo e o container é a instância viva em execução;
- Correto mapeamento de **volumes** (./dags, ./logs, ./plugins) para persistência dos dados e códigos;
- O **scheduler** é o coração do Airflow — é ele quem detecta, agenda e envia as tarefas para execução;
- Uso dos comandos CLI (docker exec, docker logs, airflow dags list-runs, etc.) como parte da rotina de **observabilidade** e **debugging**.


---

## 🧱 1️⃣ O que é um container

Um **container** é uma **“caixa isolada” que roda um serviço** — como se fosse um mini computador dentro do seu sistema, com:

- seu próprio sistema operacional (Linux leve),
- suas bibliotecas e dependências,
- e um processo principal (por exemplo, o **scheduler** do Airflow, ou o PostgreSQL).
- Ele não é uma pasta, e sim um ambiente em execução — algo vivo, criado a partir de uma imagem.

Pensa assim:

**imagem** → modelo congelado (como um bolo antes de assar)
**container** → o bolo pronto, rodando no forno 🍰🔥


## ⚙️ 2️⃣ O papel do docker-compose.yaml

O arquivo docker-compose.yaml (ou .yml) é um roteiro que define quais containers serão criados e como eles se conectam.

Exemplo simplificado (parte do seu):

```bash
services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow

  airflow-webserver:
    image: apache/airflow:2.10.4
    ports:
      - "8080:8080"
    depends_on:
      - postgres
    volumes:
      - ./dags:/opt/airflow/dags
```

💬 Isso quer dizer:

- Crie um container chamado postgres usando a imagem postgres:13
- Crie outro container airflow-webserver
- Monte (espelhe) a pasta local ./dags dentro do container, em /opt/airflow/dags


É o arquivo YAML (docker-compose.yml) que declara os serviços (webserver, scheduler, worker, postgres, redis…), as portas, volumes, variáveis de ambiente, etc. Ele é o “mapa” de como os containers (instâncias de imagens Docker) sobem e conversam entre si.

**Imagem** = molde (a “foto” imutável com sistema + dependências).

**Container** = a instância em execução dessa imagem.

**Compose (YAML)** = orquestra o conjunto (quem sobe, portas, volumes…).

---

## 🧭 3️⃣ Onde entra a pasta ~/airflow

A pasta ~/airflow é sua pasta local, no seu computador (host).
Mas no docker-compose.yaml, você manda o Docker “espelhar” partes dela dentro dos containers, via o comando volumes:.

Por exemplo:

```bash
./dags:/opt/airflow/dags
```

significa:

Tudo que está na pasta local ```~/airflow/dags```
aparece dentro do container no caminho ```/opt/airflow/dags```

Ou seja:

- editar o código Python no seu computador → reflete dentro do container automaticamente.
- mas o container não é a pasta — ele usa a pasta como parte do seu “disco virtual”.

## 🔩 4️⃣ Cada container tem um papel no seu stack

No seu projeto Airflow:

| Container                    | Função                 | Porta |
|-------------------------------|------------------------|-------|
| airflow-airflow-webserver-1   | Interface Web          | 8080  |
| airflow-airflow-scheduler-1   | Agenda e dispara DAGs  | —     |
| airflow-airflow-worker-1      | Executa tasks          | —     |
| airflow-postgres-1            | Banco de dados interno | 5432  |
| airflow-redis-1               | Fila de mensagens      | —     |
| airflow-flower-1              | Monitor Celery         | 5555  |


Esses containers se comunicam entre si (como se fossem máquinas conectadas em rede local).
O Docker Compose gerencia todos eles em conjunto — o “mini cluster” do Airflow.

## 🧭 Resumo rápido

| Termo | Significado |
|-------|--------------|
| **Imagem** | Modelo congelado (ex: apache/airflow:2.10.4) |
| **Container** | Instância rodando da imagem |
| **docker-compose.yaml** | Roteiro que define quais containers e como se conectam |
| **Volume** | Espelho entre sua pasta local e o container |
| **Host** | Seu computador (onde o Docker está rodando) |
