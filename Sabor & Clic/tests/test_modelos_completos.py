import pytest


def test_estoque_e_snapshot(app):
    from app.models.database import get_db
    from app.models.pedido_model import PedidoModel
    from app.models.cardapio_model import CardapioModel
    from app.models.errors import DomainError

    with app.app_context():
        db = get_db()
        db.execute("UPDATE pratos SET estoque=2 WHERE id_prato=1")
        db.commit()
        p = PedidoModel.criar(1, [{"idPrato": 1, "quantidade": 2}], "Rua teste", "abc")
        assert p["valor_total"] == 51
        assert PedidoModel.criar(
            1, [{"idPrato": 1, "quantidade": 2}], "Rua teste", "abc"
        )["reutilizado"]
        with pytest.raises(DomainError):
            PedidoModel.criar(1, [{"idPrato": 1, "quantidade": 1}], "Rua teste")
        CardapioModel.remover(1)
        assert PedidoModel.listar(1)[0]["itens"][0]["nome"] == "Prato A"


def test_reserva_trigger_e_cancelamento(app):
    import sqlite3
    from datetime import datetime, timedelta, timezone
    from app.models.database import get_db
    from app.models.reserva_model import ReservaModel
    from app.models.errors import DomainError

    with app.app_context():
        b = ReservaModel.criar_bancada({"nome": "Mesa teste"})
        start = datetime.now(timezone.utc) + timedelta(days=1)
        begin = start.isoformat()
        end = (start + timedelta(hours=1)).isoformat()
        rid = ReservaModel.criar(1, b, begin, end)
        with pytest.raises(DomainError):
            ReservaModel.criar(2, b, begin, end)
        with pytest.raises(DomainError):
            ReservaModel.cancelar(rid, 2)
        db = get_db()
        with pytest.raises(sqlite3.IntegrityError):
            with db:
                db.execute(
                    "INSERT INTO reservas(id_cliente,id_bancada,inicio,fim) SELECT 2,id_bancada,inicio,fim FROM reservas WHERE id_reserva=?",
                    (rid,),
                )
        ReservaModel.cancelar(rid, 1)
        second = ReservaModel.criar(2, b, begin, end)
        with pytest.raises(sqlite3.IntegrityError):
            with db:
                db.execute(
                    "UPDATE reservas SET status='confirmada' WHERE id_reserva=?", (rid,)
                )
        assert second != rid


def test_catalogo_versao_e_relatorio(app):
    from app.models.cardapio_model import CardapioModel
    from app.models.relatorio_model import RelatorioModel
    from app.models.errors import DomainError

    with app.app_context():
        data = {
            "nome": "Sopa",
            "preco": 12.5,
            "estoque": 4,
            "status": "disponivel",
            "ficha_tecnica": "Porção: 300ml",
        }
        pid = CardapioModel.criar(data)
        CardapioModel.atualizar(pid, {**data, "preco": 15}, 1)
        with pytest.raises(DomainError) as e:
            CardapioModel.atualizar(pid, data, 1)
        assert e.value.status == 409
        assert CardapioModel.buscar(pid)["versao"] == 2
        assert any(x["id_prato"] == pid for x in RelatorioModel.resumo()["estoque"])


def test_sql_reproduzivel(tmp_path):
    import sqlite3
    from pathlib import Path

    db = sqlite3.connect(tmp_path / "sql.db")
    sql = Path(__file__).resolve().parents[1] / "sql"
    for repeat in range(2):
        for name in [
            "01_modelo_fisico.sql",
            "02_insercoes_basicas.sql",
            "20_triggers.sql",
            "11_queries_relatorios.sql",
        ]:
            db.executescript((sql / name).read_text())
    assert db.execute("SELECT COUNT(*) FROM bancadas").fetchone()[0] == 2
    assert db.execute("SELECT COUNT(*) FROM funcionarios").fetchone()[0] == 0
    db.close()


def test_migracao_aditiva_legado(tmp_path):
    import sqlite3
    from app import create_app
    from app.models.database import get_db, init_db

    path = tmp_path / "legacy.db"
    db = sqlite3.connect(path)
    db.executescript(
        "CREATE TABLE funcionarios(id_funcionario INTEGER PRIMARY KEY,nome TEXT,cpf TEXT,email TEXT,senha TEXT,telefone TEXT,cargo TEXT,salario MONEY); INSERT INTO funcionarios VALUES(1,'Legado','123','legacy@test','hash',NULL,'Cozinheiro',NULL); CREATE TABLE pratos(id_prato INTEGER PRIMARY KEY,nome TEXT,descricao TEXT,preco MONEY,status TEXT); INSERT INTO pratos VALUES(1,'Legado','Original',10,'disponivel');"
    )
    db.close()
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-only-random-key-not-for-production-123456",
            "DATABASE": str(path),
        }
    )
    init_db(app)
    with app.app_context():
        db = get_db()
        assert db.execute("SELECT status FROM funcionarios").fetchone()[0] == "inativo"
        p = db.execute("SELECT * FROM pratos").fetchone()
        assert p["nome"] == "Legado" and p["estoque"] == 0 and p["versao"] == 1


def test_ultimo_estoque_concorrente(app):
    from concurrent.futures import ThreadPoolExecutor
    from app.models.database import get_db
    from app.models.pedido_model import PedidoModel
    from app.models.errors import DomainError

    with app.app_context():
        db = get_db()
        db.execute("UPDATE pratos SET estoque=1 WHERE id_prato=1")
        db.commit()

    def order(customer):
        with app.app_context():
            try:
                return PedidoModel.criar(
                    customer, [{"idPrato": 1, "quantidade": 1, "versao": 1}], "Rua"
                )["id_pedido"]
            except DomainError:
                return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(order, [1, 2]))
    assert sum(x is not None for x in results) == 1
    with app.app_context():
        assert (
            get_db()
            .execute("SELECT estoque FROM pratos WHERE id_prato=1")
            .fetchone()[0]
            == 0
        )
        assert get_db().execute("SELECT COUNT(*) FROM pedidos").fetchone()[0] == 1


def test_preco_legado_invalido_e_idempotencia_privada(app):
    from app.models.database import get_db
    from app.models.pedido_model import PedidoModel
    from app.models.errors import DomainError

    with app.app_context():
        db = get_db()
        db.execute("UPDATE pratos SET estoque=10,preco='NaN' WHERE id_prato=1")
        db.commit()
        with pytest.raises(DomainError) as e:
            PedidoModel.criar(1, [{"idPrato": 1, "quantidade": 1}], "Rua")
        assert e.value.status == 409
        assert db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0] == 0
        db.execute("UPDATE pratos SET preco=10 WHERE id_prato=1")
        db.commit()
        PedidoModel.criar(1, [{"idPrato": 1, "quantidade": 1}], "Rua", "private-key")
        assert "hash_requisicao" not in PedidoModel.listar(1)[0]
        assert "chave_requisicao" not in PedidoModel.listar(1)[0]
        with pytest.raises(DomainError) as e:
            PedidoModel.criar(
                1, [{"idPrato": 1, "quantidade": 2}], "Rua", "private-key"
            )
        assert e.value.status == 409


def test_pedido_impede_admin_sobrescrever_estoque_desatualizado(app):
    from app.models.cardapio_model import CardapioModel
    from app.models.pedido_model import PedidoModel
    from app.models.errors import DomainError

    with app.app_context():
        before = CardapioModel.buscar(1)
        PedidoModel.criar(1, [{"idPrato": 1, "quantidade": 1}], "Rua teste")
        with pytest.raises(DomainError) as error:
            CardapioModel.atualizar(1, {**before, "preco": 30}, before["versao"])
        assert error.value.status == 409
        after = CardapioModel.buscar(1)
        assert after["estoque"] == before["estoque"] - 1
        assert after["preco"] == before["preco"]
        assert after["versao"] == before["versao"] + 1


def test_schema_app_igual_sql_independente(app, tmp_path):
    import sqlite3
    from pathlib import Path
    from app.models.database import get_db

    standalone = sqlite3.connect(tmp_path / "standalone.db")
    scripts = Path(__file__).resolve().parents[1] / "sql"
    for name in ["01_modelo_fisico.sql", "20_triggers.sql"]:
        standalone.executescript((scripts / name).read_text())
    query = "SELECT type,name,tbl_name,sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type,name"
    with app.app_context():
        assert [tuple(row) for row in get_db().execute(query)] == standalone.execute(
            query
        ).fetchall()
    standalone.close()
