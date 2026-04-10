"""Ingestão meteorológica para Databricks (sem Airflow).

Este script replica a lógica principal da DAG de ingestão, mas em formato
executável como Job/Notebook no Databricks:
1. Lê localizações (JSON)
2. Consulta Open-Meteo (temperatura e chuva)
3. Valida o schema
4. Faz upsert em tabela Delta

Exemplo de uso (Databricks Job task):
  python script/databricks_ingestao.py \
    --localizacoes /dbfs/FileStore/meteo/localizacoes.json \
    --start 2026-04-01 --end 2026-04-09 \
    --target-table meteo.historico_meteo
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

FUSO = "America/Sao_Paulo"
N_DIAS_REPROCESSO = 3


def ler_localizacoes(caminho: str) -> list[dict]:
    with open(caminho, "r", encoding="utf-8") as file:
        return json.load(file)


def datas_de_janela(n_dias: int) -> tuple[str, str]:
    end_day = date.today() - timedelta(days=1)
    start_day = end_day - timedelta(days=n_dias - 1)
    return start_day.isoformat(), end_day.isoformat()


def historico(lat: float, lon: float, start_s: str, end_s: str, daily_vars: list[str], cidade: str) -> pd.DataFrame:
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ",".join(daily_vars),
        "start_date": start_s,
        "end_date": end_s,
        "timezone": FUSO,
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
            df[var] = pd.to_numeric(pd.Series(data["daily"].get(var, [])), errors="coerce")
        return df

    except Exception as err:
        print(f"[WARN] {cidade}: erro ao consultar historico -> {err}")
        return pd.DataFrame(columns=["cidade", "date"] + daily_vars)


def coletar_dados(localizacoes_path: str, start_s: str, end_s: str) -> pd.DataFrame:
    locs = ler_localizacoes(localizacoes_path)

    temp_vars = ["temperature_2m_min", "temperature_2m_max"]
    chuva_vars = ["precipitation_sum"]

    lista_temp: list[pd.DataFrame] = []
    lista_chuva: list[pd.DataFrame] = []

    for loc in locs:
        cidade = loc["cidade"]
        lat = float(loc["latitude"])
        lon = float(loc["longitude"])

        df_t = historico(lat, lon, start_s, end_s, temp_vars, cidade).rename(
            columns={"temperature_2m_min": "temp_min", "temperature_2m_max": "temp_max"}
        )
        if not df_t.empty:
            lista_temp.append(df_t)

        df_c = historico(lat, lon, start_s, end_s, chuva_vars, cidade).rename(
            columns={"precipitation_sum": "chuva_total"}
        )
        if not df_c.empty:
            lista_chuva.append(df_c)

        time.sleep(0.3)

    df_temp = pd.concat(lista_temp, ignore_index=True) if lista_temp else pd.DataFrame(columns=["cidade", "date", "temp_min", "temp_max"])
    df_chuva = pd.concat(lista_chuva, ignore_index=True) if lista_chuva else pd.DataFrame(columns=["cidade", "date", "chuva_total"])

    if not df_temp.empty:
        df_temp["date"] = pd.to_datetime(df_temp["date"], errors="coerce").dt.date
    if not df_chuva.empty:
        df_chuva["date"] = pd.to_datetime(df_chuva["date"], errors="coerce").dt.date

    df_merged = pd.merge(df_temp, df_chuva, on=["cidade", "date"], how="outer").sort_values(["cidade", "date"])
    return df_merged


def validar_schema(df: pd.DataFrame) -> None:
    obrigatorias = {"cidade", "date", "temp_min", "temp_max", "chuva_total"}
    faltando = obrigatorias - set(df.columns)
    if faltando:
        raise ValueError(f"Colunas faltando: {faltando}")

    if df["cidade"].isna().any():
        raise ValueError("Cidade contém nulos")

    datas = pd.to_datetime(df["date"], errors="coerce")
    if datas.isna().any():
        raise ValueError("Date contém valores inválidos")


def upsert_delta(spark: SparkSession, df: pd.DataFrame, target_table: str) -> int:
    if df.empty:
        print("Nada para gravar (df vazio).")
        return 0

    sdf = spark.createDataFrame(df)
    sdf = (
        sdf.withColumn("date", F.to_date("date"))
        .withColumn("temp_min", F.col("temp_min").cast("double"))
        .withColumn("temp_max", F.col("temp_max").cast("double"))
        .withColumn("chuva_total", F.col("chuva_total").cast("double"))
    )

    spark.sql(
        f"""
        CREATE TABLE IF NOT EXISTS {target_table} (
          cidade STRING,
          date DATE,
          temp_min DOUBLE,
          temp_max DOUBLE,
          chuva_total DOUBLE
        ) USING DELTA
        """
    )

    sdf.createOrReplaceTempView("stg_meteo")
    spark.sql(
        f"""
        MERGE INTO {target_table} AS t
        USING stg_meteo AS s
        ON t.cidade = s.cidade AND t.date = s.date
        WHEN MATCHED THEN UPDATE SET
          t.temp_min = s.temp_min,
          t.temp_max = s.temp_max,
          t.chuva_total = s.chuva_total
        WHEN NOT MATCHED THEN INSERT *
        """
    )

    qtd = sdf.count()
    print(f"Upsert Delta concluído. Registros processados: {qtd}")
    return qtd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingestão Open-Meteo para Databricks")
    parser.add_argument("--localizacoes", default="script/localizacoes.json", help="Caminho do JSON de localizações")
    parser.add_argument("--start", default=None, help="Data inicial (YYYY-MM-DD)")
    parser.add_argument("--end", default=None, help="Data final (YYYY-MM-DD)")
    parser.add_argument("--n-dias", type=int, default=N_DIAS_REPROCESSO, help="Janela padrão quando start/end não forem passados")
    parser.add_argument("--target-table", default="meteo.historico_meteo", help="Tabela Delta de destino")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    start_s, end_s = (args.start, args.end) if args.start and args.end else datas_de_janela(args.n_dias)

    localizacoes = Path(args.localizacoes)
    if not localizacoes.exists():
        raise FileNotFoundError(f"Arquivo de localizações não encontrado: {localizacoes}")

    print(f"Iniciando ingestão para intervalo {start_s} -> {end_s}")
    print(f"Localizações: {localizacoes}")
    print(f"Tabela destino: {args.target_table}")

    df = coletar_dados(str(localizacoes), start_s, end_s)
    validar_schema(df)

    spark = SparkSession.builder.appName("meteo-databricks-ingestao").getOrCreate()
    upsert_delta(spark, df, args.target_table)


if __name__ == "__main__":
    main()
