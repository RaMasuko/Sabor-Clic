import re

from flask import Blueprint, abort, g, jsonify, request

from ..middleware.middleware import requer_perfis
from ..models.pedido_model import PedidoModel
from ..models.database import get_db
from ..validation import inteiro, json_object, texto

pedidos_bp = Blueprint("pedidos", __name__)


def itens_validos(itens):
    if not isinstance(itens, list) or not 1 <= len(itens) <= 100:
        raise ValueError("O pedido deve conter de 1 a 100 pratos.")
    normalized, vistos = [], set()
    for item in itens:
        if not isinstance(item, dict):
            raise ValueError("Item de pedido inválido.")
        prato_id = inteiro(item.get("idPrato"), "Prato")
        quantidade = inteiro(item.get("quantidade"), "Quantidade", 1, 99)
        if prato_id in vistos:
            raise ValueError("Agrupe as quantidades do mesmo prato em um único item.")
        vistos.add(prato_id)
        novo = {"idPrato": prato_id, "quantidade": quantidade}
        if "versao" in item:
            novo["versao"] = inteiro(item["versao"], "Versão")
        normalized.append(novo)
    return normalized


@pedidos_bp.route("/api/pedidos", methods=["GET"])
@requer_perfis("cliente", "cozinheiro", "administrador")
def listar_pedidos():
    cliente_id = g.usuario["id"] if g.usuario["perfil"] == "cliente" else None
    pendentes = request.args.get("pendentes") == "1"
    return jsonify(sucesso=True, dados=PedidoModel.listar(cliente_id, pendentes))


@pedidos_bp.route("/api/pedidos", methods=["POST"])
@requer_perfis("cliente")
def criar_pedido():
    dados = json_object()
    try:
        itens = itens_validos(dados.get("itens"))
        endereco = texto(
            dados.get("endereco_entrega", g.usuario.get("endereco", "")),
            "Endereço de entrega",
            5,
            200,
        )
        chave = request.headers.get("X-Idempotency-Key")
        if chave is not None and not re.fullmatch(r"[A-Za-z0-9_-]{8,64}", chave):
            raise ValueError("Chave de requisição inválida.")
    except ValueError as error:
        abort(400, description=str(error))
    resultado = PedidoModel.criar(g.usuario["id"], itens, endereco, chave)
    return jsonify(
        sucesso=True, mensagem="Pedido registrado com sucesso!", **resultado
    ), (200 if resultado["reutilizado"] else 201)


@pedidos_bp.route("/api/pedidos/<int:id_pedido>/status", methods=["PUT"])
@requer_perfis("cozinheiro", "administrador")
def atualizar_status(id_pedido):
    status = json_object().get("status")
    if status not in ("Iniciando Preparo", "Pronto para Entrega"):
        abort(400, description="Status inválido.")
    PedidoModel.atualizar_status(id_pedido, status)
    return jsonify(sucesso=True, mensagem="Status atualizado!")


@pedidos_bp.route("/api/pedidos/<int:id_pedido>/estimativa", methods=["PUT"])
@requer_perfis("cozinheiro", "administrador")
def definir_estimativa(id_pedido):
    try:
        minutos = inteiro(
            json_object().get("minutos"), "Estimativa de preparo", 1, 1440
        )
    except ValueError as error:
        abort(400, description=str(error))
    return jsonify(
        sucesso=True,
        mensagem="Estimativa registrada.",
        dados=PedidoModel.definir_estimativa(id_pedido, minutos),
    )
