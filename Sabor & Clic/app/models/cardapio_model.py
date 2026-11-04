from .database import get_db
from .errors import DomainError


class CardapioModel:
    @staticmethod
    def listar(todos=False):
        sql = "SELECT id_prato AS id,nome,preco,descricao,status,estoque,versao,ficha_tecnica FROM pratos WHERE excluido=0"
        return [
            dict(r)
            for r in get_db().execute(
                sql
                + ("" if todos else " AND status='disponivel'")
                + " ORDER BY id_prato"
            )
        ]

    @staticmethod
    def buscar(id):
        row = (
            get_db()
            .execute(
                "SELECT id_prato AS id,nome,preco,descricao,status,estoque,versao,ficha_tecnica FROM pratos WHERE id_prato=? AND excluido=0",
                (id,),
            )
            .fetchone()
        )
        if not row:
            raise DomainError("Prato não encontrado.", 404)
        return dict(row)

    @staticmethod
    def criar(dados):
        db = get_db()
        with db:
            c = db.execute(
                "INSERT INTO pratos(nome,preco,descricao,status,estoque,ficha_tecnica) VALUES(?,?,?,?,?,?)",
                tuple(
                    dados.get(k, d)
                    for k, d in [
                        ("nome", ""),
                        ("preco", 0),
                        ("descricao", ""),
                        ("status", "disponivel"),
                        ("estoque", 0),
                        ("ficha_tecnica", ""),
                    ]
                ),
            )
        return c.lastrowid

    @staticmethod
    def atualizar(id, dados, versao):
        db = get_db()
        with db:
            c = db.execute(
                "UPDATE pratos SET nome=?,preco=?,descricao=?,status=?,estoque=?,ficha_tecnica=?,versao=versao+1 WHERE id_prato=? AND versao=? AND excluido=0",
                tuple(
                    dados.get(k, d)
                    for k, d in [
                        ("nome", ""),
                        ("preco", 0),
                        ("descricao", ""),
                        ("status", "disponivel"),
                        ("estoque", 0),
                        ("ficha_tecnica", ""),
                    ]
                )
                + (id, versao),
            )
            if not c.rowcount:
                CardapioModel.buscar(id)
                raise DomainError("O prato foi alterado. Atualize a página.", 409)

    @staticmethod
    def remover(id, versao=None):
        db = get_db()
        with db:
            c = db.execute(
                "UPDATE pratos SET excluido=1,status='indisponivel',versao=versao+1 WHERE id_prato=? AND excluido=0"
                + (" AND versao=?" if versao is not None else ""),
                (id, versao) if versao is not None else (id,),
            )
            if not c.rowcount:
                CardapioModel.buscar(id)
                raise DomainError("O prato foi alterado.", 409)

    listar_todos = listar
    buscar_por_id = buscar
