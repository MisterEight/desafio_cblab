from __future__ import annotations

"""Airflow DAG: ingere guest‑checks do ERP.

Pipeline diário (T+1) simplificado:
    Faz download *mock* do arquivo JSON
       (copia o sample para uma pasta particionada no "lake").
    Executa o parser minimalista para carregar em Postgres.

Pré‑requisitos:
    monte ./data_lake em /opt/airflow/data_lake (docker‑compose)
    monte ./src       em /opt/airflow/src       (docker‑compose)
    variáveis de conexão PG via env (PGHOST, PGPORT, etc.)
"""

import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator

# Variáveis de ambiente
Variable.set("sample_guestcheck_json_path", "/opt/airflow/src/data/ERP.json")

Variable.set("data_lake_root", "/opt/airflow/data_lake")

Variable.set("store_id", "99")

# Caminho do JSON de exemplo
SAMPLE_JSON = Variable.get("sample_guestcheck_json_path", default_var="/opt/airflow/src/data/ERP.json")
# Caminho do data lake e ID da loja
LAKE_ROOT = Path(Variable.get("data_lake_root", default_var="/opt/airflow/data_lake"))
# ID da loja, usado para particionar os dados
STORE_ID = Variable.get("store_id", default_var="99")

# Funções auxiliares para manipulação de caminhos e arquivos
def _build_lake_path(exec_ds: str) -> Path:
    dt = datetime.strptime(exec_ds, "%Y-%m-%d")
    return LAKE_ROOT / "getGuestChecks" / f"ano={dt.year}" / f"mes={dt.month:02d}" / f"dia={dt.day:02d}" / f"loja={STORE_ID}"

# Funções de ingestão e processamento
def fetch_guestchecks(**context: Any) -> str:
    ds = context["ds"] # data de execução do DAG (formato YYYY-MM-DD)
    target_dir = _build_lake_path(ds)
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / "guestChecks.json"
    shutil.copyfile(SAMPLE_JSON, target_file)
    return str(target_file)

# Função para carregar os dados no Postgres
def load_to_postgres(**context: Any) -> None:
    import sys
    # garantir que /opt/airflow/src está no PYTHONPATH
    SRC_PATH = Path("/opt/airflow/src")
    if str(SRC_PATH) not in sys.path:
        sys.path.append(str(SRC_PATH))
    from parse_guestcheck import main as parse_main

    json_path = context["ti"].xcom_pull(task_ids="fetch_json")
    parse_main(json_path)

# Configuração do DAG
default_args = {
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# Criação do DAG
dag = DAG(
    dag_id="ingest_guest_checks",
    default_args=default_args,
    start_date=datetime(2025, 7, 28),
    schedule="0 3 * * *",
    catchup=False,
    tags=["etl", "guestcheck"],
)

# Definição das tasks
with dag:
    fetch_json = PythonOperator(
        task_id="fetch_json",
        python_callable=fetch_guestchecks,
    )

    load_postgres = PythonOperator(
        task_id="load_postgres",
        python_callable=load_to_postgres,
    )

    fetch_json >> load_postgres
