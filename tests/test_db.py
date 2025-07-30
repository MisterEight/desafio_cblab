import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
import json

from src.parse_guestcheck import insert_guest_check, insert_line_items, main, get_conn

DATA_PATH = Path('data/ERP.json')

# Função auxiliar para carregar um exemplo de guest check
def _load_sample_gc():
    data = json.loads(DATA_PATH.read_text())
    gc = data['guestChecks'][0]
    gc['locRef'] = data.get('locRef')
    return gc

# Testes para verificar a criação do schema e inserção de dados
def test_schema_loaded(db_conn):
    with db_conn.cursor() as cur:
        cur.execute("SELECT to_regclass('guest_check');")
        assert cur.fetchone()[0] == 'guest_check'
        cur.execute("SELECT to_regclass('line_item');")
        assert cur.fetchone()[0] == 'line_item'

# Teste para verificar a inserção de um guest check
def test_insert_functions(db_conn):
    gc = _load_sample_gc()
    with db_conn.cursor() as cur:
        gid = insert_guest_check(cur, gc)
        insert_line_items(cur, gid, gc.get('detailLines', []))
    db_conn.commit()

    with db_conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM guest_check;')
        assert cur.fetchone()[0] == 1
        cur.execute('SELECT COUNT(*) FROM line_item;')
        assert cur.fetchone()[0] == len(gc['detailLines'])

# Teste para verificar a execução do script principal
def test_main_script(db_conn, capsys):
    main(str(DATA_PATH))
    captured = capsys.readouterr()
    assert 'Loaded' in captured.out
    with db_conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM guest_check;')
        count = cur.fetchone()[0]
    assert count > 0