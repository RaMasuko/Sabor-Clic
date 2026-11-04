from .database import get_db


class RelatorioModel:
    @staticmethod
    def resumo():
        db = get_db()
        vendas = [
            dict(r)
            for r in db.execute(
                "SELECT date(data_pedido) AS data,COUNT(*) AS pedidos,ROUND(SUM(valor_total),2) AS faturamento FROM pedidos GROUP BY date(data_pedido) ORDER BY data"
            )
        ]
        estoque = [
            dict(r)
            for r in db.execute(
                "SELECT id_prato,nome,estoque,status FROM pratos WHERE excluido=0 ORDER BY nome"
            )
        ]
        ocupacao = [
            dict(r)
            for r in db.execute(
                "SELECT b.id_bancada,b.nome,COUNT(r.id_reserva) AS reservas,COALESCE(ROUND(SUM((julianday(r.fim)-julianday(r.inicio))*1440),2),0) AS minutos_reservados FROM bancadas b LEFT JOIN reservas r ON r.id_bancada=b.id_bancada AND r.status='confirmada' GROUP BY b.id_bancada ORDER BY b.id_bancada"
            )
        ]
        return {
            "vendas": vendas,
            "estoque": estoque,
            "ocupacao": ocupacao,
            "totais": {
                "pedidos": sum(x["pedidos"] for x in vendas),
                "faturamento": round(sum(x["faturamento"] for x in vendas), 2),
                "reservas": sum(x["reservas"] for x in ocupacao),
            },
        }
