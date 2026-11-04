import hashlib
import time

from .database import get_db
from .errors import DomainError


class UsuarioModel:
    @staticmethod
    def email_em_uso(email):
        db = get_db()
        return any(
            db.execute(query, (email,)).fetchone()
            for query in (
                "SELECT 1 FROM clientes WHERE email = ? COLLATE NOCASE",
                "SELECT 1 FROM funcionarios WHERE email = ? COLLATE NOCASE",
            )
        )

    @staticmethod
    def buscar_login(email):
        candidatos = []
        for tipo, query in (
            (
                "funcionario",
                "SELECT * FROM funcionarios WHERE email = ? COLLATE NOCASE",
            ),
            ("cliente", "SELECT * FROM clientes WHERE email = ? COLLATE NOCASE"),
        ):
            candidatos.extend(
                (tipo, row) for row in get_db().execute(query, (email,)).fetchall()
            )
        return candidatos[0] if len(candidatos) == 1 else None

    @staticmethod
    def reservar_tentativa(email, ip):
        now = int(time.time())
        chaves = [
            (hashlib.sha256(("email:" + email).encode()).hexdigest(), 5),
            (hashlib.sha256(("ip:" + ip).encode()).hexdigest(), 30),
        ]
        db = get_db()
        try:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM login_attempts WHERE inicio <= ?", (now - 900,))
            for chave, limite in chaves:
                row = db.execute(
                    "SELECT tentativas FROM login_attempts WHERE chave = ?", (chave,)
                ).fetchone()
                if row and row["tentativas"] >= limite:
                    raise DomainError(
                        "Muitas tentativas de login. Aguarde 15 minutos.", 429
                    )
            for chave, _ in chaves:
                db.execute(
                    """INSERT INTO login_attempts (chave, tentativas, inicio) VALUES (?, 1, ?)
                              ON CONFLICT(chave) DO UPDATE SET tentativas = tentativas + 1""",
                    (chave, now),
                )
            db.commit()
        except Exception:
            db.rollback()
            raise
        return chaves[0][0]

    @staticmethod
    def limpar_tentativas(chave):
        db = get_db()
        db.execute("DELETE FROM login_attempts WHERE chave = ?", (chave,))
        db.commit()

    @staticmethod
    def criar_cliente(nome, email, senha_hash, endereco):
        db = get_db()
        try:
            db.execute("BEGIN IMMEDIATE")
            if UsuarioModel.email_em_uso(email):
                raise DomainError(
                    "Não foi possível cadastrar. Verifique os dados ou faça login."
                )
            db.execute(
                """INSERT INTO clientes (nome, email, senha, endereco, status)
                          VALUES (?, ?, ?, ?, 'ativo')""",
                (nome, email, senha_hash, endereco),
            )
            db.commit()
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def criar_funcionario(dados):
        db = get_db()
        try:
            db.execute("BEGIN IMMEDIATE")
            if UsuarioModel.email_em_uso(dados["email"]):
                raise DomainError(
                    "E-mail já cadastrado. Use um endereço exclusivo por conta."
                )
            db.execute(
                """INSERT INTO funcionarios
                          (nome, cpf, email, senha, cargo, perfil, status, turno, especialidade)
                          VALUES (?, ?, ?, ?, ?, ?, 'ativo', ?, ?)""",
                (
                    dados["nome"],
                    dados["cpf"],
                    dados["email"],
                    dados["senha"],
                    (
                        "Administrador"
                        if dados["perfil"] == "administrador"
                        else "Cozinheiro"
                    ),
                    dados["perfil"],
                    dados["turno"],
                    dados["especialidade"],
                ),
            )
            db.commit()
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def perfil(tipo, usuario_id):
        if tipo == "cliente":
            row = (
                get_db()
                .execute(
                    """SELECT id_cliente AS id,nome,email,endereco,
                                     'cliente' AS perfil FROM clientes WHERE id_cliente=?""",
                    (usuario_id,),
                )
                .fetchone()
            )
        else:
            row = (
                get_db()
                .execute(
                    """SELECT id_funcionario AS id,nome,email,perfil,turno,especialidade
                                     FROM funcionarios WHERE id_funcionario=?""",
                    (usuario_id,),
                )
                .fetchone()
            )
        if row is None:
            raise DomainError("Conta não encontrada.", 404)
        return dict(row)

    @staticmethod
    def atualizar_perfil(tipo, usuario_id, dados):
        db = get_db()
        with db:
            if tipo == "cliente":
                db.execute(
                    "UPDATE clientes SET nome=?,endereco=? WHERE id_cliente=?",
                    (dados["nome"], dados["endereco"], usuario_id),
                )
            else:
                db.execute(
                    "UPDATE funcionarios SET nome=?,turno=?,especialidade=? WHERE id_funcionario=?",
                    (dados["nome"], dados["turno"], dados["especialidade"], usuario_id),
                )
        return UsuarioModel.perfil(tipo, usuario_id)
