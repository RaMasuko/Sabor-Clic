import sqlite3

from flask import (
    Blueprint,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from ..accounts import criar_funcionario
from ..middleware.middleware import (
    csrf_token,
    requer_perfis,
    revoke_session,
    start_session,
)
from ..models.usuario_model import UsuarioModel
from ..models.errors import DomainError
from ..validation import email_valido, json_object, senha_valida, texto

main_bp = Blueprint("main", __name__)
_DUMMY_HASH = generate_password_hash("Credencial-inexistente-aleatoria-2026")


def api_request():
    return request.path.startswith("/api/")


def dados_formulario():
    return json_object() if api_request() else request.form


def falha_formulario(template, message, status=400):
    flash(message, "erro")
    if api_request():
        return (
            jsonify(
                sucesso=False, mensagem=message, erro=message, csrf_token=csrf_token()
            ),
            status,
        )
    return render_template(template), status


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/cadastro", methods=["GET", "POST"])
@main_bp.route("/api/cadastro", methods=["POST"])
def cadastro():
    if request.method == "POST":
        dados = dados_formulario()
        try:
            if dados.get("tipo", "cliente") != "cliente":
                raise ValueError(
                    "O cadastro público permite somente contas de cliente."
                )
            nome = texto(dados.get("nome"), "Nome", 3, 100)
            email = email_valido(dados.get("email"))
            senha = senha_valida(dados.get("senha"))
            endereco = texto(dados.get("endereco"), "Endereço de entrega", 5, 200)
            UsuarioModel.criar_cliente(
                nome, email, generate_password_hash(senha), endereco
            )
        except (ValueError, DomainError, sqlite3.IntegrityError) as error:
            message = (
                str(error)
                if isinstance(error, (ValueError, DomainError))
                else "Não foi possível cadastrar com esses dados."
            )
            return falha_formulario("cadastro.html", message)
        flash("Cadastro concluído. Faça login para continuar.", "sucesso")
        if api_request():
            return (
                jsonify(
                    sucesso=True,
                    mensagem="Cadastro concluído. Faça login para continuar.",
                    destino="/login",
                ),
                201,
            )
        return redirect(url_for("main.login"))
    return render_template("cadastro.html")


@main_bp.route("/login", methods=["GET", "POST"])
@main_bp.route("/api/login", methods=["POST"])
def login():
    if request.method == "POST":
        dados = dados_formulario()
        email = dados.get("email", "")
        senha = dados.get("senha", "")
        email = email.strip().lower() if isinstance(email, str) else ""
        senha = senha if isinstance(senha, str) else ""
        chave = UsuarioModel.reservar_tentativa(
            email[:120], request.remote_addr or "local"
        )
        candidate = (
            UsuarioModel.buscar_login(email)
            if len(email) <= 120 and 0 < len(senha) <= 128
            else None
        )
        valid = False
        try:
            valid = check_password_hash(
                candidate[1]["senha"] if candidate else _DUMMY_HASH, senha
            )
        except (ValueError, TypeError):
            pass
        if candidate and valid and candidate[1]["status"] == "ativo":
            tipo, user = candidate
            role = "cliente" if tipo == "cliente" else user["perfil"]
            if role in ("cliente", "cozinheiro", "administrador"):
                UsuarioModel.limpar_tentativas(chave)
                start_session(user, tipo)
                flash("Login realizado com sucesso.", "sucesso")
                destino = "/" if tipo == "cliente" else "/kds"
                if api_request():
                    return jsonify(
                        sucesso=True,
                        mensagem="Login realizado com sucesso.",
                        dados={"nome": user["nome"], "perfil": role},
                        destino=destino,
                        csrf_token=csrf_token(),
                    )
                return redirect(destino)
        return falha_formulario(
            "login.html", "E-mail ou senha incorretos, ou conta indisponível.", 401
        )
    return render_template("login.html")


@main_bp.route("/logout", methods=["POST"])
@main_bp.route("/api/logout", methods=["POST"])
def logout():
    revoke_session()
    flash("Você saiu da sua conta.", "sucesso")
    if api_request():
        return jsonify(
            sucesso=True,
            mensagem="Você saiu da sua conta.",
            destino="/login",
            csrf_token=csrf_token(),
        )
    return redirect(url_for("main.login"))


@main_bp.route("/api/perfil", methods=["GET"])
@requer_perfis()
def consultar_perfil():
    return jsonify(
        sucesso=True, dados=UsuarioModel.perfil(g.usuario["tipo"], g.usuario["id"])
    )


@main_bp.route("/api/perfil", methods=["PUT"])
@requer_perfis()
def atualizar_perfil():
    dados = json_object()
    cliente = g.usuario["perfil"] == "cliente"
    permitidos = {"nome", "endereco"} if cliente else {"nome", "turno", "especialidade"}
    try:
        if set(dados) - permitidos:
            raise ValueError(
                "Foram enviados campos que não podem ser alterados por este perfil."
            )
        atual = UsuarioModel.perfil(g.usuario["tipo"], g.usuario["id"])
        novo = {"nome": texto(dados.get("nome", atual["nome"]), "Nome", 3, 100)}
        if cliente:
            novo["endereco"] = texto(
                dados.get("endereco", atual.get("endereco")),
                "Endereço de entrega",
                5,
                200,
            )
        else:
            for campo in ("turno", "especialidade"):
                novo[campo] = texto(
                    dados.get(campo, atual.get(campo, "")),
                    campo.capitalize(),
                    1 if g.usuario["perfil"] == "cozinheiro" else 0,
                    100,
                )
    except ValueError as error:
        abort(400, description=str(error))
    return jsonify(
        sucesso=True,
        mensagem="Perfil atualizado.",
        dados=UsuarioModel.atualizar_perfil(g.usuario["tipo"], g.usuario["id"], novo),
    )


@main_bp.route("/kds")
@requer_perfis("cozinheiro", "administrador")
def kds():
    return render_template("kds.html")


@main_bp.route("/perfil")
@requer_perfis()
def perfil():
    return render_template(
        "perfil.html", usuario=UsuarioModel.perfil(g.usuario["tipo"], g.usuario["id"])
    )


@main_bp.route("/reservas")
@requer_perfis("cliente", "administrador")
def reservas():
    return render_template("reservas.html")


@main_bp.route("/adicionar-prato")
@requer_perfis("administrador")
def pagina_adicionar_prato():
    return render_template("novo_prato.html")


@main_bp.route("/estoque")
@requer_perfis("administrador")
def estoque():
    return render_template("estoque.html")


@main_bp.route("/relatorios")
@requer_perfis("administrador")
def relatorios():
    return render_template("relatorios.html")


@main_bp.route("/funcionarios/novo", methods=["GET", "POST"])
@main_bp.route("/api/funcionarios", methods=["POST"])
@requer_perfis("administrador")
def novo_funcionario():
    if request.method == "POST":
        dados = dados_formulario()
        try:
            criar_funcionario(
                dados.get("nome"),
                dados.get("email"),
                dados.get("cpf"),
                dados.get("senha"),
                dados.get("perfil"),
                dados.get("turno", ""),
                dados.get("especialidade", ""),
            )
        except (ValueError, DomainError, sqlite3.IntegrityError) as error:
            message = (
                str(error)
                if isinstance(error, (ValueError, DomainError))
                else "Não foi possível criar a conta com esses dados."
            )
            return falha_formulario("funcionario.html", message)
        flash("Conta criada com sucesso.", "sucesso")
        if api_request():
            return jsonify(sucesso=True, mensagem="Conta criada com sucesso."), 201
        return redirect(url_for("main.novo_funcionario"))
    return render_template("funcionario.html")
