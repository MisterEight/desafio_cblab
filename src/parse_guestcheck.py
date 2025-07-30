import os #Acessar arquivos do sistema
import json #Coletar e acessar dos dados do JSOON
import argparse #Podemos passar o JSON not terminal para o script
import psycopg2 #Driver padrão de conexão ao Postgres
from pathlib import Path #Manipular caminhos para o arquivo de JSON
from dotenv import load_dotenv #Carregar o as informações do .env
from contextlib import contextmanager #Ajuda a manusear a conexão com o banco, sem a necessida de try/catchs
from decimal import Decimal #Oferece precisão arbitrária para trabalhar com decimais, como o subtotal, etc
from psycopg2.extras import execute_values # Ajuda em inserções em lote

DISCOUNT_TYPES = {"DISCOUNT"}
PAYMENT_TYPES  = {"TENDER_MEDIA"}
SERVICE_TYPES  = {"SERVICE_CHARGE"}
ERROR_TYPES    = {"ERROR"}

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
def insert_guest_check(cur, guest_check: dict):
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
    params = guest_check.copy()
    params["store_id"] = guest_check.get("locRef", "00")  # fallback
    cur.execute(sql, params)
    return guest_check["guestCheckId"]

#Função para fazer o load dos dados de detailLines no banco.
def insert_line_items(cur, guest_check_id: int, detail_lines: list):
    records = []
    for detail in detail_lines:
        records.append(
            (
                detail["guestCheckLineItemId"],
                guest_check_id,
                detail.get("chkEmpId"),
                detail.get("lineNum"),
                detail.get("rvcNum"),
                detail.get("dtlOtNum"),
                detail.get("wsNum"),
                detail.get("detailLcl"),
                Decimal(str(detail.get("dspTtl", 0))),
                Decimal(str(detail.get("dspQty", 0))),
                Decimal(str(detail.get("aggTtl", 0))),
                Decimal(str(detail.get("aggQty", 0))),
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

#Função para fazer o load dos dados de discounts no banco.
def insert_discounts(cur, guest_check_id: int, discounts: list):
    if not discounts:
        return
    sql = """
        INSERT INTO line_item_discount (
            line_item_id, guest_check_id, discount_amount, discount_reason
        ) VALUES %s ON CONFLICT (line_item_id) DO NOTHING
    """
    records = [
        (r["guestCheckLineItemId"],
         guest_check_id,
         Decimal(str(r.get("dspTtl", 0))),
         r.get("discountReason", "AUTO"))
        for r in discounts
    ]
    execute_values(cur, sql, records)
#Função para fazer o load dos dados de payments no banco.
def insert_payments(cur, guest_check_id: int, payments: list):
    if not payments:
        return
    sql = """
        INSERT INTO line_item_payment (
            line_item_id, guest_check_id, tender_type, paid_amount
        ) VALUES %s ON CONFLICT (line_item_id) DO NOTHING
    """
    records = [
        (r["guestCheckLineItemId"],
         guest_check_id,
         r.get("tenderType", "UNKNOWN"),
         Decimal(str(r.get("paidAmount", 0))))
        for r in payments
    ]
    execute_values(cur, sql, records)
#Função para fazer o load dos dados de services no banco.
def insert_services(cur, guest_check_id: int, services: list):  
    if not services:
        return
    sql = """
        INSERT INTO line_item_service_charge (
            line_item_id, guest_check_id, service_charge_amount, service_charge_reason
        ) VALUES %s ON CONFLICT (line_item_id) DO NOTHING
    """
    records = [
        (r["guestCheckLineItemId"],
         guest_check_id,
         Decimal(str(r.get("serviceChargeAmount", 0))),
         r.get("serviceChargeReason", "UNKNOWN"))
        for r in services
    ]
    execute_values(cur, sql, records)
#Função para fazer o load dos dados de errors no banco.
def insert_errors(cur, guest_check_id: int, errors: list):
    if not errors:
        return
    sql = """
        INSERT INTO line_item_error (
            line_item_id, guest_check_id, error_code, error_message
        ) VALUES %s ON CONFLICT (line_item_id) DO NOTHING
    """
    records = [
        (r["guestCheckLineItemId"],
         guest_check_id,
         r.get("errorCode", "UNKNOWN"),
         r.get("errorMessage", "No error message"))
        for r in errors
    ]
    execute_values(cur, sql, records)

#Função para carrega o JSON e chamar as funções que irão dar load das informações no banco.
def main(path: str):
    with open(path, "r", encoding="utf-8") as fo:
        payload = json.load(fo)

    store_id = payload.get("locRef", "00")
    guest_checks = payload.get("guestChecks", [])

    with get_conn() as conn:
        with conn.cursor() as cur:
            for check in guest_checks:
                check["locRef"] = store_id
                gid = insert_guest_check(cur, check)
                insert_line_items(cur, gid, check.get("detailLines", []))
                insert_discounts(cur, gid, check.get("discounts", []))
                insert_payments(cur, gid, check.get("payments", []))
                insert_services(cur, gid, check.get("services", []))
                insert_errors(cur, gid, check.get("errors", []))
            conn.commit()
    print(f"Loaded {len(guest_checks)} guest_check(s) from {path} ✔")

#Carrega o JSON que for passado pelo terminal
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse ERP JSON into Postgres")
    parser.add_argument("json", help="Path to ERP.json")
    args = parser.parse_args()
    main(args.json)
