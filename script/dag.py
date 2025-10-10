from airflow import DAG
from airflow.decorators import task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from sqlalchemy import MetaData, Table, Column, String, Date, Float
from sqlalchemy.dialects.postgresql import insert as pg_insert
from airflow.operators.python import get_current_context

import pendulum
from datetime import datetime, date, timedelta
import time
import requests
from pathlib import Path
import pandas as pd
import json
import os

# ---------------------------------------------
# Configurações simples (ajuste conforme seu projeto)
# ---------------------------------------------

ARQ_LOCALIZACOES = Path("/opt/airflow/meteo_project/input/localizacoes.json")
DATA_DIR = Path("/opt/airflow/data/meteo")
FUSO = "America/Sao_Paulo"
N_DIAS_REPROCESSO = 3
PG_CONN_ID = "pg_meteo"
TBL_NAME = "historico_meteo"

# ---------------------------------------------
# Helpers de domínio
# ---------------------------------------------

def ler_localizacoes(caminho=ARQ_LOCALIZACOES):
    # Lê o JSON de cidades e coordenadas
    with open(caminho, 'r') as file:
        data = json.load(file)
    return data

def datas_de_janela(n_dias: int):
    # Define a janela de datas (ontem voltando n_dias - 1)
    end_day = date.today() - timedelta(days=1)
    start_day = end_day - timedelta(days=n_dias - 1)
    return start_day.isoformat(), end_day.isoformat()

def historico(lat, lon, start_s, end_s, daily_vars: list[str], cidade: str):
    # Consulta a API Open-Meteo Archive
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ",".join(daily_vars),
        "start_date": start_s,
        "end_date": end_s,
        "timezone": FUSO
    }
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if "daily" not in data or "time" not in data["daily"]:
            return pd.DataFrame(columns=["cidade", "date"] + daily_vars)

        dt = pd.to_datetime(data["daily"]["time"], errors="coerce")
        dates = dt.date if isinstance(dt, pd.DatetimeIndex) else pd.Series(dt).dt.date

        df = pd.DataFrame({"cidade": cidade, "date": dates})

        for var in daily_vars:
            serie = pd.Series(data["daily"].get(var, []))
            df[var] = pd.to_numeric(serie, errors="coerce")

        return df

    except Exception as e:
        print(f"[WARN] {cidade}: erro ao consultar historico -> {e}")
        return pd.DataFrame(columns=["cidade", "date"] + daily_vars)

def garantir_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)
    return p

# ---------------------------------------------
# DAG
# ---------------------------------------------

SAO = pendulum.timezone("America/Sao_Paulo")

with DAG(
    dag_id="meteo_historico_nivel2",
    start_date=pendulum.datetime(2025, 10, 8, 0, 0, tz=SAO),
    schedule="0 10 * * *",
    catchup=False,
    tags=["meteo", "historico", "nivel2"],
) as dag:

    @task
    def definir_intervalo(n_dias: int = N_DIAS_REPROCESSO):
        ctx = get_current_context()
        conf = (ctx.get("dag_run") and ctx["dag_run"].conf) or {}

        if "start" in conf and "end" in conf:
            start_s = str(conf["start"])
            end_s   = str(conf["end"])
        else:
            # comportamento padrão: últimas N_DIAS_REPROCESSO (3) até ontem
            end_day = date.today() - timedelta(days=1)
            start_day = end_day - timedelta(days=n_dias - 1)
            start_s, end_s = start_day.isoformat(), end_day.isoformat()

        folder = garantir_dir(DATA_DIR / f"{start_s}_a_{end_s}")
        print(f"Intervalo: {start_s} -> {end_s}")
        return {"start": start_s, "end": end_s, "folder": str(folder)}

    @task(retries=2, retry_delay=timedelta(minutes=2))
    def coletar_temperatura(intervalo: dict) -> str:
        start_s, end_s = intervalo["start"], intervalo["end"]
        folder = Path(intervalo["folder"])
        temp_parquet = folder / "temperatura.parquet"

        locs = ler_localizacoes()
        temp_vars = ["temperature_2m_min", "temperature_2m_max"]
        lista_temp = []

        for loc in locs:
            df_t = historico(
                lat=float(loc["latitude"]),
                lon=float(loc["longitude"]),
                start_s=start_s,
                end_s=end_s,
                daily_vars=temp_vars,
                cidade=loc["cidade"]
            )
            if not df_t.empty:
                df_t = df_t.rename(columns={
                    "temperature_2m_min": "temp_min",
                    "temperature_2m_max": "temp_max"
                })
                lista_temp.append(df_t)
            time.sleep(0.3)

        if lista_temp:
            df_temp_total = pd.concat(lista_temp, ignore_index=True)
        else:
            df_temp_total = pd.DataFrame(columns=["cidade", "date", "temp_min", "temp_max"])

        garantir_dir(folder)
        df_temp_total.to_parquet(temp_parquet, index=False)
        print(f"Temperatura gravada: {temp_parquet} | linhas: {len(df_temp_total)}")
        return str(temp_parquet)

    @task(retries=2, retry_delay=timedelta(minutes=2))
    def coletar_chuva(intervalo: dict) -> str:
        start_s, end_s = intervalo["start"], intervalo["end"]
        folder = Path(intervalo["folder"])
        chuva_parquet = folder / "chuva.parquet"

        locs = ler_localizacoes()
        chuva_vars = ["precipitation_sum"]
        lista_chuva = []

        for loc in locs:
            df_c = historico(
                lat=float(loc["latitude"]),
                lon=float(loc["longitude"]),
                start_s=start_s,
                end_s=end_s,
                daily_vars=chuva_vars,
                cidade=loc["cidade"]
            )
            if not df_c.empty:
                df_c = df_c.rename(columns={"precipitation_sum": "chuva_total"})
                lista_chuva.append(df_c)
            time.sleep(0.3)

        if lista_chuva:
            df_chuva_total = pd.concat(lista_chuva, ignore_index=True)
        else:
            df_chuva_total = pd.DataFrame(columns=["cidade", "date", "chuva_total"])

        garantir_dir(folder)
        df_chuva_total.to_parquet(chuva_parquet, index=False)
        print(f"Chuva gravada: {chuva_parquet} | linhas: {len(df_chuva_total)}")
        return str(chuva_parquet)

    @task
    def mergear_parquets(temp_path: str, chuva_path: str) -> str:
        temp_path = Path(temp_path)
        chuva_path = Path(chuva_path)
        merged_path = temp_path.parent / "merged.parquet"

        df_t = pd.read_parquet(temp_path) if temp_path.exists() else \
               pd.DataFrame(columns=["cidade", "date", "temp_min", "temp_max"])
        df_c = pd.read_parquet(chuva_path) if chuva_path.exists() else \
               pd.DataFrame(columns=["cidade", "date", "chuva_total"])

        if not df_t.empty:
            df_t["date"] = pd.to_datetime(df_t["date"], errors="coerce").dt.date
        if not df_c.empty:
            df_c["date"] = pd.to_datetime(df_c["date"], errors="coerce").dt.date

        df_historico = (
            pd.merge(df_t, df_c, on=["cidade", "date"], how="outer")
              .sort_values(["cidade", "date"])
        )

        df_historico.to_parquet(merged_path, index=False)
        print(f"Merged gravado: {merged_path} | linhas: {len(df_historico)}")
        print("Amostra:\n", df_historico.head().to_string(index=False))
        return str(merged_path)

    @task
    def validar_schema(merged_path: str) -> str:
        path = Path(merged_path)
        df = pd.read_parquet(path)

        obrig = {"cidade", "date", "temp_min", "temp_max", "chuva_total"}
        faltam = obrig - set(df.columns)
        if faltam:
            raise ValueError(f"Colunas faltando: {faltam}")

        if df["cidade"].isna().any():
            raise ValueError("Cidade contém nulos.")

        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
        if df["date"].isna().any():
            raise ValueError("Date contém valores inválidos.")

        print("Schema OK. Linhas:", len(df))
        return str(path)

    @task
    def upsert_postgres(merged_path: str, conn_id: str = PG_CONN_ID, table_name: str = TBL_NAME) -> int:
        df = pd.read_parquet(merged_path)
        if df.empty:
            print("Nada para gravar (df vazio).")
            return 0

        for col in ["temp_min", "temp_max", "chuva_total"]:
            if col not in df.columns:
                df[col] = pd.NA

        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date

        hook = PostgresHook(postgres_conn_id=conn_id)
        engine = hook.get_sqlalchemy_engine()
        
        with engine.begin() as conn:
            conn.execute("CREATE SCHEMA IF NOT EXISTS meteo;")             

        metadata = MetaData()
        tbl = Table(
            table_name, metadata,
            Column("cidade", String, primary_key=True),
            Column("date", Date, primary_key=True),
            Column("temp_min", Float),
            Column("temp_max", Float),
            Column("chuva_total", Float),
            schema="meteo"
        )
        metadata.create_all(bind=engine)

        rows = df[["cidade", "date", "temp_min", "temp_max", "chuva_total"]].to_dict(orient="records")

        inserted = 0
        chunk = 1000
        with engine.begin() as conn:
            for i in range(0, len(rows), chunk):
                batch = rows[i:i + chunk]
                stmt = pg_insert(tbl).values(batch)
                upsert_stmt = stmt.on_conflict_do_update(
                    index_elements=["cidade", "date"],
                    set_={
                        "temp_min": stmt.excluded.temp_min,
                        "temp_max": stmt.excluded.temp_max,
                        "chuva_total": stmt.excluded.chuva_total,
                    },
                )
                result = conn.execute(upsert_stmt)
                inserted += result.rowcount or 0

        print(f"UPSERT concluído. Linhas afetadas: {inserted}")
        return inserted

    # ---------------------
    # Encadeamento das tasks
    # ---------------------
    intervalo = definir_intervalo()
    temp_path = coletar_temperatura(intervalo)
    chuva_path = coletar_chuva(intervalo)
    merged_path = mergear_parquets(temp_path, chuva_path)
    checked_path = validar_schema(merged_path)
    upsert_postgres(checked_path)