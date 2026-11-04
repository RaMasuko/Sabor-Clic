import sqlite3
from flask import current_app, g


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(current_app.config["DATABASE"], timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
    return db


def close_db(e=None):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db(app):
    with app.app_context():
        db = get_db()
        from pathlib import Path

        sql_dir = Path(__file__).resolve().parents[2] / "sql"
        db.executescript((sql_dir / "01_modelo_fisico.sql").read_text(encoding="utf-8"))

        # CREATE IF NOT EXISTS preserva tabelas antigas; ALTER acrescenta somente
        # colunas ausentes. Funcionários legados sem status ficam inativos.
        columns = {row["name"] for row in db.execute("PRAGMA table_info(funcionarios)")}
        if "perfil" not in columns:
            db.execute(
                "ALTER TABLE funcionarios ADD COLUMN perfil TEXT NOT NULL DEFAULT 'cozinheiro'"
            )
        if "status" not in columns:
            db.execute(
                "ALTER TABLE funcionarios ADD COLUMN status TEXT NOT NULL DEFAULT 'inativo'"
            )
        # CHECKs acompanham colunas adicionadas. Tabelas que já possuíam essas
        # colunas não são reconstruídas: os triggers reforçam as regras de estoque.
        additions = {
            "pratos": {
                "estoque": "INTEGER NOT NULL DEFAULT 0 CHECK (estoque >= 0)",
                "excluido": "INTEGER NOT NULL DEFAULT 0 CHECK (excluido IN (0, 1))",
                "versao": "INTEGER NOT NULL DEFAULT 1",
                "ficha_tecnica": "TEXT NOT NULL DEFAULT ''",
            },
            "pedidos": {
                "endereco_entrega": "TEXT NOT NULL DEFAULT ''",
                "tempo_estimado_min": "INTEGER",
                "data_previsao": "TEXT",
                "chave_requisicao": "TEXT",
                "hash_requisicao": "TEXT",
            },
            "itens_pedido": {"nome_prato": "TEXT NOT NULL DEFAULT ''"},
            "funcionarios": {
                "turno": "TEXT NOT NULL DEFAULT ''",
                "especialidade": "TEXT NOT NULL DEFAULT ''",
            },
        }
        for table, fields in additions.items():
            existing = {
                r["name"] for r in db.execute("PRAGMA table_info(" + table + ")")
            }
            for name, definition in fields.items():
                if name not in existing:
                    db.execute(
                        "ALTER TABLE "
                        + table
                        + " ADD COLUMN "
                        + name
                        + " "
                        + definition
                    )
        db.execute(
            "UPDATE itens_pedido SET nome_prato=COALESCE((SELECT nome FROM pratos WHERE pratos.id_prato=itens_pedido.id_prato),'Prato') WHERE nome_prato='' "
        )
        db.executescript((sql_dir / "20_triggers.sql").read_text(encoding="utf-8"))
        db.commit()
