import os
import secrets
import sqlite3
from datetime import timedelta
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from .models.database import close_db, init_db


def _local_secret(directory):
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = directory / "secret_key"
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        value = path.read_text(encoding="utf-8").strip()
        if len(value) < 32:
            raise RuntimeError("Chave local inválida. Configure SABOR_SECRET_KEY.")
        return value
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        value = secrets.token_hex(32)
        stream.write(value)
    return value


def create_app(test_config=None):
    root = Path(__file__).resolve().parents[1]
    app = Flask(__name__, instance_path=str(root / "instance"))
    production = os.environ.get("SABOR_ENV") == "production"
    app.config.from_mapping(
        DATABASE=os.environ.get("SABOR_DATABASE", str(root / "sabor_clic.db")),
        SECRET_KEY=os.environ.get("SABOR_SECRET_KEY"),
        PRODUCTION=production,
        DEBUG=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=production,
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
        SESSION_REFRESH_EACH_REQUEST=False,
        MAX_CONTENT_LENGTH=64 * 1024,
        MAX_FORM_MEMORY_SIZE=64 * 1024,
        MAX_FORM_PARTS=20,
    )
    if test_config:
        app.config.update(test_config)
    if not app.config["SECRET_KEY"]:
        if production:
            raise RuntimeError(
                "Produção exige SABOR_SECRET_KEY aleatória com ao menos 32 caracteres."
            )
        app.config["SECRET_KEY"] = _local_secret(Path(app.instance_path))
    if len(app.config["SECRET_KEY"]) < 32:
        raise RuntimeError("A chave de sessão deve ter pelo menos 32 caracteres.")

    app.teardown_appcontext(close_db)
    init_db(app)
    from .middleware.middleware import init_security
    from .controllers.main_controller import main_bp
    from .controllers.cardapio_controller import cardapio_bp
    from .controllers.pedidos_controller import pedidos_bp
    from .commands import register_commands
    from .controllers.reservas_controller import reservas_bp
    from .models.errors import DomainError

    init_security(app)
    app.register_blueprint(main_bp)
    app.register_blueprint(cardapio_bp)
    app.register_blueprint(pedidos_bp)
    app.register_blueprint(reservas_bp)
    register_commands(app)

    @app.errorhandler(DomainError)
    def domain_error(error):
        if request.path.startswith("/api/"):
            response = jsonify(sucesso=False, mensagem=str(error), erro=str(error))
        else:
            response = app.make_response(
                render_template("erro.html", mensagem=str(error), codigo=error.status)
            )
        response.status_code = error.status
        if error.status == 429:
            response.headers["Retry-After"] = "900"
        return response

    @app.errorhandler(HTTPException)
    def http_error(error):
        message = (
            error.description
            if error.code in (400, 401, 403, 404, 409, 429)
            else {
                405: "Método não permitido.",
                413: "Requisição muito grande.",
                415: "Envie dados no formato JSON.",
            }.get(error.code, "Não foi possível processar a solicitação.")
        )
        if request.path.startswith("/api/"):
            response = jsonify(sucesso=False, mensagem=message, erro=message)
        else:
            response = app.make_response(
                render_template("erro.html", mensagem=message, codigo=error.code)
            )
        response.status_code = error.code
        if error.code == 429:
            response.headers["Retry-After"] = "900"
        return response

    @app.errorhandler(Exception)
    def unexpected_error(error):
        try:
            from .models.database import get_db

            get_db().rollback()
        except sqlite3.Error:
            pass
        app.logger.exception("Falha interna ao processar requisição")
        message = "Não foi possível concluir a operação. Tente novamente."
        if request.path.startswith("/api/"):
            return jsonify(sucesso=False, mensagem=message, erro=message), 500
        return render_template("erro.html", mensagem=message, codigo=500), 500

    return app
