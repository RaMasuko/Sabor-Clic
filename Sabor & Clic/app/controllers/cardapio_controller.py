from flask import Blueprint, abort, g, jsonify, request

from ..middleware.middleware import requer_perfis
from ..models.cardapio_model import CardapioModel
from ..validation import inteiro, json_object, preco_valido, texto

cardapio_bp = Blueprint("cardapio", __name__)


def dados_prato(dados):
    try:
        status = dados.get("status", "disponivel")
        if status not in ("disponivel", "indisponivel"):
            raise ValueError("Status de prato inválido.")
        return {
            "nome": texto(dados.get("nome"), "Nome do prato", 1, 100),
            "preco": str(preco_valido(dados.get("preco"))),
            "descricao": texto(dados.get("descricao", ""), "Descrição", 0, 250),
            "estoque": inteiro(dados.get("estoque", 0), "Estoque", 0, 1000000),
            "status": status,
            "ficha_tecnica": texto(
                dados.get("ficha_tecnica", ""), "Ficha técnica", 0, 2000
            ),
        }
    except ValueError as error:
        abort(400, description=str(error))


@cardapio_bp.route("/api/cardapio", methods=["GET"])
def get_cardapio():
    todos = request.args.get("todos") == "1"
    if todos and (not g.usuario or g.usuario["perfil"] != "administrador"):
        abort(403, description="Somente o administrador consulta pratos inativos.")
    return jsonify(sucesso=True, dados=CardapioModel.listar(todos=todos))


@cardapio_bp.route("/api/cardapio", methods=["POST"])
@requer_perfis("administrador")
def criar_prato():
    prato_id = CardapioModel.criar(dados_prato(json_object()))
    return (
        jsonify(
            sucesso=True,
            mensagem="Prato cadastrado com sucesso!",
            dados={"id": prato_id},
            id=prato_id,
        ),
        201,
    )


@cardapio_bp.route("/api/cardapio/<int:prato_id>", methods=["GET"])
@requer_perfis("administrador")
def consultar_prato(prato_id):
    return jsonify(sucesso=True, dados=CardapioModel.buscar(prato_id))


@cardapio_bp.route("/api/cardapio/<int:prato_id>", methods=["PUT"])
@requer_perfis("administrador")
def atualizar_prato(prato_id):
    dados = json_object()
    try:
        versao = inteiro(dados.get("versao"), "Versão")
    except ValueError as error:
        abort(400, description=str(error))
    CardapioModel.atualizar(prato_id, dados_prato(dados), versao)
    return jsonify(sucesso=True, mensagem="Prato atualizado com sucesso!")


@cardapio_bp.route("/api/cardapio/<int:prato_id>", methods=["DELETE"])
@requer_perfis("administrador")
def remover_prato(prato_id):
    dados = json_object()
    try:
        versao = inteiro(dados.get("versao"), "Versão")
    except ValueError as error:
        abort(400, description=str(error))
    CardapioModel.remover(prato_id, versao)
    return jsonify(
        sucesso=True, mensagem="Prato removido do catálogo. O histórico foi preservado."
    )
