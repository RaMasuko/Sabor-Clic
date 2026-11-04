import sqlite3

import pytest
from conftest import csrf, login, post_json
from app.models.database import get_db


def test_cadastro_publico_nao_cria_funcionario(client, app):
    response = client.post(
        "/cadastro",
        data={
            "nome": "Intruso",
            "email": "intruso@teste.com",
            "senha": "SenhaSegura123!",
            "tipo": "funcionario",
            "csrf_token": csrf(client),
        },
    )
    assert response.status_code == 400
    with app.app_context():
        assert (
            get_db()
            .execute(
                "SELECT count(*) FROM funcionarios WHERE email='intruso@teste.com'"
            )
            .fetchone()[0]
            == 0
        )


def test_cliente_cadastra_e_entra_com_senha_hash(client, app):
    response = client.post(
        "/cadastro",
        data={
            "nome": "Cliente Novo",
            "email": "novo@teste.com",
            "senha": "TesteSeguro123!",
            "endereco": "Rua de Teste, 123",
            "csrf_token": csrf(client),
        },
    )
    assert response.status_code == 302
    with app.app_context():
        row = (
            get_db()
            .execute("SELECT senha FROM clientes WHERE email='novo@teste.com'")
            .fetchone()
        )
        assert row and row["senha"] != "TesteSeguro123!"
    assert login(client, "novo@teste.com").status_code == 302


@pytest.mark.parametrize(
    "email,expected",
    [("um@teste.com", 403), ("cozinha@teste.com", 403), ("admin@teste.com", 201)],
)
def test_somente_admin_cadastra_prato(client, email, expected):
    login(client, email)
    assert (
        post_json(
            client, "/api/cardapio", {"nome": "Novo", "preco": 15, "descricao": "Teste"}
        ).status_code
        == expected
    )


def test_anonimo_nao_acessa_api_restrita(client):
    assert client.get("/api/pedidos").status_code == 401


def test_cozinheiro_nao_faz_pedido_com_id_de_cliente(client, app):
    login(client, "cozinha@teste.com")
    assert (
        post_json(
            client,
            "/api/pedidos",
            {"itens": [{"idPrato": 1, "quantidade": 1, "subtotal": 1}]},
        ).status_code
        == 403
    )
    with app.app_context():
        assert get_db().execute("SELECT count(*) FROM pedidos").fetchone()[0] == 0


def test_preco_e_recalculado_no_servidor(client, app):
    login(client)
    response = post_json(
        client,
        "/api/pedidos",
        {"itens": [{"idPrato": 1, "quantidade": 2, "subtotal": 0.02}]},
    )
    assert response.status_code == 201
    with app.app_context():
        db = get_db()
        assert db.execute("SELECT valor_total FROM pedidos").fetchone()[0] == 51
        assert (
            db.execute("SELECT preco_unitario FROM itens_pedido").fetchone()[0] == 25.50
        )


@pytest.mark.parametrize(
    "items",
    [
        [],
        None,
        "x",
        [None],
        [{}],
        [{"idPrato": 1, "quantidade": 0, "subtotal": 0}],
        [{"idPrato": 1, "quantidade": -2, "subtotal": -51}],
        [{"idPrato": 1, "quantidade": 1.5, "subtotal": 38.25}],
        [{"idPrato": 1, "quantidade": True, "subtotal": 25.50}],
        [{"idPrato": 999, "quantidade": 1, "subtotal": 1}],
        [{"idPrato": 2, "quantidade": 1, "subtotal": 10.25}],
        [{"idPrato": 1, "quantidade": 1000, "subtotal": 1}],
    ],
)
def test_pedido_invalido_nao_persiste(client, app, items):
    login(client)
    assert post_json(client, "/api/pedidos", {"itens": items}).status_code in (400, 409)
    with app.app_context():
        assert get_db().execute("SELECT count(*) FROM pedidos").fetchone()[0] == 0


def test_pedido_invalido_nao_deixa_insercao_parcial(client, app):
    login(client)
    response = post_json(
        client,
        "/api/pedidos",
        {
            "itens": [
                {"idPrato": 1, "quantidade": 1, "subtotal": 25.50},
                {"idPrato": 999, "quantidade": 1, "subtotal": 1},
            ]
        },
    )
    assert response.status_code in (400, 409)
    with app.app_context():
        assert get_db().execute("SELECT count(*) FROM itens_pedido").fetchone()[0] == 0
        assert get_db().execute("SELECT count(*) FROM pedidos").fetchone()[0] == 0


def test_cliente_ve_apenas_seus_pedidos(client, app):
    login(client)
    assert (
        post_json(
            client, "/api/pedidos", {"itens": [{"idPrato": 1, "quantidade": 1}]}
        ).status_code
        == 201
    )
    assert len(client.get("/api/pedidos").json["dados"]) == 1
    login(client, "dois@teste.com")
    assert client.get("/api/pedidos").json["dados"] == []


@pytest.mark.parametrize(
    "price", ["abc", None, 0, -1, True, "NaN", "Infinity", 1.001, 1000001]
)
def test_preco_invalido_retorna_400(client, price):
    login(client, "admin@teste.com")
    assert (
        post_json(client, "/api/cardapio", {"nome": "Novo", "preco": price}).status_code
        == 400
    )


@pytest.mark.parametrize("data", [None, [], 42, "texto"])
def test_json_estrutura_invalida(client, data):
    login(client)
    token = csrf(client, "/")
    import json

    response = client.post(
        "/api/pedidos",
        data=json.dumps(data),
        content_type="application/json",
        headers={"X-CSRFToken": token},
    )
    assert response.status_code == 400


def test_json_malformado_retorna_json(client):
    login(client)
    response = client.post(
        "/api/pedidos",
        data="{",
        content_type="application/json",
        headers={"X-CSRFToken": csrf(client, "/")},
    )
    assert response.status_code == 400 and response.is_json


def test_csrf_bloqueia_login_sem_token(client):
    assert (
        client.post(
            "/login", data={"email": "um@teste.com", "senha": "TesteSeguro123!"}
        ).status_code
        == 400
    )


def test_csrf_bloqueia_api_sem_token(client, app):
    login(client, "admin@teste.com")
    assert (
        client.post("/api/cardapio", json={"nome": "Novo", "preco": 10}).status_code
        == 400
    )
    with app.app_context():
        assert get_db().execute("SELECT count(*) FROM pratos").fetchone()[0] == 2


def test_csrf_token_de_outro_navegador_nao_funciona(client, app):
    token = csrf(app.test_client())
    assert (
        client.post(
            "/login",
            data={
                "email": "um@teste.com",
                "senha": "TesteSeguro123!",
                "csrf_token": token,
            },
        ).status_code
        == 400
    )


def test_senha_errada_e_injection_nao_entram(client):
    response = client.post(
        "/login",
        data={
            "email": "' OR 1=1 --",
            "senha": "TesteSeguro123!",
            "endereco": "Rua de Teste, 123",
            "csrf_token": csrf(client),
        },
    )
    assert response.status_code == 401
    with client.session_transaction() as s:
        assert "usuario_id" not in s


def test_conta_inativa_nao_entra(client):
    assert login(client, "inativo@teste.com").status_code == 401


def test_sessao_confere_status_atual_no_banco(client, app):
    login(client)
    with app.app_context():
        db = get_db()
        db.execute("UPDATE clientes SET status='inativo' WHERE id_cliente=1")
        db.commit()
    assert client.get("/api/pedidos").status_code == 401


def test_limite_de_tentativas_login(client):
    for _ in range(5):
        response = client.post(
            "/login",
            data={
                "email": "um@teste.com",
                "senha": "errada",
                "csrf_token": csrf(client),
            },
        )
        assert response.status_code == 401
    assert (
        client.post(
            "/login",
            data={
                "email": "um@teste.com",
                "senha": "errada",
                "csrf_token": csrf(client),
            },
        ).status_code
        == 429
    )


def test_logout_revoga_cookie_anterior(client, app):
    login(client)
    stolen = client.get_cookie("session").value
    assert client.get("/logout").status_code == 405
    assert (
        client.post("/logout", data={"csrf_token": csrf(client, "/")}).status_code
        == 302
    )
    replay = app.test_client()
    replay.set_cookie("session", stolen)
    assert replay.get("/api/pedidos").status_code == 401


def test_status_invalido_e_pedido_inexistente(client):
    login(client, "cozinha@teste.com")
    assert (
        post_json(
            client, "/api/pedidos/1/status", {"status": "qualquer"}, "PUT"
        ).status_code
        == 400
    )
    assert (
        post_json(
            client, "/api/pedidos/999/status", {"status": "Iniciando Preparo"}, "PUT"
        ).status_code
        == 404
    )


def test_status_segue_fluxo_e_registra_auditoria(client, app):
    login(client)
    response = post_json(
        client,
        "/api/pedidos",
        {"itens": [{"idPrato": 1, "quantidade": 1, "subtotal": 25.50}]},
    )
    assert response.status_code == 201
    login(client, "cozinha@teste.com")
    assert (
        post_json(
            client, "/api/pedidos/1/status", {"status": "Pronto para Entrega"}, "PUT"
        ).status_code
        == 409
    )
    assert (
        post_json(
            client, "/api/pedidos/1/status", {"status": "Iniciando Preparo"}, "PUT"
        ).status_code
        == 200
    )
    assert (
        post_json(
            client, "/api/pedidos/1/status", {"status": "Pronto para Entrega"}, "PUT"
        ).status_code
        == 200
    )
    with app.app_context():
        assert get_db().execute("SELECT count(*) FROM log_pedidos").fetchone()[0] == 2


def test_admin_inicial_sem_senha_padrao(client, app):
    runner = app.test_cli_runner()
    result = runner.invoke(
        args=[
            "criar-admin",
            "--nome",
            "Admin Novo",
            "--email",
            "novo.admin@teste.com",
            "--cpf",
            "33333333333",
        ],
        input="SenhaSegura123!\nSenhaSegura123!\n",
    )
    assert result.exit_code == 0, result.output
    assert (
        login(client, "novo.admin@teste.com").status_code == 401
    )  # senha diferente da fixture
    response = client.post(
        "/login",
        data={
            "email": "novo.admin@teste.com",
            "senha": "SenhaSegura123!",
            "csrf_token": csrf(client),
        },
    )
    assert response.status_code == 302
    assert (
        post_json(client, "/api/cardapio", {"nome": "Novo", "preco": 12}).status_code
        == 201
    )


def test_csrf_unicode_retorna_400(client):
    csrf(client)
    assert (
        client.post(
            "/login",
            data={"csrf_token": "çã🔒", "email": "um@teste.com", "senha": "errada"},
        ).status_code
        == 400
    )


def test_sessao_expirada_nao_acessa_pedidos(client, app):
    login(client)
    with app.app_context():
        db = get_db()
        db.execute("UPDATE auth_sessions SET expira_em=0")
        db.commit()
    assert client.get("/api/pedidos").status_code == 401


def test_sessao_reflete_rebaixamento_de_perfil(client, app):
    login(client, "admin@teste.com")
    with app.app_context():
        db = get_db()
        db.execute("UPDATE funcionarios SET perfil='cozinheiro' WHERE id_funcionario=1")
        db.commit()
    assert (
        post_json(client, "/api/cardapio", {"nome": "Novo", "preco": 10}).status_code
        == 403
    )


@pytest.mark.parametrize("email", ["um@teste.com", "cozinha@teste.com"])
def test_somente_admin_cria_contas_da_equipe(client, email):
    login(client, email)
    assert (
        client.post(
            "/funcionarios/novo",
            data={
                "nome": "Equipe Nova",
                "email": "equipe@teste.com",
                "cpf": "44444444444",
                "senha": "TesteSeguro123!",
                "perfil": "administrador",
                "csrf_token": csrf(client, "/"),
            },
        ).status_code
        == 403
    )


def test_admin_cria_cozinheiro_sem_permissao_de_admin(client):
    login(client, "admin@teste.com")
    response = client.post(
        "/funcionarios/novo",
        data={
            "nome": "Equipe Nova",
            "email": "equipe@teste.com",
            "cpf": "44444444444",
            "senha": "TesteSeguro123!",
            "perfil": "cozinheiro",
            "turno": "Noite",
            "especialidade": "Massas",
            "csrf_token": csrf(client, "/"),
        },
    )
    assert response.status_code == 302
    login(client, "equipe@teste.com")
    assert client.get("/kds").status_code == 200
    assert (
        post_json(client, "/api/cardapio", {"nome": "Novo", "preco": 10}).status_code
        == 403
    )


def test_cadastro_nao_reutiliza_email_de_funcionario(client, app):
    response = client.post(
        "/cadastro",
        data={
            "nome": "Nome Teste",
            "email": "ADMIN@TESTE.COM",
            "senha": "TesteSeguro123!",
            "endereco": "Rua de Teste, 123",
            "csrf_token": csrf(client),
        },
    )
    assert response.status_code == 400
    with app.app_context():
        assert (
            get_db()
            .execute(
                "SELECT count(*) FROM clientes WHERE email='admin@teste.com' COLLATE NOCASE"
            )
            .fetchone()[0]
            == 0
        )


def test_cliente_nao_muda_status(client, app):
    login(client)
    assert (
        post_json(
            client, "/api/pedidos", {"itens": [{"idPrato": 1, "quantidade": 1}]}
        ).status_code
        == 201
    )
    assert (
        post_json(
            client, "/api/pedidos/1/status", {"status": "Iniciando Preparo"}, "PUT"
        ).status_code
        == 403
    )
    with app.app_context():
        assert (
            get_db().execute("SELECT status FROM pedidos").fetchone()[0] == "Aguardando"
        )


def test_chave_antiga_nao_assina_nova_sessao(client, app):
    from flask.sessions import SecureCookieSessionInterface
    from flask import Flask

    old = Flask("old")
    old.secret_key = "sabor_clic_secret_key_projeto_integrador"
    cookie = (
        SecureCookieSessionInterface()
        .get_signing_serializer(old)
        .dumps({"usuario_id": 1, "tipo": "funcionario"})
    )
    client.set_cookie("session", cookie)
    assert client.get("/api/pedidos").status_code == 401


def test_falha_interna_nao_expoe_sql(client, app):
    login(client, "admin@teste.com")
    with app.app_context():
        db = get_db()
        db.execute("DROP TABLE pratos")
        db.commit()
    response = post_json(client, "/api/cardapio", {"nome": "Novo", "preco": 10})
    assert response.status_code == 500
    assert "no such table" not in response.get_data(as_text=True)
    assert response.json["sucesso"] is False


def test_banco_exige_chave_estrangeira(app):
    with app.app_context():
        with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
            get_db().execute(
                "INSERT INTO pedidos (id_cliente,data_pedido,valor_total) VALUES (9999,'2026-11-03',1)"
            )


def test_cookie_e_cabecalhos_de_seguranca(client):
    response = client.get("/login")
    assert "HttpOnly" in response.headers["Set-Cookie"]
    assert "SameSite=Lax" in response.headers["Set-Cookie"]
    assert response.headers["Cache-Control"] == "no-store"
    assert "script-src 'self'" in response.headers["Content-Security-Policy"]


def test_senha_fraca_nao_cadastra(client, app):
    assert (
        client.post(
            "/cadastro",
            data={
                "nome": "Cliente Novo",
                "email": "fraco@teste.com",
                "senha": "123456",
                "csrf_token": csrf(client),
            },
        ).status_code
        == 400
    )
    with app.app_context():
        assert (
            get_db()
            .execute("SELECT count(*) FROM clientes WHERE email='fraco@teste.com'")
            .fetchone()[0]
            == 0
        )


def test_terminal_reativa_cozinheiro_revisado_sem_promover(client, app):
    with app.app_context():
        db = get_db()
        db.execute(
            "UPDATE funcionarios SET status='inativo' WHERE email='cozinha@teste.com'"
        )
        db.commit()
    assert login(client, "cozinha@teste.com").status_code == 401
    result = app.test_cli_runner().invoke(
        args=["ativar-funcionario", "--email", "cozinha@teste.com"], input="y\n"
    )
    assert result.exit_code == 0, result.output
    assert login(client, "cozinha@teste.com").status_code == 302
    assert client.get("/kds").status_code == 200
    assert (
        post_json(client, "/api/cardapio", {"nome": "Novo", "preco": 10}).status_code
        == 403
    )
