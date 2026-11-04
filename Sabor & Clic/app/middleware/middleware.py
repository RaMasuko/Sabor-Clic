"""Autenticação, autorização, CSRF e cabeçalhos comuns às rotas."""

import hashlib
import secrets
import time
from functools import wraps

from flask import abort, current_app, g, redirect, request, session, url_for

from ..models.database import get_db


def csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_urlsafe(32)
    return session["_csrf_token"]


def revoke_session():
    token = session.get("auth_sid")
    if isinstance(token, str):
        db = get_db()
        db.execute(
            "DELETE FROM auth_sessions WHERE token_hash = ?",
            (hashlib.sha256(token.encode()).hexdigest(),),
        )
        db.commit()
    session.clear()


def start_session(user, tipo):
    revoke_session()
    token = secrets.token_urlsafe(32)
    now = int(time.time())
    user_id = user["id_cliente"] if tipo == "cliente" else user["id_funcionario"]
    db = get_db()
    db.execute("DELETE FROM auth_sessions WHERE expira_em <= ?", (now,))
    db.execute(
        "INSERT INTO auth_sessions VALUES (?, ?, ?, ?, ?)",
        (
            hashlib.sha256(token.encode()).hexdigest(),
            tipo,
            user_id,
            now,
            now + int(current_app.permanent_session_lifetime.total_seconds()),
        ),
    )
    db.commit()
    session.permanent = True
    session.update(auth_sid=token, usuario_id=user_id, tipo=tipo)
    csrf_token()


def _load_user():
    g.usuario = None
    token = session.get("auth_sid")
    if not isinstance(token, str):
        if "usuario_id" in session:
            session.clear()
        return
    db = get_db()
    auth = db.execute(
        "SELECT * FROM auth_sessions WHERE token_hash = ? AND expira_em > ?",
        (hashlib.sha256(token.encode()).hexdigest(), int(time.time())),
    ).fetchone()
    if (
        not auth
        or auth["tipo"] != session.get("tipo")
        or auth["usuario_id"] != session.get("usuario_id")
    ):
        revoke_session()
        return
    if auth["tipo"] == "cliente":
        row = db.execute(
            "SELECT id_cliente AS id, nome, email, status, endereco FROM clientes WHERE id_cliente = ?",
            (auth["usuario_id"],),
        ).fetchone()
        role = "cliente"
        cargo = "Cliente"
    elif auth["tipo"] == "funcionario":
        row = db.execute(
            "SELECT id_funcionario AS id, nome, email, status, perfil, cargo, turno, especialidade FROM funcionarios WHERE id_funcionario = ?",
            (auth["usuario_id"],),
        ).fetchone()
        role = row["perfil"] if row else None
        cargo = row["cargo"] if row else ""
    else:
        row = None
        role = None
    if (
        not row
        or row["status"] != "ativo"
        or role not in ("cliente", "cozinheiro", "administrador")
    ):
        revoke_session()
        return
    g.usuario = dict(row)
    g.usuario.update(perfil=role, cargo=cargo, tipo=auth["tipo"])


def requer_perfis(*perfis):
    def decorator(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            if g.usuario is None:
                if request.path.startswith("/api/"):
                    abort(401, description="Faça login para continuar.")
                return redirect(url_for("main.login"))
            if perfis and g.usuario["perfil"] not in perfis:
                abort(
                    403, description="Seu perfil não tem permissão para esta operação."
                )
            return function(*args, **kwargs)

        return wrapped

    return decorator


def init_security(app):
    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.context_processor
    def usuario_context():
        return {"usuario_atual": getattr(g, "usuario", None)}

    @app.before_request
    def security_checks():
        if request.endpoint == "static":
            return
        if app.config["PRODUCTION"] and not request.is_secure:
            abort(400, description="Use HTTPS para acessar este ambiente.")
        _load_user()
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            provided = request.headers.get("X-CSRFToken") or request.form.get(
                "csrf_token"
            )
            expected = session.get("_csrf_token")
            if (
                not isinstance(provided, str)
                or not isinstance(expected, str)
                or not secrets.compare_digest(
                    provided.encode("utf-8"), expected.encode("utf-8")
                )
            ):
                abort(
                    400,
                    description="Token de segurança inválido ou expirado. Atualize a página.",
                )

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
            "base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
        )
        if request.endpoint != "static":
            response.headers["Cache-Control"] = "no-store"
        if app.config["PRODUCTION"] and request.is_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response
