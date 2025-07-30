from __future__ import annotations
import shutil, json
from datetime import datetime, timedelta
from pathlib import Path
from airflow.models import DAG, Variable
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup

# Variáveis de ambiente
Variable.set("sample_guestcheck_json_path", "/opt/airflow/src/data/ERP.json") #

Variable.set("data_lake_root", "/opt/airflow/data_lake")

Variable.set("store_id", "99")

# parâmetros globais
LAKE_ROOT = Path(Variable.get("data_lake_root", "/opt/airflow/data_lake"))
STORE     = Variable.get("store_id", "99")
SAMPLES   = {
    "getGuestChecks":      "/opt/airflow/src/data/ERP.json",
    "getCheckDetails":     "/opt/airflow/src/data/mock_check_details.json",
    "getFiscalInvoice":    "/opt/airflow/src/data/mock_fiscal_invoice.json",
    "getTransactions":     "/opt/airflow/src/data/mock_transactions.json",
    "getCashManagementDetails": "/opt/airflow/src/data/mock_cash_management.json",
}

# função para construir o caminho do data lake
def build_path(endpoint: str, ds: str) -> Path:
    d = datetime.strptime(ds, "%Y-%m-%d")
    return (LAKE_ROOT / endpoint /
            f"ano={d.year}" / f"mes={d.month:02d}" / f"dia={d.day:02d}" /
            f"loja={STORE}")

# função para buscar os dados de um endpoint e salvar no data lake
def fetch(endpoint: str, **context):
    ds = context["ds"]
    target_dir = build_path(endpoint, ds)
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SAMPLES[endpoint], target_dir / f"{endpoint}.json")
    return str(target_dir / f"{endpoint}.json")   # devolve caminho p/ XCom

# configuração do DAG
default_args = {"retries": 1, "retry_delay": timedelta(minutes=3)}

# criação do DAG
with DAG(
    dag_id="ingest_endpoints",
    start_date=datetime(2025, 7, 29),
    schedule="0 3 * * *",
    catchup=False,
    default_args=default_args,
    tags=["etl", "lake"],
) as dag:

    # cria dinamicamente uma tarefa fetch_… para cada endpoint
    fetch_tasks = {}
    for ep in SAMPLES.keys():
        fetch_tasks[ep] = PythonOperator(
            task_id=f"fetch_{ep}",
            python_callable=fetch,
            op_kwargs={"endpoint": ep}
        )
