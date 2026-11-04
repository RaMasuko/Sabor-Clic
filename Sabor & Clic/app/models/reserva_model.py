import sqlite3
from datetime import datetime, timezone, timedelta
from .database import get_db
from .errors import DomainError


def utc(value):
    try:
        d = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if d.tzinfo is None:
            raise ValueError()
        return d.astimezone(timezone.utc)
    except (ValueError, AttributeError, OverflowError):
        raise DomainError("Data deve incluir fuso horário.")


def iso(d):
    return d.isoformat(timespec="seconds").replace("+00:00", "Z")


class ReservaModel:
    @staticmethod
    def bancadas(todos=False):
        return [
            dict(r)
            for r in get_db().execute(
                "SELECT * FROM bancadas"
                + ("" if todos else " WHERE ativo=1")
                + " ORDER BY id_bancada"
            )
        ]

    @staticmethod
    def criar_bancada(dados):
        db = get_db()
        with db:
            c = db.execute(
                "INSERT INTO bancadas(nome,localizacao) VALUES(?,?)",
                (dados["nome"], dados.get("localizacao", "")),
            )
        return c.lastrowid

    @staticmethod
    def listar(cliente_id=None):
        return [
            dict(r)
            for r in get_db().execute(
                "SELECT r.*,b.nome AS bancada,c.nome AS cliente FROM reservas r JOIN bancadas b ON b.id_bancada=r.id_bancada JOIN clientes c ON c.id_cliente=r.id_cliente"
                + (" WHERE r.id_cliente=?" if cliente_id is not None else "")
                + " ORDER BY r.inicio",
                (cliente_id,) if cliente_id is not None else (),
            )
        ]

    @staticmethod
    def criar(cliente_id, bancada_id, inicio, fim):
        start, end = utc(inicio), utc(fim)
        now = datetime.now(timezone.utc)
        if not now < start <= now + timedelta(
            days=90
        ) or not start < end <= start + timedelta(hours=12):
            raise DomainError("Intervalo de reserva inválido.")
        db = get_db()
        try:
            db.execute("BEGIN IMMEDIATE")
            c = db.execute(
                "INSERT INTO reservas(id_cliente,id_bancada,inicio,fim) VALUES(?,?,?,?)",
                (cliente_id, bancada_id, iso(start), iso(end)),
            )
            db.commit()
            return c.lastrowid
        except Exception as e:
            db.rollback()
            if isinstance(e, sqlite3.IntegrityError):
                raise DomainError(
                    "Bancada indisponível ou horário já reservado.", 409
                ) from e
            raise

    @staticmethod
    def cancelar(id, cliente_id=None):
        db = get_db()
        with db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM reservas WHERE id_reserva=?"
                + (" AND id_cliente=?" if cliente_id is not None else ""),
                (id, cliente_id) if cliente_id is not None else (id,),
            ).fetchone()
            if not row:
                raise DomainError("Reserva não encontrada.", 404)
            if row["status"] != "confirmada" or utc(row["inicio"]) <= datetime.now(
                timezone.utc
            ):
                raise DomainError("Reserva não pode ser cancelada.", 409)
            db.execute(
                "UPDATE reservas SET status='cancelada' WHERE id_reserva=?", (id,)
            )
