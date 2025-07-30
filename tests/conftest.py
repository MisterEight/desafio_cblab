import os
import psycopg2
import pytest
from pathlib import Path
from dotenv import load_dotenv
SCHEMA_SQL = Path("sql/schema_warehouse.sql").read_text()

# Fixture para a conexão com o banco de dados
@pytest.fixture(scope='session')
def db_conn():
    load_dotenv()
    conn = psycopg2.connect(
        host=os.getenv('PGHOST'),
        port=os.getenv('PGPORT'),
        user=os.getenv('PGUSER'),
        password=os.getenv('PGPASSWORD'),
        dbname=os.getenv('PGDATABASE'),
    )
    yield conn
    conn.close()

# Fixture para limpar o banco de dados antes de cada teste
@pytest.fixture(autouse=True)
def clean_db(db_conn):
    with db_conn.cursor() as cur:
        cur.execute('DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;')
        cur.execute(SCHEMA_SQL)
    db_conn.commit()
    yield
    with db_conn.cursor() as cur:
        cur.execute('DROP SCHEMA public CASCADE; CREATE SCHEMA public;')
    db_conn.commit()