# Airflow com Docker Compose — Guia de Entendimento Rápido

> **Objetivo**: explicar de forma prática como funciona o `docker-compose.yml` do seu ambiente Airflow (CeleryExecutor + Redis + Postgres), para você documentar e não esquecer no futuro.

---

## 1) Visão geral

Este `docker-compose.yml` sobe um **cluster local do Airflow** com:

- **PostgreSQL**: banco do Airflow (metadados e resultados do Celery)
- **Redis**: broker de mensagens do Celery
- **Airflow Webserver**: UI em `http://localhost:8080`
- **Airflow Scheduler**: agenda e orquestra tasks
- **Airflow Worker (Celery)**: executa tasks
- **Airflow Triggerer**: dispara tasks deferrable
- **Flower**: monitor dos workers Celery em `http://localhost:5555`
- **airflow-init**: job de inicialização (cria DB e usuário admin)

> **Importante**: esta stack é para **desenvolvimento local**. Não use em produção.

---

## 2) Diagrama rápido (conexões)

```
          +----------------+
          |   Webserver    | 8080
          +--------+-------+
                   |
                   | REST / Metadados
                   v
+----------+   +---+---------------------+     +------------------+
|  Flower  |   |      Scheduler          | --> |  Worker (Celery) |
| 5555     |   +-----------+-------------+     +---------+--------+
+----------+               |                         ^    |
                           | Celery (Broker)         |    | Result Backend
                           v                         |    v
                        +-------+                    | +--------+
                        | Redis | <------------------+ |Postgres|
                        | 6379  |                        | 5433  |
                        +-------+                        +--------+
```

- **Broker (Redis)**: envia mensagens das tasks para os **Workers**.
- **Result Backend (Postgres)**: guarda estados/resultados de execução.
- **Webserver** fala com **Scheduler**/**DB** para exibir status.

---

## 3) Serviços (o que cada um faz)

| Serviço              | Função                                  | Porta Host→Container | Saúde (healthcheck) |
|----------------------|------------------------------------------|----------------------|---------------------|
| `postgres`           | Banco do Airflow                         | `5433 → 5432`        | `pg_isready`        |
| `redis`              | Broker Celery                            | `6379 → 6379`        | `redis-cli ping`    |
| `airflow-init`       | Inicializa DB e cria usuário admin       | —                    | —                   |
| `airflow-webserver`  | UI Airflow                               | `8080 → 8080`        | `/health`           |
| `airflow-scheduler`  | Agenda/dispara DAGs                      | —                    | `airflow jobs check`|
| `airflow-worker`     | Executa tasks Celery                     | —                    | `celery ... ping`   |
| `airflow-triggerer`  | Tarefas deferrable                       | —                    | `airflow jobs check`|
| `flower`             | Monitor Celery                           | `5555 → 5555`        | `curl /`            |

---

## 4) Bloco comum (`x-airflow-common`)

No Compose, o **anchor** `&airflow-common` centraliza configurações compartilhadas pelos serviços Airflow:

```yaml
x-airflow-common: &airflow-common
  image: apache/airflow:2.10.4
  user: "50000:0"  # UID do usuário airflow + GID=0
  environment: &airflow-common-env
    AIRFLOW__CORE__EXECUTOR: CeleryExecutor
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: "true"
    AIRFLOW__CORE__LOAD_EXAMPLES: "false"
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
    AIRFLOW__CELERY__RESULT_BACKEND: db+postgresql://airflow:airflow@postgres/airflow
    AIRFLOW__CELERY__BROKER_URL: redis://:@redis:6379/0
  volumes:
    - ./dags:/opt/airflow/dags
    - ./logs:/opt/airflow/logs
    - ./plugins:/opt/airflow/plugins
    - ./meteo_project:/opt/airflow/meteo_project
```

**Por que isso importa?**
- Evita repetição de configs entre `webserver`, `scheduler`, `worker`, `triggerer`, `flower`.
- Garante que todos vejam as mesmas **DAGs**, **plugins** e **logs** via volumes mapeados.

### Variáveis-chave
- `AIRFLOW__CORE__EXECUTOR=CeleryExecutor`: habilita o modo distribuído com Celery.
- `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN`: string de conexão do banco **dentro da rede Docker** (host `postgres`).
- `AIRFLOW__CELERY__BROKER_URL`: URL do Redis (broker).
- `AIRFLOW__CELERY__RESULT_BACKEND`: onde salvar resultados (Postgres).
- `AIRFLOW__WEBSERVER__SECRET_KEY` e `AIRFLOW__CORE__FERNET_KEY`: chaves de segurança (dev).

> **Dica**: em projetos reais, mova segredos para um `.env` e **não comite**.

---

## 5) Volumes (mapeamentos locais → container)

| Pasta local              | Pasta no container             | Para quê?                 |
|--------------------------|--------------------------------|---------------------------|
| `./dags`                 | `/opt/airflow/dags`            | DAGs                      |
| `./logs`                 | `/opt/airflow/logs`            | Logs de execução          |
| `./plugins`              | `/opt/airflow/plugins`         | Plugins                    |
| `./meteo_project`        | `/opt/airflow/meteo_project`   | Código/projeto auxiliar   |
| `postgres-db-volume`     | `/var/lib/postgresql/data`     | Dados do Postgres         |

> **Observação (Windows/WSL)**: manter os arquivos **no WSL** (ex: `~/airflow`) evita problemas de performance/permissão ao montar pastas do Windows.

---

## 6) Portas expostas

- **UI Airflow**: `http://localhost:8080`
- **Flower**: `http://localhost:5555`
- **Postgres (host)**: `localhost:5433` (mapeado para `5432` no container)
- **Redis**: `6379` (exposto, mas geralmente não precisa acessar direto)

---

## 7) Fluxo de inicialização (primeira vez)

1. **Subir serviços de infra** (Postgres/Redis sobem automaticamente):
   ```bash
   docker compose up -d postgres redis
   ```
2. **Rodar init** (cria DB e usuário admin `airflow/airflow`):
   ```bash
   docker compose run --rm airflow-init
   ```
3. **Subir Airflow**:
   ```bash
   docker compose up -d airflow-webserver airflow-scheduler airflow-worker airflow-triggerer flower
   ```
4. Acessar **UI**: `http://localhost:8080` (login: `airflow` / `airflow`).

> **Depois**: Use apenas `docker compose up -d` para subir tudo de uma vez.

---

## 8) Comandos úteis do dia a dia

```bash
# Subir tudo em segundo plano
docker compose up -d

# Ver logs (ex.: scheduler)
docker compose logs -f airflow-scheduler

# Reiniciar um serviço
docker compose restart airflow-worker

# Executar um comando dentro do scheduler
docker compose exec airflow-scheduler bash -lc "airflow dags list"

# Reset (cuidado: apaga metadados!)
docker compose down -v  # remove containers e volumes

# Copiar DAGs para a área de transferência (WSL → Windows)
cat dags/minha_dag.py | clip.exe
```

---

## 9) Troubleshooting (erros comuns)

### 9.1 Scheduler não agenda / DAGs pausadas
- Verifique se `AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION` = `true` → ative as DAGs na UI.

### 9.2 ImportError ao carregar DAGs
- Veja erros com:
  ```bash
  docker compose exec airflow-scheduler bash -lc "airflow dags list-import-errors -o table"
  ```
- Corrija versões de libs, caminhos, e **não use argumentos inexistentes** no `DAG(...)` (ex.: `timezone` não é argumento válido — use `default_args` ou `pendulum.timezone` para `start_date`).

### 9.3 Worker “offline” no Flower
- Cheque broker/resultado:
  - `AIRFLOW__CELERY__BROKER_URL` (Redis),
  - `AIRFLOW__CELERY__RESULT_BACKEND` (Postgres)
- Verifique o healthcheck do worker (o `celery ... inspect ping`)

### 9.4 Permissões de arquivos/UID
- A imagem usa `user: "50000:0"`. Garanta que o host (WSL) permita escrever em `./logs` e `./dags`.
- Se necessário, ajuste permissões:
  ```bash
  sudo chown -R $USER:$USER dags logs plugins meteo_project
  ```

### 9.5 Porta 8080 ocupada
- Altere o mapeamento:
  ```yaml
  airflow-webserver:
    ports:
      - "8081:8080"  # host:container
  ```

---

## 10) Segurança (modo dev vs. prod)

- **Segredos** (`FERNET_KEY`, `SECRET_KEY`, senhas): use `.env` e **não comite**.
- Limite portas expostas (em dev tudo bem; em prod, prefira rede privada e proxy).
- Use imagens versionadas (ex.: `apache/airflow:2.10.4`) e **fixe** versões de libs.

**Exemplo `.env` simples:**
```dotenv
AIRFLOW_IMAGE=apache/airflow:2.10.4
AIRFLOW_UID=50000
AIRFLOW_GID=0
AIRFLOW__WEBSERVER__SECRET_KEY=troque-isto
AIRFLOW__CORE__FERNET_KEY=troque-isto
POSTGRES_PASSWORD=troque-isto
```
E no compose, referenciar com `${VAR}`.

---

## 11) Customizações frequentes

- **Mudar executor** para LocalExecutor (sem Celery):
  ```yaml
  AIRFLOW__CORE__EXECUTOR: LocalExecutor
  ```
  > Remova `redis`, `worker` e `flower` do compose.

- **Adicionar conexões/variables** via CLI:
  ```bash
  docker compose exec airflow-webserver bash -lc \
    "airflow connections add 'pg_meteo' \
      --conn-uri 'postgresql+psycopg2://airflow:airflow@postgres:5432/airflow'"
  
  docker compose exec airflow-webserver bash -lc \
    "airflow variables set FUSO 'America/Sao_Paulo'"
  ```

- **Libraries extras** (requirements): crie um `requirements.txt` e monte como volume ou construa uma imagem customizada.

---

## 12) Checklist pós-subida

- [ ] `http://localhost:8080` abre? Login OK?
- [ ] `http://localhost:5555` mostra o worker **online**?
- [ ] `airflow dags list` mostra suas DAGs?
- [ ] Logs aparecem em `./logs`?
- [ ] DAG exemplo executa com sucesso?

---

## 13) Referência do seu Compose (trechos-chave)

```yaml
version: "3.8"

services:
  postgres:
    image: postgres:13
    ports:
      - "5433:5432"
    volumes:
      - postgres-db-volume:/var/lib/postgresql/data

  redis:
    image: redis:latest
    ports:
      - "6379:6379"

  airflow-webserver:
    <<: *airflow-common
    command: webserver
    ports:
      - "8080:8080"

  airflow-scheduler:
    <<: *airflow-common
    command: scheduler

  airflow-worker:
    <<: *airflow-common
    command: celery worker

  flower:
    <<: *airflow-common
    command: celery flower
    ports:
      - "5555:5555"

volumes:
  postgres-db-volume:
```

> **Nota**: no seu arquivo completo há também `airflow-triggerer` e `airflow-init`, além dos **healthchecks** detalhados — mantê-los é recomendável.

---

## 14) Copiar/colar rápido (WSL → Windows)

- Visualizar no terminal e selecionar:
  ```bash
  cat docker-compose.yml
  ```
- Copiar direto pro clipboard do Windows:
  ```bash
  cat docker-compose.yml | clip.exe
  ```
- Abrir no VS Code:
  ```bash
  code docker-compose.yml
  ```

---

### Fim
Este guia serve como **material-base** para colocar no seu README (ou Wiki) e para consulta futura. Sempre que evoluir o Compose, atualize as seções 3–5 (serviços, volumes, portas) e o **Checklist**.

