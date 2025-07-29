import os #Acessar arquivos do sistema
import json #Coletar e acessar dos dados do JSOON
import argparse #Podemos passar o JSON not terminal para o script
import psycopg2 #Driver padrão de conexão ao Postgres
from pathlib import Path #Manipular caminhos para o arquivo de JSON
from dotenv import load_dotenv #Carregar o as informações do .env
from contextlib import contextmanager #Ajuda a manusear a conexão com o banco, sem a necessida de try/catchs
from decimal import Decimal #Oferece precisão arbitrária para trabalhar com decimais, como o subtotal, etc
from psycopg2.extras import execute_values # Ajuda em inserções em lote

@contextmanager
#Função para fazer a conexão com o banco.
def get_conn():
    load_dotenv()
    conn = psycopg2.connect(
        host=os.getenv("PGHOST"),
        port=int(os.getenv("PGPORT")),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
        dbname=os.getenv("PGDATABASE"),
    )
    try:
        yield conn
    finally:
        conn.close()

#Função para fazer o load dos dados de guest_check no banco.
def insert_guest_check(cur, gc: dict):
    """Insert one guest_check row and return primary key (guest_check_id)."""
    sql = """
        INSERT INTO guest_check (
            guest_check_id, store_id, employee_number, table_name, table_number,
            check_number, revenue_center_number, order_type_number,
            service_rounds, check_printeds, guest_count,
            sub_total, discount_total, check_total, non_taxable_sales_total,
            opened_utc, closed_utc, last_updated_utc, last_transaction_utc,
            closed_flag
        ) VALUES (
            %(guestCheckId)s, %(store_id)s, %(empNum)s, %(tblName)s, %(tblNum)s,
            %(chkNum)s, %(rvcNum)s, %(otNum)s,
            %(numSrvcRd)s, %(numChkPrntd)s, %(gstCnt)s,
            %(subTtl)s, %(dscTtl)s, %(chkTtl)s, %(nonTxblSlsTtl)s,
            %(opnLcl)s, %(clsdLcl)s, %(lastUpdatedLcl)s, %(lastTransLcl)s,
            %(clsdFlag)s
        ) ON CONFLICT (guest_check_id) DO NOTHING;
    """
    params = gc.copy()
    params["store_id"] = gc.get("locRef", "00")  # fallback
    cur.execute(sql, params)
    return gc["guestCheckId"]

#Função para fazer o load dos dados de detailLines no banco.
def insert_line_items(cur, guest_check_id: int, detail_lines: list):
    records = []
    for dl in detail_lines:
        records.append(
            (
                dl["guestCheckLineItemId"],
                guest_check_id,
                dl.get("chkEmpId"),
                dl.get("lineNum"),
                dl.get("rvcNum"),
                dl.get("dtlOtNum"),
                dl.get("wsNum"),
                dl.get("detailLcl"),
                Decimal(str(dl.get("dspTtl", 0))),
                Decimal(str(dl.get("dspQty", 0))),
                Decimal(str(dl.get("aggTtl", 0))),
                Decimal(str(dl.get("aggQty", 0))),
            )
        )

    sql = """
        INSERT INTO line_item (
            line_item_id, guest_check_id, employee_id, line_number,
            revenue_center_number, order_type_number, workstation_number,
            detail_utc, display_total, display_quantity,
            aggregation_total, aggregation_quantity
        ) VALUES %s ON CONFLICT (line_item_id) DO NOTHING;
    """
    execute_values(cur, sql, records)


#Função para carrega o JSON e chamar as funções que irão dar load das informações no banco.
def main(path: str):
    with open(path, "r", encoding="utf-8") as fo:
        payload = json.load(fo)

    store_id = payload.get("locRef", "00")
    guest_checks = payload.get("guestChecks", [])

    with get_conn() as conn:
        with conn.cursor() as cur:
            for gc in guest_checks:
                gc["locRef"] = store_id
                gid = insert_guest_check(cur, gc)
                insert_line_items(cur, gid, gc.get("detailLines", []))
            conn.commit()
    print(f"Loaded {len(guest_checks)} guest_check(s) from {path} ✔")

#Carrega o JSON que for passado pelo terminal
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse ERP JSON into Postgres")
    parser.add_argument("json", help="Path to ERP.json")
    args = parser.parse_args()
    main(args.json)
