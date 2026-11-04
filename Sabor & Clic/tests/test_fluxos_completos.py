from datetime import datetime, timedelta, timezone

import pytest
from conftest import csrf, login, post_json
from app.models.database import get_db


def futuro(hours=24):
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def test_login_e_cadastro_aceitam_json_sem_recarregar(client):
    response = post_json(
        client,
        "/api/cadastro",
        {
            "nome": "Cliente API",
            "email": "api@teste.com",
            "senha": "TesteSeguro123!",
            "endereco": "Rua Teste, 123",
        },
    )
    assert response.status_code == 201
    response = post_json(
        client, "/api/login", {"email": "api@teste.com", "senha": "TesteSeguro123!"}
    )
    assert response.status_code == 200
    assert response.json["dados"]["perfil"] == "cliente"
    assert response.json["csrf_token"]
    assert client.get("/api/perfil").json["dados"]["endereco"] == "Rua Teste, 123"


def test_perfil_nao_permite_elevar_permissao(client):
    login(client)
    response = post_json(
        client,
        "/api/perfil",
        {"nome": "Cliente Um", "endereco": "Rua Nova, 5", "perfil": "administrador"},
        "PUT",
    )
    assert response.status_code == 400
    assert client.get("/api/perfil").json["dados"]["perfil"] == "cliente"


def test_perfil_atualiza_endereco_e_cook_caracteristicas(client):
    login(client)
    assert (
        post_json(
            client,
            "/api/perfil",
            {"nome": "Nome Atualizado", "endereco": "Rua Nova, 5"},
            "PUT",
        ).status_code
        == 200
    )
    assert client.get("/api/perfil").json["dados"]["endereco"] == "Rua Nova, 5"
    login(client, "cozinha@teste.com")
    assert (
        post_json(
            client,
            "/api/perfil",
            {"nome": "Chef Teste", "turno": "Noite", "especialidade": "Massas"},
            "PUT",
        ).status_code
        == 200
    )
    assert client.get("/api/perfil").json["dados"]["especialidade"] == "Massas"


def test_admin_crud_cardapio_preserva_historico(client, app):
    login(client)
    response = post_json(
        client, "/api/pedidos", {"itens": [{"idPrato": 1, "quantidade": 1}]}
    )
    assert response.status_code == 201
    login(client, "admin@teste.com")
    pratos = client.get("/api/cardapio?todos=1").json["dados"]
    p = next(p for p in pratos if p["id"] == 1)
    response = post_json(
        client,
        "/api/cardapio/1",
        {
            "nome": "Prato Renomeado",
            "preco": 30,
            "descricao": "Nova descrição",
            "estoque": 20,
            "status": "disponivel",
            "versao": p["versao"],
        },
        "PUT",
    )
    assert response.status_code == 200
    p = next(
        p for p in client.get("/api/cardapio?todos=1").json["dados"] if p["id"] == 1
    )
    assert (
        post_json(
            client, "/api/cardapio/1", {"versao": p["versao"]}, "DELETE"
        ).status_code
        == 200
    )
    assert not any(p["id"] == 1 for p in client.get("/api/cardapio").json["dados"])
    login(client)
    history = client.get("/api/pedidos").json["dados"]
    assert history[0]["itens"][0]["nome"] == "Prato A"
    assert history[0]["valor_total"] == 25.5


def test_cardapio_edicao_concorrente_nao_sobrescreve(client):
    login(client, "admin@teste.com")
    data = {
        "nome": "Nome Novo",
        "preco": 25.5,
        "estoque": 10,
        "descricao": "Teste",
        "status": "disponivel",
        "versao": 1,
    }
    assert post_json(client, "/api/cardapio/1", data, "PUT").status_code == 200
    data["nome"] = "Sobrescrita indevida"
    assert post_json(client, "/api/cardapio/1", data, "PUT").status_code == 409


def test_cardapio_todos_restrito_ao_admin(client):
    login(client)
    assert client.get("/api/cardapio?todos=1").status_code == 403


def test_estoque_baixa_pela_trigger_e_bloqueia_falta(client, app):
    login(client)
    with app.app_context():
        db = get_db()
        db.execute("UPDATE pratos SET estoque=2 WHERE id_prato=1")
        db.commit()
    assert (
        post_json(
            client, "/api/pedidos", {"itens": [{"idPrato": 1, "quantidade": 2}]}
        ).status_code
        == 201
    )
    assert (
        post_json(
            client, "/api/pedidos", {"itens": [{"idPrato": 1, "quantidade": 1}]}
        ).status_code
        == 409
    )
    with app.app_context():
        db = get_db()
        assert (
            db.execute("SELECT estoque FROM pratos WHERE id_prato=1").fetchone()[0] == 0
        )
        assert db.execute("SELECT count(*) FROM pedidos").fetchone()[0] == 1


def test_pedido_repetido_com_mesma_chave_nao_baixa_duas_vezes(client, app):
    login(client)
    body = {"itens": [{"idPrato": 1, "quantidade": 1}]}

    def send(data):
        return client.post(
            "/api/pedidos",
            json=data,
            headers={
                "X-CSRFToken": csrf(client, "/"),
                "X-Idempotency-Key": "pedido-teste-123",
            },
        )

    assert send(body).status_code == 201
    result = send(body)
    assert result.status_code == 200 and result.json["reutilizado"] is True
    assert send({"itens": [{"idPrato": 1, "quantidade": 2}]}).status_code == 409
    with app.app_context():
        assert get_db().execute("SELECT count(*) FROM pedidos").fetchone()[0] == 1


def test_cozinheiro_registra_tempo_estimado(client):
    login(client)
    assert (
        post_json(
            client, "/api/pedidos", {"itens": [{"idPrato": 1, "quantidade": 1}]}
        ).status_code
        == 201
    )
    assert (
        post_json(
            client, "/api/pedidos/1/estimativa", {"minutos": 30}, "PUT"
        ).status_code
        == 403
    )
    login(client, "cozinha@teste.com")
    response = post_json(client, "/api/pedidos/1/estimativa", {"minutos": 30}, "PUT")
    assert response.status_code == 200
    assert response.json["dados"]["tempo_estimado_min"] == 30
    assert response.json["dados"]["data_previsao"]


@pytest.mark.parametrize("minutes", [0, -1, 1.5, True, "10", 1441, None])
def test_estimativa_invalida(client, minutes):
    login(client, "cozinha@teste.com")
    assert (
        post_json(
            client, "/api/pedidos/1/estimativa", {"minutos": minutes}, "PUT"
        ).status_code
        == 400
    )


def test_reservas_reais_bloqueiam_sobreposicao_e_isolam_clientes(client, app):
    login(client)
    bancada = client.get("/api/bancadas").json["dados"][0]["id_bancada"]
    start, end = futuro(24), futuro(26)
    response = post_json(
        client, "/api/reservas", {"id_bancada": bancada, "inicio": start, "fim": end}
    )
    assert response.status_code == 201
    reserva_id = response.json["dados"]["id_reserva"]
    login(client, "dois@teste.com")
    assert client.get("/api/reservas").json["dados"] == []
    assert (
        post_json(client, f"/api/reservas/{reserva_id}", {}, "DELETE").status_code
        == 404
    )
    assert (
        post_json(
            client,
            "/api/reservas",
            {"id_bancada": bancada, "inicio": futuro(25), "fim": futuro(27)},
        ).status_code
        == 409
    )
    login(client)
    assert (
        post_json(client, f"/api/reservas/{reserva_id}", {}, "DELETE").status_code
        == 200
    )
    login(client, "dois@teste.com")
    assert (
        post_json(
            client,
            "/api/reservas",
            {"id_bancada": bancada, "inicio": start, "fim": end},
        ).status_code
        == 201
    )


@pytest.mark.parametrize(
    "start,end",
    [
        ("ontem", "amanhã"),
        ("2026-01-01T10:00:00", "2026-01-01T11:00:00"),
        ("2020-01-01T10:00:00Z", "2020-01-01T11:00:00Z"),
        ("2099-01-01T10:00:00Z", "2099-01-01T11:00:00Z"),
    ],
)
def test_reserva_data_invalida(client, start, end):
    login(client)
    assert (
        post_json(
            client, "/api/reservas", {"id_bancada": 1, "inicio": start, "fim": end}
        ).status_code
        == 400
    )


def test_relatorios_somente_admin(client):
    login(client)
    assert client.get("/api/relatorios").status_code == 403
    login(client, "admin@teste.com")
    response = client.get("/api/relatorios")
    assert response.status_code == 200
    assert set(response.json["dados"]) == {"vendas", "estoque", "ocupacao", "totais"}


def test_api_bancadas_criacao_admin(client):
    login(client)
    assert (
        post_json(
            client, "/api/bancadas", {"nome": "Bancada Nova", "localizacao": "Centro"}
        ).status_code
        == 403
    )
    login(client, "admin@teste.com")
    assert (
        post_json(
            client, "/api/bancadas", {"nome": "Bancada Nova", "localizacao": "Centro"}
        ).status_code
        == 201
    )


def test_logout_json_revoga_sessao(client):
    login(client)
    token = client.get_cookie("session").value
    response = post_json(client, "/api/logout", {})
    assert response.status_code == 200 and response.json["csrf_token"]
    client.set_cookie("session", token)
    assert client.get("/api/perfil").status_code == 401


@pytest.mark.parametrize(
    "start,end",
    [
        ("0001-01-01T00:00:00+14:00", "0001-01-01T01:00:00+14:00"),
        ("9999-12-31T23:00:00-14:00", "9999-12-31T23:30:00-14:00"),
    ],
)
def test_reserva_data_extrema_retorna_validacao(client, start, end):
    login(client)
    assert (
        post_json(
            client, "/api/reservas", {"id_bancada": 1, "inicio": start, "fim": end}
        ).status_code
        == 400
    )


def test_pedido_com_versao_desatualizada_nao_grava(client, app):
    login(client)
    response = post_json(
        client,
        "/api/pedidos",
        {"itens": [{"idPrato": 1, "quantidade": 1, "versao": 999}]},
    )
    assert response.status_code == 409
    with app.app_context():
        assert get_db().execute("SELECT count(*) FROM pedidos").fetchone()[0] == 0
        assert (
            get_db()
            .execute("SELECT estoque FROM pratos WHERE id_prato=1")
            .fetchone()[0]
            == 100
        )


@pytest.mark.parametrize("price", [0, 1.001, 1000001])
def test_preco_legado_fora_da_regra_nao_e_vendido(client, app, price):
    login(client)
    with app.app_context():
        db = get_db()
        db.execute("UPDATE pratos SET preco=? WHERE id_prato=1", (price,))
        db.commit()
    response = post_json(
        client, "/api/pedidos", {"itens": [{"idPrato": 1, "quantidade": 1}]}
    )
    assert response.status_code == 409
    with app.app_context():
        assert get_db().execute("SELECT count(*) FROM pedidos").fetchone()[0] == 0
        assert (
            get_db()
            .execute("SELECT estoque FROM pratos WHERE id_prato=1")
            .fetchone()[0]
            == 100
        )
