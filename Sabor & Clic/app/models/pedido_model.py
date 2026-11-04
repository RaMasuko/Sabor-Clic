import hashlib
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from ..validation import preco_valido
from .database import get_db
from .errors import DomainError


class PedidoModel:
    @staticmethod
    def listar(cliente_id=None, pendentes=False):
        sql = "SELECT p.id_pedido,p.data_pedido,p.status,p.valor_total,p.endereco_entrega,p.tempo_estimado_min,p.data_previsao,c.nome AS cliente FROM pedidos p JOIN clientes c ON c.id_cliente=p.id_cliente WHERE 1=1"
        args = []
        if cliente_id is not None:
            sql += " AND p.id_cliente=?"
            args.append(cliente_id)
        if pendentes:
            sql += " AND p.status<>'Pronto para Entrega'"
        rows = []
        for r in get_db().execute(sql + " ORDER BY p.id_pedido DESC", args):
            d = dict(r)
            d["data"] = d.pop("data_pedido")
            d["itens"] = [
                dict(i)
                for i in get_db().execute(
                    "SELECT nome_prato AS nome,quantidade,preco_unitario FROM itens_pedido WHERE id_pedido=? ORDER BY id_item",
                    (r["id_pedido"],),
                )
            ]
            rows.append(d)
        return rows

    @staticmethod
    def criar(cliente_id, itens, endereco, chave=None):
        normalized = {}
        for item in itens:
            pid = item["idPrato"]
            qty = item["quantidade"]
            if type(pid) is not int or type(qty) is not int or qty <= 0:
                raise DomainError("Item inválido.")
            if pid in normalized:
                if normalized[pid].get("versao") != item.get("versao"):
                    raise DomainError("Versões incompatíveis.", 409)
                normalized[pid]["quantidade"] += qty
            else:
                normalized[pid] = {
                    "idPrato": pid,
                    "quantidade": qty,
                    **({"versao": item["versao"]} if "versao" in item else {}),
                }
        if not normalized:
            raise DomainError("Pedido vazio.")
        digest = hashlib.sha256(
            json.dumps(
                {
                    "itens": sorted(normalized.values(), key=lambda i: i["idPrato"]),
                    "endereco": endereco,
                },
                sort_keys=True,
                ensure_ascii=False,
            ).encode()
        ).hexdigest()
        db = get_db()
        try:
            db.execute("BEGIN IMMEDIATE")
            if chave:
                old = db.execute(
                    "SELECT * FROM pedidos WHERE id_cliente=? AND chave_requisicao=?",
                    (cliente_id, chave),
                ).fetchone()
                if old:
                    if old["hash_requisicao"] != digest:
                        raise DomainError("Chave já utilizada com outro pedido.", 409)
                    db.commit()
                    return {
                        "id_pedido": old["id_pedido"],
                        "valor_total": old["valor_total"],
                        "reutilizado": True,
                    }
            rows = []
            total = Decimal("0")
            for item in normalized.values():
                p = db.execute(
                    "SELECT * FROM pratos WHERE id_prato=? AND excluido=0",
                    (item["idPrato"],),
                ).fetchone()
                if (
                    not p
                    or p["status"] != "disponivel"
                    or p["estoque"] < item["quantidade"]
                ):
                    raise DomainError(
                        "Prato indisponível ou estoque insuficiente.", 409
                    )
                if "versao" in item and item["versao"] != p["versao"]:
                    raise DomainError("O cardápio foi alterado.", 409)
                try:
                    price = preco_valido(p["preco"])
                except ValueError:
                    raise DomainError(
                        "Preço inválido no catálogo. Contate a equipe.", 409
                    )
                total += price * item["quantidade"]
                rows.append((p, item["quantidade"]))
            c = db.execute(
                "INSERT INTO pedidos(id_cliente,data_pedido,valor_total,endereco_entrega,chave_requisicao,hash_requisicao) VALUES(?,?,?,?,?,?)",
                (
                    cliente_id,
                    datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    str(total),
                    endereco,
                    chave or None,
                    digest,
                ),
            )
            for p, qty in rows:
                db.execute(
                    "INSERT INTO itens_pedido(id_pedido,id_prato,quantidade,preco_unitario,nome_prato) VALUES(?,?,?,?,?)",
                    (c.lastrowid, p["id_prato"], qty, p["preco"], p["nome"]),
                )
            db.commit()
            return {
                "id_pedido": c.lastrowid,
                "valor_total": float(total),
                "reutilizado": False,
            }
        except Exception as error:
            db.rollback()
            if isinstance(error, sqlite3.IntegrityError):
                raise DomainError(
                    "Não foi possível concluir o pedido. Verifique disponibilidade e dados.",
                    409,
                ) from error
            raise

    @staticmethod
    def atualizar_status(id, status):
        previous = {
            "Iniciando Preparo": "Aguardando",
            "Pronto para Entrega": "Iniciando Preparo",
        }.get(status)
        if not previous:
            raise DomainError("Transição inválida.", 409)
        db = get_db()
        with db:
            if not db.execute(
                "UPDATE pedidos SET status=? WHERE id_pedido=? AND status=?",
                (status, id, previous),
            ).rowcount:
                if not db.execute(
                    "SELECT 1 FROM pedidos WHERE id_pedido=?", (id,)
                ).fetchone():
                    raise DomainError("Pedido não encontrado.", 404)
                raise DomainError("Transição inválida.", 409)

    @staticmethod
    def definir_estimativa(id, minutos):
        if type(minutos) is not int or not 1 <= minutos <= 1440:
            raise DomainError("Estimativa inválida.")
        previsao = (
            (datetime.now(timezone.utc) + timedelta(minutes=minutos))
            .isoformat()
            .replace("+00:00", "Z")
        )
        db = get_db()
        with db:
            if not db.execute(
                "UPDATE pedidos SET tempo_estimado_min=?,data_previsao=? WHERE id_pedido=? AND status<>'Pronto para Entrega'",
                (minutos, previsao, id),
            ).rowcount:
                if not db.execute(
                    "SELECT 1 FROM pedidos WHERE id_pedido=?", (id,)
                ).fetchone():
                    raise DomainError("Pedido não encontrado.", 404)
                raise DomainError("Pedido já finalizado.", 409)
        return {"tempo_estimado_min": minutos, "data_previsao": previsao}
