from flask import Blueprint, abort, g, jsonify, request

from ..middleware.middleware import requer_perfis
from ..models.reserva_model import ReservaModel
from ..models.relatorio_model import RelatorioModel
from ..validation import inteiro, json_object, texto

reservas_bp = Blueprint("reservas", __name__)


@reservas_bp.route("/api/bancadas", methods=["GET"])
@requer_perfis("cliente", "administrador")
def bancadas():
    todos = request.args.get("todos") == "1"
    if todos and g.usuario["perfil"] != "administrador":
        abort(403, description="Somente o administrador consulta bancadas inativas.")
    return jsonify(sucesso=True, dados=ReservaModel.bancadas(todos))


@reservas_bp.route("/api/bancadas", methods=["POST"])
@requer_perfis("administrador")
def criar_bancada():
    dados = json_object()
    try:
        nome = texto(dados.get("nome"), "Nome da bancada", 3, 100)
        localizacao = texto(dados.get("localizacao", ""), "Localização", 0, 200)
    except ValueError as error:
        abort(400, description=str(error))
    bancada_id = ReservaModel.criar_bancada({"nome": nome, "localizacao": localizacao})
    return (
        jsonify(
            sucesso=True,
            mensagem="Bancada cadastrada.",
            dados={"id_bancada": bancada_id},
        ),
        201,
    )


@reservas_bp.route("/api/reservas", methods=["GET"])
@requer_perfis("cliente", "administrador")
def listar_reservas():
    cliente_id = g.usuario["id"] if g.usuario["perfil"] == "cliente" else None
    return jsonify(sucesso=True, dados=ReservaModel.listar(cliente_id))


@reservas_bp.route("/api/reservas", methods=["POST"])
@requer_perfis("cliente")
def criar_reserva():
    dados = json_object()
    try:
        bancada_id = inteiro(dados.get("id_bancada"), "Bancada")
        inicio = texto(dados.get("inicio"), "Início", 10, 40)
        fim = texto(dados.get("fim"), "Fim", 10, 40)
    except ValueError as error:
        abort(400, description=str(error))
    reserva_id = ReservaModel.criar(g.usuario["id"], bancada_id, inicio, fim)
    return (
        jsonify(
            sucesso=True,
            mensagem="Reserva confirmada.",
            dados={"id_reserva": reserva_id},
        ),
        201,
    )


@reservas_bp.route("/api/reservas/<int:reserva_id>", methods=["DELETE"])
@requer_perfis("cliente", "administrador")
def cancelar_reserva(reserva_id):
    cliente_id = g.usuario["id"] if g.usuario["perfil"] == "cliente" else None
    ReservaModel.cancelar(reserva_id, cliente_id)
    return jsonify(sucesso=True, mensagem="Reserva cancelada.")


@reservas_bp.route("/api/relatorios", methods=["GET"])
@requer_perfis("administrador")
def relatorios():
    return jsonify(sucesso=True, dados=RelatorioModel.resumo())
